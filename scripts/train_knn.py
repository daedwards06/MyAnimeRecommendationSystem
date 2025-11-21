import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
from surprise import Dataset, Reader, KNNBasic
from joblib import dump

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR


def _load_surprise_df(df: pd.DataFrame) -> Dataset:
    reader = Reader(rating_scale=(df["rating"].min(), df["rating"].max()))
    return Dataset.load_from_df(df[["user_id", "anime_id", "rating"]], reader)


def train_knn(k: int = 40, user_based: bool = True, sim_name: str = "cosine") -> Path:
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    data = _load_surprise_df(inter)
    trainset = data.build_full_trainset()
    algo = KNNBasic(k=k, sim_options={"name": sim_name, "user_based": user_based})
    algo.fit(trainset)
    out = MODELS_DIR / ("knn_user_v1.0.joblib" if user_based else "knn_item_v1.0.joblib")
    dump(algo, out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    train_knn()
