"""Learned Stage-2 reranker: LightGBM LambdaRank over the weighted blend's candidates (Task 2.3).

Each user's candidates are the top-N items of the hand-weighted MF / kNN / popularity blend,
so the learned and hand-weighted rankings are compared on identical candidate sets. Features
are the blend's own signals plus the content and metadata affinities Stage 2 uses. Every
user-side signal is computed from the user's *train* history only; the held-out item enters
the frame as the label and nowhere else.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import dump
from scipy.sparse import csr_matrix

LEARNED_RERANKER_NAME = "learned_reranker"
N_CANDIDATES = 200

CF_FEATURES: tuple[str, ...] = (
    "blend_score",
    "blend_rank",
    "knn_score",
    "knn_rank",
    "mf_score",
    "mf_rank",
    "pop_score",
    "pop_pct",
)
FEATURES: tuple[str, ...] = (
    *CF_FEATURES,
    "synopsis_tfidf_sim",
    "synopsis_neural_sim",
    "genre_overlap",
    "theme_overlap",
    "mal_score",
    "log_members",
    "episodes",
    "year",
    "type_code",
    "history_len",
)

DEFAULT_PARAMS: dict[str, Any] = {
    "objective": "lambdarank",
    "n_estimators": 600,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 50,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "lambdarank_truncation_level": 20,
    "verbose": -1,
}
EARLY_STOPPING_ROUNDS = 50

# A catalog-aligned score vector for one user; NaN where the source has no score.
Scorer = Callable[[int], np.ndarray]

_META_COLS = ("mal_score", "log_members", "episodes", "year", "type_code")


def _multi_hot(values: Sequence[Any]) -> csr_matrix:
    vocab: dict[str, int] = {}
    rows, cols = [], []
    for r, val in enumerate(values):
        if val is None or isinstance(val, float):
            tags = []
        elif isinstance(val, str):  # older metadata stores tags pipe-joined
            tags = [t.strip() for t in val.split("|") if t.strip()]
        else:
            tags = list(val)
        for tag in tags:
            rows.append(r)
            cols.append(vocab.setdefault(str(tag), len(vocab)))
    data = np.ones(len(rows), dtype=np.float32)
    return csr_matrix((data, (rows, cols)), shape=(len(values), max(1, len(vocab))))


def _align_rows(item_ids: np.ndarray, source_ids: Sequence[int], matrix: Any) -> Any:
    """Rows of `matrix` reordered to `item_ids`; items the source lacks get a zero row."""
    lookup = {int(a): r for r, a in enumerate(source_ids)}
    idx = np.array([lookup.get(int(a), -1) for a in item_ids])
    present = idx >= 0
    if isinstance(matrix, csr_matrix):
        picked = matrix[np.where(present, idx, 0)]
        mask = csr_matrix((present.astype(np.float32), (np.arange(len(idx)), np.arange(len(idx)))))
        return csr_matrix(mask @ picked)
    out = np.zeros((len(item_ids), matrix.shape[1]), dtype=np.float32)
    out[present] = np.asarray(matrix, dtype=np.float32)[idx[present]]
    return out


def _l2_rows(matrix: Any) -> Any:
    if isinstance(matrix, csr_matrix):
        norms = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
        norms[norms == 0] = 1.0
        return csr_matrix(matrix.multiply(1.0 / norms[:, None]))
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


@dataclass
class ItemSide:
    """Item features on one catalog index, so every per-user vector lines up."""

    item_ids: np.ndarray
    pos: dict[int, int]
    pop: np.ndarray
    pop_pct: np.ndarray
    synopsis_tfidf: csr_matrix
    synopsis_neural: np.ndarray
    genres: csr_matrix
    themes: csr_matrix
    meta: np.ndarray  # n_items x len(_META_COLS), NaN where unknown

    @classmethod
    def build(
        cls,
        item_ids: Sequence[int],
        pop: Mapping[int, float],
        metadata: pd.DataFrame,
        *,
        tfidf_ids: Sequence[int],
        tfidf_matrix: csr_matrix,
        neural_ids: Sequence[int],
        neural_matrix: np.ndarray,
    ) -> ItemSide:
        ids = np.asarray([int(i) for i in item_ids])
        pos = {int(a): k for k, a in enumerate(ids)}
        pop_vec = np.array([float(pop.get(int(a), 0.0)) for a in ids])
        pop_pct = pd.Series(pop_vec).rank(pct=True).to_numpy()

        meta = metadata.drop_duplicates("anime_id").set_index("anime_id").reindex(ids)
        year = pd.to_datetime(meta["aired_from"], errors="coerce", utc=True).dt.year
        type_code = meta["type"].astype("category").cat.codes.replace(-1, np.nan)
        meta_mat = np.column_stack([
            meta["mal_score"].to_numpy(dtype=float),
            np.log1p(meta["members_count"].to_numpy(dtype=float)),
            meta["episodes"].to_numpy(dtype=float),
            year.to_numpy(dtype=float),
            type_code.to_numpy(dtype=float),
        ])
        return cls(
            item_ids=ids,
            pos=pos,
            pop=pop_vec,
            pop_pct=pop_pct,
            synopsis_tfidf=_l2_rows(_align_rows(ids, tfidf_ids, csr_matrix(tfidf_matrix))),
            synopsis_neural=_l2_rows(_align_rows(ids, neural_ids, neural_matrix)),
            genres=_multi_hot(meta["genres"].tolist()),
            themes=_multi_hot(meta["themes"].tolist()),
            meta=meta_mat,
        )


def blend_scores(mf: np.ndarray, knn: np.ndarray, pop: np.ndarray, weights: Mapping[str, float]) -> np.ndarray:
    """The hand-weighted blend; a source with no score for an item contributes 0, as in `weighted_blend`."""
    return (
        float(weights.get("mf", 0.0)) * np.nan_to_num(mf, nan=0.0)
        + float(weights.get("knn", 0.0)) * np.nan_to_num(knn, nan=0.0)
        + float(weights.get("pop", 0.0)) * pop
    )


def _desc_rank(values: np.ndarray) -> np.ndarray:
    """0-based descending rank among the candidates; NaN stays NaN."""
    out = np.full(len(values), np.nan)
    finite = np.isfinite(values)
    out[finite] = pd.Series(values[finite]).rank(ascending=False, method="min").to_numpy() - 1
    return out


def _profile_cosine(matrix: Any, hist: np.ndarray, cand: np.ndarray) -> np.ndarray:
    if hist.size == 0:
        return np.zeros(len(cand))
    profile = np.asarray(matrix[hist].mean(axis=0)).ravel()
    norm = np.linalg.norm(profile)
    if norm == 0:
        return np.zeros(len(cand))
    return np.asarray(matrix[cand] @ (profile / norm)).ravel()


def _tag_overlap(tags: csr_matrix, hist: np.ndarray, cand: np.ndarray) -> np.ndarray:
    """Mean share of the user's history carrying each of the candidate's tags."""
    if hist.size == 0:
        return np.zeros(len(cand))
    share = np.asarray(tags[hist].mean(axis=0)).ravel()
    cand_tags = tags[cand]
    n_tags = np.asarray(cand_tags.sum(axis=1)).ravel()
    return np.asarray(cand_tags @ share).ravel() / np.maximum(n_tags, 1.0)


def user_candidates(
    user_id: int,
    items: ItemSide,
    mf: np.ndarray,
    knn: np.ndarray,
    train_items: Sequence[int],
    weights: Mapping[str, float],
    n_candidates: int = N_CANDIDATES,
) -> pd.DataFrame:
    """Feature rows for one user's top-`n_candidates` blended candidates, in blend order."""
    hist = _history_positions(items, train_items)
    blend = blend_scores(mf, knn, items.pop, weights)
    blend[hist] = -np.inf
    eligible = np.flatnonzero(np.isfinite(blend))
    n = min(n_candidates, eligible.size)
    if n == 0:
        return pd.DataFrame(columns=["user_id", "anime_id", *FEATURES])
    # Score descending, catalog position ascending on ties: one deterministic order.
    order = np.lexsort((eligible, -blend[eligible]))[:n]
    return candidate_features(user_id, items, mf, knn, hist, eligible[order], blend)


