import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import random

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import numpy as np
from joblib import load

from src.models.constants import (
    DATA_PROCESSED_DIR,
    MODELS_DIR,
    METRICS_DIR,
    TOP_K_DEFAULT,
    DEFAULT_SAMPLE_USERS,
    DEFAULT_HYBRID_WEIGHTS,
)
from src.eval.splits import build_validation, sample_user_ids
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.models.hybrid import weighted_blend, reciprocal_rank_fusion
from src.models.baselines import popularity_scores
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender
from src.eval.metrics_extra import item_coverage, gini_index


def _build_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Backward compat shim; delegate to shared util
    return build_validation(df)


# JSON serializer that handles NumPy types and arrays
def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)


def _evaluate(model_name: str, recommendations: dict[int, list[int]], relevant: dict[int, set[int]], k: int) -> dict:
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


def main(k: int, sample_users: int, w_mf: float, w_knn: float, w_pop: float, save_examples: int = 2):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = _build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    # Load or fit models
    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"
    if knn_path.exists():
        knn_model: ItemKNNRecommender = load(knn_path)
    else:
        knn_model = ItemKNNRecommender().fit(train_df)
    if mf_path.exists():
        mf_model: FunkSVDRecommender = load(mf_path)
    else:
        mf_model = FunkSVDRecommender().fit(train_df)

    # Build histories and popularity scores
    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    pop_series = popularity_scores(train_df)  # pandas Series item_id -> score
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    # Per-user recommendations
    recs_knn: dict[int, list[int]] = {}
    recs_mf: dict[int, list[int]] = {}
    recs_pop: dict[int, list[int]] = {}
    recs_blend: dict[int, list[int]] = {}
    recs_rrf: dict[int, list[int]] = {}

    examples: dict[str, dict] = {}

    for idx, u in enumerate(users):
        seen = train_hist.get(u, set())

        # KNN scores and recs
        knn_scores = knn_model.score_all(u, exclude_seen=True)
        knn_top = sorted(knn_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        recs_knn[u] = [i for i, _ in knn_top]

        # MF scores and recs
        mf_scores_arr = mf_model.predict_user(u)
        # mask seen
        for it in seen:
            if it in mf_model.item_to_index:
                mf_scores_arr[mf_model.item_to_index[it]] = -np.inf
        # map to dict
        mf_scores = {mf_model.index_to_item[i]: float(s) for i, s in enumerate(mf_scores_arr) if np.isfinite(s)}
        mf_top_idx = np.argpartition(-mf_scores_arr, range(min(k, len(mf_scores_arr))))[:k]
        mf_top_idx = mf_top_idx[np.argsort(-mf_scores_arr[mf_top_idx])]
        recs_mf[u] = [mf_model.index_to_item[i] for i in mf_top_idx if np.isfinite(mf_scores_arr[i])]

        # Popularity recs (mask seen)
        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}
        pop_top = sorted(pop_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        recs_pop[u] = [i for i, _ in pop_top]

        # Weighted blend (scores)
        sources = {
            "mf": mf_scores,
            "knn": knn_scores,
            "pop": pop_scores,
        }
        weights = {"mf": w_mf, "knn": w_knn, "pop": w_pop}
        recs_blend[u] = weighted_blend(sources, weights, top_k=k)

        # RRF (rank fusion)
        rankings = {
            "mf": recs_mf[u],
            "knn": recs_knn[u],
            "pop": recs_pop[u],
        }
        recs_rrf[u] = reciprocal_rank_fusion(rankings, top_k=k)

        # Capture a few examples
        if len(examples) < save_examples:
            examples[str(u)] = {
                "knn": recs_knn[u][:5],
                "mf": recs_mf[u][:5],
                "pop": recs_pop[u][:5],
                "blend": recs_blend[u][:5],
                "rrf": recs_rrf[u][:5],
            }

    # Evaluate
    total_items = int(train_df["anime_id"].nunique())
    metrics_knn = _evaluate("item_knn_sklearn", recs_knn, val_hist, k)
    metrics_knn["item_coverage@k"] = item_coverage(recs_knn, total_items)
    metrics_knn["gini_index@k"] = gini_index(recs_knn)

    metrics_mf = _evaluate("mf_sgd", recs_mf, val_hist, k)
    metrics_mf["item_coverage@k"] = item_coverage(recs_mf, total_items)
    metrics_mf["gini_index@k"] = gini_index(recs_mf)

    metrics_pop = _evaluate("popularity", recs_pop, val_hist, k)
    metrics_pop["item_coverage@k"] = item_coverage(recs_pop, total_items)
    metrics_pop["gini_index@k"] = gini_index(recs_pop)

    metrics_blend = _evaluate("hybrid_weighted", recs_blend, val_hist, k)
    metrics_blend["item_coverage@k"] = item_coverage(recs_blend, total_items)
    metrics_blend["gini_index@k"] = gini_index(recs_blend)
    # Attach weights metadata for traceability
    metrics_blend["weights"] = {"mf": w_mf, "knn": w_knn, "pop": w_pop}
    metrics_rrf = _evaluate("hybrid_rrf", recs_rrf, val_hist, k)
    metrics_rrf["item_coverage@k"] = item_coverage(recs_rrf, total_items)
    metrics_rrf["gini_index@k"] = gini_index(recs_rrf)

    # Write artifacts
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    def _write(obj, name):
        (METRICS_DIR / f"{name}_{ts}.json").write_text(json.dumps(obj, indent=2, default=_json_default))

    _write(metrics_knn, "item_knn_sklearn")
    _write(metrics_mf, "mf_sgd")
    _write(metrics_pop, "popularity_baseline")
    _write(metrics_blend, "hybrid_weighted")
    _write(metrics_rrf, "hybrid_rrf")
    _write(examples, "hybrid_examples")

    # Append combined CSV rows
    out_csv = METRICS_DIR / "summary.csv"
    pd.DataFrame([metrics_knn, metrics_mf, metrics_pop, metrics_blend, metrics_rrf]).to_csv(
        out_csv, mode="a", header=not out_csv.exists(), index=False
    )

    print(json.dumps({
        "knn": metrics_knn,
        "mf": metrics_mf,
        "pop": metrics_pop,
        "blend": metrics_blend,
        "rrf": metrics_rrf
    }, indent=2, default=_json_default))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate hybrid blends of MF, KNN, and Popularity")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    parser.add_argument("--w-mf", type=float, default=DEFAULT_HYBRID_WEIGHTS["mf"])
    parser.add_argument("--w-knn", type=float, default=DEFAULT_HYBRID_WEIGHTS["knn"])
    parser.add_argument("--w-pop", type=float, default=DEFAULT_HYBRID_WEIGHTS["pop"])
    args = parser.parse_args()
    main(k=args.k, sample_users=args.sample_users, w_mf=args.w_mf, w_knn=args.w_knn, w_pop=args.w_pop)
