from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def _build_mappings(df: pd.DataFrame) -> Tuple[Dict[int, int], Dict[int, int]]:
    users = df["user_id"].astype(int).unique()
    items = df["anime_id"].astype(int).unique()
    u2i = {u: i for i, u in enumerate(users)}
    it2i = {it: i for i, it in enumerate(items)}
    return u2i, it2i


def _build_ui(df: pd.DataFrame, u2i: Dict[int, int], it2i: Dict[int, int]) -> csr_matrix:
    rows = df["user_id"].map(u2i).values
    cols = df["anime_id"].map(it2i).values
    data = df["rating"].astype(float).values
    return csr_matrix((data, (rows, cols)), shape=(len(u2i), len(it2i)))


@dataclass
class FunkSVDRecommender:
    """Simple matrix factorization via SGD (FunkSVD) for explicit ratings.

    Optimization: minimize squared error with L2 regularization.
    """

    n_factors: int = 64
    lr: float = 0.005
    reg: float = 0.05
    n_epochs: int = 10
    random_state: int = 42

    def __post_init__(self):
        self.user_to_index: Dict[int, int] | None = None
        self.item_to_index: Dict[int, int] | None = None
        self.index_to_user: Dict[int, int] | None = None
        self.index_to_item: Dict[int, int] | None = None
        self.P: np.ndarray | None = None  # users x factors
        self.Q: np.ndarray | None = None  # items x factors
        self.global_mean: float = 0.0

    def fit(self, interactions: pd.DataFrame) -> "FunkSVDRecommender":
        """Train with centered ratings, small init, L2 reg, and gradient clipping to avoid overflow."""
        df = interactions.dropna(subset=["user_id", "anime_id", "rating"]).copy()
        rng = np.random.default_rng(self.random_state)
        u2i, it2i = _build_mappings(df)
        self.user_to_index = u2i
        self.item_to_index = it2i
        self.index_to_user = {v: k for k, v in u2i.items()}
        self.index_to_item = {v: k for k, v in it2i.items()}

        # Build training triplets and center ratings
        u_idx = df["user_id"].map(u2i).astype(int).values
        i_idx = df["anime_id"].map(it2i).astype(int).values
        ratings = df["rating"].astype(float).values
        self.global_mean = float(np.nanmean(ratings))
        y = ratings - self.global_mean

        n_u = len(u2i)
        n_i = len(it2i)
        self.P = (0.01 * rng.standard_normal((n_u, self.n_factors))).astype(np.float32)
        self.Q = (0.01 * rng.standard_normal((n_i, self.n_factors))).astype(np.float32)

        n_obs = len(y)
        for _ in range(self.n_epochs):
            order = rng.permutation(n_obs)
            for idx in order:
                u = u_idx[idx]
                i = i_idx[idx]
                r = y[idx]
                # prediction without global mean (already centered)
                pred = float(self.P[u] @ self.Q[i])
                err = r - pred
                # clip error to stabilize updates
                if err > 5.0:
                    err = 5.0
                elif err < -5.0:
                    err = -5.0
                p_u = self.P[u]
                q_i = self.Q[i]
                # gradient updates with L2
                self.P[u] = p_u + self.lr * (err * q_i - self.reg * p_u)
                self.Q[i] = q_i + self.lr * (err * p_u - self.reg * q_i)
        return self

    def predict_user(self, user_id: int) -> np.ndarray:
        assert self.P is not None and self.Q is not None and self.user_to_index is not None
        if user_id not in self.user_to_index:
            return np.zeros(self.Q.shape[0], dtype=np.float32)
        uidx = self.user_to_index[user_id]
        scores = self.global_mean + self.P[uidx] @ self.Q.T
        return scores

    def recommend(self, user_id: int, top_k: int = 10, exclude: set[int] | None = None) -> List[int]:
        scores = self.predict_user(user_id)
        if exclude:
            # mask seen
            for it in exclude:
                if it in self.item_to_index:
                    scores[self.item_to_index[it]] = -np.inf
        top_idx = np.argpartition(-scores, range(min(top_k, len(scores))))[:top_k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]
        return [self.index_to_item[i] for i in top_idx if np.isfinite(scores[i])]