def _history_positions(items: ItemSide, train_items: Sequence[int]) -> np.ndarray:
    return np.array(sorted({items.pos[int(i)] for i in train_items if int(i) in items.pos}), dtype=int)


def candidate_features(
    user_id: int,
    items: ItemSide,
    mf: np.ndarray,
    knn: np.ndarray,
    hist: np.ndarray,
    cand: np.ndarray,
    blend: np.ndarray,
) -> pd.DataFrame:
    """Feature rows for the catalog positions `cand`, taken to be in blend order."""
    n = len(cand)
    frame = {
        "user_id": np.full(n, int(user_id), dtype=np.int64),
        "anime_id": items.item_ids[cand].astype(np.int64),
        "blend_score": blend[cand],
        "blend_rank": np.arange(n, dtype=float),
        "knn_score": knn[cand],
        "knn_rank": _desc_rank(knn[cand]),
        "mf_score": mf[cand],
        "mf_rank": _desc_rank(mf[cand]),
        "pop_score": items.pop[cand],
        "pop_pct": items.pop_pct[cand],
        "synopsis_tfidf_sim": _profile_cosine(items.synopsis_tfidf, hist, cand),
        "synopsis_neural_sim": _profile_cosine(items.synopsis_neural, hist, cand),
        "genre_overlap": _tag_overlap(items.genres, hist, cand),
        "theme_overlap": _tag_overlap(items.themes, hist, cand),
        "history_len": np.full(n, float(hist.size)),
    }
    for j, col in enumerate(_META_COLS):
        frame[col] = items.meta[cand, j]
    return pd.DataFrame(frame)


