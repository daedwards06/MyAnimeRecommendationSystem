import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import random
import itertools

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import numpy as np
from joblib import load

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, METRICS_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS
from src.eval.splits import build_validation, sample_user_ids
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.models.baselines import popularity_scores
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender


def _build_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return build_validation(df)


def _evaluate(recommendations: dict[int, list[int]], relevant: dict[int, set[int]], k: int) -> tuple[float, float]:
    ndcgs, maps = [], []
    for u, recs in recommendations.items():
        rel = relevant.get(u, set())
        ndcgs.append(ndcg_at_k(recs, rel, k))
        maps.append(average_precision_at_k(recs, rel, k))
    n = max(1, len(recommendations))
    return float(sum(ndcgs) / n), float(sum(maps) / n)


def _linspace_around(center: float, delta: float, steps: int) -> list[float]:
    if steps <= 1:
        return [center]
    lo, hi = center - delta, center + delta
    return [lo + i * (hi - lo) / (steps - 1) for i in range(steps)]


def main(k: int, sample_users: int, grid_mf: list[float], grid_knn: list[float], grid_pop: list[float]):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = _build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    # Load or fit models
    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"
    knn_model: ItemKNNRecommender = load(knn_path) if knn_path.exists() else ItemKNNRecommender().fit(train_df)
    mf_model: FunkSVDRecommender = load(mf_path) if mf_path.exists() else FunkSVDRecommender().fit(train_df)

    # Histories and base scores
    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    pop_series = popularity_scores(train_df)
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    # Cache per-user source scores once
    per_user_scores = {}
    for u in users:
        seen = train_hist.get(u, set())
        knn_scores = knn_model.score_all(u, exclude_seen=True)
        mf_scores_arr = mf_model.predict_user(u)
        for it in seen:
            if mf_model.item_to_index and it in mf_model.item_to_index:
                mf_scores_arr[mf_model.item_to_index[it]] = -np.inf
        mf_scores = {mf_model.index_to_item[i]: float(s) for i, s in enumerate(mf_scores_arr) if np.isfinite(s)}
        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}
        per_user_scores[u] = {"mf": mf_scores, "knn": knn_scores, "pop": pop_scores}

    # Sweep
    rows = []
    for w_mf, w_knn, w_pop in itertools.product(grid_mf, grid_knn, grid_pop):
        if abs((w_mf + w_knn + w_pop) - 1.0) > 1e-6:
            # Normalize weights to sum to 1
            s = w_mf + w_knn + w_pop
            w_mf, w_knn, w_pop = w_mf / s, w_knn / s, w_pop / s
        recs = {}
        for u, src in per_user_scores.items():
            agg: dict[int, float] = {}
            for item, sc in src["mf"].items():
                agg[item] = agg.get(item, 0.0) + w_mf * sc
            for item, sc in src["knn"].items():
                agg[item] = agg.get(item, 0.0) + w_knn * sc
            for item, sc in src["pop"].items():
                agg[item] = agg.get(item, 0.0) + w_pop * sc
            top = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:k]
            recs[u] = [i for i, _ in top]
        ndcg, ap = _evaluate(recs, val_hist, k)
        rows.append({
            "w_mf": w_mf,
            "w_knn": w_knn,
            "w_pop": w_pop,
            "k": k,
            "users": len(users),
            "ndcg@k": ndcg,
            "map@k": ap,
        })

    df = pd.DataFrame(rows).sort_values("ndcg@k", ascending=False)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out_csv = METRICS_DIR / f"hybrid_weight_sweep_{ts}.csv"
    df.to_csv(out_csv, index=False)
    print(json.dumps({"best": df.iloc[0].to_dict(), "file": str(out_csv)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grid sweep for hybrid weighted blend")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    parser.add_argument("--grid-mf", type=str, default="0.5,0.6,0.7")
    parser.add_argument("--grid-knn", type=str, default="0.2,0.3,0.4")
    parser.add_argument("--grid-pop", type=str, default="0.1,0.2")
    parser.add_argument(
        "--around",
        type=str,
        default="",
        help="Optional center weights 'mf,knn,pop' to generate a fine grid around with delta/steps",
    )
    parser.add_argument("--delta", type=float, default=0.05, help="Half-width around center for fine sweep")
    parser.add_argument("--steps", type=int, default=5, help="Number of steps per dimension for fine sweep")
    args = parser.parse_args()
    if args.around:
        try:
            c_mf, c_knn, c_pop = [float(x) for x in args.around.split(",")]
            grid_mf = _linspace_around(c_mf, args.delta, args.steps)
            grid_knn = _linspace_around(c_knn, args.delta, args.steps)
            grid_pop = _linspace_around(c_pop, args.delta, args.steps)
        except Exception:
            raise SystemExit("--around must be three comma-separated floats: mf,knn,pop")
    else:
        grid_mf = [float(x) for x in args.grid_mf.split(",")]
        grid_knn = [float(x) for x in args.grid_knn.split(",")]
        grid_pop = [float(x) for x in args.grid_pop.split(",")]
    main(args.k, args.sample_users, grid_mf, grid_knn, grid_pop)
