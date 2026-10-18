from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


@dataclass
class ImplicitALSRecommender:
    """Implicit-feedback matrix factorization (Hu, Koren & Volinsky, 2008) fit by ALS.

    Every interaction is a positive "watched" signal with confidence 1 + alpha, whatever its
    rating; every unobserved pair is a negative with confidence 1. FunkSVD only fits the observed
    ratings, so it never learns which items a user chose to watch; this objective is that signal.
    """

    n_factors: int = 64
    reg: float = 0.1
    alpha: float = 10.0
    n_iters: int = 10
    random_state: int = 42

    def __post_init__(self):
        self.user_to_index: dict[int, int] | None = None
        self.item_to_index: dict[int, int] | None = None
        self.index_to_item: dict[int, int] | None = None
        self.X: np.ndarray | None = None  # users x factors
        self.Y: np.ndarray | None = None  # items x factors

    def fit(self, interactions: pd.DataFrame) -> ImplicitALSRecommender:
        df = interactions.dropna(subset=["user_id", "anime_id"])
        users = df["user_id"].astype(int).unique()
        items = df["anime_id"].astype(int).unique()
        self.user_to_index = {u: i for i, u in enumerate(users)}
        self.item_to_index = {it: i for i, it in enumerate(items)}
        self.index_to_item = {i: it for it, i in self.item_to_index.items()}

        rows = df["user_id"].map(self.user_to_index).to_numpy()
        cols = df["anime_id"].map(self.item_to_index).to_numpy()
        ui = csr_matrix((np.ones(len(df), dtype=np.float32), (rows, cols)), shape=(len(users), len(items)))
        ui.sum_duplicates()
        iu = ui.T.tocsr()

        rng = np.random.default_rng(self.random_state)
        self.X = (0.01 * rng.standard_normal((len(users), self.n_factors))).astype(np.float64)
        self.Y = (0.01 * rng.standard_normal((len(items), self.n_factors))).astype(np.float64)
        for _ in range(self.n_iters):
            self.X = self._solve(ui, self.Y)
            self.Y = self._solve(iu, self.X)
        self.X = self.X.astype(np.float32)
        self.Y = self.Y.astype(np.float32)
        return self

    def _solve(self, mat: csr_matrix, fixed: np.ndarray) -> np.ndarray:
        """Exact least-squares update of one side, rows of `mat` against the `fixed` factors.

        With binary preferences and uniform confidence, row u's normal equations are
        (FᵀF + α·F_uᵀF_u + λI) x_u = (1 + α)·Σ F_u, where F_u are the factors of u's items.
        """
        base = fixed.T @ fixed + self.reg * np.eye(self.n_factors)
        out = np.zeros((mat.shape[0], self.n_factors))
        indptr, indices = mat.indptr, mat.indices
        for r in range(mat.shape[0]):
            idx = indices[indptr[r] : indptr[r + 1]]
            if idx.size == 0:
                continue
            f_u = fixed[idx]
            out[r] = np.linalg.solve(base + self.alpha * (f_u.T @ f_u), (1.0 + self.alpha) * f_u.sum(axis=0))
        return out

    def predict_user(self, user_id: int) -> np.ndarray:
        assert self.X is not None and self.Y is not None and self.user_to_index is not None
        if user_id not in self.user_to_index:
            return np.zeros(self.Y.shape[0], dtype=np.float32)
        return self.Y @ self.X[self.user_to_index[user_id]]

    def recommend(self, user_id: int, top_k: int = 10, exclude: set[int] | None = None) -> list[int]:
        assert self.item_to_index is not None and self.index_to_item is not None
        scores = self.predict_user(user_id)
        for it in exclude or ():
            if it in self.item_to_index:
                scores[self.item_to_index[it]] = -np.inf
        k = min(top_k, len(scores))
        top_idx = np.argpartition(-scores, k - 1)[:k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]
        return [self.index_to_item[i] for i in top_idx if np.isfinite(scores[i])]
