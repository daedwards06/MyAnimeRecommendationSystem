from __future__ import annotations
import numpy as np
import pandas as pd


def sample_negatives(
    interactions: pd.DataFrame,
    items: pd.DataFrame,
    num_neg_per_pos: int = 5,
    strategy: str = "pop_recent",
    seed: int | None = 42,
) -> pd.DataFrame:
    """Sample negative (user, anime_id) pairs not present in interactions.

    Strategies:
    - pop_recent: probability proportional to normalized popularity and inverse days_since_release

    Returns a DataFrame with columns [user_id, anime_id, label] where label=0 for negatives.
    """
    rng = np.random.default_rng(seed)
    inter = interactions[["user_id", "anime_id"]].drop_duplicates()
    by_user = inter.groupby("user_id")["anime_id"].apply(set)

    cand = items[["anime_id", "popularity", "days_since_release"]].copy()
    cand["popularity"] = pd.to_numeric(cand["popularity"], errors="coerce").fillna(0.0)
    # Lower days_since_release => more recent; convert to recency score
    recency = pd.to_numeric(cand["days_since_release"], errors="coerce")
    recency = recency.fillna(recency.max() if pd.notna(recency.max()) else 0)
    cand["recency_score"] = 1.0 / (1.0 + recency)

    # Build sampling weights
    w = cand["popularity"].astype(float)
    w = (w - w.min()) / (w.max() - w.min() + 1e-8)
    if strategy == "pop_recent":
        w = 0.7 * w + 0.3 * cand["recency_score"].astype(float)
    w = w.clip(lower=1e-8)
    cand["weight"] = w

    anime_ids = cand["anime_id"].to_numpy()
    weights = cand["weight"].to_numpy()
    weights = weights / weights.sum()

    samples = []
    for user_id, pos_set in by_user.items():
        needed = num_neg_per_pos * len(pos_set)
        # Avoid sampling positives
        mask = ~np.isin(anime_ids, list(pos_set))
        pool = anime_ids[mask]
        pool_w = weights[mask]
        pool_w = pool_w / pool_w.sum()
        if len(pool) == 0 or needed == 0:
            continue
        # Sample with replacement for efficiency
        negs = rng.choice(pool, size=needed, replace=True, p=pool_w)
        samples.extend((int(user_id), int(aid), 0) for aid in negs)

    if not samples:
        return pd.DataFrame(columns=["user_id", "anime_id", "label"])
    out = pd.DataFrame(samples, columns=["user_id", "anime_id", "label"])
    return out
