from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_interactions(base_dir: Path) -> pd.DataFrame:
    """Load interactions from processed parquet; fallback to raw ratings CSV if needed.

    Expected columns: user_id, anime_id, rating; may include split column for train/val/test.
    """
    processed = base_dir / "interactions.parquet"
    if processed.exists():
        return pd.read_parquet(processed)
    # Fallback to raw Kaggle file if present
    raw_csv = Path("data/raw/rating.csv")
    if raw_csv.exists():
        df = pd.read_csv(raw_csv)
        # Normalize column names if necessary
        rename_map = {}
        for c in df.columns:
            lc = c.lower()
            if lc == "user_id" and c != "user_id":
                rename_map[c] = "user_id"
            if lc in ("anime_id", "item_id") and c != "anime_id":
                rename_map[c] = "anime_id"
            if lc in ("rating", "score") and c != "rating":
                rename_map[c] = "rating"
        if rename_map:
            df = df.rename(columns=rename_map)
        return df[["user_id", "anime_id", "rating"]]
    raise FileNotFoundError("Could not locate processed interactions.parquet or raw rating.csv")


def load_items(base_dir: Path) -> pd.DataFrame:
    path = base_dir / "items.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def load_users(base_dir: Path) -> pd.DataFrame:
    path = base_dir / "users.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def build_id_maps(interactions: pd.DataFrame) -> tuple[dict[int, int], dict[int, int]]:
    user_ids = interactions["user_id"].unique()
    item_ids = interactions["anime_id"].unique()
    return ({u: i for i, u in enumerate(user_ids)}, {a: j for j, a in enumerate(item_ids)})
