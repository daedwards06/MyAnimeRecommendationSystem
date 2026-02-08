"""Hybrid recommendation and similarity utilities.

This module provides a lightweight inference layer that blends
MF, kNN, and popularity signals and exposes explanation shares.

Artifact contract enforcement (fail-loud) is expected to happen at
app startup (see `src.app.artifacts_loader`). This module avoids
constructing placeholder score arrays for missing artifacts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from src.models.user_embedding import compute_personalized_scores

from .constants import BALANCED_WEIGHTS, DIVERSITY_EMPHASIZED_WEIGHTS


@dataclass
class HybridComponents:
    """Container for hybrid score components.

    Attributes
    ----------
    mf : np.ndarray | None
        User-item matrix factorization scores (shape: [num_users, num_items]).
    knn : np.ndarray | None
        User-item kNN contribution scores (shape: [num_users, num_items]).
    pop : np.ndarray | None
        Item popularity scores (shape: [num_items]).
    item_ids : np.ndarray
        Mapping from column index -> external anime_id.
    """

    mf: np.ndarray | None
    knn: np.ndarray | None
    pop: np.ndarray | None
    item_ids: np.ndarray

    @property
    def num_items(self) -> int:
        return int(self.item_ids.shape[0])


class HybridRecommender:
    """Hybrid blending of MF, kNN, and popularity scores.

    NOTES:
        - Assumes user indices align across mf/knn matrices.
        - Popularity vector is broadcast across users.
        - All inputs should be float arrays; casting is applied if needed.
    """

    def __init__(self, components: HybridComponents) -> None:
        self.c = components
        # Normalize inputs to float32 for memory efficiency.
        if self.c.mf is not None:
            self.c.mf = self.c.mf.astype(np.float32, copy=False)
        if self.c.knn is not None:
            self.c.knn = self.c.knn.astype(np.float32, copy=False)
        if self.c.pop is not None:
            self.c.pop = self.c.pop.astype(np.float32, copy=False)

    def _blend(self, user_index: int, weights: dict[str, float]) -> np.ndarray:
        """Blend MF, kNN, and popularity scores for a given user.

        NOTE (Phase 2, Task 2.1): In seed-based (non-personalized) mode, the
        scoring pipeline may substitute mean-user CF scores instead of using
        user_index=0, to represent average community preferences rather than
        one arbitrary training user's taste. See USE_MEAN_USER_CF in constants.
        """
        mf_part = 0.0
        knn_part = 0.0
        pop_part = 0.0
        if self.c.mf is not None:
            mf_part = weights.get("mf", 0.0) * self.c.mf[user_index]
        if self.c.knn is not None:
            knn_part = weights.get("knn", 0.0) * self.c.knn[user_index]
        if self.c.pop is not None:
            pop_part = weights.get("pop", 0.0) * self.c.pop
        return mf_part + knn_part + pop_part

    def used_components_for_weights(self, weights: dict[str, float]) -> list[str]:
        """Which components are actually active for this run (artifact present and weight != 0)."""
        used: list[str] = []
        if self.c.mf is not None and float(weights.get("mf", 0.0)) != 0.0:
            used.append("mf")
        if self.c.knn is not None and float(weights.get("knn", 0.0)) != 0.0:
            used.append("knn")
        if self.c.pop is not None and float(weights.get("pop", 0.0)) != 0.0:
            used.append("pop")
        return used

    def raw_components_for_item(self, user_index: int, item_index: int, weights: dict[str, float]) -> dict[str, float]:
        """Return the raw weighted component contributions for a single item."""
        mf_val = 0.0
        knn_val = 0.0
        pop_val = 0.0
        if self.c.mf is not None:
            mf_val = float(weights.get("mf", 0.0)) * float(self.c.mf[user_index, item_index])
        if self.c.knn is not None:
            knn_val = float(weights.get("knn", 0.0)) * float(self.c.knn[user_index, item_index])
        if self.c.pop is not None:
            pop_val = float(weights.get("pop", 0.0)) * float(self.c.pop[item_index])
        return {"mf": mf_val, "knn": knn_val, "pop": pop_val}

    def explain_item(self, user_index: int, item_index: int, weights: dict[str, float]) -> dict[str, float]:
        """Return normalized source contribution shares for a specific user-item.

        Shares are computed from the *actual weighted raw contributions* used for that item.
        Negative contributions are clamped to 0 for share display.
        """
        raw = self.raw_components_for_item(user_index, item_index, weights)
        used = self.used_components_for_weights(weights)
        return compute_component_shares(raw, used_components=used)

    def get_top_n_for_user(
        self,
        user_index: int,
        n: int = 10,
        weights: dict[str, float] | None = None,
        exclude_item_ids: Sequence[int] | None = None,
        override_mf_scores: np.ndarray | None = None,
    ) -> list[dict[str, float]]:
        """Compute top-N recommendations for a user index.

        Parameters
        ----------
        override_mf_scores : optional ndarray
            If provided, replaces the MF component in the blend with these
            pre-computed scores (e.g. mean-user community baseline).  Shape
            must match ``self.c.item_ids``.
        """
        w = weights or BALANCED_WEIGHTS
        if override_mf_scores is not None:
            # Build blended scores manually, swapping in the override MF component.
            scores = np.zeros(len(self.c.item_ids), dtype=np.float32)
            scores += float(w.get("mf", 0.0)) * override_mf_scores
            if self.c.knn is not None:
                scores += float(w.get("knn", 0.0)) * self.c.knn[user_index]
            if self.c.pop is not None:
                scores += float(w.get("pop", 0.0)) * self.c.pop
        else:
            scores = self._blend(user_index, w)
        if exclude_item_ids:
            mask = np.isin(self.c.item_ids, np.asarray(exclude_item_ids))
            scores = scores.copy()
            scores[mask] = -np.inf
        # Efficient partial selection
        top_idx = np.argpartition(scores, -n)[-n:]
        ordered = top_idx[np.argsort(scores[top_idx])[::-1]]
        result: list[dict[str, float]] = []
        used = self.used_components_for_weights(w)
        for i in ordered:
            raw = self.raw_components_for_item(user_index, int(i), w)
            result.append(
                {
                    "anime_id": int(self.c.item_ids[i]),
                    "score": float(scores[i]),
                    "explanation": compute_component_shares(raw, used_components=used),
                    "_raw_components": raw,
                    "_used_components": used,
                }
            )
        return result

    def get_personalized_recommendations(
        self,
        user_embedding: np.ndarray,
        mf_model,
        n: int = 10,
        weights: dict[str, float] | None = None,
        exclude_item_ids: Sequence[int] | None = None,
    ) -> list[dict[str, float]]:
        """Compute top-N personalized recommendations using user embedding."""
        w = weights or BALANCED_WEIGHTS

        # Enforce MF artifact contract for personalization.
        missing: list[str] = []
        if mf_model is None:
            missing = ["mf_model"]
        else:
            for attr in ("Q", "item_to_index", "index_to_item"):
                if not hasattr(mf_model, attr):
                    missing.append(attr)
        if missing:
            raise ValueError(
                "MF artifact contract violation: missing "
                + ", ".join(missing)
                + ". Required: Q, item_to_index, index_to_item."
            )

        personalized_mf_scores = compute_personalized_scores(user_embedding, mf_model, exclude_anime_ids=None)
        if not personalized_mf_scores:
            return []

        mf_scores_array = np.zeros(len(self.c.item_ids), dtype=np.float32)
        for idx, item_id in enumerate(self.c.item_ids):
            if item_id in personalized_mf_scores:
                mf_scores_array[idx] = personalized_mf_scores[item_id]

        # Blend personalized MF with popularity (kNN is not used in this path today)
        scores = float(w.get("mf", 0.0)) * mf_scores_array
        if self.c.pop is not None:
            scores += float(w.get("pop", 0.0)) * self.c.pop

        if exclude_item_ids:
            mask = np.isin(self.c.item_ids, np.asarray(exclude_item_ids))
            scores = scores.copy()
            scores[mask] = -np.inf

        top_idx = np.argpartition(scores, -n)[-n:]
        ordered = top_idx[np.argsort(scores[top_idx])[::-1]]

        result: list[dict[str, float]] = []
        used: list[str] = []
        if float(w.get("mf", 0.0)) != 0.0:
            used.append("mf")
        if self.c.pop is not None and float(w.get("pop", 0.0)) != 0.0:
            used.append("pop")

        for i in ordered:
            raw_mf = float(w.get("mf", 0.0)) * float(mf_scores_array[int(i)])
            raw_pop = 0.0
            if self.c.pop is not None:
                raw_pop = float(w.get("pop", 0.0)) * float(self.c.pop[int(i)])
            raw = {"mf": raw_mf, "knn": 0.0, "pop": raw_pop}
            result.append(
                {
                    "anime_id": int(self.c.item_ids[i]),
                    "score": float(scores[i]),
                    "explanation": compute_component_shares(raw, used_components=used),
                    "_raw_components": raw,
                    "_used_components": used,
                }
            )
        return result


COMPONENT_ORDER: tuple[str, ...] = ("mf", "knn", "pop")


def compute_component_shares(
    raw_components: dict[str, float],
    *,
    used_components: Sequence[str] | None = None,
    clamp_negative_to_zero: bool = True,
) -> dict[str, float]:
    """Convert raw component contributions into normalized shares.

    Rules:
      - Only components listed in used_components participate in the normalization.
      - If clamp_negative_to_zero=True, negative raw contributions are treated as 0 for sharing.
      - If the (clamped) total is <= 0, all shares are 0.

    Returns a dict with keys mf/knn/pop always present plus:
      - _used: ordered list of the components considered
    """
    used_set = set(used_components) if used_components is not None else set(COMPONENT_ORDER)
    used_ordered = [k for k in COMPONENT_ORDER if k in used_set]

    contrib: dict[str, float] = {}
    for k in used_ordered:
        v = float(raw_components.get(k, 0.0) or 0.0)
        if clamp_negative_to_zero:
            v = max(0.0, v)
        contrib[k] = v
    total = float(sum(contrib.values()))

    out: dict[str, float] = {"mf": 0.0, "knn": 0.0, "pop": 0.0}
    if total > 0.0:
        for k in used_ordered:
            out[k] = contrib[k] / total
    out["_used"] = used_ordered
    return out


# --- Similarity Utilities -------------------------------------------------

@lru_cache(maxsize=16)
def compute_dense_similarity(
    matrix_hash: str,
    seed_index: int,
    feature_matrix: np.ndarray,
    top_k: int,
) -> list[int]:
    """Return top-k similar item indices using dense dot-product similarity.

    Assumes rows correspond to items. Excludes the seed item.
    matrix_hash is any stable identifier used to differentiate cached matrices
    (e.g. str(id(feature_matrix)) or a checksum).
    """
    seed_vec = feature_matrix[seed_index]
    sims = feature_matrix @ seed_vec
    sims[seed_index] = -np.inf
    top = np.argpartition(sims, -top_k)[-top_k:]
    return top[np.argsort(sims[top])[::-1]].tolist()


def get_content_only_recs_for_new_item(
    item_index: int,
    tfidf_matrix: np.ndarray,
    top_k: int = 10,
) -> list[int]:
    """Content-only TF-IDF similarity path for cold-start items."""
    seed_vec = tfidf_matrix[item_index]
    sims = tfidf_matrix @ seed_vec
    sims[item_index] = -np.inf
    top = np.argpartition(sims, -top_k)[-top_k:]
    return top[np.argsort(sims[top])[::-1]].tolist()


def choose_weights(mode: str) -> dict[str, float]:
    """Return weight preset by mode string ('balanced' or 'diversity')."""
    mode_norm = mode.strip().lower()
    if mode_norm.startswith("div"):
        return DIVERSITY_EMPHASIZED_WEIGHTS
    return BALANCED_WEIGHTS


__all__ = [
    "HybridComponents",
    "HybridRecommender",
    "choose_weights",
    "compute_component_shares",
    "compute_dense_similarity",
    "get_content_only_recs_for_new_item",
]
