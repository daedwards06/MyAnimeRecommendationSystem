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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from joblib import dump, load
from threadpoolctl import threadpool_limits

from src.models.als_implicit import ImplicitALSRecommender
from src.models.constants import (
    ALS_EVAL_ARTIFACT,
    EVAL_ARTIFACTS_DIR,
    KNN_EVAL_ARTIFACT,
    KNN_MODEL_STEM,
    MF_EVAL_ARTIFACT,
    MF_MODEL_STEM,
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
# Offline-only (not served). alpha=5 was picked by scripts/diagnose_mf.py on validation users
# outside the reporting cohort (reports/mf_diagnostic.md).
ALS_PARAMS: dict[str, Any] = {
    "n_factors": 64,
    "reg": 0.1,
    "alpha": 5.0,
    "n_iters": 10,
    "random_state": RANDOM_SEED,
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


def load_eval_als(
    train_df: pd.DataFrame,
    *,
    artifacts_dir: Path | None = None,
    cache: bool = True,
) -> ImplicitALSRecommender:
    """Implicit ALS fit on the train split, cached like `load_eval_models`."""
    out_dir = Path(artifacts_dir) if artifacts_dir is not None else EVAL_ARTIFACTS_DIR
    path = out_dir / f"{ALS_EVAL_ARTIFACT}.joblib"
    fingerprint = {**train_fingerprint(train_df), "params": ALS_PARAMS}
    if _is_fresh(path, fingerprint):
        return load(path)
    logger.info("Fitting eval implicit ALS on train split (%s)", fingerprint)
    # ~85K tiny (64 x 64) solves per sweep: a multithreaded BLAS spends far longer coordinating
    # threads than computing.
    with threadpool_limits(limits=1):
        model = ImplicitALSRecommender(**ALS_PARAMS).fit(train_df)
    if cache:
        _save(model, path, fingerprint)
    return model


def knn_eval_scores(knn_model: ItemKNNRecommender, user_id: int, seen: set[int]) -> dict[int, float]:
    """kNN scores for every item outside `seen`, the user's train-split history.

    The exclusion set must come from the eval's train history, never from the model's own
    matrix (`exclude_seen=True`). A matrix that contains the held-out item masks the ground
    truth before scoring (the Task 0.4 bug), and `getcol().nonzero()` drops explicit 0 ratings,
    so train items a user watched without rating stayed eligible as recommendations.
    """
    scores = knn_model.score_all(user_id, exclude_seen=False)
    for item in seen:
        scores.pop(item, None)
    return scores


def knn_eval_recommend(knn_model: ItemKNNRecommender, user_id: int, seen: set[int], top_k: int) -> list[int]:
    scores = knn_eval_scores(knn_model, user_id, seen)
    return [item for item, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]]


def run_metadata(*, k: int, sample_users: int, generated_at: str | None = None) -> dict[str, Any]:
    """Provenance stamped into every metrics JSON so a row can be traced to its run.

    `artifacts` names the train-split models evaluation actually scores; `served_stems`
    names the full-fit artifacts the app serves, which are deliberately not the same.
    """
    return {
        "seed": RANDOM_SEED,
        "k": k,
        "sample_users": sample_users,
        "generated_at": generated_at or datetime.now(UTC).isoformat(timespec="seconds"),
        "artifacts": {"mf": MF_EVAL_ARTIFACT, "knn": KNN_EVAL_ARTIFACT, "als": ALS_EVAL_ARTIFACT},
        "served_stems": {"mf": MF_MODEL_STEM, "knn": KNN_MODEL_STEM},
    }
