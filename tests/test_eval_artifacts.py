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
    knn_eval_recommend,
    knn_eval_scores,
    load_eval_models,
    train_fingerprint,
)
from src.models.constants import EVAL_ARTIFACTS_DIR, KNN_EVAL_ARTIFACT, MF_EVAL_ARTIFACT, MODELS_DIR
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender

ROOT = Path(__file__).resolve().parents[1]


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


@pytest.fixture
def knn_fit_with_holdout() -> tuple[ItemKNNRecommender, set[int], int, int]:
    """kNN fit on data that still contains user 0's held-out item 5.

    User 0's train history is items 0-4, where item 3 was watched but not rated (0). Users 1-6
    rated items 0-2 and 5 highly, so item 5 is user 0's strongest unseen neighbour.
    """
    rows = [(0, i, r) for i, r in zip(range(5), [9.0, 8.0, 9.0, 0.0, 7.0])] + [(0, 5, 9.0)]
    for u in range(1, 7):
        rows += [(u, 0, 9.0), (u, 1, 8.0), (u, 2, 9.0), (u, 5, 10.0), (u, 6 + u % 2, 3.0)]
    df = pd.DataFrame(rows, columns=["user_id", "anime_id", "rating"])
    return ItemKNNRecommender(popularity_weight=0.0).fit(df), {0, 1, 2, 3, 4}, 5, 3


def test_knn_eval_does_not_mask_the_holdout(knn_fit_with_holdout):
    """Task 0.4 regression: the exclusion set is the train history, never the model's matrix.

    Fit on the full table, the model's own seen-mask contains the held-out item and removes the
    ground truth before scoring; that is how item-kNN published NDCG@10 = 0.0017.
    """
    knn, seen, holdout, _ = knn_fit_with_holdout
    assert holdout not in knn.score_all(0, exclude_seen=True)

    scores = knn_eval_scores(knn, 0, seen)
    assert holdout in scores
    assert knn_eval_recommend(knn, 0, seen, top_k=1) == [holdout]


def test_knn_eval_excludes_zero_rated_train_items(knn_fit_with_holdout):
    """The model's mask uses `nonzero()`, so a watched-but-unrated (0) train item slipped through."""
    knn, seen, _, unrated = knn_fit_with_holdout
    assert unrated in knn.score_all(0, exclude_seen=True)

    scores = knn_eval_scores(knn, 0, seen)
    assert not seen & scores.keys()
    assert unrated not in knn_eval_recommend(knn, 0, seen, top_k=10)


@pytest.mark.parametrize("script", ["evaluate_knn_mf.py", "evaluate_hybrid.py"])
def test_ablation_eval_scripts_exclude_by_train_history(script: str):
    source = (ROOT / "scripts" / script).read_text(encoding="utf-8")
    assert "exclude_seen=True" not in source
    assert "knn_eval_" in source


def test_mf_returns_nothing_for_an_unknown_user(interactions: pd.DataFrame):
    """An unknown user used to get items in index order, an accidental popularity fallback.

    33 cohort users have no train history; that tie-break hit five of them and was worth +0.0044
    NDCG@10 to MF in the published table.
    """
    mf = FunkSVDRecommender(n_epochs=1).fit(interactions)

    assert mf.recommend(999, top_k=5) == []
    assert len(mf.recommend(0, top_k=5)) == 5
