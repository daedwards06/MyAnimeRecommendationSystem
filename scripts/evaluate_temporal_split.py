#!/usr/bin/env python
"""Temporal split sanity check for Phase 4.

Procedure:
1. Load interactions parquet with columns: user_id, anime_id, rating, timestamp
2. Sort by timestamp; allocate earliest fraction to train, remainder to validation.
3. Train FunkSVD MF model on train partition.
4. For each validation user, generate recommendations (exclude seen training items) and compute metrics at K values.
5. Aggregate mean metrics (both binary and graded NDCG) and write JSON artifact for comparison against unified slice.

Outputs:
  reports/artifacts/temporal_split_comparison.json
  
Notes:
  - Binary NDCG treats all relevant items equally (gain=1)
  - Graded NDCG uses exponential gain (2^rating - 1) to emphasize highly-rated items
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import sys
import pandas as pd
import numpy as np

# Ensure project root (parent of scripts/) is on sys.path for 'src' package imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.models.mf_sgd import FunkSVDRecommender
from src.eval.metrics import evaluate_ranking
from src.eval.metrics_extra import item_coverage, gini_index

DEFAULT_K_VALUES = [5, 10, 20]


def temporal_split(df: pd.DataFrame, frac: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_sorted = df.sort_values("timestamp")
    cutoff = int(len(df_sorted) * frac)
    return df_sorted.iloc[:cutoff].copy(), df_sorted.iloc[cutoff:].copy()


def evaluate_model(model: FunkSVDRecommender, train_df: pd.DataFrame, val_df: pd.DataFrame, k_values: List[int]) -> Dict[str, Any]:
    # Build per-user seen set from training
    train_seen = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    users = val_df["user_id"].unique()
    # Build user relevant sets from validation interactions (positive rating threshold optional)
    val_groups = val_df.groupby("user_id")

    per_user_recs: Dict[int, List[int]] = {}
    metric_accumulators = {"ndcg": [], "map": []}

    for u in users:
        relevant = set(val_groups.get_group(u)["anime_id"].tolist()) if u in val_groups.groups else set()
        # Recommend top max(k_values)
        max_k = max(k_values)
        recs = model.recommend(u, top_k=max_k, exclude=train_seen.get(u, set()))
        per_user_recs[u] = recs
        # Compute metrics (binary)
        m = evaluate_ranking(recs, relevant, k_values)
        # Store only ndcg/map at each k
        for k in k_values:
            metric_accumulators["ndcg"].append(m["ndcg"][k])
            metric_accumulators["map"].append(m["map"][k])

    # Aggregate: mean over users for final K values
    metrics_out = {}
    
    # Binary NDCG and MAP
    for k in k_values:
        ndcg_k = []
        ndcg_graded_k = []
        map_k = []
        
        for u in users:
            if u not in val_groups.groups:
                continue
            
            user_val_data = val_groups.get_group(u)
            relevant = set(user_val_data["anime_id"].tolist())
            
            # Build item_ratings dict for graded NDCG
            item_ratings = dict(zip(user_val_data["anime_id"], user_val_data["rating"]))
            
            recs = per_user_recs[u]
            
            # Binary metrics
            m_binary = evaluate_ranking(recs, relevant, [k])
            ndcg_k.append(m_binary["ndcg"][k])
            map_k.append(m_binary["map"][k])
            
            # Graded NDCG
            m_graded = evaluate_ranking(recs, relevant, [k], item_ratings=item_ratings, gain_fn="exponential")
            ndcg_graded_k.append(m_graded["ndcg_graded"][k])
        
        metrics_out[f"ndcg_binary@{k}"] = float(np.mean(ndcg_k)) if ndcg_k else 0.0
        metrics_out[f"ndcg_graded@{k}"] = float(np.mean(ndcg_graded_k)) if ndcg_graded_k else 0.0
        metrics_out[f"map@{k}"] = float(np.mean(map_k)) if map_k else 0.0

    coverage_k10 = item_coverage({u: recs[:10] for u, recs in per_user_recs.items()}, total_items=len(model.item_to_index or {}))
    gini_k10 = gini_index({u: recs[:10] for u, recs in per_user_recs.items()})

    metrics_out["coverage@10"] = coverage_k10
    metrics_out["gini@10"] = gini_k10
    return metrics_out


def main(args: argparse.Namespace) -> None:
    interactions = pd.read_parquet(args.interactions)
    base_required = {"user_id", "anime_id", "rating"}
    missing_base = base_required - set(interactions.columns)
    if missing_base:
        raise SystemExit(f"Missing required columns in interactions file: {missing_base}")

    # Timestamp optional: if absent, create a synthetic ordering surrogate.
    if "timestamp" not in interactions.columns:
        # Prefer alternative columns if present (e.g., 'date', 'rating_date').
        alt_cols = [c for c in ["date", "rating_date", "updated_at"] if c in interactions.columns]
        if alt_cols:
            # Convert first available alt col to ordinal timestamp
            col = alt_cols[0]
            try:
                interactions[col] = pd.to_datetime(interactions[col], errors="coerce")
                interactions["timestamp"] = interactions[col].astype("int64") // 1_000_000_000
            except Exception:
                interactions["timestamp"] = range(len(interactions))
            source_note = f"synthetic from '{col}'"
        else:
            # Fallback deterministic synthetic ordering: row index
            interactions["timestamp"] = range(len(interactions))
            source_note = "synthetic from row index"
    else:
        source_note = "original timestamp"

    train_df, val_df = temporal_split(interactions, args.train_frac)
    print(f"Train rows: {len(train_df)} | Val rows: {len(val_df)}")

    model = FunkSVDRecommender(n_epochs=args.epochs, n_factors=args.factors, lr=args.lr, reg=args.reg).fit(train_df)
    metrics_temporal = evaluate_model(model, train_df, val_df, DEFAULT_K_VALUES)

    unified_metrics: Dict[str, Any] = {}
    if args.unified_metrics and Path(args.unified_metrics).exists():
        unified_metrics = json.loads(Path(args.unified_metrics).read_text(encoding="utf-8"))

    comparison = {
        "train_frac": args.train_frac,
        "timestamp_source": source_note,
        "temporal": metrics_temporal,
        "unified": unified_metrics,
        "interpretation": (
            "Binary NDCG treats all relevant items equally; Graded NDCG (exponential gain: 2^rating - 1) "
            "emphasizes highly-rated items and provides more nuanced quality signal. "
            "Review deltas: large drops may indicate time-based drift or leakage. "
            "If timestamp_source is synthetic, treat results as heuristic only."
        ),
    }

    out_path = Path("reports/artifacts/temporal_split_comparison.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(comparison, indent=2))
    print(f"[ok] Wrote temporal comparison to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Temporal split evaluation for robustness check.")
    parser.add_argument("--interactions", default="data/processed/interactions.parquet")
    parser.add_argument("--train-frac", type=float, default=0.7)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--factors", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.005)
    parser.add_argument("--reg", type=float, default=0.05)
    parser.add_argument("--unified-metrics", help="Path to unified slice metrics JSON (optional)")
    main(parser.parse_args())
