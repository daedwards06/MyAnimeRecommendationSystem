"""Optuna sweep for the weighted MF / kNN / popularity blend.

Tuning users are validation users *outside* the reporting cohort (`reporting_and_tuning_users`),
so the ablation never scores weights on the users they were fit to.

The three sources are summed raw, and their scales differ by orders of magnitude (kNN similarity
roughly ±0.5, MF predicted rating 2–10, popularity log-count × mean rating 0–80), so useful weight
ratios span several decades. Weights are therefore searched log-uniformly before normalizing.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import optuna
import pandas as pd
import numpy as np

from src.models.constants import (
    DATA_PROCESSED_DIR,
    OPTUNA_DIR,
    RANDOM_SEED,
    REPORTING_COHORT_USERS,
    TOP_K_DEFAULT,
)
from src.eval.splits import build_validation, reporting_and_tuning_users
from src.eval.eval_artifacts import load_eval_models
from src.models.baselines import popularity_scores
from src.eval.metrics import ndcg_at_k
from src.eval.metrics_extra import item_coverage, gini_index

WEIGHT_LOW = 1e-4


def _prepare_cache(sample_users: int, report_users: int):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    report, users = reporting_and_tuning_users(val_df["user_id"].unique().tolist(), report_users, sample_users)
    overlap = len(set(report) & set(users))
    print(f"Tuning users: {len(users)} | reporting cohort: {len(report)} | overlap: {overlap}", flush=True)
    if overlap:
        raise SystemExit("Tuning and reporting users overlap; refusing to tune on the reporting cohort.")

    # Train-split artifacts: the served models in models/ trained on the val rows.
    knn_model, mf_model = load_eval_models(train_df)

    item_ids = np.asarray([mf_model.index_to_item[i] for i in range(len(mf_model.index_to_item))])
    col = {int(a): j for j, a in enumerate(item_ids)}

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    pop_series = popularity_scores(train_df)
    pop_vec = np.zeros(len(item_ids), dtype=np.float64)
    for item, score in pop_series.items():
        if int(item) in col:
            pop_vec[col[int(item)]] = float(score)

    n_users, n_items = len(users), len(item_ids)
    mf = np.zeros((n_users, n_items), dtype=np.float64)
    knn = np.zeros((n_users, n_items), dtype=np.float64)
    seen_mask = np.zeros((n_users, n_items), dtype=bool)
    for r, u in enumerate(users):
        mf[r] = mf_model.predict_user(u)
        for item, score in knn_model.score_all(u, exclude_seen=True).items():
            if int(item) in col:
                knn[r, col[int(item)]] = score
        for item in train_hist.get(u, set()):
            if int(item) in col:
                seen_mask[r, col[int(item)]] = True

    meta = {
        "tuning_users": len(users),
        "reporting_cohort_users": len(report),
        "tuning_reporting_overlap": overlap,
        "seed": RANDOM_SEED,
    }
    total_items = int(train_df["anime_id"].nunique())
    return users, (mf, knn, pop_vec, seen_mask, item_ids), val_hist, total_items, meta


def _metrics_for_weights(users, cache, val_hist, total_items: int, k: int, w_mf: float, w_knn: float, w_pop: float):
    mf, knn, pop_vec, seen_mask, item_ids = cache
    scores = w_mf * mf + w_knn * knn + w_pop * pop_vec[None, :]
    scores[seen_mask] = -np.inf
    top = np.argpartition(-scores, k, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(scores, top, axis=1), axis=1)
    top = np.take_along_axis(top, order, axis=1)
    recs = {u: [int(i) for i in item_ids[top[r]]] for r, u in enumerate(users)}
    ndcgs = [ndcg_at_k(recs[u], val_hist.get(u, set()), k) for u in users]
    ndcg_mean = float(sum(ndcgs) / max(1, len(ndcgs)))
    return ndcg_mean, item_coverage(recs, total_items), gini_index(recs)


def tune_hybrid(n_trials: int = 40, k: int = TOP_K_DEFAULT, sample_users: int = REPORTING_COHORT_USERS,
                report_users: int = REPORTING_COHORT_USERS,
                diversity_metric: str = "coverage", lambda_diversity: float = 0.0,
                pop_cap: float | None = None):
    users, cache, val_hist, total_items, meta = _prepare_cache(sample_users, report_users)

    def objective(trial: optuna.Trial) -> float:
        w_mf = trial.suggest_float("w_mf", WEIGHT_LOW, 1.0, log=True)
        w_knn = trial.suggest_float("w_knn", WEIGHT_LOW, 1.0, log=True)
        w_pop = trial.suggest_float("w_pop", WEIGHT_LOW, 1.0, log=True)
        s = w_mf + w_knn + w_pop
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
        trial.set_user_attr("weights_normalized", {"w_mf": w_mf, "w_knn": w_knn, "w_pop": w_pop})
        ndcg_mean, cov, gini = _metrics_for_weights(users, cache, val_hist, total_items, k, w_mf, w_knn, w_pop)
        trial.set_user_attr("ndcg", ndcg_mean)
        trial.set_user_attr("coverage", cov)
        trial.set_user_attr("gini", gini)
        if diversity_metric == "coverage":
            return ndcg_mean + lambda_diversity * cov
        elif diversity_metric == "gini":
            return ndcg_mean - lambda_diversity * gini
        else:
            return ndcg_mean

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(objective, n_trials=n_trials)

    OPTUNA_DIR.mkdir(parents=True, exist_ok=True)
    df = study.trials_dataframe()
    df.to_csv(OPTUNA_DIR / "hybrid_weights_trials.csv", index=False)
    best_trial = study.best_trial
    with open(OPTUNA_DIR / "hybrid_weights_best.json", "w") as f:
        json.dump({
            "best_value": study.best_value,
            "best_params": best_trial.params,
            "weights_normalized": best_trial.user_attrs.get("weights_normalized"),
            "tuning_metrics": {m: best_trial.user_attrs.get(m) for m in ("ndcg", "coverage", "gini")},
            "objective": {"diversity_metric": diversity_metric, "lambda_diversity": lambda_diversity, "pop_cap": pop_cap},
            "n_trials": n_trials,
            "k": k,
            **meta,
        }, f, indent=2)
    print("Best:", study.best_value, best_trial.user_attrs.get("weights_normalized"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optuna tuning for hybrid blend weights (optionally diversity-aware)")
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=REPORTING_COHORT_USERS,
                        help="Number of tuning users, drawn from validation users outside the reporting cohort")
    parser.add_argument("--report-users", type=int, default=REPORTING_COHORT_USERS,
                        help="Size of the reporting cohort to exclude (must match the eval scripts' --sample-users)")
    parser.add_argument("--diversity-metric", choices=["coverage", "gini", "none"], default="none",
                        help="Which diversity metric to include in the objective: coverage adds, gini subtracts")
    parser.add_argument("--lambda-diversity", type=float, default=0.0,
                        help="Weight for diversity metric in the objective")
    parser.add_argument("--pop-cap", type=float, default=None,
                        help="Optional hard cap for popularity weight after normalization (e.g., 0.5)")
    args = parser.parse_args()
    tune_hybrid(n_trials=args.trials, k=args.k, sample_users=args.sample_users, report_users=args.report_users,
                diversity_metric=args.diversity_metric, lambda_diversity=args.lambda_diversity,
                pop_cap=args.pop_cap)
