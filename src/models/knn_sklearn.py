from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize


def _build_mappings(df: pd.DataFrame) -> Tuple[Dict[int, int], Dict[int, int]]:
    users = df["user_id"].astype(int).unique()
    items = df["anime_id"].astype(int).unique()
    u2i = {u: i for i, u in enumerate(users)}
    it2i = {it: i for i, it in enumerate(items)}
    return u2i, it2i


def _build_user_item_matrix(df: pd.DataFrame, u2i: Dict[int, int], it2i: Dict[int, int]) -> csr_matrix:
    rows = df["user_id"].map(u2i).values
    cols = df["anime_id"].map(it2i).values
    data = df["rating"].astype(float).values
    n_users = len(u2i)
    n_items = len(it2i)
    mat = csr_matrix((data, (rows, cols)), shape=(n_users, n_items))
    return mat


@dataclass
class ItemKNNRecommender:
    """Lightweight item-based cosine recommender.

    Instead of querying k-nearest-neighbors per seen item (which can bias toward high-degree items
    and returns zero relevance for sparse holdouts), we build an item-user matrix and compute a
    user preference vector as the rating-weighted sum of normalized item vectors the user has seen.
    Recommendations are ranked by cosine similarity between each candidate item vector and this
    user profile.
    """

    normalize_items: bool = True
    min_rating: float = -np.inf  # allow filtering low-quality interactions if desired
    center_ratings: bool = True  # center user ratings when building profile
    rating_weight_power: float = 1.0  # raise |rating|^p to emphasize strong prefs (sign preserved)
    profile_shrinkage: float = 10.0  # scale profile by n_rated / (n_rated + shrinkage)
    popularity_weight: float = 0.02  # small popularity prior added to scores

    def __post_init__(self):
        self.user_to_index: Dict[int, int] | None = None
        self.item_to_index: Dict[int, int] | None = None
        self.index_to_item: Dict[int, int] | None = None
        self.item_user_matrix: csr_matrix | None = None  # shape: n_items x n_users (normalized if chosen)
        self.raw_item_user: csr_matrix | None = None
        self.item_pop: np.ndarray | None = None

    def fit(self, interactions: pd.DataFrame) -> "ItemKNNRecommender":
        # Optionally filter by min_rating
        df = interactions[interactions["rating"].astype(float) >= self.min_rating].copy()
        u2i, it2i = _build_mappings(df)
        mat_ui = _build_user_item_matrix(df, u2i, it2i)  # users x items
        mat_iu = mat_ui.T.tocsr()  # items x users
        if self.normalize_items:
            # row-wise (item-wise) L2 normalization for cosine scoring
            mat_iu = normalize(mat_iu, axis=1)
        self.user_to_index = u2i
        self.item_to_index = it2i
        self.index_to_item = {v: k for k, v in it2i.items()}
        self.item_user_matrix = mat_iu
        self.raw_item_user = mat_ui.T.tocsr()
        # Popularity prior per item: log1p(counts) normalized to [0,1]
        counts = np.bincount(mat_ui.indices, minlength=mat_ui.shape[1]).astype(np.float32)
        pop = np.log1p(counts)
        maxp = float(pop.max()) if pop.size > 0 else 1.0
        self.item_pop = (pop / maxp) if maxp > 0 else pop
        return self

    def _user_profile(self, user_id: int) -> np.ndarray:
        """Build a user profile in the user-space (length = n_users) as a
        rating-weighted combination of item vectors.

        We compute: profile = (ratings_row @ item_user_matrix), where
        ratings_row is a 1 x n_items sparse row for the user, and
        item_user_matrix is (n_items x n_users). Result is 1 x n_users.
        """
        assert self.item_user_matrix is not None and self.user_to_index is not None and self.raw_item_user is not None
        uidx = self.user_to_index[user_id]
        # items x 1 vector of ratings for user
        user_ratings_col = self.raw_item_user.getcol(uidx)
        if user_ratings_col.nnz == 0:
            return np.zeros(self.item_user_matrix.shape[1], dtype=np.float32)
        # Optionally center ratings for this user
        ratings_row = user_ratings_col.T
        if ratings_row.nnz > 0:
            col = user_ratings_col.copy()
            # Center ratings if enabled
            if self.center_ratings and col.data.size:
                mu = float(col.data.mean())
                col.data = (col.data - mu).astype(np.float32)
            # Apply rating weight power (preserve sign)
            if col.data.size and self.rating_weight_power != 1.0:
                sign = np.sign(col.data)
                col.data = sign * (np.abs(col.data) ** float(self.rating_weight_power))
            ratings_row = col.T
        # (1 x items) @ (items x users) -> (1 x users)
        # Convert sparse result to dense 1D vector safely (compat with SciPy versions)
        profile_sparse = (ratings_row @ self.item_user_matrix)
        profile = profile_sparse.toarray().ravel().astype(np.float32)
        # Apply profile shrinkage to avoid overconfident profiles for very short histories
        n_rated = float(user_ratings_col.nnz)
        if self.profile_shrinkage > 0 and n_rated > 0:
            shrink = n_rated / (n_rated + float(self.profile_shrinkage))
            profile *= shrink
        return profile

    def recommend(self, user_id: int, top_k: int = 10, exclude_seen: bool = True) -> List[int]:
        if self.user_to_index is None or self.item_user_matrix is None:
            raise RuntimeError("Model not fitted.")
        if user_id not in self.user_to_index:
            return []
        profile = self._user_profile(user_id)  # user-dimension vector
        if np.allclose(profile, 0):
            # Cold-start: return empty list; caller can fallback to popularity
            return []
        # Compute cosine similarity: item_row (items x users) dot profile / (||item_row|| * ||profile||)
        item_mat = self.item_user_matrix  # items x users (normalized rows if normalize_items)
        denom = np.linalg.norm(profile) if not self.normalize_items else np.linalg.norm(profile)
        if denom == 0:
            return []
        sims = (item_mat @ profile) / denom  # since rows already normalized, divide by profile norm only
        # Add small popularity prior to stabilize ranking
        if self.item_pop is not None and self.popularity_weight != 0.0:
            sims = sims + self.popularity_weight * self.item_pop
        sims = np.asarray(sims).ravel()
        # Exclude seen items
        if exclude_seen:
            uidx = self.user_to_index[user_id]
            seen = self.raw_item_user.getcol(uidx).nonzero()[0]
            sims[seen] = -np.inf
        # Top-k indices
        k = min(top_k, len(sims))
        top_idx = np.argpartition(-sims, k - 1)[:k]
        top_idx = top_idx[np.argsort(-sims[top_idx])]
        return [self.index_to_item[i] for i in top_idx if np.isfinite(sims[i])]

    def score_all(self, user_id: int, exclude_seen: bool = True) -> Dict[int, float]:
        """Return scores for all items for a user. Useful for hybrid blending.

        Scores are cosine similarities with optional popularity prior; higher is better.
        """
        if self.user_to_index is None or self.item_user_matrix is None:
            raise RuntimeError("Model not fitted.")
        if user_id not in self.user_to_index:
            return {}
        profile = self._user_profile(user_id)
        if np.allclose(profile, 0):
            return {}
        item_mat = self.item_user_matrix
        denom = np.linalg.norm(profile) if not self.normalize_items else np.linalg.norm(profile)
        if denom == 0:
            return {}
        sims = (item_mat @ profile) / denom
        if self.item_pop is not None and self.popularity_weight != 0.0:
            sims = sims + self.popularity_weight * self.item_pop
        sims = np.asarray(sims).ravel()
        # Optionally mask seen
        if exclude_seen:
            uidx = self.user_to_index[user_id]
            seen = self.raw_item_user.getcol(uidx).nonzero()[0]
            sims[seen] = -np.inf
        # Map back to item ids
        out: Dict[int, float] = {}
        for idx, sc in enumerate(sims):
            if np.isfinite(sc):
                out[self.index_to_item[idx]] = float(sc)
        return out
