import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
from surprise import Dataset, Reader, SVD
from joblib import dump

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED


def train_svd(n_factors: int = 100, reg_all: float = 0.02, lr_all: float = 0.005) -> Path:
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    reader = Reader(rating_scale=(inter["rating"].min(), inter["rating"].max()))
    data = Dataset.load_from_df(inter[["user_id", "anime_id", "rating"]], reader)
    trainset = data.build_full_trainset()
    algo = SVD(n_factors=n_factors, reg_all=reg_all, lr_all=lr_all, random_state=RANDOM_SEED)
    algo.fit(trainset)
    out = MODELS_DIR / "svd_v1.0.joblib"
    dump(algo, out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    train_svd()
