"""Data cleaning and splitting utilities for Phase 2.

This module provides a small, testable surface for:
- Loading raw Kaggle CSVs (ratings/anime/users where applicable)
- Basic cleaning (null handling, type coercion, duplicate removal)
- Genre/theme parsing from metadata (plus studios/demographics when present)
- Train/validation/test splitting (user-aware and optional time-based)

Implementations are conservative and avoid heavy dependencies.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class SplitConfig:
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    time_col: str | None = None  # if provided, do time-aware split
    user_col: str = "user_id"
    item_col: str = "anime_id"


# ---------- Loading ----------

def load_ratings(path: Path) -> pd.DataFrame:
    """Load Kaggle ratings and coerce to expected types.
    Expected columns: user_id, anime_id, rating, [timestamp?].
    """
    df = pd.read_csv(path)
    if "user_id" in df.columns:
        df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("Int64")
    if "anime_id" in df.columns:
        df["anime_id"] = pd.to_numeric(df["anime_id"], errors="coerce").astype("Int64")
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    # Drop rows missing essentials and finalize integer types
    df = df.dropna(subset=[c for c in ["user_id", "anime_id", "rating"] if c in df.columns])
    for c in ("user_id", "anime_id"):
        if c in df.columns:
            df[c] = df[c].astype(int)
    return df


def load_anime(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize known fields if present
    for col in ("genres", "themes", "studios", "demographics"):
        if col in df.columns:
            df[col] = df[col].fillna("")
    if "anime_id" in df.columns:
        df["anime_id"] = pd.to_numeric(df["anime_id"], errors="coerce").astype("Int64")
        df = df.dropna(subset=["anime_id"])
        df["anime_id"] = df["anime_id"].astype(int)
    return df


def load_kaggle_items(path: Path) -> pd.DataFrame:
    """Load Kaggle baseline anime.csv to anchor cold-start detection."""
    return load_anime(path)


# ---------- Cleaning ----------

def clean_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean interactions by removing nulls/dupes and clipping ratings.

    - Drop null essentials
    - Deduplicate (user_id, anime_id), keeping last to resolve conflicts
    - Clip ratings to non-negative (adjust upper bound if needed)
    """
    essentials = {"user_id", "anime_id", "rating"}
    if essentials.issubset(df.columns):
        df = df.dropna(subset=list(essentials))
        df = df.drop_duplicates(subset=["user_id", "anime_id"], keep="last")
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
        df["rating"] = df["rating"].clip(lower=0.0)
    return df


def _split_str_list(x: object, seps: Iterable[str] = (",", "|")) -> list[str]:
    """Split strings by common separators, trimming spaces; [] for null/empty."""
    if not isinstance(x, str) or not x.strip():
        return []
    s = x
    for sep in seps:
        s = s.replace(sep, ",")
    return [t.strip() for t in s.split(",") if t.strip()]


def parse_genre_list(x) -> list[str]:
    """Coerce strings or array-like to a list[str]. Strings split on comma/pipe.
    Accept list/tuple/set/np.ndarray/pd.Series and return cleaned strings.
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return []
    if isinstance(x, (list, tuple, set)):
        return [str(t).strip() for t in x if str(t).strip()]
    if isinstance(x, np.ndarray):
        return [str(t).strip() for t in x.tolist() if str(t).strip()]
    if isinstance(x, pd.Series):
        return [str(t).strip() for t in x.dropna().tolist() if str(t).strip()]
    if isinstance(x, str):
        s = x.replace("|", ",")
        return [p.strip() for p in s.split(",") if p.strip()]
    return []


def normalize_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Add *_list columns for genres/themes/studios/demographics when present."""
    out = df.copy()
    # Use robust list coercion for all supported columns (handles list/array/Series/strings)
    if "genres" in out.columns and "genres_list" not in out.columns:
        out["genres_list"] = out["genres"].apply(parse_genre_list)
    if "themes" in out.columns and "themes_list" not in out.columns:
        out["themes_list"] = out["themes"].apply(parse_genre_list)
    if "studios" in out.columns and "studios_list" not in out.columns:
        out["studios_list"] = out["studios"].apply(parse_genre_list)
    if "demographics" in out.columns and "demographics_list" not in out.columns:
        out["demographics_list"] = out["demographics"].apply(parse_genre_list)
    # Optionally pass-through already-normalized arrays in *_list columns
    for col in ("genres_list", "themes_list"):
        if col in out.columns:
            out[col] = out[col].apply(parse_genre_list)
    return out


# ---------- Splitting ----------

def user_based_split(df: pd.DataFrame, cfg: SplitConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Per-user split: for each user, assign interactions to train/val/test.
    If time_col is provided, sort per user by time before splitting to reduce leakage.
    """
    assert cfg.user_col in df.columns and cfg.item_col in df.columns
    val_ratio = cfg.val_ratio
    test_ratio = cfg.test_ratio
    # Deterministic shuffling handled via pandas.sample(random_state)

    def split_user(group: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        g = group.sort_values(cfg.time_col) if cfg.time_col and cfg.time_col in group.columns else group.sample(frac=1.0, random_state=42)
        n = len(g)
        n_test = int(round(n * test_ratio))
        n_val = int(round(n * val_ratio))
        test = g.tail(n_test) if n_test > 0 else g.iloc[0:0]
        val = g.iloc[max(0, n - n_test - n_val):max(0, n - n_test)] if n_val > 0 else g.iloc[0:0]
        train = g.iloc[0:max(0, n - n_val - n_test)]
        return train, val, test

    trains = []
    vals = []
    tests = []
    for _, grp in df.groupby(cfg.user_col, sort=False):
        tr, va, te = split_user(grp)
        trains.append(tr)
        vals.append(va)
        tests.append(te)

    train_df = pd.concat(trains, ignore_index=True)
    val_df = pd.concat(vals, ignore_index=True)
    test_df = pd.concat(tests, ignore_index=True)
    return train_df, val_df, test_df


__all__ = [
    "SplitConfig",
    "clean_interactions",
    "load_anime",
    "load_ratings",
    "normalize_metadata",
    "user_based_split",
]
