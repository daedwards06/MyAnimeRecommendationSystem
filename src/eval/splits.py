from __future__ import annotations
import random
from typing import Tuple, List

import pandas as pd

from src.models.constants import RANDOM_SEED


def build_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (train_df, val_df) using existing split labels when available,
    otherwise create a simple per-user holdout (last by time if available, else random).
    """
    if "split" in df.columns:
        train_df = df[df["split"].isin(["train", "val_train", "train_val", "train_only"]) | (df["split"].isna())]
        val_df = df[df["split"].isin(["val", "validation", "valid"])].copy()
        if val_df.empty:
            return df, df
        return train_df, val_df
    rng = random.Random(RANDOM_SEED)
    work = df.copy()
    if "timestamp" in work.columns:
        work = work.sort_values(["user_id", "timestamp"])  # ascending
        val_rows = work.groupby("user_id", group_keys=False).tail(1)
    else:
        val_rows = (
            work.groupby("user_id", group_keys=False)
            .apply(lambda g: g.sample(1, random_state=rng.randint(0, 1_000_000)))
            .reset_index(drop=True)
        )
    val_pairs = set(zip(val_rows["user_id"], val_rows["anime_id"]))
    train_df = work[~work.apply(lambda r: (r["user_id"], r["anime_id"]) in val_pairs, axis=1)]
    return train_df, val_rows


def sample_user_ids(user_ids: List[int], max_users: int, seed: int | None = None) -> List[int]:
    """Deterministically sample up to max_users from user_ids using the given seed (defaults to RANDOM_SEED)."""
    if seed is None:
        seed = RANDOM_SEED
    if len(user_ids) <= max_users:
        return list(user_ids)
    rng = random.Random(seed)
    return rng.sample(list(user_ids), max_users)
