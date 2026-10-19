#!/usr/bin/env python
"""Learned reranker experiment: does LightGBM LambdaRank beat the hand-weighted blend? (Task 2.3)

Candidates are each user's top-200 items under the served, re-tuned weighted blend, so the
hand-weighted and learned rankings are scored on identical candidate sets. The ranker trains
on validation users outside the reporting cohort (`reporting_and_tuning_users`), split
train / early-stopping by user, and is scored once on the 1,000-user reporting cohort.

Three seeds vary both the train / early-stopping user split and LightGBM's own seed. The
decision rule (from the plan): the learned ranker ships only if its NDCG@10 gain over the
hand-weighted blend exceeds the seed-to-seed spread *and* the paired bootstrap interval on
the difference excludes 0 for every seed.

Feature frames take ~35 minutes to build (kNN scores every user against the catalog), so they
are cached under `experiments/artifacts/` keyed on the users, weights and train split.

Usage:
    python scripts/train_learned_reranker.py --sample-users 1000 --k 10
Output: reports/learned_reranker.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from joblib import dump, load

from src.eval.bootstrap import bootstrap_mean_ci, paired_bootstrap_diff_ci
from src.eval.eval_artifacts import knn_eval_scores, load_eval_models, train_fingerprint
from src.eval.metrics import average_precision_at_k, ndcg_at_k
from src.eval.metrics_extra import gini_index, item_coverage
from src.eval.splits import build_validation, reporting_and_tuning_users
from src.models.baselines import popularity_scores
from src.models.constants import (
    DATA_PROCESSED_DIR,
    DEFAULT_HYBRID_WEIGHTS,
    EVAL_ARTIFACTS_DIR,
    MODELS_DIR,
    REPORTING_COHORT_USERS,
    TOP_K_DEFAULT,
)
from src.models.hybrid import reciprocal_rank_fusion
from src.models.learned_reranker import (
    CF_FEATURES,
    FEATURES,
    N_CANDIDATES,
    ItemSide,
    ServedReranker,
    build_feature_frame,
    feature_importance,
    ranked_lists,
    save_reranker,
    train_ranker,
)

REPORT_PATH = ROOT / "reports" / "learned_reranker.md"
SEEDS = (42, 43, 44)
VAL_SHARE = 0.2


def _single_artifact(prefix: str) -> Path:
    found = sorted(MODELS_DIR.glob(f"{prefix}_v*.joblib"))
    if len(found) != 1:
        raise SystemExit(f"expected one {prefix} artifact in {MODELS_DIR}, found {len(found)}")
    return found[0]


def build_items(train_df: pd.DataFrame, item_ids: np.ndarray) -> ItemSide:
    tfidf = load(_single_artifact("synopsis_tfidf"))
    neural = load(_single_artifact("synopsis_neural_embeddings"))
    pop = {int(i): float(s) for i, s in popularity_scores(train_df).items()}
    return ItemSide.build(
        item_ids,
        pop,
        pd.read_parquet(DATA_PROCESSED_DIR / "anime_metadata.parquet"),
        tfidf_ids=tfidf.anime_ids,
        tfidf_matrix=tfidf.tfidf_matrix,
        neural_ids=neural.anime_ids,
        neural_matrix=neural.embeddings,
    )


class Scorers:
    """Catalog-aligned MF and kNN scores; keeps the cohort's vectors for the RRF row."""

    def __init__(self, mf_model, knn_model, items: ItemSide, train_hist: dict[int, set[int]]):
        self.mf_model, self.knn_model, self.items, self.train_hist = mf_model, knn_model, items, train_hist
        order = np.array([items.pos.get(int(mf_model.index_to_item[i]), -1) for i in range(len(mf_model.index_to_item))])
        self._mf_keep = order >= 0
        self._mf_pos = order[self._mf_keep]
        self.memo: dict[str, dict[int, np.ndarray]] | None = None

    def mf(self, u: int) -> np.ndarray:
        out = np.full(len(self.items.item_ids), np.nan)
        if u in self.mf_model.user_to_index:
            out[self._mf_pos] = np.asarray(self.mf_model.predict_user(u), dtype=np.float64)[self._mf_keep]
        if self.memo is not None:
            self.memo["mf"][u] = out
        return out

    def knn(self, u: int) -> np.ndarray:
        out = np.full(len(self.items.item_ids), np.nan)
        for item, s in knn_eval_scores(self.knn_model, u, self.train_hist.get(u, set())).items():
            k = self.items.pos.get(int(item))
            if k is not None:
                out[k] = s
        if self.memo is not None:
            self.memo["knn"][u] = out
        return out


