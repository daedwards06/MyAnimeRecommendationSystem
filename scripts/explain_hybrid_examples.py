import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import numpy as np
from joblib import load

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, METRICS_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS, DEFAULT_HYBRID_WEIGHTS
from src.eval.splits import build_validation, sample_user_ids
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender
from src.models.baselines import popularity_scores
from src.models.hybrid import weighted_blend
from src.eval.explain import blend_explanations


def main(k: int = TOP_K_DEFAULT, sample_users: int = DEFAULT_SAMPLE_USERS, w_mf: float = None, w_knn: float = None, w_pop: float = None, max_users: int = 5):
    if w_mf is None:
        w_mf = DEFAULT_HYBRID_WEIGHTS["mf"]
    if w_knn is None:
        w_knn = DEFAULT_HYBRID_WEIGHTS["knn"]
    if w_pop is None:
        w_pop = DEFAULT_HYBRID_WEIGHTS["pop"]

    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"
    knn_model: ItemKNNRecommender = load(knn_path) if knn_path.exists() else ItemKNNRecommender().fit(train_df)
    mf_model: FunkSVDRecommender = load(mf_path) if mf_path.exists() else FunkSVDRecommender().fit(train_df)

    pop_series = popularity_scores(train_df)
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    out = {}
    for u in users[:max_users]:
        seen = train_hist.get(u, set())
        mf_scores_arr = mf_model.predict_user(u)
        for it in seen:
            if mf_model.item_to_index and it in mf_model.item_to_index:
                mf_scores_arr[mf_model.item_to_index[it]] = -np.inf
        mf_scores = {mf_model.index_to_item[i]: float(s) for i, s in enumerate(mf_scores_arr) if np.isfinite(s)}
        knn_scores = knn_model.score_all(u, exclude_seen=True)
        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}
        sources = {"mf": mf_scores, "knn": knn_scores, "pop": pop_scores}
        weights = {"mf": w_mf, "knn": w_knn, "pop": w_pop}
        recs = weighted_blend(sources, weights, top_k=k)
        out[str(u)] = {
            "top": recs,
            "contributions": blend_explanations(recs[:5], sources, weights),
        }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (METRICS_DIR / "hybrid_explanations.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate explanation breakdowns for hybrid blended recommendations")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    parser.add_argument("--w-mf", type=float, default=None)
    parser.add_argument("--w-knn", type=float, default=None)
    parser.add_argument("--w-pop", type=float, default=None)
    parser.add_argument("--max-users", type=int, default=5)
    args = parser.parse_args()
    main(args.k, args.sample_users, args.w_mf, args.w_knn, args.w_pop, args.max_users)
