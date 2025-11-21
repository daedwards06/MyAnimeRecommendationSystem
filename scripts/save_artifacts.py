import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from datetime import datetime, timezone
import pandas as pd
from joblib import dump

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender


# Use timezone-aware UTC timestamp; fallback handled for older Python versions
try:
    # Python 3.12+ provides datetime.UTC
    UTC = datetime.UTC  # type: ignore[attr-defined]
except AttributeError:  # older versions
    UTC = timezone.utc

VERSION_SUFFIX = datetime.now(UTC).strftime("v%Y.%m.%d_%H%M%S")


def main():
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    # Fit fresh models (or you could load existing and re-save)
    knn = ItemKNNRecommender().fit(interactions)
    mf = FunkSVDRecommender().fit(interactions)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    knn_path = MODELS_DIR / f"item_knn_sklearn_{VERSION_SUFFIX}.joblib"
    mf_path = MODELS_DIR / f"mf_sgd_{VERSION_SUFFIX}.joblib"
    dump(knn, knn_path)
    dump(mf, mf_path)

    # Update artifacts manifest (non-destructive append)
    manifest_path = DATA_PROCESSED_DIR / "artifacts_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}
    manifest.setdefault("models", []).append({
        "knn": str(knn_path),
        "mf": str(mf_path),
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print("Saved artifacts:", knn_path.name, mf_path.name)


if __name__ == "__main__":
    main()
