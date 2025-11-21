"""Evaluate baseline popularity recommender on a validation-like split.

This script:
- Loads interactions from data/processed or falls back to data/raw/rating.csv
- Computes global popularity ranking
- For a sample of users, recommends top-K excluding seen items
- Computes NDCG@10 and MAP@10 and logs to experiments/metrics
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import random

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd

from src.models.constants import DATA_PROCESSED_DIR, METRICS_DIR, TOP_K_DEFAULT
from src.models.baselines import popularity_scores
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.models.data_loader import load_interactions


def main(sample_users: int = 500, k: int = TOP_K_DEFAULT) -> None:
    df = load_interactions(DATA_PROCESSED_DIR)

    # If there is a split column, use validation rows to form relevance; otherwise use all history
    if "split" in df.columns:
        train_df = df[df["split"].isin(["train", "val_train", "train_val", "train_only"]) | (df["split"].isna())]
        val_df = df[df["split"].isin(["val", "validation", "valid"])].copy()
        if val_df.empty:
            # fallback: use overall interactions as relevance
            train_df = df
            val_df = df
    else:
        # No split info: create a simple per-user holdout of 1 item for validation
        rng = random.Random(42)
        df_sorted = df.copy()
        # If timestamp exists, we could use last interaction, else random
        if "timestamp" in df_sorted.columns:
            df_sorted = df_sorted.sort_values(["user_id", "timestamp"])  # ascending
            val_rows = df_sorted.groupby("user_id").tail(1)
        else:
            # Randomly sample one row per user (suppress future warning by disabling group keys)
            val_rows = (
                df_sorted.groupby("user_id", group_keys=False)
                .apply(lambda g: g.sample(1, random_state=rng.randint(0, 1_000_000)))
                .reset_index(drop=True)
            )
    val_keys = set(zip(val_rows["user_id"], val_rows["anime_id"]))
    # Build train and val by membership
    val_df = pd.DataFrame(val_rows, copy=True)
    train_df = df[~df.apply(lambda r: (r["user_id"], r["anime_id"]) in val_keys, axis=1)]

    pop = popularity_scores(train_df)
    ranked_global = [int(i) for i in pop.index]

    users = val_df["user_id"].unique().tolist()
    random.seed(42)
    if len(users) > sample_users:
        users = random.sample(users, sample_users)

    ndcgs, maps = [], []
    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    for u in users:
        seen = train_hist.get(u, set())
        relevant = set(val_hist.get(u, set()))
        # Recommend by global popularity excluding items the user has already seen
        recs = [i for i in ranked_global if i not in seen][:k]
        ndcgs.append(ndcg_at_k(recs, relevant, k))
        maps.append(average_precision_at_k(recs, relevant, k))

    metrics = {
        "model": "popularity_baseline",
        "k": k,
        "users_evaluated": len(users),
        "ndcg@k_mean": float(sum(ndcgs) / max(1, len(ndcgs))),
        "map@k_mean": float(sum(maps) / max(1, len(maps))),
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out_json = METRICS_DIR / f"popularity_baseline_{ts}.json"
    out_json.write_text(json.dumps(metrics, indent=2))
    # Append to summary CSV
    out_csv = METRICS_DIR / "summary.csv"
    pd.DataFrame([metrics]).to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
