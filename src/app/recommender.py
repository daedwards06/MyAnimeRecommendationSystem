"""Hybrid recommendation and similarity utilities.

This module provides a lightweight inference layer that blends
MF, kNN, and popularity signals and exposes explanation shares.

Artifact contract enforcement (fail-loud) is expected to happen at
app startup (see `src.app.artifacts_loader`). This module avoids
constructing placeholder score arrays for missing artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np

from .constants import BALANCED_WEIGHTS, DIVERSITY_EMPHASIZED_WEIGHTS
from src.models.user_embedding import compute_personalized_scores


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

    mf: Optional[np.ndarray]
    knn: Optional[np.ndarray]
    pop: Optional[np.ndarray]
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

    def _blend(self, user_index: int, weights: Dict[str, float]) -> np.ndarray:
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

    def explain_item(self, user_index: int, item_index: int, weights: Dict[str, float]) -> Dict[str, float]:
        """Return normalized source contribution shares for a specific user-item."""
        mf_val = 0.0
        knn_val = 0.0
        pop_val = 0.0
        if self.c.mf is not None:
            mf_val = weights.get("mf", 0.0) * float(self.c.mf[user_index, item_index])
        if self.c.knn is not None:
            knn_val = weights.get("knn", 0.0) * float(self.c.knn[user_index, item_index])
        if self.c.pop is not None:
            pop_val = weights.get("pop", 0.0) * float(self.c.pop[item_index])
        total = mf_val + knn_val + pop_val
        if total <= 0:
            return {"mf": 0.0, "knn": 0.0, "pop": 0.0}
        return {"mf": mf_val / total, "knn": knn_val / total, "pop": pop_val / total}

    def get_top_n_for_user(
        self,
        user_index: int,
        n: int = 10,
        weights: Optional[Dict[str, float]] = None,
        exclude_item_ids: Optional[Sequence[int]] = None,
    ) -> List[Dict[str, float]]:
        """Compute top-N recommendations for a user index.

        Parameters
        ----------
        user_index : int
            Internal user index (aligned with score matrices).
        n : int
            Number of items to return.
        weights : Optional[Dict[str, float]]
            Blending weights; defaults to BALANCED_WEIGHTS.
        exclude_item_ids : Optional[Sequence[int]]
            External item IDs to force out of ranking (e.g., already liked).
        """
        w = weights or BALANCED_WEIGHTS
        scores = self._blend(user_index, w)
        if exclude_item_ids:
            mask = np.isin(self.c.item_ids, np.asarray(exclude_item_ids))
            scores = scores.copy()
            scores[mask] = -np.inf
        # Efficient partial selection
        top_idx = np.argpartition(scores, -n)[-n:]
        ordered = top_idx[np.argsort(scores[top_idx])[::-1]]
        result: List[Dict[str, float]] = []
        for i in ordered:
            result.append(
                {
                    "anime_id": int(self.c.item_ids[i]),
                    "score": float(scores[i]),
                    "explanation": self.explain_item(user_index, i, w),
                }
            )
        return result

    def get_personalized_recommendations(
        self,
        user_embedding: np.ndarray,
        mf_model,
        n: int = 10,
        weights: Optional[Dict[str, float]] = None,
        exclude_item_ids: Optional[Sequence[int]] = None,
    ) -> List[Dict[str, float]]:
        """Compute top-N personalized recommendations using user embedding.

        Parameters
        ----------
        user_embedding : np.ndarray
            User embedding vector (shape: [n_factors]) generated from ratings.
        mf_model
            Matrix factorization model with Q (item factors) and item_to_index mapping.
        n : int
            Number of items to return.
        weights : Optional[Dict[str, float]]
            Blending weights; defaults to BALANCED_WEIGHTS.
        exclude_item_ids : Optional[Sequence[int]]
            External item IDs to exclude from ranking.
        
        Returns
        -------
        List[Dict[str, float]]
            Top-N recommendations with anime_id, score, and explanation.
        """
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
        
        # Compute personalized MF scores using user embedding
        personalized_mf_scores = compute_personalized_scores(
            user_embedding, mf_model, exclude_anime_ids=None
        )

        # If we cannot score anything (e.g., no overlap with training items),
        # return no results rather than ranking arbitrary items.
        if not personalized_mf_scores:
            return []
        
        # Build personalized MF score array aligned with item_ids
        # Initialize with zeros
        mf_scores_array = np.zeros(len(self.c.item_ids), dtype=np.float32)
        for idx, item_id in enumerate(self.c.item_ids):
            if item_id in personalized_mf_scores:
                mf_scores_array[idx] = personalized_mf_scores[item_id]
        
        # Blend personalized MF with kNN and popularity
        scores = w.get("mf", 0.0) * mf_scores_array
        if self.c.knn is not None and "knn" in w:
            # For kNN, use seed-based scoring (no user-specific kNN yet)
            # Could be extended later with seed blending
            pass
        if self.c.pop is not None:
            scores += w.get("pop", 0.0) * self.c.pop
        
        # Apply exclusion filter
        if exclude_item_ids:
            mask = np.isin(self.c.item_ids, np.asarray(exclude_item_ids))
            scores = scores.copy()
            scores[mask] = -np.inf
        
        # Efficient partial selection
        top_idx = np.argpartition(scores, -n)[-n:]
        ordered = top_idx[np.argsort(scores[top_idx])[::-1]]
        
        result: List[Dict[str, float]] = []
        for i in ordered:
            result.append(
                {
                    "anime_id": int(self.c.item_ids[i]),
                    "score": float(scores[i]),
                    "explanation": {
                        "mf": w.get("mf", 0.0),
                        "knn": 0.0,
                        "pop": w.get("pop", 0.0),
                    },
                }
            )
        return result


# --- Similarity Utilities -------------------------------------------------

@lru_cache(maxsize=16)
def compute_dense_similarity(
    matrix_hash: str,
    seed_index: int,
    feature_matrix: np.ndarray,
    top_k: int,
) -> List[int]:
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
) -> List[int]:
    """Content-only TF-IDF similarity path for cold-start items."""
    seed_vec = tfidf_matrix[item_index]
    sims = tfidf_matrix @ seed_vec
    sims[item_index] = -np.inf
    top = np.argpartition(sims, -top_k)[-top_k:]
    return top[np.argsort(sims[top])[::-1]].tolist()


def choose_weights(mode: str) -> Dict[str, float]:
    """Return weight preset by mode string ('balanced' or 'diversity')."""
    mode_norm = mode.strip().lower()
    if mode_norm.startswith("div"):
        return DIVERSITY_EMPHASIZED_WEIGHTS
    return BALANCED_WEIGHTS


__all__ = [
    "HybridComponents",
    "HybridRecommender",
    "compute_dense_similarity",
    "get_content_only_recs_for_new_item",
    "choose_weights",
]
