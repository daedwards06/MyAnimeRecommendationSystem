import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import json
import optuna
import pandas as pd

from src.models.constants import DATA_PROCESSED_DIR, OPTUNA_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS
from src.eval.splits import build_validation, sample_user_ids
from src.models.mf_sgd import FunkSVDRecommender
from src.eval.metrics import ndcg_at_k


def _evaluate_model(model: FunkSVDRecommender, train_df: pd.DataFrame, val_df: pd.DataFrame, users: list[int], k: int) -> float:
    model = model.fit(train_df)
    # Histories and relevance
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    ndcgs = []
    for u in users:
        seen = train_hist.get(u, set())
        scores = model.predict_user(u)
        # mask seen
        for it in seen:
            if model.item_to_index and it in model.item_to_index:
                scores[model.item_to_index[it]] = -float("inf")
        # rank
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        recs = [model.index_to_item[i] for i in top]
        ndcgs.append(ndcg_at_k(recs, val_hist.get(u, set()), k))
    return float(sum(ndcgs) / max(1, len(ndcgs)))


essential_ranges = {
    "n_factors": (16, 256),
    "lr": (1e-4, 5e-2),
    "reg": (1e-4, 1e-1),
    "n_epochs": (4, 20),
}


def tune_mf(n_trials: int = 40, k: int = TOP_K_DEFAULT, sample_users: int = DEFAULT_SAMPLE_USERS):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_factors": trial.suggest_int("n_factors", *essential_ranges["n_factors"]),
            "lr": trial.suggest_float("lr", *essential_ranges["lr"], log=True),
            "reg": trial.suggest_float("reg", *essential_ranges["reg"], log=True),
            "n_epochs": trial.suggest_int("n_epochs", *essential_ranges["n_epochs"]),
        }
        model = FunkSVDRecommender(**params)
        return _evaluate_model(model, train_df, val_df, users, k)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)

    OPTUNA_DIR.mkdir(parents=True, exist_ok=True)
    df = study.trials_dataframe()
    df.to_csv(OPTUNA_DIR / "mf_sgd_trials.csv", index=False)
    with open(OPTUNA_DIR / "mf_sgd_best.json", "w") as f:
        json.dump({"best_value": study.best_value, "best_params": study.best_params}, f, indent=2)
    print("Best:", study.best_value, study.best_params)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optuna tuning for FunkSVD MF hyperparameters")
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    args = parser.parse_args()
    tune_mf(n_trials=args.trials, k=args.k, sample_users=args.sample_users)
