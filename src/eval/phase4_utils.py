"""Phase 4 utility helpers (lift computation, JSON sanitization)."""
from __future__ import annotations
from typing import Any, Iterable
import numpy as np
import pandas as pd


def compute_lifts(df: pd.DataFrame, baseline_model: str, metrics: Iterable[str]) -> pd.DataFrame:
    """Compute relative lifts vs baseline_model for provided metrics.

    If baseline metric value is 0, lift is set to None.
    Expects df rows with a 'model' column and metric columns.
    """
    base_row = df[df["model"] == baseline_model]
    if base_row.empty:
        raise ValueError(f"Baseline model '{baseline_model}' not found in DataFrame")
    base = base_row.iloc[0]
    out_rows = []
    for _, row in df.iterrows():
        record = {"model": row["model"]}
        for m in metrics:
            val = row[m]
            record[m] = val
            b = base[m]
            lift_col = f"{m}_lift_vs_{baseline_model}_pct"
            if b == 0:
                record[lift_col] = None
            else:
                record[lift_col] = (val - b) / b * 100.0
        out_rows.append(record)
    return pd.DataFrame(out_rows)


def json_safe(obj: Any) -> Any:
    """Recursively convert numpy scalar/array components to native Python types."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(json_safe(v) for v in obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return [json_safe(v) for v in obj.tolist()]
    return obj

__all__ = ["compute_lifts", "json_safe"]
