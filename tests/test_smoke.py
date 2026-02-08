"""Smoke tests — verify critical modules import without errors."""

import pytest


class TestCoreImports:
    """Verify that all core modules import cleanly."""

    def test_scoring_pipeline_imports(self):
        from src.app.scoring_pipeline import (
            ScoringContext,
            PipelineResult,
            run_seed_based_pipeline,
            run_personalized_pipeline,
            run_browse_pipeline,
            blend_personalized_and_seed,
            apply_post_filters,
            finalize_explanation_shares,
        )
        assert ScoringContext is not None
        assert PipelineResult is not None

    def test_recommender_imports(self):
        from src.app.recommender import (
            HybridComponents,
            HybridRecommender,
            compute_component_shares,
            choose_weights,
        )
        assert HybridComponents is not None
        assert HybridRecommender is not None

    def test_model_imports(self):
        from src.models.mf_sgd import FunkSVDRecommender
        from src.models.hybrid import weighted_blend, reciprocal_rank_fusion
        from src.models.user_embedding import generate_user_embedding
        assert FunkSVDRecommender is not None

    def test_eval_imports(self):
        from src.eval.metrics import (
            ndcg_at_k,
            average_precision_at_k,
            precision_at_k,
            recall_at_k,
            ndcg_at_k_graded,
        )
        assert ndcg_at_k is not None

    def test_feature_imports(self):
        from src.features.cold_start import flag_cold_start, content_only_score
        from src.features.scaling import compute_feature_stats
        assert flag_cold_start is not None

    def test_constants_load(self):
        from src.app.constants import (
            BALANCED_WEIGHTS,
            DIVERSITY_EMPHASIZED_WEIGHTS,
            DEFAULT_TOP_N,
            compute_quality_factor,
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