def _top(scores: np.ndarray, seen: np.ndarray, item_ids: np.ndarray, k: int) -> list[int]:
    s = np.where(np.isnan(scores), -np.inf, scores).copy()
    s[seen] = -np.inf
    top = np.argpartition(-s, k - 1)[:k]
    top = top[np.argsort(-s[top])]
    return [int(item_ids[t]) for t in top if np.isfinite(s[t])]


def rrf_lists(users: list[int], scorers: Scorers, memo: dict, k: int) -> dict[int, list[int]]:
    """RRF over full-catalog MF / kNN / popularity top-K lists, as in `evaluate_hybrid.py`."""
    items = scorers.items
    out = {}
    for u in users:
        seen = np.array([items.pos[i] for i in scorers.train_hist.get(u, ()) if i in items.pos], dtype=int)
        mf = _top(memo["mf"][u], seen, items.item_ids, k) if u in scorers.mf_model.user_to_index else []
        out[u] = reciprocal_rank_fusion(
            {"mf": mf, "knn": _top(memo["knn"][u], seen, items.item_ids, k), "pop": _top(items.pop, seen, items.item_ids, k)},
            top_k=k,
        )
    return out


def cached_frame(name: str, users: list[int], fingerprint: dict, build) -> dict:
    key = json.dumps({"users": users, "fp": fingerprint, "weights": DEFAULT_HYBRID_WEIGHTS,
                      "n": N_CANDIDATES, "features": FEATURES}, sort_keys=True)
    tag = hashlib.sha1(key.encode()).hexdigest()[:12]
    path = EVAL_ARTIFACTS_DIR / f"learned_reranker_features_{name}_{tag}.joblib"
    if path.exists():
        print(f"[{name}] cached feature frame: {path.name}", flush=True)
        return load(path)
    t0 = time.time()
    out = build()
    print(f"[{name}] built {len(out['frame']):,} rows for {len(users):,} users in {time.time() - t0:.0f}s", flush=True)
    EVAL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    dump(out, path)
    return out


# ---------- scoring ----------

def score_lists(lists: dict[int, list[int]], users: list[int], holdout: dict[int, set[int]], k: int, total_items: int) -> dict:
    recs = {u: lists.get(u, [])[:k] for u in users}
    ndcg = np.array([ndcg_at_k(recs[u], holdout.get(u, set()), k) for u in users])
    ap = np.array([average_precision_at_k(recs[u], holdout.get(u, set()), k) for u in users])
    return {"ndcg": ndcg, "map": ap, "coverage": item_coverage(recs, total_items), "gini": gini_index(recs)}


def ci(values: np.ndarray) -> str:
    mean, lo, hi = bootstrap_mean_ci(values)
    return f"{mean:.4f} [{lo:.4f}, {hi:.4f}]"


def fmt_diff(a: np.ndarray, b: np.ndarray) -> str:
    d, lo, hi = paired_bootstrap_diff_ci(a, b)
    return f"{d:+.4f} [{lo:+.4f}, {hi:+.4f}]"


def table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join([":---"] + ["---:"] * (len(header) - 1)) + "|"]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows])


def split_pool(pool: list[int], seed: int) -> tuple[set[int], set[int]]:
    shuffled = list(np.random.default_rng(seed).permutation(pool))
    n_val = int(round(VAL_SHARE * len(shuffled)))
    return {int(u) for u in shuffled[n_val:]}, {int(u) for u in shuffled[:n_val]}


# ---------- main ----------

