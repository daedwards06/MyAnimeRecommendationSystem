from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pandas as pd


def compute_feature_stats(df: pd.DataFrame, cols: Iterable[str]) -> dict:
    out: dict[str, dict] = {}
    for c in cols:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        s = s.dropna()
        if len(s) == 0:
            continue
        out[c] = {
            "count": int(s.count()),
            "mean": float(s.mean()),
            "std": float(s.std(ddof=0)),
            "min": float(s.min()),
            "max": float(s.max()),
        }
    return out


def save_feature_stats(stats: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
