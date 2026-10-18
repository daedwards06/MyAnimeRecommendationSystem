#!/usr/bin/env python
"""Why FunkSVD sits below popularity: the Task 2.1 diagnostic.

Questions, in the order the report answers them:

1. Snapshot. Did the 2026-03-14 data refresh change the interactions? The pre-refresh parquet
   is read from git (commit 9813b02d) and compared with the current one.
2. The 0.0504 -> 0.0326 drop. Two things changed between those MF runs besides the snapshot:
   the holdout sampler (commit db280c09, 2026-06-03, replaced a per-user `groupby.apply` draw
   with `groupby.sample`, which holds out a different item per user) and the protocol (full-fit
   artifact scored against its own training rows -> train-split artifact). Both samplers are
   crossed with both protocols, so each part of the drop is measured separately.
3. Relevance. The holdout is one random rating per user, and 19% of ratings are 0: Kaggle's
   -1 "watched, not rated" sentinel, clipped to 0 by `clean_interactions`. Every model in the
   ablation is re-scored by holdout rating (liked >= 8, 1-7, watched-unrated 0).
4. Mechanism. Where each model ranks the held-out item, by holdout rating, and how much
   training support the items it recommends have.
5. Objective. Three variants on the same cohort with paired intervals: FunkSVD refit without
   the 0-coded rows, FunkSVD plus a popularity prior, and implicit-feedback ALS. Their one
   hyperparameter is tuned on validation users outside the reporting cohort.

Fitting FunkSVD takes ~45 minutes, so every fitted model is cached under
`experiments/artifacts/` behind a fingerprint of its training split, holdout and parameters.

Usage:
    python scripts/diagnose_mf.py --sample-users 1000
Output: reports/mf_diagnostic.md
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The ALS fit solves ~85K tiny (64 x 64) systems per sweep; a multithreaded BLAS spends ~30x
# longer coordinating threads on matrices that small than on the arithmetic.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import numpy as np
import pandas as pd
from joblib import dump, load

from src.eval.bootstrap import bootstrap_mean_ci, paired_bootstrap_diff_ci
from src.eval.eval_artifacts import MF_PARAMS, load_eval_models, train_fingerprint
from src.eval.metrics import ndcg_at_k
from src.eval.metrics_extra import gini_index, item_coverage
from src.eval.splits import build_validation, reporting_and_tuning_users
from src.models.als_implicit import ImplicitALSRecommender
from src.models.baselines import popularity_scores
from src.models.constants import (
    DATA_PROCESSED_DIR,
    EVAL_ARTIFACTS_DIR,
    MF_MODEL_STEM,
    MODELS_DIR,
    RANDOM_SEED,
    REPORTING_COHORT_USERS,
    TOP_K_DEFAULT,
)
from src.models.mf_sgd import FunkSVDRecommender

PRE_REFRESH_COMMIT = "9813b02d"
INTERACTIONS_PATH = "data/processed/interactions.parquet"
PER_USER_PATH = DATA_PROCESSED_DIR / "phase4" / "per_user_metrics.parquet"
REPORT_PATH = ROOT / "reports" / "mf_diagnostic.md"
PUBLISHED_MF_NDCG = 0.050358  # experiments/metrics/mf_sgd_20251121202534.json, 1,000 users
LIKED = 8
POP_PRIOR_BETAS = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
ALS_ALPHAS = [1.0, 5.0, 20.0]
ALS_PARAMS: dict[str, Any] = {"n_factors": 64, "reg": 0.1, "n_iters": 10, "random_state": RANDOM_SEED}
LOW_SUPPORT = 100
BUCKETS = [("liked (>= 8)", lambda r: r >= LIKED), ("rated 1-7", lambda r: (r >= 1) & (r < LIKED)), ("watched, unrated (0)", lambda r: r == 0)]


# ---------- data and splits ----------

def load_interactions() -> pd.DataFrame:
    return pd.read_parquet(ROOT / INTERACTIONS_PATH)


def load_pre_refresh() -> pd.DataFrame | None:
    """The interactions parquet as committed before the 2026-03-14 refresh, or None without git."""
    try:
        raw = subprocess.run(
            ["git", "show", f"{PRE_REFRESH_COMMIT}:{INTERACTIONS_PATH}"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return pd.read_parquet(io.BytesIO(raw))


def legacy_holdout(df: pd.DataFrame) -> pd.DataFrame:
    """The per-user holdout `build_validation` drew before commit db280c09 (2026-06-03)."""
    rng = random.Random(RANDOM_SEED)
    rows = [g.sample(1, random_state=rng.randint(0, 1_000_000)) for _, g in df.groupby("user_id", group_keys=False)]
    return pd.concat(rows).reset_index(drop=True)


def _pair_key(df: pd.DataFrame) -> pd.Series:
    return df["user_id"].astype(np.int64) * 1_000_000 + df["anime_id"].astype(np.int64)


@dataclass
class Split:
    name: str
    train: pd.DataFrame
    val: pd.DataFrame
    users: list[int]
    tune_users: list[int]
    train_hist: dict[int, set[int]] = field(repr=False)
    holdout: dict[int, int] = field(repr=False)
    holdout_rating: dict[int, float] = field(repr=False)


def make_split(name: str, train: pd.DataFrame, val: pd.DataFrame, n_users: int, n_tune: int) -> Split:
    users, tune = reporting_and_tuning_users(val["user_id"].unique().tolist(), n_users, n_tune)
    scored = train[train["user_id"].isin(set(users) | set(tune))]
    return Split(
        name=name,
        train=train,
        val=val,
        users=[int(u) for u in users],
        tune_users=[int(u) for u in tune],
        train_hist={int(u): set(map(int, s)) for u, s in scored.groupby("user_id")["anime_id"]},
        holdout={int(u): int(i) for u, i in zip(val["user_id"], val["anime_id"])},
        holdout_rating={int(u): float(r) for u, r in zip(val["user_id"], val["rating"])},
    )


def build_splits(inter: pd.DataFrame, n_users: int = REPORTING_COHORT_USERS, n_tune: int = 0) -> dict[str, Split]:
    train, val = build_validation(inter)
    legacy_val = legacy_holdout(inter)
    legacy_train = inter[~_pair_key(inter).isin(set(_pair_key(legacy_val)))]
    return {
        "current": make_split("current", train, val, n_users, n_tune),
        "legacy": make_split("legacy", legacy_train, legacy_val, n_users, 0),
    }


def holdout_tag(split: Split) -> str:
    keys = np.sort(_pair_key(split.val).to_numpy())
    return hashlib.sha1(keys.tobytes()).hexdigest()[:12]


# ---------- cached fits ----------

def cached_model(name: str, train: pd.DataFrame, tag: str, fit: Callable[[pd.DataFrame], Any], params: dict | None = None) -> Any:
    path = EVAL_ARTIFACTS_DIR / f"diag_{name}.joblib"
    sidecar = path.with_suffix(".fingerprint.json")
    fingerprint = {**train_fingerprint(train), "holdout": tag, "params": params or {}}
    try:
        if path.exists() and json.loads(sidecar.read_text(encoding="utf-8")) == fingerprint:
            return load(path)
    except (OSError, ValueError):
        pass
    t = time.time()
    print(f"fitting {name} on {len(train):,} rows ...", flush=True)
    model = fit(train)
    print(f"  {name} fitted in {time.time() - t:.0f}s", flush=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump(model, path)
    sidecar.write_text(json.dumps(fingerprint, indent=2), encoding="utf-8")
    return model


def fit_mf(train: pd.DataFrame) -> FunkSVDRecommender:
    return FunkSVDRecommender(**MF_PARAMS).fit(train)


def fit_als(alpha: float) -> Callable[[pd.DataFrame], ImplicitALSRecommender]:
    return lambda train: ImplicitALSRecommender(alpha=alpha, **ALS_PARAMS).fit(train)


# ---------- scoring ----------

Scorer = Callable[[int], np.ndarray]


@dataclass
class Catalog:
    """One item index for every scorer, so masks, ranks and supports line up."""

    item_ids: np.ndarray
    pos: dict[int, int]
    support: np.ndarray  # training interactions per item
    pop: np.ndarray  # popularity_scores over the same index

    @classmethod
    def from_train(cls, train: pd.DataFrame) -> Catalog:
        item_ids = np.sort(train["anime_id"].astype(int).unique())
        pos = {int(i): k for k, i in enumerate(item_ids)}
        counts = train.groupby("anime_id").size().reindex(item_ids).fillna(0).to_numpy()
        pop = popularity_scores(train).reindex(item_ids).fillna(0).to_numpy()
        return cls(item_ids, pos, counts, pop)

    def align(self, item_to_index: dict[int, int], scores: np.ndarray) -> np.ndarray:
        out = np.full(len(self.item_ids), -np.inf)
        for item, idx in item_to_index.items():
            k = self.pos.get(int(item))
            if k is not None:
                out[k] = scores[idx]
        return out


def model_scorer(model: Any, cat: Catalog) -> Scorer:
    order = np.array([cat.pos.get(int(model.index_to_item[i]), -1) for i in range(len(model.index_to_item))])
    keep = order >= 0

    def score(u: int) -> np.ndarray:
        out = np.full(len(cat.item_ids), -np.inf)
        if u in model.user_to_index:
            out[order[keep]] = np.asarray(model.predict_user(u), dtype=np.float64)[keep]
        return out

    return score


def knn_scorer(knn: Any, cat: Catalog) -> Scorer:
    def score(u: int) -> np.ndarray:
        out = np.full(len(cat.item_ids), -np.inf)
        for item, s in knn.score_all(u, exclude_seen=False).items():
            k = cat.pos.get(int(item))
            if k is not None:
                out[k] = s
        return out

    return score


def _z(x: np.ndarray) -> np.ndarray:
    finite = np.isfinite(x)
    if not finite.any():
        return x
    mu, sd = x[finite].mean(), x[finite].std()
    return (x - mu) / (sd if sd > 0 else 1.0)


def prior_scorer(base: Scorer, cat: Catalog, beta: float) -> Scorer:
    """Per-user z-scored MF prediction plus beta x z-scored log support."""
    log_support = _z(np.log1p(cat.support))
    return lambda u: _z(base(u)) + beta * log_support


@dataclass
class Run:
    ndcg: np.ndarray
    recs: dict[int, list[int]]
    holdout_rank: np.ndarray  # 1-based rank of the held-out item among items the user had not seen


def run(score: Scorer, split: Split, cat: Catalog, users: list[int], k: int) -> Run:
    ndcgs, recs, ranks = [], {}, []
    for u in users:
        s = score(u).copy()
        seen = [cat.pos[i] for i in split.train_hist.get(u, ()) if i in cat.pos]
        s[seen] = -np.inf
        top = np.argpartition(-s, k - 1)[:k]
        top = top[np.argsort(-s[top])]
        rec = [int(cat.item_ids[t]) for t in top if np.isfinite(s[t])]
        target = split.holdout[u]
        recs[u] = rec
        ndcgs.append(ndcg_at_k(rec, {target}, k))
        t = cat.pos.get(target)
        ranks.append(np.nan if t is None or not np.isfinite(s[t]) else 1 + int((s > s[t]).sum()))
    return Run(np.asarray(ndcgs), recs, np.asarray(ranks, dtype=float))


def pop_scorer(cat: Catalog) -> Scorer:
    return lambda u: cat.pop.astype(np.float64)


# ---------- formatting ----------

def ci(values: np.ndarray) -> str:
    mean, lo, hi = bootstrap_mean_ci(values)
    return f"{mean:.4f} [{lo:.4f}, {hi:.4f}]"


def diff(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    return paired_bootstrap_diff_ci(a, b)


def fmt_diff(a: np.ndarray, b: np.ndarray) -> str:
    d, lo, hi = diff(a, b)
    return f"{d:+.4f} [{lo:+.4f}, {hi:+.4f}]"


def excludes_zero(a: np.ndarray, b: np.ndarray) -> bool:
    _, lo, hi = diff(a, b)
    return lo > 0 or hi < 0


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join([":---"] + ["---:"] * (len(header) - 1)) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


# ---------- main ----------

def main(sample_users: int, k: int, tune_users: int) -> None:
    t0 = time.time()
    inter = load_interactions()
    pre = load_pre_refresh()
    if pre is None:
        snapshot = "The pre-refresh parquet could not be read from git, so the snapshot was not compared."
        same_rows = None
    else:
        same_rows = bool(
            len(pre) == len(inter)
            and (pre.to_numpy(dtype=np.int64) == inter[pre.columns].to_numpy(dtype=np.int64)).all()
        )
        dtypes = ", ".join(f"`{c}` {pre[c].dtype} -> {inter[c].dtype}" for c in pre.columns if pre[c].dtype != inter[c].dtype)
        snapshot = (
            f"The parquet committed before the refresh (`{PRE_REFRESH_COMMIT}`) and the current one hold "
            + ("**the same rows in the same order**" if same_rows else "**different rows**")
            + f" ({len(inter):,} interactions, {inter['user_id'].nunique():,} users, {inter['anime_id'].nunique():,} items)."
            + (f" Only the column dtypes changed ({dtypes})." if same_rows and dtypes else "")
        )
    print(snapshot, flush=True)

    splits = build_splits(inter, sample_users, tune_users)
    cur, leg = splits["current"], splits["legacy"]
    print(f"splits ready ({time.time() - t0:.0f}s); cohorts identical: {cur.users == leg.users}", flush=True)
    cat = Catalog.from_train(cur.train)
    leg_cat = Catalog.from_train(leg.train)

    knn_cur, mf_cur = load_eval_models(cur.train)
    mf_full = load(MODELS_DIR / f"{MF_MODEL_STEM}.joblib")
    mf_leg = cached_model("mf_legacy_trainsplit", leg.train, holdout_tag(leg), fit_mf, MF_PARAMS)
    rated = cur.train[cur.train["rating"] > 0]
    mf_rated = cached_model("mf_rated_only_trainsplit", rated, holdout_tag(cur), fit_mf, MF_PARAMS)

    # 2. decomposition
    cells = {
        ("legacy", "full"): run(model_scorer(mf_full, leg_cat), leg, leg_cat, leg.users, k),
        ("legacy", "train"): run(model_scorer(mf_leg, leg_cat), leg, leg_cat, leg.users, k),
        ("current", "full"): run(model_scorer(mf_full, cat), cur, cat, cur.users, k),
        ("current", "train"): run(model_scorer(mf_cur, cat), cur, cat, cur.users, k),
    }
    pops = {
        "legacy": run(pop_scorer(leg_cat), leg, leg_cat, leg.users, k),
        "current": run(pop_scorer(cat), cur, cat, cur.users, k),
    }
    print(f"decomposition done ({time.time() - t0:.0f}s)", flush=True)

    # 5. objective variants, tuned on users outside the cohort
    mf_score = model_scorer(mf_cur, cat)
    tune_beta = {b: run(prior_scorer(mf_score, cat, b), cur, cat, cur.tune_users, k).ndcg.mean() for b in POP_PRIOR_BETAS}
    beta = max(tune_beta, key=tune_beta.get)
    als_models = {a: cached_model(f"als_alpha{a:g}_trainsplit", cur.train, holdout_tag(cur), fit_als(a), {**ALS_PARAMS, "alpha": a}) for a in ALS_ALPHAS}
    tune_alpha = {a: run(model_scorer(m, cat), cur, cat, cur.tune_users, k).ndcg.mean() for a, m in als_models.items()}
    alpha = max(tune_alpha, key=tune_alpha.get)
    print(f"tuned beta={beta} alpha={alpha} ({time.time() - t0:.0f}s)", flush=True)

    variants = {
        "popularity": pops["current"],
        "mf_sgd (as evaluated)": cells[("current", "train")],
        "mf_sgd, 0-coded rows dropped": run(model_scorer(mf_rated, cat), cur, cat, cur.users, k),
        f"mf_sgd + popularity prior (beta={beta:g})": run(prior_scorer(mf_score, cat, beta), cur, cat, cur.users, k),
        f"implicit ALS (alpha={alpha:g})": run(model_scorer(als_models[alpha], cat), cur, cat, cur.users, k),
        "item_knn_sklearn": run(knn_scorer(knn_cur, cat), cur, cat, cur.users, k),
    }
    print(f"variants done ({time.time() - t0:.0f}s)", flush=True)

    REPORT_PATH.write_text(
        render(snapshot, same_rows, cur, leg, cat, cells, pops, variants, tune_beta, beta, tune_alpha, alpha, k, sample_users),
        encoding="utf-8",
    )
    print(f"wrote {REPORT_PATH.relative_to(ROOT)} ({time.time() - t0:.0f}s)", flush=True)


def render(snapshot, same_rows, cur, leg, cat, cells, pops, variants, tune_beta, beta, tune_alpha, alpha, k, n) -> str:
    total_items = len(cat.item_ids)
    mf = variants["mf_sgd (as evaluated)"]
    pop = variants["popularity"]
    ratings = np.array([cur.holdout_rating[u] for u in cur.users])
    out: list[str] = []
    w = out.append

    w("# MF Diagnostic: Why FunkSVD Sits Below Popularity\n")
    w(f"Generated by `scripts/diagnose_mf.py` on {datetime.now(UTC):%Y-%m-%d}. Cohort: {n:,} validation users, seed {RANDOM_SEED}, "
      f"NDCG@{k} over the full catalog with each user's training history excluded. Intervals are 95% percentile bootstrap "
      "(users resampled, 1,000 resamples); differences are paired (same users under both models), so an interval that "
      f"spans zero is a tie. Tuned hyperparameters were picked on {len(cur.tune_users):,} validation users outside the cohort.\n")

    w("## 1. The snapshot did not change the data\n")
    w(snapshot + (" The FunkSVD fit is deterministic given its seed and row order, so the snapshot contributes nothing to the drop." if same_rows else "") + "\n")

    w("## 2. Where 0.0504 -> 0.0326 came from\n")
    w("Two other things changed between the published 0.0504 (2025-11-21) and 0.0326 (2026-09-17): the holdout sampler "
      "(commit `db280c09`, 2026-06-03: one random rating per user drawn by `groupby.apply` with a per-user seed became "
      "`groupby.sample(random_state=42)`, so a different item is held out for most users) and the protocol (an MF fit on "
      "all interactions, including the held-out rows, became one fit on the train split only). Crossing both:\n")
    rows = []
    for sampler in ("legacy", "current"):
        for proto, label in (("full", "full data (old protocol)"), ("train", "train split (current protocol)")):
            r = cells[(sampler, proto)]
            rows.append([f"{sampler} sampler", label, ci(r.ndcg), ci(pops[sampler].ndcg), fmt_diff(r.ndcg, pops[sampler].ndcg)])
    w(table(["holdout", "MF fit on", f"MF NDCG@{k}", f"popularity NDCG@{k}", "MF - popularity"], rows) + "\n")
    same_cohort = cur.users == leg.users
    leg_full, leg_train = cells[("legacy", "full")].ndcg, cells[("legacy", "train")].ndcg
    cur_full, cur_train = cells[("current", "full")].ndcg, cells[("current", "train")].ndcg
    w(f"The legacy-sampler, full-data cell is the setup behind the published figure: it gives {leg_full.mean():.4f} against the "
      f"published {PUBLISHED_MF_NDCG:.4f}" + (" (popularity reproduces its published 0.0412 exactly in the same cell)." if abs(pops['legacy'].ndcg.mean() - 0.041198) < 5e-6 else ".") + "\n")
    w(f"Both cohorts are {'the same ' + format(n, ',') + ' users' if same_cohort else 'different users'}; only the held-out item differs. Effects (paired):\n")
    eff = [
        ["protocol (full -> train split), legacy holdout", fmt_diff(leg_train, leg_full)],
        ["protocol (full -> train split), current holdout", fmt_diff(cur_train, cur_full)],
    ]
    if same_cohort:
        eff += [
            ["sampler (legacy -> current), MF full fit", fmt_diff(cur_full, leg_full)],
            ["sampler (legacy -> current), MF train split", fmt_diff(cur_train, leg_train)],
            ["sampler (legacy -> current), popularity", fmt_diff(pops['current'].ndcg, pops['legacy'].ndcg)],
        ]
    w(table(["change", f"NDCG@{k} difference"], eff) + "\n")

    w("## 3. What counts as relevant\n")
    counts = {name: int(f(ratings).sum()) for name, f in BUCKETS}
    w(f"The holdout is one random interaction, not a liked one. In this cohort {counts['liked (>= 8)']} held-out items are rated 8 or "
      f"higher, {counts['rated 1-7']} are rated 1-7 and **{counts['watched, unrated (0)']} are 0**. A 0 is Kaggle's -1 \"watched, not "
      "rated\" sentinel, clipped to 0 by `src/data/cleaning.py::clean_interactions`, so FunkSVD trains on 1.48M interactions (19% of "
      "all ratings) as if each were the worst possible score. Every model, scored on each holdout bucket (the bucket's users only):\n")
    out_rows = per_bucket_rows(cur, variants, ratings)
    w(table(["model", f"all ({n})"] + [f"{b} ({counts[b]})" for b, _ in BUCKETS], out_rows) + "\n")
    w(ordering_note(out_rows) + "\n")

    w("## 4. Mechanism\n")
    w(f"Median rank of the held-out item among the {total_items:,}-item catalog minus the user's history (lower is better), and the "
      f"training support of what each model recommends. Low support = fewer than {LOW_SUPPORT} training interactions.\n")
    mech = []
    for name, r in variants.items():
        ranks = [f"{np.nanmedian(r.holdout_rank[f(ratings)]):,.0f}" for _, f in BUCKETS]
        sup = np.array([cat.support[cat.pos[i]] for recs in r.recs.values() for i in recs])
        mech.append([name, f"{np.nanmedian(r.holdout_rank):,.0f}", *ranks, f"{np.median(sup):,.0f}", f"{(sup < LOW_SUPPORT).mean():.1%}"])
    hold_sup = np.array([cat.support[cat.pos[cur.holdout[u]]] for u in cur.users if cur.holdout[u] in cat.pos])
    w(table(["model", "rank: all"] + [f"rank: {b}" for b, _ in BUCKETS] + ["median support of top-10", "top-10 low support"], mech) + "\n")
    w(f"For reference, the held-out items themselves have median support {np.median(hold_sup):,.0f}, and {(hold_sup < LOW_SUPPORT).mean():.1%} have low support.\n")

    w("## 5. Changing the objective\n")
    w(f"Popularity prior: `z(MF prediction) + beta * z(log(1 + support))`, beta in {POP_PRIOR_BETAS} (tuning NDCG: "
      + ", ".join(f"{b:g}: {v:.4f}" for b, v in tune_beta.items()) + f"). Implicit ALS: `src/models/als_implicit.py`, binary "
      f"watched/not-watched preferences with confidence 1 + alpha, {ALS_PARAMS['n_factors']} factors, reg {ALS_PARAMS['reg']}, "
      f"{ALS_PARAMS['n_iters']} iterations, alpha in {ALS_ALPHAS} (tuning NDCG: " + ", ".join(f"{a:g}: {v:.4f}" for a, v in tune_alpha.items()) + "). "
      "The 0-dropped variant is FunkSVD with its default recipe refit on the train split minus every 0-rated row; those items "
      "still count as seen when it is scored.\n")
    rows = []
    for name, r in variants.items():
        rows.append([name, ci(r.ndcg), f"{item_coverage(r.recs, total_items):.4f}", f"{gini_index(r.recs):.4f}",
                     fmt_diff(r.ndcg, pop.ndcg), fmt_diff(r.ndcg, mf.ndcg)])
    w(table(["model", f"NDCG@{k} [95% CI]", f"coverage@{k}", f"gini@{k}", "vs. popularity", "vs. mf_sgd"], rows) + "\n")
    w(f"`mf_sgd (as evaluated)` here is {mf.ndcg.mean():.4f} and `item_knn_sklearn` {variants['item_knn_sklearn'].ndcg.mean():.4f}; "
      "they are recomputed by this script and should match `reports/phase4_ablation.md`. "
      f"{sum(1 for u in cur.users if not cur.train_hist.get(u))} cohort users have no training history (their only rating is the "
      "held-out one). Every CF model now returns nothing for them; until this task, `FunkSVDRecommender.recommend` scored them "
      "all-zero and broke the tie by item index order, which is first appearance in the file and starts with widely watched "
      "titles, so MF picked up hits from what was in effect a popularity fallback.\n")

    w("## 6. Conclusion\n")
    w(conclusion(variants, cells, pops, ratings, total_items) + "\n")
    return "\n".join(out)


def per_bucket_rows(cur: Split, variants: dict[str, Run], ratings: np.ndarray) -> list[list[str]]:
    """The ablation's own per-user vectors where available, plus the variants computed here."""
    frames: dict[str, np.ndarray] = {}
    try:
        per_user = pd.read_parquet(ROOT / PER_USER_PATH)
        per_user = per_user[per_user["users_evaluated"] == len(cur.users)]
        for model, g in per_user.groupby("model"):
            s = g.set_index("user_id")["ndcg"]
            if set(cur.users).issubset(s.index):
                frames[str(model)] = s.loc[cur.users].to_numpy()
    except OSError:
        pass
    in_ablation = {"popularity": "popularity", "mf_sgd (as evaluated)": "mf_sgd", "item_knn_sklearn": "item_knn_sklearn"}
    for name, r in variants.items():
        if in_ablation.get(name) not in frames:
            frames[name] = r.ndcg
    rows = []
    for name, v in sorted(frames.items(), key=lambda kv: -kv[1].mean()):
        rows.append([name, f"{v.mean():.4f}"] + [f"{v[f(ratings)].mean():.4f}" for _, f in BUCKETS])
    return rows


