import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
from joblib import dump

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED
from src.models.mf_sgd import FunkSVDRecommender


def main():
    df = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    model = FunkSVDRecommender(n_factors=64, lr=0.005, reg=0.05, n_epochs=10, random_state=RANDOM_SEED)
    model.fit(df)
    out = MODELS_DIR / "mf_sgd_v1.0.joblib"
    dump(model, out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