def build_feature_frame(
    users: Sequence[int],
    items: ItemSide,
    scorers: Mapping[str, Scorer],
    train_hist: Mapping[int, Sequence[int]],
    holdout: Mapping[int, set[int]],
    weights: Mapping[str, float],
    n_candidates: int = N_CANDIDATES,
) -> pd.DataFrame:
    """Per-(user, candidate) rows, grouped contiguously by user, with `label` = held-out item.

    Raises if a user's held-out item is in their train history: every feature is built from
    that history, so the overlap would put the label inside the features.
    """
    parts = []
    for u in users:
        hist = train_hist.get(u, ())
        target = holdout.get(u, set())
        leaked = target & {int(i) for i in hist}
        if leaked:
            raise ValueError(f"user {u}: held-out items {sorted(leaked)} are in the train history")
        part = user_candidates(u, items, scorers["mf"](u), scorers["knn"](u), hist, weights, n_candidates)
        part["label"] = part["anime_id"].isin(target).astype(np.int8)
        parts.append(part)
    if not parts:
        return pd.DataFrame(columns=["user_id", "anime_id", *FEATURES, "label"])
    return pd.concat(parts, ignore_index=True)


def _with_positive(frame: pd.DataFrame) -> pd.DataFrame:
    """Groups with no positive carry no LambdaRank gradient and score a vacuous NDCG of 1."""
    has_pos = frame.groupby("user_id", sort=False)["label"].transform("max") > 0
    return frame[has_pos]


def _group_sizes(frame: pd.DataFrame) -> np.ndarray:
    return frame.groupby("user_id", sort=False).size().to_numpy()


