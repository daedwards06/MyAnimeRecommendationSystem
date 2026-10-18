"""Item-kNN is served in the app (Task 0.9): per-request kNN vectors, and the weights that use them."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.pipeline_runner import RecommenderEngine, _profile_ratings
from src.app.constants import (
    BALANCED_WEIGHTS,
    COMMUNITY_BASELINE_WEIGHTS,
    DIVERSITY_EMPHASIZED_WEIGHTS,
)
from src.app.recommender import (
    HybridComponents,
    HybridRecommender,
    choose_weights,
    knn_scores_from_ratings,
)
from src.models.constants import DEFAULT_HYBRID_WEIGHTS
from src.models.knn_sklearn import ItemKNNRecommender

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def knn_model() -> ItemKNNRecommender:
    rng = np.random.default_rng(0)
    rows = [
        (u, i, float(rng.integers(1, 11)))
        for u in range(40)
        for i in range(100, 120)
        if rng.random() < 0.4
    ]
    return ItemKNNRecommender().fit(pd.DataFrame(rows, columns=["user_id", "anime_id", "rating"]))


class _TinyMF:
    def __init__(self, n_items: int):
        rng = np.random.default_rng(1)
        self.Q = rng.standard_normal((n_items, 4)).astype(np.float32)
        self.item_to_index = {100 + i: i for i in range(n_items)}
        self.index_to_item = {i: 100 + i for i in range(n_items)}


class TestKnnScoresFromRatings:
    def test_matches_score_all_for_a_training_user(self, knn_model):
        item_ids = np.arange(100, 120, dtype=np.int64)
        for user_id in list(knn_model.user_to_index)[:5]:
            col = knn_model.raw_item_user.getcol(knn_model.user_to_index[user_id]).tocoo()
            ratings = {knn_model.index_to_item[r]: float(v) for r, v in zip(col.row, col.data, strict=True)}
            ours = knn_scores_from_ratings(knn_model, item_ids, ratings, center=True)
            ref = knn_model.score_all(user_id, exclude_seen=False)
            if not ref:
                continue
            expected = np.asarray([ref.get(int(a), 0.0) for a in item_ids])
            np.testing.assert_allclose(ours, expected, atol=1e-5)

    def test_unknown_items_score_zero_and_order_follows_item_ids(self, knn_model):
        item_ids = np.asarray([105, 999, 101], dtype=np.int64)
        out = knn_scores_from_ratings(knn_model, item_ids, {101: 1.0}, center=False)
        full = knn_scores_from_ratings(knn_model, np.asarray([101, 105]), {101: 1.0}, center=False)
        assert out[1] == 0.0
        assert out[0] == pytest.approx(full[1])
        assert out[2] == pytest.approx(full[0])

    def test_none_when_no_rated_item_is_known(self, knn_model):
        assert knn_scores_from_ratings(knn_model, np.arange(100, 120), {999: 9.0}, center=True) is None

    def test_seed_is_its_own_nearest_neighbour(self, knn_model):
        item_ids = np.arange(100, 120, dtype=np.int64)
        out = knn_scores_from_ratings(knn_model, item_ids, {107: 1.0}, center=False)
        assert int(item_ids[np.argmax(out)]) == 107

    def test_all_equal_ratings_still_give_a_profile_when_centred(self, knn_model):
        item_ids = np.arange(100, 120, dtype=np.int64)
        centred = knn_scores_from_ratings(knn_model, item_ids, {101: 8.0, 102: 8.0}, center=True)
        plain = knn_scores_from_ratings(knn_model, item_ids, {101: 8.0, 102: 8.0}, center=False)
        assert centred is not None
        np.testing.assert_allclose(centred, plain)


class TestEngineServesKnn:
    def _engine(self, knn_model) -> RecommenderEngine:
        item_ids = np.arange(100, 120, dtype=np.int64)
        components = HybridComponents(
            mf=np.ones((1, len(item_ids)), dtype=np.float32), knn=None, pop=None, item_ids=item_ids
        )
        return RecommenderEngine(
            recommender=HybridRecommender(components), components=components, knn_model=knn_model
        )

    def test_seed_request_populates_knn_without_touching_the_engine(self, knn_model):
        engine = self._engine(knn_model)
        row = engine.knn_scores({107: 1.0}, center=False)
        recommender, components = engine.for_request(row)
        assert components.knn is not None and components.knn.shape == (1, 20)
        assert engine.components.knn is None
        recs = recommender.get_top_n_for_user(0, n=1, weights={"mf": 0.0, "knn": 1.0, "pop": 0.0})
        assert recs[0]["anime_id"] == 107
        assert "knn" in recs[0]["_used_components"]

    def test_no_knn_model_means_no_knn_row(self, knn_model):
        engine = self._engine(knn_model)
        engine.knn_model = None
        assert engine.knn_scores({107: 1.0}, center=False) is None
        _, components = engine.for_request(None)
        assert components.knn is None

    def test_personalized_path_has_a_knn_term(self, knn_model):
        engine = self._engine(knn_model)
        ratings = {101: 10.0, 102: 9.0, 115: 2.0}
        row = engine.knn_scores(ratings, center=True)
        recommender, _ = engine.for_request(row)
        recs = recommender.get_personalized_recommendations(
            user_embedding=np.ones(4, dtype=np.float32),
            mf_model=_TinyMF(20),
            n=20,
            weights={"mf": 0.0, "knn": 1.0, "pop": 0.0},
        )
        assert [r["anime_id"] for r in recs] == [int(a) for a in np.arange(100, 120)[np.argsort(-row, kind="stable")]]
        assert recs[0]["_used_components"] == ["knn"]
        assert recs[0]["_raw_components"]["knn"] == pytest.approx(float(row.max()))

    def test_profile_ratings_keys_are_ints(self):
        assert _profile_ratings({"ratings": {"101": 9, 102: "7", "x": 3}}) == {101: 9.0, 102: 7.0}


class TestServedWeights:
    def test_balanced_is_the_retuned_blend(self):
        best = json.loads((ROOT / "experiments/optuna_studies/hybrid_weights_best.json").read_text())
        tuned = {k: best["weights_normalized"][f"w_{k}"] for k in ("mf", "knn", "pop")}
        assert tuned == DEFAULT_HYBRID_WEIGHTS
        for k in ("mf", "knn", "pop"):
            assert BALANCED_WEIGHTS[k] == pytest.approx(DEFAULT_HYBRID_WEIGHTS[k], abs=1e-4)
        assert max(BALANCED_WEIGHTS, key=BALANCED_WEIGHTS.get) == "knn"

    def test_presets(self):
        assert choose_weights("Balanced") is BALANCED_WEIGHTS
        assert choose_weights("Diversity") is DIVERSITY_EMPHASIZED_WEIGHTS
        assert DIVERSITY_EMPHASIZED_WEIGHTS == {"mf": 0.0, "knn": 1.0, "pop": 0.0}

    def test_community_baseline_has_no_knn_and_ranks_by_mf(self):
        assert COMMUNITY_BASELINE_WEIGHTS["knn"] == 0.0
        assert COMMUNITY_BASELINE_WEIGHTS["mf"] > 0.99
