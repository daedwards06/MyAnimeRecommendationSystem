"""Artifact loader utilities for Phase 5 Streamlit app.

Provides lightweight functions to load Phase 4 evaluation artifacts.
"""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

BASE_REPORTS = Path("reports")
FIG_DIR = BASE_REPORTS / "figures" / "phase4"
ARTIFACTS_DIR = BASE_REPORTS / "artifacts"
EXPERIMENTS_METRICS = Path("experiments") / "metrics"


def load_metric_curves(parquet_path: str = "data/processed/phase4/metrics_by_k.parquet") -> pd.DataFrame:
    """Load per-K metric curves DataFrame.

    Expected columns: model, K, ndcg, map, coverage, gini
    """
    path = Path(parquet_path)
    if not path.exists():
        raise FileNotFoundError(f"Metric curves parquet not found: {path}")
    return pd.read_parquet(path)


def load_ablation(csv_path: str = "reports/phase4_ablation.csv") -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Ablation CSV not found: {path}")
    return pd.read_csv(path)


def load_hybrid_explanations(user_id: str | int | None = None, explanations_path: str = str(EXPERIMENTS_METRICS / "hybrid_explanations.json")) -> dict:
    path = Path(explanations_path)
    if not path.exists():
        raise FileNotFoundError(f"Hybrid explanations file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if user_id is None:
        return data
    return data.get(str(user_id), {})


def load_temporal_summary(path: str = str(ARTIFACTS_DIR / "temporal_split_comparison.json")) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Temporal split artifact missing: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def load_genre_exposure(path: str = str(ARTIFACTS_DIR / "genre_exposure.json")) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_novelty_bias(path: str = str(ARTIFACTS_DIR / "novelty_bias.json")) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

__all__ = [
    "load_metric_curves",
    "load_ablation",
    "load_hybrid_explanations",
    "load_temporal_summary",
    "load_genre_exposure",
    "load_novelty_bias",
]
