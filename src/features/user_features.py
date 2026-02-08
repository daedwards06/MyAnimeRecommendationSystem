from __future__ import annotations

import pandas as pd


def build_user_features(
    interactions: pd.DataFrame,
    meta: pd.DataFrame,
    time_col: str | None = None,
) -> pd.DataFrame:
    """Compute simple per-user features for personalization.

    - interactions_per_user: count of rows per user
    - mean_rating_per_user: average rating per user (if rating exists)
    - days_since_last: days since last interaction (if time_col provided)
    - genre_diversity: number of distinct genres interacted with (from meta.genres)
    """
    df = interactions.copy()
    if "user_id" not in df.columns:
        raise KeyError("interactions missing user_id column")
    if "anime_id" not in df.columns:
        raise KeyError("interactions missing anime_id column")

    # Basic aggregates
    agg = df.groupby("user_id").agg(
        interactions_per_user=("anime_id", "size"),
        mean_rating_per_user=("rating", "mean"),
    )

    # Recency
    if time_col and time_col in df.columns:
        t = pd.to_datetime(df[time_col], errors="coerce", utc=True)
        last_t = df.assign(_t=t).groupby("user_id")["_t"].max()
        now = pd.Timestamp.utcnow()
        days_since_last = (now - last_t).dt.days.astype("Int64")
        agg["days_since_last"] = days_since_last
    else:
        agg["days_since_last"] = pd.NA

    # Genre diversity via meta.genres
    if "genres" in meta.columns:
        genres = meta[["anime_id", "genres"]].copy()
        # Explode genres list
        exploded = genres.explode("genres").dropna(subset=["genres"])  # rows: (anime_id, genre)
        ui = df[["user_id", "anime_id"]].drop_duplicates()
        merged = ui.merge(exploded, on="anime_id", how="left").dropna(subset=["genres"])  # (user_id, genre)
        diversity = merged.groupby("user_id")["genres"].nunique()
        agg["genre_diversity"] = diversity
    else:
        agg["genre_diversity"] = pd.NA

    agg = agg.reset_index()
    return agg
