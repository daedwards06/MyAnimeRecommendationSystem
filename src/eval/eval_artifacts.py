"""Train-split CF artifacts for offline evaluation.

The artifacts in `models/` are fit on the *full* interaction table, which is correct for
serving and wrong for measurement: `build_validation` carves its holdout out of that same
table, so a served artifact has already seen every validation pair it would be scored on.
Evaluation therefore uses its own artifacts, fit on the train split only, cached under
`experiments/artifacts/` (git-ignored) because refitting kNN and MF on ~7.8M rows per run is
expensive.

The cache is keyed on the shape of the train split it was fit from; a mismatch refits rather
than silently scoring against a stale model.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from joblib import dump, load

from src.models.constants import (
    EVAL_ARTIFACTS_DIR,
    KNN_EVAL_ARTIFACT,
    MF_EVAL_ARTIFACT,
    RANDOM_SEED,
)
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender

logger = logging.getLogger(__name__)

MF_PARAMS: dict[str, Any] = {
    "n_factors": 64,
    "lr": 0.005,
    "reg": 0.05,
    "n_epochs": 10,
    "random_state": RANDOM_SEED,
}
KNN_PARAMS: dict[str, Any] = {
    "normalize_items": True,
    "center_ratings": True,
    "popularity_weight": 0.02,
}


def train_fingerprint(train_df: pd.DataFrame) -> dict[str, int]:
    """Shape of the split an artifact was fit from, used to detect a stale cache."""
    return {
        "n_rows": int(len(train_df)),
        "n_users": int(train_df["user_id"].nunique()),
        "n_items": int(train_df["anime_id"].nunique()),
    }


def _sidecar_path(artifact_path: Path) -> Path:
    return artifact_path.with_suffix(".fingerprint.json")


def _read_fingerprint(artifact_path: Path) -> dict[str, int] | None:
    try:
        return json.loads(_sidecar_path(artifact_path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _is_fresh(artifact_path: Path, fingerprint: dict[str, int]) -> bool:
    return artifact_path.exists() and _read_fingerprint(artifact_path) == fingerprint


def _save(model: Any, artifact_path: Path, fingerprint: dict[str, int]) -> None:
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    dump(model, artifact_path)
    _sidecar_path(artifact_path).write_text(json.dumps(fingerprint, indent=2), encoding="utf-8")


def fit_knn(train_df: pd.DataFrame) -> ItemKNNRecommender:
    return ItemKNNRecommender(**KNN_PARAMS).fit(train_df)


def fit_mf(train_df: pd.DataFrame) -> FunkSVDRecommender:
    return FunkSVDRecommender(**MF_PARAMS).fit(train_df)


def build_eval_artifacts(train_df: pd.DataFrame, *, artifacts_dir: Path | None = None) -> dict[str, Path]:
    """Fit kNN and MF on `train_df` and write them to the eval artifact cache."""
    out_dir = Path(artifacts_dir) if artifacts_dir is not None else EVAL_ARTIFACTS_DIR
    fingerprint = train_fingerprint(train_df)
    paths = {
        "knn": out_dir / f"{KNN_EVAL_ARTIFACT}.joblib",
        "mf": out_dir / f"{MF_EVAL_ARTIFACT}.joblib",
    }
    _save(fit_knn(train_df), paths["knn"], fingerprint)
    _save(fit_mf(train_df), paths["mf"], fingerprint)
    return paths


def load_eval_models(
    train_df: pd.DataFrame,
    *,
    artifacts_dir: Path | None = None,
    cache: bool = True,
) -> tuple[ItemKNNRecommender, FunkSVDRecommender]:
    """Return (kNN, MF) fit on the train split only — never the served `models/` artifacts.

    Reuses the cached artifacts when their fingerprint matches `train_df`, otherwise refits.
    """
    out_dir = Path(artifacts_dir) if artifacts_dir is not None else EVAL_ARTIFACTS_DIR
    fingerprint = train_fingerprint(train_df)
    knn_path = out_dir / f"{KNN_EVAL_ARTIFACT}.joblib"
    mf_path = out_dir / f"{MF_EVAL_ARTIFACT}.joblib"

    if _is_fresh(knn_path, fingerprint):
        knn_model: ItemKNNRecommender = load(knn_path)
    else:
        logger.info("Fitting eval kNN on train split (%s)", fingerprint)
        knn_model = fit_knn(train_df)
        if cache:
            _save(knn_model, knn_path, fingerprint)

    if _is_fresh(mf_path, fingerprint):
        mf_model: FunkSVDRecommender = load(mf_path)
    else:
        logger.info("Fitting eval MF on train split (%s)", fingerprint)
        mf_model = fit_mf(train_df)
        if cache:
            _save(mf_model, mf_path, fingerprint)

    return knn_model, mf_model