def main(sample_users: int, k: int, ranker_users: int) -> None:
    t0 = time.time()
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    cohort, pool = reporting_and_tuning_users(val_df["user_id"].unique().tolist(), sample_users, ranker_users)
    cohort, pool = [int(u) for u in cohort], [int(u) for u in pool]
    overlap = len(set(cohort) & set(pool))
    print(f"Ranker users: {len(pool)} | reporting cohort: {len(cohort)} | overlap: {overlap}", flush=True)
    if overlap:
        raise SystemExit("Ranker and reporting users overlap; refusing to train on the reporting cohort.")

    knn_model, mf_model = load_eval_models(train_df)
    train_hist = {int(u): {int(i) for i in s} for u, s in train_df.groupby("user_id")["anime_id"].apply(set).items()}
    holdout = {int(u): {int(i) for i in s} for u, s in val_df.groupby("user_id")["anime_id"].apply(set).items()}
    item_ids = np.sort(train_df["anime_id"].astype(int).unique())
    total_items = int(len(item_ids))
    items = build_items(train_df, item_ids)
    scorers = Scorers(mf_model, knn_model, items, train_hist)
    fp = train_fingerprint(train_df)
    print(f"Loaded data and models in {time.time() - t0:.0f}s", flush=True)

    def _frame(users):
        return build_feature_frame(users, items, {"mf": scorers.mf, "knn": scorers.knn},
                                   train_hist, holdout, DEFAULT_HYBRID_WEIGHTS)

    def _build_cohort():
        scorers.memo = {"mf": {}, "knn": {}}
        frame = _frame(cohort)
        out = {"frame": frame, "rrf": rrf_lists(cohort, scorers, scorers.memo, k)}
        scorers.memo = None
        return out

    pool_frame = cached_frame("pool", pool, fp, lambda: {"frame": _frame(pool)})["frame"]
    cohort_data = cached_frame("cohort", cohort, fp, _build_cohort)
    cohort_frame, rrf = cohort_data["frame"], cohort_data["rrf"]

    hand = score_lists(ranked_lists(cohort_frame), cohort, holdout, k, total_items)
    rrf_run = score_lists(rrf, cohort, holdout, k, total_items)
    recall_cands = float(cohort_frame.groupby("user_id")["label"].max().reindex(cohort).fillna(0).mean())
    pool_hits = pool_frame.groupby("user_id")["label"].max()

    runs: dict[str, dict[int, dict]] = {"cf": {}, "full": {}}
    importances = []
    iterations: dict[str, list[int]] = {"cf": [], "full": []}
    saved_path = None
    for seed in SEEDS:
        train_users, es_users = split_pool(pool, seed)
        tr = pool_frame[pool_frame["user_id"].isin(train_users)]
        es = pool_frame[pool_frame["user_id"].isin(es_users)]
        for variant, feats in (("cf", CF_FEATURES), ("full", FEATURES)):
            model = train_ranker(tr, es, features=feats, seed=seed)
            iterations[variant].append(int(model.best_iteration_ or model.n_estimators))
            scores = model.predict(cohort_frame[list(feats)])
            runs[variant][seed] = score_lists(ranked_lists(cohort_frame, scores), cohort, holdout, k, total_items)
            if variant == "full":
                importances.append(feature_importance(model, feats).set_index("feature")["gain_share"])
                if seed == SEEDS[0]:
                    served = ServedReranker(
                        model=model,
                        features=list(feats),
                        pop={int(a): float(p) for a, p in zip(items.item_ids, items.pop)},
                        weights=dict(DEFAULT_HYBRID_WEIGHTS),
                        meta={"seed": seed, "train_users": len(train_users), "early_stopping_users": len(es_users),
                              "train_fingerprint": fp, "cohort_ndcg": float(runs[variant][seed]["ndcg"].mean())},
                    )
                    saved_path = save_reranker(served, EVAL_ARTIFACTS_DIR)
            print(f"seed {seed} {variant}: NDCG@{k} {runs[variant][seed]['ndcg'].mean():.4f} "
                  f"(hand-weighted {hand['ndcg'].mean():.4f})", flush=True)

    report = render(
        k=k, cohort=cohort, pool=pool, pool_hits=pool_hits, hand=hand, rrf_run=rrf_run, runs=runs,
        importances=importances, iterations=iterations, recall_cands=recall_cands, saved_path=saved_path,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)} in {time.time() - t0:.0f}s total", flush=True)


def decide(hand: dict, full: dict[int, dict]) -> dict:
    means = np.array([r["ndcg"].mean() for r in full.values()])
    diffs = [paired_bootstrap_diff_ci(r["ndcg"], hand["ndcg"]) for r in full.values()]
    gain = float(means.mean() - hand["ndcg"].mean())
    spread = float(means.max() - means.min())
    all_exclude = all(lo > 0 for _, lo, _ in diffs)
    if all_exclude:
        relation = "better"
    elif all(hi < 0 for _, _, hi in diffs):
        relation = "worse"
    else:
        relation = "tie"
    return {"gain": gain, "spread": spread, "all_ci_exclude_zero": all_exclude, "relation": relation,
            "wins": gain > spread and all_exclude}


