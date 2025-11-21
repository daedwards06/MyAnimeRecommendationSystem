import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from implicit.als import AlternatingLeastSquares
from joblib import dump

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED


def build_sparse(df: pd.DataFrame):
    users = df["user_id"].astype("category")
    items = df["anime_id"].astype("category")
    rows = users.cat.codes.values
    cols = items.cat.codes.values
    # confidence weighting: log(1 + rating)
    data = np.log1p(df["rating"].astype(float).values)
    return coo_matrix((data, (rows, cols))), users, items


def train_als(factors: int = 64, regularization: float = 0.01, iterations: int = 15):
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    mat, users, items = build_sparse(inter)
    model = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=iterations,
        random_state=RANDOM_SEED,
    )
    model.fit(mat)
    artifact = {
        "model": model,
        "user_index": dict(enumerate(users.cat.categories.astype(int).tolist())),
        "item_index": dict(enumerate(items.cat.categories.astype(int).tolist())),
    }
    out = MODELS_DIR / "als_implicit_v1.0.joblib"
    dump(artifact, out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    train_als()
