import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
from joblib import dump

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR
from src.models.knn_sklearn import ItemKNNRecommender


def main():
    df = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    # Updated API: ItemKNNRecommender computes a rating-weighted user profile with cosine scoring.
    # Key params: normalize_items (bool), min_rating (float), center_ratings (bool), popularity_weight (float)
    model = ItemKNNRecommender(normalize_items=True, center_ratings=True, popularity_weight=0.02).fit(df)
    out = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    dump(model, out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
