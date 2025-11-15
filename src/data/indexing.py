from __future__ import annotations
import pandas as pd


def build_id_indices(interactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build contiguous integer indices for users and items.

    Returns:
        user_index: columns [user_id, user_idx]
        item_index: columns [anime_id, item_idx]
    """
    users = pd.DataFrame({"user_id": interactions["user_id"].dropna().astype(int).unique()})
    users = users.sort_values("user_id").reset_index(drop=True)
    users["user_idx"] = range(len(users))

    items = pd.DataFrame({"anime_id": interactions["anime_id"].dropna().astype(int).unique()})
    items = items.sort_values("anime_id").reset_index(drop=True)
    items["item_idx"] = range(len(items))
    return users, items
