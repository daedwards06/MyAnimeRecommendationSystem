from __future__ import annotations

import numpy as np
import pandas as pd


def popularity_scores(interactions: pd.DataFrame) -> pd.Series:
    """Compute popularity score per anime_id using log(1+count) * mean_rating.

    Expects columns: anime_id, rating.
    Returns a Series indexed by anime_id sorted descending by score.
    """
    agg = interactions.groupby("anime_id").agg(
        num_ratings=("rating", "count"),
        mean_rating=("rating", "mean"),
    )
    agg["pop_score"] = np.log1p(agg["num_ratings"]) * agg["mean_rating"]
    return agg["pop_score"].sort_values(ascending=False)


def recommend_popularity(
    interactions: pd.DataFrame, top_k: int = 10, exclude: set[int] | None = None
) -> list[int]:
    """Return top_k anime_ids by popularity, optionally excluding a set (e.g., already seen)."""
    scores = popularity_scores(interactions)
    ranked = [int(i) for i in scores.index]
    if exclude:
        ranked = [i for i in ranked if i not in exclude]
    return ranked[:top_k]
