from __future__ import annotations

import random

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
    work = df.copy()
    if "timestamp" in work.columns:
        work = work.sort_values(["user_id", "timestamp"])  # ascending
        val_rows = work.groupby("user_id", group_keys=False).tail(1)
    else:
        val_rows = work.groupby("user_id", group_keys=False).sample(1, random_state=RANDOM_SEED)
    val_pairs = set(zip(val_rows["user_id"], val_rows["anime_id"]))
    train_df = work[~work.apply(lambda r: (r["user_id"], r["anime_id"]) in val_pairs, axis=1)]
    return train_df, val_rows


def sample_user_ids(user_ids: list[int], max_users: int, seed: int | None = None) -> list[int]:
    """Deterministically sample up to max_users from user_ids using the given seed (defaults to RANDOM_SEED)."""
    if seed is None:
        seed = RANDOM_SEED
    if len(user_ids) <= max_users:
        return list(user_ids)
    rng = random.Random(seed)
    return rng.sample(list(user_ids), max_users)


def reporting_and_tuning_users(
    user_ids: list[int],
    n_report: int,
    n_tune: int,
    seed: int | None = None,
) -> tuple[list[int], list[int]]:
    """Return (reporting cohort, tuning users), disjoint by construction.

    The reporting cohort is exactly `sample_user_ids(user_ids, n_report, seed)`, the cohort every
    evaluation script scores, so weights tuned on the second list are never tuned on the users
    the published numbers come from.
    """
    report = sample_user_ids(user_ids, n_report, seed)
    held_out = set(report)
    pool = [u for u in user_ids if u not in held_out]
    return report, sample_user_ids(pool, n_tune, seed)
