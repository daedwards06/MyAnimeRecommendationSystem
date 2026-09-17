"""Train and save the collaborative-filtering artifacts (kNN + FunkSVD).

This is the only trainer for these two families.

  --split full   (default) fit on every interaction and write timestamped artifacts to
                 models/. This is what the app serves.
  --split train  fit on the train split only and write to experiments/artifacts/, for
                 offline evaluation. A model fit on `full` has already seen the validation
                 rows it would be scored against.

A `full` run does not repoint the app: it prints the constant lines to paste into
src/models/constants.py, so swapping the served artifact stays a reviewed change.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from datetime import datetime, timezone

import pandas as pd
from joblib import dump

from src.eval.eval_artifacts import build_eval_artifacts, fit_knn, fit_mf
from src.eval.splits import build_validation
from src.models.constants import DATA_PROCESSED_DIR, EVAL_ARTIFACTS_DIR, MODELS_DIR

try:
    UTC = datetime.UTC  # type: ignore[attr-defined]
except AttributeError:  # Python < 3.11
    UTC = timezone.utc


def version_suffix() -> str:
    return datetime.now(UTC).strftime("v%Y.%m.%d_%H%M%S")


def save_full(interactions: pd.DataFrame) -> dict[str, Path]:
    suffix = version_suffix()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "knn": MODELS_DIR / f"item_knn_sklearn_{suffix}.joblib",
        "mf": MODELS_DIR / f"mf_sgd_{suffix}.joblib",
    }
    dump(fit_knn(interactions), paths["knn"])
    dump(fit_mf(interactions), paths["mf"])

    manifest_path = DATA_PROCESSED_DIR / "artifacts_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}
    manifest.setdefault("models", []).append(
        {
            "knn": str(paths["knn"]),
            "mf": str(paths["mf"]),
            "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", choices=("full", "train"), default="full")
    args = parser.parse_args(argv)

    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")

    if args.split == "train":
        train_df, val_df = build_validation(interactions)
        paths = build_eval_artifacts(train_df)
        print(f"Fit on train split: {len(train_df):,} rows ({len(val_df):,} held out)")
        print(f"Saved eval artifacts to {EVAL_ARTIFACTS_DIR}:", paths["knn"].name, paths["mf"].name)
        return 0

    paths = save_full(interactions)
    print(f"Fit on all {len(interactions):,} interactions")
    print("Saved artifacts:", paths["knn"].name, paths["mf"].name)
    print("\nTo serve these, update src/models/constants.py:")
    print(f'    MF_MODEL_STEM = "{paths["mf"].stem}"')
    print(f'    KNN_MODEL_STEM = "{paths["knn"].stem}"')
    print("Then remove the superseded artifacts so one stem per family remains.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