def train_ranker(
    train: pd.DataFrame,
    val: pd.DataFrame | None = None,
    *,
    features: Sequence[str] = FEATURES,
    seed: int = 42,
    params: Mapping[str, Any] | None = None,
) -> Any:
    """Fit LightGBM LambdaRank; early-stops on NDCG@10 over `val` when given."""
    import lightgbm as lgb

    train = _with_positive(train)
    if train.empty:
        raise ValueError("no training user has the held-out item among their candidates")
    model = lgb.LGBMRanker(**{**DEFAULT_PARAMS, **(params or {}), "random_state": seed})
    fit_kwargs: dict[str, Any] = {}
    val = None if val is None else _with_positive(val)
    if val is not None and not val.empty:
        fit_kwargs = {
            "eval_set": [(val[list(features)], val["label"])],
            "eval_group": [_group_sizes(val)],
            "eval_at": [10],
            "callbacks": [lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
        }
    with warnings.catch_warnings():
        # 4.7 renamed eval_set to eval_X / eval_y; the old name still works across every 4.x.
        warnings.filterwarnings("ignore", message="The argument 'eval_set' is deprecated")
        model.fit(train[list(features)], train["label"], group=_group_sizes(train), **fit_kwargs)
    return model


def ranked_lists(frame: pd.DataFrame, scores: np.ndarray | None = None, k: int | None = None) -> dict[int, list[int]]:
    """Per-user item lists, by `scores` descending (blend order on ties), or blend order if None."""
    work = frame[["user_id", "anime_id", "blend_rank"]].copy()
    work["_s"] = -work["blend_rank"] if scores is None else np.asarray(scores, dtype=float)
    work = work.sort_values(["user_id", "_s", "blend_rank"], ascending=[True, False, True], kind="mergesort")
    lists = work.groupby("user_id", sort=False)["anime_id"].apply(list)
    return {int(u): [int(i) for i in (items if k is None else items[:k])] for u, items in lists.items()}


def feature_importance(model: Any, features: Sequence[str] = FEATURES) -> pd.DataFrame:
    booster = model.booster_
    gain = booster.feature_importance(importance_type="gain")
    split = booster.feature_importance(importance_type="split")
    out = pd.DataFrame({"feature": list(features), "gain": gain, "splits": split})
    out["gain_share"] = out["gain"] / max(out["gain"].sum(), 1e-12)
    return out.sort_values("gain", ascending=False, ignore_index=True)


@dataclass
class ServedReranker:
    """What a `learned_reranker_v*.joblib` holds: the ranker plus the training-time inputs the app
    does not otherwise have (train-split popularity, the blend weights), so serve-time features
    come from the same code and on the same scales as the training features.
    """

    model: Any
    features: list[str]
    pop: dict[int, float]
    weights: dict[str, float]
    n_candidates: int = N_CANDIDATES
    meta: dict[str, Any] = field(default_factory=dict)

    def item_side(self, item_ids: Sequence[int], metadata: pd.DataFrame, *, tfidf_artifact: Any, neural_artifact: Any) -> ItemSide:
        return ItemSide.build(
            item_ids,
            self.pop,
            metadata,
            tfidf_ids=tfidf_artifact.anime_ids,
            tfidf_matrix=tfidf_artifact.tfidf_matrix,
            neural_ids=neural_artifact.anime_ids,
            neural_matrix=neural_artifact.embeddings,
        )

    def score(
        self,
        items: ItemSide,
        mf: np.ndarray,
        knn: np.ndarray,
        watched_ids: Sequence[int],
        candidate_ids: Sequence[int],
    ) -> np.ndarray:
        """Learned scores for `candidate_ids`, which must arrive in the blend's order."""
        hist = _history_positions(items, watched_ids)
        cand = np.array([items.pos[int(a)] for a in candidate_ids], dtype=int)
        blend = blend_scores(mf, knn, items.pop, self.weights)
        frame = candidate_features(0, items, mf, knn, hist, cand, blend)
        return np.asarray(self.model.predict(frame[self.features]), dtype=float)


def save_reranker(served: ServedReranker, out_dir: Path) -> Path:
    """Write `learned_reranker_vYYYY.MM.DD_HHMMSS.joblib`, the stem convention `models/` uses."""
    stem = f"{LEARNED_RERANKER_NAME}_v{datetime.now(UTC):%Y.%m.%d_%H%M%S}"
    path = Path(out_dir) / f"{stem}.joblib"
    path.parent.mkdir(parents=True, exist_ok=True)
    dump(served, path)
    return path
