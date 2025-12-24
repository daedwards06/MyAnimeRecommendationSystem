"""Quick MF-training membership checker.

Usage:
  python check_in_training_membership.py 34096

Prints whether the anime_id is present in the selected MF model's item_to_index,
plus a title lookup from the loaded metadata.

This script is intentionally small and does not modify app behavior.
"""

from __future__ import annotations

import os
import sys

from src.app.artifacts_loader import build_artifacts


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python check_in_training_membership.py <anime_id>")
        return 2

    anime_id = int(argv[1])

    bundle = build_artifacts()
    metadata = bundle["metadata"]
    mf = bundle["models"]["mf"]

    in_training = anime_id in mf.item_to_index

    rows = metadata.loc[metadata["anime_id"] == anime_id]
    title = None
    if len(rows) > 0:
        if "title_display" in rows.columns:
            title = rows["title_display"].iloc[0]
        elif "title" in rows.columns:
            title = rows["title"].iloc[0]

    key_type = None
    try:
        key_type = type(next(iter(mf.item_to_index.keys()))).__name__ if mf.item_to_index else None
    except Exception:
        key_type = "<unreadable>"

    print(
        {
            "APP_MF_MODEL_STEM": os.environ.get("APP_MF_MODEL_STEM"),
            "anime_id": anime_id,
            "in_training": in_training,
            "title": title,
            "metadata_row_found": bool(len(rows) > 0),
            "item_to_index_key_type_sample": key_type,
            "item_to_index_size": len(mf.item_to_index) if mf.item_to_index else 0,
        }
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
