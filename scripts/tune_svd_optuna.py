import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import optuna
import pandas as pd
from surprise import SVD, Dataset, Reader

from src.models.constants import DATA_PROCESSED_DIR, OPTUNA_DIR, RANDOM_SEED
from src.eval.metrics import ndcg_at_k


def _load_data():
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    reader = Reader(rating_scale=(inter["rating"].min(), inter["rating"].max()))
    return Dataset.load_from_df(inter[["user_id", "anime_id", "rating"]], reader)


def objective(trial: optuna.Trial) -> float:
    data = _load_data()
    train = data.build_full_trainset()
    algo = SVD(
        n_factors=trial.suggest_int("n_factors", 50, 200),
        reg_all=trial.suggest_float("reg_all", 0.002, 0.08, log=True),
        lr_all=trial.suggest_float("lr_all", 0.001, 0.02, log=True),
        random_state=RANDOM_SEED,
    )
    algo.fit(train)

    item_inner_ids = list(train.all_items())
    item_raw = [train.to_raw_iid(i) for i in item_inner_ids]
    users = list(train.all_users())[:200]

    ndcgs = []
    for u in users:
        u_raw = train.to_raw_uid(u)
        relevant = {train.to_raw_iid(i) for (i, _) in train.ur[u]}
        preds = [(iid, algo.predict(u_raw, iid).est) for iid in item_raw]
        ranked = [iid for iid, est in sorted(preds, key=lambda x: x[1], reverse=True)]
        ndcgs.append(ndcg_at_k(ranked, relevant, 10))
    return float(sum(ndcgs) / max(1, len(ndcgs)))


if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)
    OPTUNA_DIR.mkdir(parents=True, exist_ok=True)
    study.trials_dataframe().to_csv(OPTUNA_DIR / "svd_trials_v1.0.csv", index=False)
    print("Best:", study.best_value, study.best_params)
