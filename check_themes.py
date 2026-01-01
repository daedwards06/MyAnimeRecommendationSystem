"""Quick integrity check for the `themes` column in the processed metadata parquet.

Why this exists:
- In this dataset, `themes` often loads as a `numpy.ndarray` (object dtype), not a Python list.
- That means naive `isinstance(x, list)` checks can miss empty theme lists (e.g., `[]`).

Usage:
  python check_themes.py
  python check_themes.py --path data/processed/anime_metadata.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _to_py(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, float) and np.isnan(x):
        return None
    # pyarrow scalars sometimes expose .as_py()
    if hasattr(x, "as_py"):
        try:
            return x.as_py()
        except Exception:
            return x
    return x


def is_empty_themes(x: Any) -> bool:
    x = _to_py(x)
    if x is None:
        return True

    if isinstance(x, (list, tuple, set, dict, np.ndarray)):
        return len(x) == 0

    if isinstance(x, str):
        t = x.strip()
        if t in {"", "[]", "{}"}:
            return True
        if t.startswith("[") and t.endswith("]"):
            try:
                arr = json.loads(t)
                return isinstance(arr, list) and len(arr) == 0
            except Exception:
                return False

    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("data/processed/anime_metadata.parquet"),
        help="Path to the processed anime metadata parquet.",
    )
    parser.add_argument(
        "--show-samples",
        type=int,
        default=8,
        help="How many empty/non-empty samples to print.",
    )
    args = parser.parse_args()

    df = pd.read_parquet(args.path, columns=["anime_id", "themes"])
    s = df["themes"]

    empty_mask = s.map(is_empty_themes)
    total = len(df)
    empty_count = int(empty_mask.sum())
    nonempty_count = int((~empty_mask).sum())

    print("path", str(args.path))
    print("rows_total", total)
    print("themes_dtype", s.dtype)
    print("empty_count", empty_count)
    print("nonempty_count", nonempty_count)
    print("empty_pct", float(empty_count / total) if total else 0.0)

    # Specific check requested in chat
    aid = 21
    if (df["anime_id"] == aid).any():
        val = df.loc[df["anime_id"] == aid, "themes"].iloc[0]
        print(f"anime_id={aid} themes", val, "type", type(val))

    n = max(0, int(args.show_samples))
    if n:
        print("sample_empty")
        for anime_id, themes in df.loc[empty_mask, ["anime_id", "themes"]].head(n).itertuples(
            index=False
        ):
            print(" ", anime_id, themes, type(themes))

        print("sample_nonempty")
        for anime_id, themes in df.loc[~empty_mask, ["anime_id", "themes"]].head(n).itertuples(
            index=False
        ):
            print(" ", anime_id, themes, type(themes))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