def render(*, k, cohort, pool, pool_hits, hand, rrf_run, runs, importances, iterations, recall_cands, saved_path) -> str:
    n = len(cohort)
    header = [f"ranking (cohort, {n:,} users)", f"NDCG@{k} [95% CI]", f"MAP@{k} [95% CI]",
              f"coverage@{k}", f"gini@{k}", "NDCG diff vs hand-weighted [paired 95% CI]"]

    def row(label, r, vs_hand=True):
        return [label, ci(r["ndcg"]), ci(r["map"]), f"{r['coverage']:.4f}", f"{r['gini']:.4f}",
                fmt_diff(r["ndcg"], hand["ndcg"]) if vs_hand else "—"]

    rows = [row("hand-weighted blend (served, Task 0.6 weights)", hand, vs_hand=False), row("hybrid RRF (full catalog)", rrf_run)]
    for variant, label in (("cf", "LambdaRank, CF signals only"), ("full", "LambdaRank, all signals")):
        for seed, r in runs[variant].items():
            rows.append(row(f"{label} (seed {seed})", r))

    imp = pd.concat(importances, axis=1).mean(axis=1).sort_values(ascending=False)
    imp_rows = [[f, f"{v:.3f}"] for f, v in imp.items()]
    d_full, d_cf = decide(hand, runs["full"]), decide(hand, runs["cf"])
    w = DEFAULT_HYBRID_WEIGHTS

    out = [
        "# Learned Reranker: LightGBM LambdaRank vs. the Hand-Weighted Blend",
        "",
        f"Generated by `scripts/train_learned_reranker.py` on {datetime.now(UTC):%Y-%m-%d}. "
        f"Cohort: the {n:,}-user reporting cohort (seed 42) the ablation uses, NDCG@{k} with each user's "
        "training history excluded. Intervals are 95% percentile bootstrap (users resampled, 1,000 "
        "resamples); differences are paired (same users under both rankings), so an interval that "
        "spans zero is a tie.",
        "",
        "## Setup",
        "",
        f"- **Candidates.** Each user's top {N_CANDIDATES} items under the served weighted blend "
        f"(mf {w['mf']:.3f} / knn {w['knn']:.3f} / pop {w['pop']:.4f}, the Task 0.6 re-tune). The "
        "hand-weighted row is the blend's own order over those candidates, so it is the ablation's "
        "`hybrid_weighted_tuned` row; the learned rows reorder the same candidates. The held-out item "
        f"is among the candidates for {recall_cands:.1%} of cohort users, which caps what any reranker "
        "can reach.",
        f"- **Training users.** {len(pool):,} validation users outside the reporting cohort (zero "
        f"overlap), of whom {int(pool_hits.sum()):,} have their held-out item among the candidates; "
        "only those carry a LambdaRank gradient. Each seed splits them 80 / 20 into training and "
        f"early-stopping users (early stopping on NDCG@10). Best iterations, all signals: "
        f"{', '.join(map(str, iterations['full']))}; CF only: {', '.join(map(str, iterations['cf']))}.",
        "- **Label.** 1 for the user's held-out interaction, 0 for every other candidate. Every feature "
        "is computed from the train split: MF and kNN are the train-split artifacts, popularity is "
        "counted on train rows, and the content and metadata affinities are profiles of the user's "
        "train history (`build_feature_frame` refuses a user whose held-out item is in that history).",
        "- **Features.** CF: blend score and rank, kNN score and rank, MF score and rank, popularity "
        "score and percentile. Content and metadata (the signals Stage 2 uses, as user-profile "
        "affinities): synopsis TF-IDF and synopsis neural cosine to the user's history, genre and "
        "theme overlap with it, MAL score, log members, episodes, year, type, history length.",
        f"- **Seeds.** {', '.join(map(str, SEEDS))}: each changes the train / early-stopping user split "
        "and LightGBM's bagging seed. The reporting cohort does not change.",
        "",
        "## Results",
        "",
        table(header, rows),
        "",
        "## Decision rule",
        "",
        "The plan's rule: wire the ranker into the app only if its NDCG@10 gain over the hand-weighted "
        "blend exceeds the seed-to-seed spread **and** the paired bootstrap interval on the difference "
        "excludes 0.",
        "",
        table(["ranker", "mean gain over hand-weighted", "seed-to-seed spread (max - min)", "paired CI excludes 0 (all seeds)", "verdict"], [
            ["all signals", f"{d_full['gain']:+.4f}", f"{d_full['spread']:.4f}", "yes" if d_full["all_ci_exclude_zero"] else "no",
             "**ship behind `RERANKER_MODE=learned`**" if d_full["wins"] else "not shipped"],
            ["CF signals only", f"{d_cf['gain']:+.4f}", f"{d_cf['spread']:.4f}", "yes" if d_cf["all_ci_exclude_zero"] else "no",
             "(diagnostic only)"],
        ]),
        "",
        "## Feature importance (all signals)",
        "",
        "Share of total split gain, averaged over the three seeds.",
        "",
        table(["feature", "gain share"], imp_rows),
        "",
        "## Conclusion",
        "",
        conclusion(hand, rrf_run, runs, d_full, d_cf, imp, recall_cands),
        "",
        f"Model artifact (seed {SEEDS[0]}, all signals): `{saved_path.as_posix() if saved_path else 'not saved'}` "
        "(git-ignored). When the rule says ship, it is copied to `models/` under the same stem and named "
        "by `LEARNED_RERANKER_STEM` in `src/models/constants.py`.",
        "",
    ]
    return "\n".join(out)


