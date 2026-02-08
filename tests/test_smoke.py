"""Smoke tests — verify critical modules import without errors."""

import pytest


class TestCoreImports:
    """Verify that all core modules import cleanly."""

    def test_scoring_pipeline_imports(self):
        from src.app.scoring_pipeline import (
            PipelineResult,
            ScoringContext,
        )
        assert ScoringContext is not None
        assert PipelineResult is not None

    def test_recommender_imports(self):
        from src.app.recommender import (
            HybridComponents,
            HybridRecommender,
        )
        assert HybridComponents is not None
        assert HybridRecommender is not None

    def test_model_imports(self):
        from src.models.mf_sgd import FunkSVDRecommender
        assert FunkSVDRecommender is not None

    def test_eval_imports(self):
        from src.eval.metrics import (
            ndcg_at_k,
        )
        assert ndcg_at_k is not None

    def test_feature_imports(self):
        from src.features.cold_start import flag_cold_start
        assert flag_cold_start is not None

    def test_constants_load(self):
        from src.app.constants import (
            BALANCED_WEIGHTS,
            DEFAULT_TOP_N,
            DIVERSITY_EMPHASIZED_WEIGHTS,
        )
        assert sum(BALANCED_WEIGHTS.values()) == pytest.approx(1.0, abs=0.01)
        assert sum(DIVERSITY_EMPHASIZED_WEIGHTS.values()) == pytest.approx(1.0, abs=0.01)
        assert DEFAULT_TOP_N > 0

    def test_quality_factor_modes(self):
        from src.app.constants import compute_quality_factor
        # mal_scaled
        qf = compute_quality_factor(8.0, mode="mal_scaled")
        assert 0.0 < qf <= 1.0
        # binary
        qf_bin = compute_quality_factor(8.0, mode="binary")
        assert qf_bin == 1.0
        qf_low = compute_quality_factor(5.0, mode="binary")
        assert qf_low == 0.5
        # disabled
        assert compute_quality_factor(3.0, mode="disabled") == 1.0

    def test_component_shares_sum_to_one(self):
        from src.app.recommender import compute_component_shares
        shares = compute_component_shares(
            {"mf": 0.5, "knn": 0.3, "pop": 0.2},
            used_components=["mf", "knn", "pop"],
        )
        total = shares["mf"] + shares["knn"] + shares["pop"]
        assert total == pytest.approx(1.0, abs=1e-6)
