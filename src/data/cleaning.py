"""Data cleaning and splitting utilities (skeleton).

This module provides a small, testable surface for:
- Loading raw Kaggle CSVs (ratings/anime/users where applicable)
- Basic cleaning (null handling, type coercion, duplicate removal)
- Genre/theme parsing from metadata
- Train/validation/test splitting (user-aware and optional time-based)

Implementations are conservative and avoid heavy dependencies.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class SplitConfig:
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    time_col: Optional[str] = None  # if provided, do time-aware split
    user_col: str = "user_id"
    item_col: str = "anime_id"


# ---------- Loading ----------

def load_ratings(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expected columns: user_id, anime_id, rating, (timestamp optional)
    # Coerce dtypes
    if "user_id" in df.columns:
        df["user_id"] = df["user_id"].astype(int)
    if "anime_id" in df.columns:
        df["anime_id"] = df["anime_id"].astype(int)
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    return df


def load_anime(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize known fields if present
    for col in ("genres", "themes"):
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df


# ---------- Cleaning ----------

def clean_interactions(df: pd.DataFrame) -> pd.DataFrame:
    # Drop rows with missing essentials
    df = df.dropna(subset=["user_id", "anime_id", "rating"]) if set(["user_id","anime_id","rating"]).issubset(df.columns) else df
    # Remove duplicates (keep last)
    if set(["user_id","anime_id"]).issubset(df.columns):
        df = df.drop_duplicates(subset=["user_id", "anime_id"], keep="last")
    # Clip ratings to reasonable range if known (e.g., 1..10)
    if "rating" in df.columns:
        df["rating"] = df["rating"].clip(lower=0.0)  # adjust after inspecting dataset scale
    return df


def parse_genre_list(x: str) -> list[str]:
    if not isinstance(x, str) or not x.strip():
        return []
    # Kaggle often uses comma-separated genres
    parts = [p.strip() for p in x.split(",") if p.strip()]
    return parts


def normalize_metadata(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "genres" in out.columns:
        out["genres_list"] = out["genres"].apply(parse_genre_list)
    if "themes" in out.columns:
        out["themes_list"] = out["themes"].apply(parse_genre_list)
    return out


# ---------- Splitting ----------

def user_based_split(df: pd.DataFrame, cfg: SplitConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Per-user split: for each user, assign interactions to train/val/test.
    If time_col is provided, sort per user by time before splitting to reduce leakage.
    """
    assert cfg.user_col in df.columns and cfg.item_col in df.columns
    val_ratio = cfg.val_ratio
    test_ratio = cfg.test_ratio
    rng = np.random.default_rng(42)

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
    "load_ratings",
    "load_anime",
    "clean_interactions",
    "normalize_metadata",
    "user_based_split",
]
