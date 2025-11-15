"""Evaluate simple baselines on prepared splits.

Baselines:
- Popularity@K: rank by item popularity from items.parquet
- (Optional) Content-only@K: cosine similarity from TF-IDF or embeddings to a user's profile (average of consumed items)

Metrics:
- Precision@K, Recall@K, MAP@K, NDCG@K (macro-averaged over users with at least 1 test interaction)

Usage (PowerShell):
  python scripts/evaluate_baselines.py --k 10
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def precision_recall_at_k(recommended: list[int], relevant: set[int]) -> tuple[float, float]:
    if not recommended:
        return 0.0, 0.0
    hits = sum(1 for i in recommended if i in relevant)
    prec = hits / len(recommended)
    rec = hits / max(1, len(relevant))
    return prec, rec


def apk(recommended: list[int], relevant: set[int]) -> float:
    if not recommended:
        return 0.0
    score = 0.0
    hits = 0
    for i, item in enumerate(recommended, start=1):
        if item in relevant:
            hits += 1
            score += hits / i
    return score / max(1, len(relevant))


def ndcg_at_k(recommended: list[int], relevant: set[int]) -> float:
    if not recommended:
        return 0.0
    dcg = 0.0
    for i, item in enumerate(recommended, start=1):
        rel = 1.0 if item in relevant else 0.0
        if rel > 0:
            dcg += rel / np.log2(i + 1)
    # Ideal DCG
    ideal_rels = [1.0] * min(len(relevant), len(recommended))
    idcg = sum(r / np.log2(i + 2) for i, r in enumerate(ideal_rels))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_popularity(
    train: pd.DataFrame,
    test: pd.DataFrame,
    items: pd.DataFrame,
    k: int = 10,
) -> dict[str, float]:
    # Rank items by popularity descending
    if "popularity" not in items.columns:
        raise KeyError("items.parquet missing 'popularity' column")
    ranked = items[["anime_id", "popularity"]].sort_values("popularity", ascending=False)[
        "anime_id"
    ].tolist()
    train_hist = train.groupby("user_id")["anime_id"].apply(set).to_dict()
    test_hist = test.groupby("user_id")["anime_id"].apply(set).to_dict()
    users = sorted(test_hist.keys())

    precs: list[float] = []
    recs: list[float] = []
    maps: list[float] = []
    ndcgs: list[float] = []
    for u in users:
        seen = train_hist.get(u, set())
        relevant = test_hist[u]
        if not relevant:
            continue
        # Recommend top-K excluding seen
        recs_u = [i for i in ranked if i not in seen][:k]
        p, r = precision_recall_at_k(recs_u, relevant)
        precs.append(p)
        recs.append(r)
        maps.append(apk(recs_u, relevant))
        ndcgs.append(ndcg_at_k(recs_u, relevant))
    return {
        "users": len(users),
        "users_with_test": sum(1 for u in users if len(test_hist.get(u, set())) > 0),
        "precision@k": float(np.mean(precs)) if precs else 0.0,
        "recall@k": float(np.mean(recs)) if recs else 0.0,
        "map@k": float(np.mean(maps)) if maps else 0.0,
        "ndcg@k": float(np.mean(ndcgs)) if ndcgs else 0.0,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Evaluate baseline recommenders on prepared splits")
    ap.add_argument("--train", type=Path, default=Path("data/processed/train.parquet"))
    ap.add_argument("--val", type=Path, default=Path("data/processed/val.parquet"))
    ap.add_argument("--test", type=Path, default=Path("data/processed/test.parquet"))
    ap.add_argument("--items", type=Path, default=Path("data/processed/items.parquet"))
    ap.add_argument("--k", type=int, default=10)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    print("[load] train/val/test/items")
    train = pd.read_parquet(args.train)
    val = pd.read_parquet(args.val)
    test = pd.read_parquet(args.test)
    items = pd.read_parquet(args.items)
    print(
        f"[info] shapes train/val/test/items: {train.shape} {val.shape} {test.shape} {items.shape}"
    )

    print(f"[eval] Popularity@{args.k}")
    pop_metrics = evaluate_popularity(train, test, items, k=int(args.k))
    for k_, v in pop_metrics.items():
        print(f"  {k_}: {v}")

    print("[done] baseline evaluation")


if __name__ == "__main__":
    main()
