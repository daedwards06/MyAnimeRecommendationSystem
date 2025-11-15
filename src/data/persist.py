from __future__ import annotations
from pathlib import Path

import pandas as pd


def _densify_sparse_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert pandas SparseDtype columns to dense float32 to ensure parquet compatibility.
    Note: This may increase memory usage for very wide matrices (e.g., TF-IDF)."""
    out = df.copy()
    for col in out.columns:
        dt = out[col].dtype
        # pandas SparseDtype check
        if pd.api.types.is_sparse(dt):
            out[col] = out[col].sparse.to_dense().astype("float32")
    return out


def to_parquet(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Densify sparse columns for parquet writers that don't support SparseDtype (pyarrow)
    df_out = _densify_sparse_columns(df)
    df_out.to_parquet(path, index=index)
