#!/usr/bin/env python
"""Aggregate per-model metrics across K into a unified parquet for Phase 4 plots.

Searches experiment metric JSON files under `experiments/metrics/` that contain
per-K ranking and diversity metrics. Expected JSON schema (example):
{
  "model": "mf",
  "generated_at": "2025-11-21T20:27:56Z",
  "metrics_by_k": [
      {"K": 5, "ndcg": 0.0412, "map": 0.0301, "coverage": 0.055, "gini": 0.79},
      {"K": 10, "ndcg": 0.05036, "map": 0.03900, "coverage": 0.071, "gini": 0.784}
  ]
}

Outputs: `data/processed/phase4/metrics_by_k.parquet`

Usage:
    python scripts/aggregate_phase4_metrics.py \
        --metrics-dir experiments/metrics \
        --output data/processed/phase4/metrics_by_k.parquet
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

REQUIRED_PER_K = {"K", "ndcg", "map", "coverage", "gini"}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_rows(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    model = obj.get("model") or obj.get("model_name")
    rows = []
    for entry in obj.get("metrics_by_k", []):
        if not REQUIRED_PER_K.issubset(entry.keys()):
            continue
        rows.append({
            "model": model,
            "K": entry["K"],
            "ndcg": entry["ndcg"],
            "map": entry["map"],
            "coverage": entry["coverage"],
            "gini": entry["gini"],
        })
    return rows


def aggregate(metrics_dir: Path) -> pd.DataFrame:
    all_rows: List[Dict[str, Any]] = []
    for path in metrics_dir.glob("*.json"):
        try:
            obj = load_json(path)
        except Exception as e:
            print(f"WARN: failed to read {path}: {e}")
            continue
        rows = extract_rows(obj)
        if not rows:
            print(f"INFO: no per-K rows found in {path}")
        all_rows.extend(rows)
    if not all_rows:
        raise SystemExit("No metrics extracted; ensure JSON files have 'metrics_by_k' entries.")
    df = pd.DataFrame(all_rows).dropna()
    # Basic validation
    if df.empty:
        raise SystemExit("Aggregated DataFrame is empty after dropna().")
    return df.sort_values(["model", "K"]).reset_index(drop=True)


def main(args: argparse.Namespace) -> None:
    metrics_dir = Path(args.metrics_dir)
    if not metrics_dir.exists():
        raise SystemExit(f"Metrics directory does not exist: {metrics_dir}")
    df = aggregate(metrics_dir)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    print(f"Wrote aggregated metrics parquet: {out_path} (rows={len(df)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-dir", default="experiments/metrics", help="Directory containing model metric JSON files.")
    parser.add_argument("--output", default="data/processed/phase4/metrics_by_k.parquet", help="Output parquet path.")
    main(parser.parse_args())