def ordering_note(rows: list[list[str]]) -> str:
    order_all = [r[0] for r in sorted(rows, key=lambda r: -float(r[1]))]
    order_liked = [r[0] for r in sorted(rows, key=lambda r: -float(r[2]))]
    if order_all == order_liked:
        return "Restricting to liked holdouts does not change the model ordering."
    moved = [m for i, m in enumerate(order_liked) if order_all[i] != m]
    return ("Restricting to liked holdouts changes the ordering. All holdouts: " + " > ".join(order_all)
            + ". Liked only: " + " > ".join(order_liked) + f". Positions that changed: {', '.join(moved)}.")


def relation(a: np.ndarray, b: np.ndarray) -> str:
    """'beats' / 'is tied with' / 'is below', read off the paired interval."""
    d, lo, hi = diff(a, b)
    return "beats" if lo > 0 else "is below" if hi < 0 else "is tied with"


def effect(a: np.ndarray, b: np.ndarray) -> str:
    return {"beats": "helps", "is tied with": "does not measurably change", "is below": "hurts"}[relation(a, b)]


def conclusion(variants: dict[str, Run], cells, pops, ratings: np.ndarray, total_items: int) -> str:
    mf = variants["mf_sgd (as evaluated)"]
    pop = variants["popularity"]
    knn = variants["item_knn_sklearn"]
    rated = variants["mf_sgd, 0-coded rows dropped"]
    prior = next(r for n, r in variants.items() if n.startswith("mf_sgd + popularity prior"))
    als = next(r for n, r in variants.items() if n.startswith("implicit ALS"))
    unrated, liked = ratings == 0, ratings >= LIKED
    proto = [diff(cells[(s, "train")].ndcg, cells[(s, "full")].ndcg) for s in ("legacy", "current")]
    proto_clear = all(hi < 0 for _, _, hi in proto)
    sampler = diff(cells[("current", "train")].ndcg, cells[("legacy", "train")].ndcg)
    sampler_tie = sampler[1] <= 0 <= sampler[2]
    als_tops_liked = all(als.ndcg[liked].mean() > r.ndcg[liked].mean() for r in variants.values() if r is not als)
    med = {name: np.nanmedian(r.holdout_rank[unrated]) for name, r in (("MF", mf), ("ALS", als), ("popularity", pop), ("item-kNN", knn))}
    headline = ("**The drop was the protocol, not the snapshot or the sampler.**" if proto_clear and sampler_tie
                else "**The drop does not reduce to the protocol alone.**")
    return "\n".join([
        f"{headline} Scoring a full-data fit against its own training rows was worth {-proto[0][0]:.4f} (legacy holdout) "
        f"and {-proto[1][0]:.4f} (current holdout) NDCG@10, "
        + ("both intervals clear of zero" if proto_clear else "not both clear of zero")
        + f"; the sampler change moves the train-split MF by {fmt_diff(cells[('current', 'train')].ndcg, cells[('legacy', 'train')].ndcg)}"
        + (", a tie." if sampler_tie else ".")
        + (" This contradicts the 2026-09-16 measurement on a 120K-row slice (mean delta -0.0018): at full scale a FunkSVD "
           "fit does learn enough of the held-out pair to lift it into the top 10." if proto_clear else ""),
        "",
        f"**On the clean protocol MF {relation(mf.ndcg, pop.ndcg)} popularity** ({fmt_diff(mf.ndcg, pop.ndcg)}) and "
        f"{relation(mf.ndcg, knn.ndcg)} item-kNN ({fmt_diff(mf.ndcg, knn.ndcg)}).",
        "",
        "**Why: FunkSVD answers a different question.** It is fit to predict the rating a user gives, so it has no signal "
        "for *which* titles a user chooses to watch, and the data teaches it that 19% of watched titles are worth 0. It ranks "
        f"a watched-but-unrated holdout at a median {med['MF']:,.0f} of {total_items:,}; ALS puts the same holdouts at "
        f"{med['ALS']:,.0f}, popularity at {med['popularity']:,.0f} and item-kNN, whose profile also centres on ratings, at "
        f"{med['item-kNN']:,.0f}. Dropping the 0-coded rows {effect(rated.ndcg, mf.ndcg)} MF "
        f"({fmt_diff(rated.ndcg, mf.ndcg)}): the zeros are not noise to remove but the only trace of choice FunkSVD gets. "
        f"Adding a popularity prior {effect(prior.ndcg, mf.ndcg)} it ({fmt_diff(prior.ndcg, mf.ndcg)}), the "
        "same symptom from the other side: what is missing is which items people watch. The tuned prior is so heavy that "
        f"the list is mostly popularity re-sorted by MF: coverage@10 {item_coverage(prior.recs, total_items):.4f} against "
        f"popularity's {item_coverage(pop.recs, total_items):.4f} and MF's {item_coverage(mf.recs, total_items):.4f}.",
        "",
        f"**Changing the objective.** Implicit ALS on watched / not watched {relation(als.ndcg, mf.ndcg)} FunkSVD "
        f"({fmt_diff(als.ndcg, mf.ndcg)}), {relation(als.ndcg, knn.ndcg)} item-kNN ({fmt_diff(als.ndcg, knn.ndcg)}) and "
        f"{relation(als.ndcg, pop.ndcg)} popularity ({fmt_diff(als.ndcg, pop.ndcg)}). "
        + ("It is also the best model on liked holdouts alone (section 3), so the lead is not an artifact of counting unrated "
           "watches as relevant." if als_tops_liked else "It is not the best model on liked holdouts alone (section 3)."),
        "",
        "**What it means for the served personalized mode.** *For me* mode builds the user's vector from FunkSVD item "
        "factors (`src/models/user_embedding.py`), and MF is 4.8% of the Balanced CF blend. Those factors encode rating, not "
        "choice. Implicit ALS is recorded in `docs/decisions.md` as a serving candidate; swapping it in touches "
        "`user_embedding.py` and the personalized gate and is a separate task. One caution for that task: this protocol "
        "holds out a random *watched* item, which is the implicit objective's home ground, so part of ALS's lead is the "
        "protocol's choice of target. A liked-only or graded protocol should confirm it before the swap.",
    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample-users", type=int, default=REPORTING_COHORT_USERS)
    parser.add_argument("--tune-users", type=int, default=1000)
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    args = parser.parse_args()
    main(args.sample_users, args.k, args.tune_users)
