from __future__ import annotations
import numpy as np
import pandas as pd


def interaction_signals(interactions: pd.DataFrame) -> pd.DataFrame:
    """num_ratings, mean_rating, popularity = log1p(num_ratings) * mean_rating."""
    grp = (
        interactions.groupby("anime_id")
        .agg(num_ratings=("rating", "size"), mean_rating=("rating", "mean"))
        .reset_index()
    )
    grp["popularity"] = np.log1p(grp["num_ratings"]) * grp["mean_rating"].fillna(0.0)
    return grp


def recency_from_metadata(
    meta: pd.DataFrame, date_cols: list[str] | None = None
) -> pd.DataFrame:
    """released_year, days_since_release derived from first available date col."""
    date_cols = date_cols or ["aired_from", "release_date"]
    out = meta[["anime_id"]].copy()
    date = None
    for c in date_cols:
        if c in meta.columns:
            d = pd.to_datetime(meta[c], errors="coerce", utc=True)
            date = d if date is None else date.fillna(d)
    if date is None:
        out["released_year"] = pd.NA
        out["days_since_release"] = pd.NA
        return out
    now = pd.Timestamp.utcnow()
    out["released_year"] = date.dt.year
    out["days_since_release"] = (now - date).dt.days.astype("Int64")
    return out