def conclusion(hand, rrf_run, runs, d_full, d_cf, imp, recall_cands) -> str:
    h = hand["ndcg"].mean()
    full = np.mean([r["ndcg"].mean() for r in runs["full"].values()])
    cf = np.mean([r["ndcg"].mean() for r in runs["cf"].values()])
    top = ", ".join(f"`{f}`" for f in imp.index[:3])
    cf_text = f"Learning a ranker over the CF signals alone gives {cf:.4f} ({d_cf['gain']:+.4f} vs. {h:.4f}), " + {
        "better": "a gain every seed's interval supports, so the tuned weights leave accuracy on the table even "
                  "before new signals are added.",
        "tie": "a tie: the Optuna-tuned weights already extract what the three CF scores can give.",
        "worse": "worse on every seed: a three-weight linear blend tuned directly on NDCG is a hard baseline for "
                 "a learned model to beat with the same inputs.",
    }[d_cf["relation"]]
    if d_full["wins"]:
        verdict = (
            f"With the content and metadata signals added it reaches {full:.4f} ({d_full['gain']:+.4f} over the "
            f"hand-weighted blend's {h:.4f}), larger than the seed-to-seed spread ({d_full['spread']:.4f}) with every "
            "seed's paired interval above zero, so it meets the rule and is wired behind `RERANKER_MODE=learned`."
        )
    else:
        reason = []
        if d_full["gain"] <= d_full["spread"]:
            reason.append(f"the gain ({d_full['gain']:+.4f}) is not larger than the seed-to-seed spread ({d_full['spread']:.4f})")
        if not d_full["all_ci_exclude_zero"]:
            reason.append("not every seed's paired interval excludes zero")
        verdict = (
            f"With the content and metadata signals added it reaches {full:.4f} ({d_full['relation']} on the paired "
            f"intervals); it does not meet the rule because {' and '.join(reason)}, so the app is unchanged."
        )
    return (
        f"{cf_text} {verdict} The most-used features are {top}. RRF over the same three sources scores "
        f"{rrf_run['ndcg'].mean():.4f}. Any reranker of these candidates is capped by their recall: the held-out "
        f"item is in the top {N_CANDIDATES} for {recall_cands:.1%} of users, so a better first stage (the implicit "
        "ALS in `reports/mf_diagnostic.md` ranks far better on its own) moves the ceiling more than reordering can."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample-users", type=int, default=REPORTING_COHORT_USERS,
                        help="Reporting cohort size (must match the ablation's --sample-users)")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--ranker-users", type=int, default=4000,
                        help="Validation users outside the cohort used to train and early-stop the ranker")
    args = parser.parse_args()
    main(args.sample_users, args.k, args.ranker_users)
