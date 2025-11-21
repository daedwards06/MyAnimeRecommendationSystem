"""Evaluate scikit-learn ItemKNN and FunkSVD MF recommenders.

Procedure:
1. Load interactions from processed parquet.
2. Construct a lightweight validation split (use provided split column if present; else hold out one item per user).
3. For each sampled user:
   - Recommend top-K from ItemKNN (excluding seen)
   - Recommend top-K from MF (excluding seen)
4. Compute NDCG@K and MAP@K; write JSON lines + summary CSV under experiments/metrics.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import random
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
from joblib import load

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, METRICS_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS
from src.eval.splits import build_validation, sample_user_ids
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender
from src.eval.metrics_extra import item_coverage, gini_index

print("DEBUG evaluate_knn_mf module import start", flush=True)


def _build_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return build_validation(df)


def evaluate(model_name: str, recommendations: dict[int, list[int]], relevant: dict[int, set[int]], k: int) -> dict:
    ndcgs, maps = [], []
    for u, recs in recommendations.items():
        rel = relevant.get(u, set())
        ndcgs.append(ndcg_at_k(recs, rel, k))
        maps.append(average_precision_at_k(recs, rel, k))
    return {
        "model": model_name,
        "k": k,
        "users_evaluated": len(recommendations),
        "ndcg@k_mean": float(sum(ndcgs) / max(1, len(ndcgs))),
        "map@k_mean": float(sum(maps) / max(1, len(maps))),
    }


def main(k: int = TOP_K_DEFAULT, sample_users: int = DEFAULT_SAMPLE_USERS):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = _build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    # Load or fit models (prefer existing artifacts)
    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"
    if not knn_path.exists():
        from src.models.knn_sklearn import ItemKNNRecommender
        knn_model = ItemKNNRecommender().fit(train_df)
    else:
        knn_model: ItemKNNRecommender = load(knn_path)
    if not mf_path.exists():
        from src.models.mf_sgd import FunkSVDRecommender
        mf_model = FunkSVDRecommender(n_factors=64, lr=0.005, reg=0.05, n_epochs=10).fit(train_df)
    else:
        mf_model: FunkSVDRecommender = load(mf_path)

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    knn_recs: dict[int, list[int]] = {}
    mf_recs: dict[int, list[int]] = {}
    for u in users:
        seen = train_hist.get(u, set())
        knn_recs[u] = knn_model.recommend(u, top_k=k, exclude_seen=True)
        mf_recs[u] = mf_model.recommend(u, top_k=k, exclude=seen)

    # Debug sample
    sample_user = users[0] if users else None
    if sample_user is not None:
        print(f"DEBUG users={len(users)} sample_user={sample_user} knn_recs={knn_recs.get(sample_user)} mf_recs={mf_recs.get(sample_user)}", flush=True)

    total_items = int(interactions["anime_id"].nunique())
    metrics_knn = evaluate("item_knn_sklearn", knn_recs, val_hist, k)
    metrics_knn["item_coverage@k"] = item_coverage(knn_recs, total_items)
    metrics_knn["gini_index@k"] = gini_index(knn_recs)
    metrics_mf = evaluate("mf_sgd", mf_recs, val_hist, k)
    metrics_mf["item_coverage@k"] = item_coverage(mf_recs, total_items)
    metrics_mf["gini_index@k"] = gini_index(mf_recs)

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    (METRICS_DIR / f"item_knn_sklearn_{ts}.json").write_text(json.dumps(metrics_knn, indent=2))
    (METRICS_DIR / f"mf_sgd_{ts}.json").write_text(json.dumps(metrics_mf, indent=2))

    # Append combined CSV rows (use top-level pandas import)
    out_csv = METRICS_DIR / "summary.csv"
    pd.DataFrame([metrics_knn, metrics_mf]).to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False)

    print(json.dumps({"knn": metrics_knn, "mf": metrics_mf}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Evaluate ItemKNN and MF baselines.")
        parser.add_argument("--k", type=int, default=TOP_K_DEFAULT, help="Top-K for evaluation")
        parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS, help="Number of users to sample for eval")
        args = parser.parse_args()
        print("DEBUG entering main()", flush=True)
        main(k=args.k, sample_users=args.sample_users)
        print("DEBUG finished main()", flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR evaluate_knn_mf: {e}", flush=True)
