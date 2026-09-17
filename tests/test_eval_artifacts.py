"""Tests for src/eval/eval_artifacts.py.

The point of the module is that offline evaluation never scores the served artifacts, which
are fit on the same rows the validation split is carved from.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.eval.eval_artifacts import (
    build_eval_artifacts,
    load_eval_models,
    train_fingerprint,
)
from src.models.constants import EVAL_ARTIFACTS_DIR, KNN_EVAL_ARTIFACT, MF_EVAL_ARTIFACT, MODELS_DIR


@pytest.fixture
def interactions() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for user_id in range(40):
        for anime_id in rng.choice(15, size=8, replace=False):
            rows.append({"user_id": user_id, "anime_id": int(anime_id), "rating": float(rng.integers(1, 11))})
    return pd.DataFrame(rows)


def test_fingerprint_tracks_split_shape(interactions: pd.DataFrame):
    fp = train_fingerprint(interactions)
    assert fp == {"n_rows": len(interactions), "n_users": 40, "n_items": 15}
    assert train_fingerprint(interactions.iloc[:-1]) != fp


def test_build_writes_artifacts_and_fingerprint(tmp_path: Path, interactions: pd.DataFrame):
    paths = build_eval_artifacts(interactions, artifacts_dir=tmp_path)

    for path in paths.values():
        assert path.exists()
        sidecar = path.with_suffix(".fingerprint.json")
        assert json.loads(sidecar.read_text(encoding="utf-8")) == train_fingerprint(interactions)


def test_load_reuses_cache_when_fingerprint_matches(tmp_path: Path, interactions: pd.DataFrame):
    paths = build_eval_artifacts(interactions, artifacts_dir=tmp_path)
    mtimes = {k: p.stat().st_mtime_ns for k, p in paths.items()}

    knn_model, mf_model = load_eval_models(interactions, artifacts_dir=tmp_path)

    assert knn_model is not None and mf_model is not None
    assert {k: p.stat().st_mtime_ns for k, p in paths.items()} == mtimes


def test_load_refits_when_split_changed(tmp_path: Path, interactions: pd.DataFrame):
    paths = build_eval_artifacts(interactions.iloc[:100], artifacts_dir=tmp_path)
    stale = train_fingerprint(interactions.iloc[:100])

    load_eval_models(interactions, artifacts_dir=tmp_path)

    for path in paths.values():
        written = json.loads(path.with_suffix(".fingerprint.json").read_text(encoding="utf-8"))
        assert written == train_fingerprint(interactions)
        assert written != stale


def test_load_fits_without_cache_when_disabled(tmp_path: Path, interactions: pd.DataFrame):
    knn_model, mf_model = load_eval_models(interactions, artifacts_dir=tmp_path, cache=False)

    assert knn_model is not None and mf_model is not None
    assert not any(tmp_path.glob("*.joblib"))


def test_eval_artifacts_live_outside_models_dir():
    """A trainsplit artifact inside models/ would make the app's stem selection ambiguous."""
    assert EVAL_ARTIFACTS_DIR.resolve() != MODELS_DIR.resolve()
    assert MODELS_DIR.resolve() not in EVAL_ARTIFACTS_DIR.resolve().parents

    for stem in (MF_EVAL_ARTIFACT, KNN_EVAL_ARTIFACT):
        assert not (MODELS_DIR / f"{stem}.joblib").exists()
