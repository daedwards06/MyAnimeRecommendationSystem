import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import optuna
import pandas as pd
import numpy as np

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, OPTUNA_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS
from src.eval.splits import build_validation, sample_user_ids
from joblib import load
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender
from src.models.baselines import popularity_scores
from src.eval.metrics import ndcg_at_k
from src.eval.metrics_extra import item_coverage, gini_index


def _prepare_cache(k: int, sample_users: int):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"
    knn_model: ItemKNNRecommender = load(knn_path) if knn_path.exists() else ItemKNNRecommender().fit(train_df)
    mf_model: FunkSVDRecommender = load(mf_path) if mf_path.exists() else FunkSVDRecommender().fit(train_df)

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    pop_series = popularity_scores(train_df)
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    per_user = {}
    for u in users:
        seen = train_hist.get(u, set())
        knn_scores = knn_model.score_all(u, exclude_seen=True)
        mf_scores_arr = mf_model.predict_user(u)
        for it in seen:
            if mf_model.item_to_index and it in mf_model.item_to_index:
                mf_scores_arr[mf_model.item_to_index[it]] = -np.inf
        mf_scores = {mf_model.index_to_item[i]: float(s) for i, s in enumerate(mf_scores_arr) if np.isfinite(s)}
        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}
        per_user[u] = {"mf": mf_scores, "knn": knn_scores, "pop": pop_scores}

    total_items = int(train_df["anime_id"].nunique())
    return users, per_user, val_hist, total_items


def _metrics_for_weights(users, per_user_scores, val_hist, total_items: int, k: int, w_mf: float, w_knn: float, w_pop: float):
    ndcgs = []
    recs = {}
    for u in users:
        src = per_user_scores[u]
        agg = {}
        for item, sc in src["mf"].items():
            agg[item] = agg.get(item, 0.0) + w_mf * sc
        for item, sc in src["knn"].items():
            agg[item] = agg.get(item, 0.0) + w_knn * sc
        for item, sc in src["pop"].items():
            agg[item] = agg.get(item, 0.0) + w_pop * sc
        ranked = [i for i, _ in sorted(agg.items(), key=lambda x: x[1], reverse=True)[:k]]
        recs[u] = ranked
        ndcgs.append(ndcg_at_k(ranked, val_hist.get(u, set()), k))
    ndcg_mean = float(sum(ndcgs) / max(1, len(ndcgs)))
    cov = item_coverage(recs, total_items)
    gini = gini_index(recs)
    return ndcg_mean, cov, gini


def tune_hybrid(n_trials: int = 40, k: int = TOP_K_DEFAULT, sample_users: int = DEFAULT_SAMPLE_USERS,
                diversity_metric: str = "coverage", lambda_diversity: float = 0.0,
                pop_cap: float | None = None):
    users, per_user_scores, val_hist, total_items = _prepare_cache(k, sample_users)

    def objective(trial: optuna.Trial) -> float:
        # Suggest non-negative weights and normalize to sum 1
        w_mf = trial.suggest_float("w_mf", 0.0, 1.0)
        w_knn = trial.suggest_float("w_knn", 0.0, 1.0)
        w_pop = trial.suggest_float("w_pop", 0.0, 1.0)
        s = w_mf + w_knn + w_pop
        if s == 0:
            return 0.0
        w_mf, w_knn, w_pop = w_mf / s, w_knn / s, w_pop / s
        # Optional hard cap on popularity weight
        if pop_cap is not None:
            if w_pop > pop_cap:
                # re-normalize the remainder proportionally if pop exceeds cap
                excess = w_pop - pop_cap
                w_pop = pop_cap
                rem = w_mf + w_knn
                if rem > 0:
                    scale = (rem + excess) / rem
                    w_mf /= scale
                    w_knn /= scale
        # Store the actual weights used after normalization/capping
        trial.set_user_attr("weights_normalized", {"w_mf": w_mf, "w_knn": w_knn, "w_pop": w_pop})
        ndcg_mean, cov, gini = _metrics_for_weights(users, per_user_scores, val_hist, total_items, k, w_mf, w_knn, w_pop)
        # Diversity-aware objective
        if diversity_metric == "coverage":
            return ndcg_mean + lambda_diversity * cov
        elif diversity_metric == "gini":
            return ndcg_mean - lambda_diversity * gini
        else:
            return ndcg_mean

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)

    OPTUNA_DIR.mkdir(parents=True, exist_ok=True)
    df = study.trials_dataframe()
    df.to_csv(OPTUNA_DIR / "hybrid_weights_trials.csv", index=False)
    best_trial = study.best_trial
    with open(OPTUNA_DIR / "hybrid_weights_best.json", "w") as f:
        json.dump({
            "best_value": study.best_value,
            "best_params": best_trial.params,
            "weights_normalized": best_trial.user_attrs.get("weights_normalized")
        }, f, indent=2)
    print("Best:", study.best_value, study.best_params)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optuna tuning for hybrid blend weights (optionally diversity-aware)")
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    parser.add_argument("--diversity-metric", choices=["coverage", "gini", "none"], default="none",
                        help="Which diversity metric to include in the objective: coverage adds, gini subtracts")
    parser.add_argument("--lambda-diversity", type=float, default=0.0,
                        help="Weight for diversity metric in the objective")
    parser.add_argument("--pop-cap", type=float, default=None,
                        help="Optional hard cap for popularity weight after normalization (e.g., 0.5)")
    args = parser.parse_args()
    div_metric = args.diversity_metric
    if div_metric == "none":
        div_metric = None
    tune_hybrid(n_trials=args.trials, k=args.k, sample_users=args.sample_users,
                diversity_metric=(div_metric or "none"), lambda_diversity=args.lambda_diversity,
                pop_cap=args.pop_cap)
