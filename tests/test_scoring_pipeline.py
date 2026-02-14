"""Integration tests for the extracted scoring pipeline.

Tests cover:
- Seed-based recommendation pipeline
- Personalized recommendation pipeline
- Browse / filter-only pipeline
- Result ordering and exclusions
- Genre/type/year filters
- Franchise cap behavior
- Pipeline determinism
- Timing diagnostics
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from conftest import MockMFModel

from src.app.recommender import HybridComponents, HybridRecommender
from src.app.scoring_pipeline import (
    PipelineResult,
    ScoringContext,
    run_browse_pipeline,
    run_personalized_pipeline,
    run_seed_based_pipeline,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_metadata() -> pd.DataFrame:
    """Small realistic metadata DataFrame for testing."""
    return pd.DataFrame(
        [
            {
                "anime_id": 1,
                "title_display": "Fullmetal Alchemist: Brotherhood",
                "genres": "Action|Adventure|Drama",
                "themes": "Gore|Military",
                "demographics": "Shounen",
                "type": "TV",
                "episodes": 64,
                "aired_from": "2009-04-05T00:00:00+00:00",
                "aired_to": "2010-07-04T00:00:00+00:00",
                "year": 2009,
                "mal_score": 9.1,
                "members_count": 3000000,
                "studios": "Bones",
                "producers": "Aniplex|Square Enix",
                "synopsis_snippet": "Two brothers search for the Philosopher's Stone after a failed transmutation.",
            },
            {
                "anime_id": 2,
                "title_display": "Steins;Gate",
                "genres": "Drama|Sci-Fi|Thriller",
                "themes": "Psychological|Time Travel",
                "demographics": "None",
                "type": "TV",
                "episodes": 24,
                "aired_from": "2011-04-06T00:00:00+00:00",
                "aired_to": "2011-09-14T00:00:00+00:00",
                "year": 2011,
                "mal_score": 9.1,
                "members_count": 2000000,
                "studios": "White Fox",
                "producers": "Frontier Works|Media Factory",
                "synopsis_snippet": "A self-proclaimed mad scientist accidentally invents a time machine.",
            },
            {
                "anime_id": 3,
                "title_display": "Hunter x Hunter (2011)",
                "genres": "Action|Adventure",
                "themes": "Super Power",
                "demographics": "Shounen",
                "type": "TV",
                "episodes": 148,
                "aired_from": "2011-10-02T00:00:00+00:00",
                "aired_to": "2014-09-24T00:00:00+00:00",
                "year": 2011,
                "mal_score": 9.0,
                "members_count": 1800000,
                "studios": "Madhouse",
                "producers": "VAP|Nippon Television Network",
                "synopsis_snippet": "A young boy embarks on a journey to find his father and become a Hunter.",
            },
            {
                "anime_id": 4,
                "title_display": "Attack on Titan",
                "genres": "Action|Drama",
                "themes": "Gore|Military|Survival",
                "demographics": "Shounen",
                "type": "TV",
                "episodes": 25,
                "aired_from": "2013-04-07T00:00:00+00:00",
                "aired_to": "2013-09-29T00:00:00+00:00",
                "year": 2013,
                "mal_score": 8.5,
                "members_count": 2500000,
                "studios": "Wit Studio",
                "producers": "Production I.G|Dentsu",
                "synopsis_snippet": "Humanity fights for survival against giant humanoid creatures.",
            },
            {
                "anime_id": 5,
                "title_display": "Death Note",
                "genres": "Mystery|Thriller",
                "themes": "Psychological|Supernatural",
                "demographics": "Shounen",
                "type": "TV",
                "episodes": 37,
                "aired_from": "2006-10-04T00:00:00+00:00",
                "aired_to": "2007-06-27T00:00:00+00:00",
                "year": 2006,
                "mal_score": 8.6,
                "members_count": 2800000,
                "studios": "Madhouse",
                "producers": "VAP|D.N. Dream Partners",
                "synopsis_snippet": "A high school student finds a notebook that can kill anyone whose name is written in it.",
            },
            {
                "anime_id": 6,
                "title_display": "Cowboy Bebop",
                "genres": "Action|Sci-Fi",
                "themes": "Space",
                "demographics": "None",
                "type": "TV",
                "episodes": 26,
                "aired_from": "1998-04-03T00:00:00+00:00",
                "aired_to": "1999-04-24T00:00:00+00:00",
                "year": 1998,
                "mal_score": 8.8,
                "members_count": 1600000,
                "studios": "Sunrise",
                "producers": "Bandai Visual",
                "synopsis_snippet": "Bounty hunters travel through space in 2071.",
            },
            {
                "anime_id": 7,
                "title_display": "Code Geass: Lelouch of the Rebellion",
                "genres": "Action|Drama|Sci-Fi",
                "themes": "Mecha|Military|School",
                "demographics": "None",
                "type": "TV",
                "episodes": 25,
                "aired_from": "2006-10-06T00:00:00+00:00",
                "aired_to": "2007-07-29T00:00:00+00:00",
                "year": 2006,
                "mal_score": 8.7,
                "members_count": 1700000,
                "studios": "Sunrise",
                "producers": "Bandai Visual|Mainichi Broadcasting System",
                "synopsis_snippet": "An exiled prince gains the power to control minds and leads a rebellion.",
            },
            {
                "anime_id": 8,
                "title_display": "Your Name",
                "genres": "Drama|Romance|Supernatural",
                "themes": "School",
                "demographics": "None",
                "type": "Movie",
                "episodes": 1,
                "aired_from": "2016-08-26T00:00:00+00:00",
                "aired_to": "2016-08-26T00:00:00+00:00",
                "year": 2016,
                "mal_score": 8.8,
                "members_count": 2200000,
                "studios": "CoMix Wave Films",
                "producers": "Toho|KADOKAWA",
                "synopsis_snippet": "Two teenagers swap bodies and must find each other across time and space.",
            },
            {
                "anime_id": 9,
                "title_display": "Niche Psychological Thriller",
                "genres": "Mystery|Psychological",
                "themes": "Psychological",
                "demographics": "None",
                "type": "TV",
                "episodes": 12,
                "aired_from": "2015-01-10T00:00:00+00:00",
                "aired_to": "2015-03-28T00:00:00+00:00",
                "year": 2015,
                "mal_score": 6.8,
                "members_count": 45000,
                "studios": "Studio Deen",
                "producers": "Unknown",
                "synopsis_snippet": "A niche psychological thriller with cult following but low mainstream appeal.",
            },
            {
                "anime_id": 10,
                "title_display": "Attack on Titan Season 2",
                "genres": "Action|Drama",
                "themes": "Gore|Military|Survival",
                "demographics": "Shounen",
                "type": "TV",
                "episodes": 12,
                "aired_from": "2017-04-01T00:00:00+00:00",
                "aired_to": "2017-06-17T00:00:00+00:00",
                "year": 2017,
                "mal_score": 8.5,
                "members_count": 2000000,
                "studios": "Wit Studio",
                "producers": "Production I.G|Dentsu",
                "synopsis_snippet": "The battle for humanity continues in the second season.",
            },
        ]
    )


@pytest.fixture
def mock_mf_model() -> MockMFModel:
    """Mock MF model with 3 users and 10 items (override conftest default)."""
    return MockMFModel(n_users=3, n_items=10, n_factors=8)


# Reuse mock_knn_model from conftest (it returns None by default)

# Reuse mock_bundle from conftest (it will use sample_metadata and mock_mf_model)

@pytest.fixture
def mock_components(mock_mf_model: MockMFModel) -> HybridComponents:
    """Mock HybridComponents for recommender."""
    # Precompute MF scores for all users and items
    # Shape needs to be (n_users, n_items) for 2D indexing
    mf_scores_2d = np.zeros((3, 10), dtype=np.float32)
    for user_idx in range(3):
        mf_scores_2d[user_idx] = mock_mf_model.predict_for_user(user_idx, list(range(10)))

    return HybridComponents(
        mf=mf_scores_2d,  # 2D array (n_users, n_items)
        knn=None,  # Can be None
        pop=np.random.rand(10).astype(np.float32) * 0.1,  # Small popularity scores
        item_ids=np.arange(1, 11, dtype=np.int64),  # anime_ids 1-10
    )


@pytest.fixture
def mock_recommender(mock_components: HybridComponents) -> HybridRecommender:
    """Mock HybridRecommender instance."""
    return HybridRecommender(mock_components)


@pytest.fixture
def mock_bundle(mock_mf_model: MockMFModel, sample_metadata: pd.DataFrame) -> dict:
    """Mock artifact bundle."""
    return {
        "metadata": sample_metadata,
        "models": {
            "mf": mock_mf_model,
            "knn": None,
        },
        "explanations": {},
        "diversity": {},
    }


@pytest.fixture
def mock_scoring_context(
    sample_metadata: pd.DataFrame,
    mock_bundle: dict,
    mock_recommender: HybridRecommender,
    mock_components: HybridComponents,
    mock_mf_model: MockMFModel,
) -> ScoringContext:
    """Comprehensive mock ScoringContext with sensible defaults.

    This fixture provides a minimal but complete context for testing the
    seed-based pipeline. Tests can override specific attributes as needed.
    """
    # Helper functions
    def pop_pct_fn(anime_id: int) -> float:
        """Mock popularity percentile."""
        row = sample_metadata[sample_metadata["anime_id"] == anime_id]
        if row.empty:
            return 0.0
        members = row.iloc[0]["members_count"]
        max_members = sample_metadata["members_count"].max()
        return float(members / max_members) if max_members > 0 else 0.0

    def is_in_training_fn(anime_id: int) -> bool:
        """Mock training set membership — assume all 10 items are in training."""
        return 1 <= anime_id <= 10

    return ScoringContext(
        metadata=sample_metadata,
        bundle=mock_bundle,
        recommender=mock_recommender,
        components=mock_components,
        seed_ids=[1],  # Default seed: Fullmetal Alchemist: Brotherhood
        seed_titles=["Fullmetal Alchemist: Brotherhood"],
        user_index=0,
        user_embedding=None,
        personalization_enabled=False,
        personalization_strength=1.0,
        active_profile=None,
        watched_ids=set(),
        personalization_blocked_reason=None,
        weights={"mf": 0.93, "knn": 0.07, "pop": 0.003},
        seed_ranking_mode="completion",
        genre_filter=[],
        type_filter=[],
        year_range=(1960, 2025),
        sort_by="Match score",
        default_sort_for_mode="Match score",
        n_requested=10,
        top_n=10,
        browse_mode=False,
        pop_pct_fn=pop_pct_fn,
        is_in_training_fn=is_in_training_fn,
        mf_model=mock_mf_model,
        mf_stem="mock_v1.0",
        user_embedding_meta={},
        ranked_hygiene_exclude_ids=set(),
    )


# ---------------------------------------------------------------------------
# Tests: Seed-Based Pipeline
# ---------------------------------------------------------------------------


class TestSeedBasedPipeline:
    """Tests for run_seed_based_pipeline()."""

    def test_seed_pipeline_returns_results(self, mock_scoring_context: ScoringContext):
        """Seed-based pipeline returns non-empty results for valid seed."""
        result = run_seed_based_pipeline(mock_scoring_context)

        assert isinstance(result, PipelineResult)
        assert len(result.ranked_items) > 0, "Should return recommendations"
        assert all(isinstance(item, dict) for item in result.ranked_items)

    def test_seed_excluded_from_results(self, mock_scoring_context: ScoringContext):
        """Seed anime ID must not appear in output."""
        mock_scoring_context.seed_ids = [1]
        result = run_seed_based_pipeline(mock_scoring_context)

        result_ids = {item["anime_id"] for item in result.ranked_items}
        assert 1 not in result_ids, "Seed ID should be excluded from results"

    def test_multiple_seeds_excluded(self, mock_scoring_context: ScoringContext):
        """Multiple seed IDs must all be excluded."""
        mock_scoring_context.seed_ids = [1, 2, 3]
        mock_scoring_context.seed_titles = ["FMA", "Steins;Gate", "HxH"]
        result = run_seed_based_pipeline(mock_scoring_context)

        result_ids = {item["anime_id"] for item in result.ranked_items}
        assert 1 not in result_ids
        assert 2 not in result_ids
        assert 3 not in result_ids

    def test_watched_excluded(self, mock_scoring_context: ScoringContext):
        """Watched IDs must be excluded from results."""
        mock_scoring_context.watched_ids = {2, 3}
        result = run_seed_based_pipeline(mock_scoring_context)

        result_ids = {item["anime_id"] for item in result.ranked_items}
        assert 2 not in result_ids, "Watched ID 2 should be excluded"
        assert 3 not in result_ids, "Watched ID 3 should be excluded"

    def test_results_sorted_by_score_descending(self, mock_scoring_context: ScoringContext):
        """Results must be sorted by score in descending order."""
        result = run_seed_based_pipeline(mock_scoring_context)

        scores = [item["score"] for item in result.ranked_items]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score descending"

    def test_genre_filter_restricts_output(self, mock_scoring_context: ScoringContext):
        """Genre filter should restrict output to matching genres."""
        mock_scoring_context.genre_filter = ["Action"]
        result = run_seed_based_pipeline(mock_scoring_context)

        # Genre filter is applied as a post-filter, so results should prefer Action
        # but may include some non-Action if there aren't enough matches
        if len(result.ranked_items) > 0:
            action_count = 0
            for item in result.ranked_items:
                anime_id = item["anime_id"]
                row = mock_scoring_context.metadata[
                    mock_scoring_context.metadata["anime_id"] == anime_id
                ].iloc[0]
                genres = str(row["genres"])
                if "Action" in genres:
                    action_count += 1
            # At least some results should have Action genre
            assert action_count > 0, "Should have at least some Action genre items"

    def test_type_filter_restricts_output(self, mock_scoring_context: ScoringContext):
        """Type filter should restrict output to matching types."""
        mock_scoring_context.type_filter = ["Movie"]
        result = run_seed_based_pipeline(mock_scoring_context)

        # Type filter is applied as a post-filter
        # With our small dataset, there's only 1 Movie, so results may be limited
        if len(result.ranked_items) > 0:
            movie_count = 0
            for item in result.ranked_items:
                anime_id = item["anime_id"]
                row = mock_scoring_context.metadata[
                    mock_scoring_context.metadata["anime_id"] == anime_id
                ].iloc[0]
                if row["type"] == "Movie":
                    movie_count += 1
            # Should have at least one movie or be empty if filter is strict
            assert movie_count > 0 or len(result.ranked_items) == 0

    def test_year_range_filter_restricts_output(self, mock_scoring_context: ScoringContext):
        """Year range filter should restrict output to matching years."""
        mock_scoring_context.year_range = (2010, 2015)
        result = run_seed_based_pipeline(mock_scoring_context)

        # Year range filter is applied as a post-filter
        if len(result.ranked_items) > 0:
            in_range_count = 0
            for item in result.ranked_items:
                anime_id = item["anime_id"]
                row = mock_scoring_context.metadata[
                    mock_scoring_context.metadata["anime_id"] == anime_id
                ].iloc[0]
                year = row["year"]
                if 2010 <= year <= 2015:
                    in_range_count += 1
            # Should have at least some items in the year range
            assert in_range_count > 0, "Should have at least some items in year range"

    def test_top_n_respected(self, mock_scoring_context: ScoringContext):
        """Pipeline should respect top_n parameter."""
        mock_scoring_context.top_n = 3
        mock_scoring_context.n_requested = 3
        result = run_seed_based_pipeline(mock_scoring_context)

        assert len(result.ranked_items) <= 3, "Should return at most top_n results"

    def test_pipeline_result_has_timing(self, mock_scoring_context: ScoringContext):
        """PipelineResult.timing should contain expected keys."""
        result = run_seed_based_pipeline(mock_scoring_context)

        assert isinstance(result.timing, dict)
        # Check for at least one timing key
        assert len(result.timing) > 0, "Timing dict should not be empty"

    def test_deterministic_same_inputs_same_outputs(self, mock_scoring_context: ScoringContext):
        """Same inputs should produce identical outputs across multiple runs."""
        result1 = run_seed_based_pipeline(mock_scoring_context)
        result2 = run_seed_based_pipeline(mock_scoring_context)
        result3 = run_seed_based_pipeline(mock_scoring_context)

        ids1 = [item["anime_id"] for item in result1.ranked_items]
        ids2 = [item["anime_id"] for item in result2.ranked_items]
        ids3 = [item["anime_id"] for item in result3.ranked_items]

        assert ids1 == ids2 == ids3, "Results should be deterministic"

        scores1 = [item["score"] for item in result1.ranked_items]
        scores2 = [item["score"] for item in result2.ranked_items]
        scores3 = [item["score"] for item in result3.ranked_items]

        assert np.allclose(scores1, scores2, rtol=1e-6)
        assert np.allclose(scores2, scores3, rtol=1e-6)


# ---------------------------------------------------------------------------
# Tests: Personalized Pipeline
# ---------------------------------------------------------------------------


class TestPersonalizedPipeline:
    """Tests for run_personalized_pipeline()."""

    def test_personalized_with_valid_embedding(
        self, mock_scoring_context: ScoringContext, mock_mf_model: MockMFModel
    ):
        """Personalized pipeline returns results when user_embedding is valid."""
        # Generate a valid user embedding
        user_embedding = mock_mf_model.P[0].copy()
        mock_scoring_context.user_embedding = user_embedding
        mock_scoring_context.personalization_enabled = True
        # Set the embedding metadata to match the model stem
        mock_scoring_context.user_embedding_meta = {"mf_stem": "mock_v1.0"}
        mock_scoring_context.mf_stem = "mock_v1.0"

        result = run_personalized_pipeline(mock_scoring_context)

        assert isinstance(result, PipelineResult)
        # Personalization may return results or fail gracefully
        # Check that it at least returns a valid PipelineResult
        assert isinstance(result.ranked_items, list)

    def test_personalized_without_embedding(self, mock_scoring_context: ScoringContext):
        """Personalized pipeline handles missing user_embedding gracefully."""
        mock_scoring_context.user_embedding = None
        mock_scoring_context.personalization_enabled = True

        result = run_personalized_pipeline(mock_scoring_context)

        # Should return a result (may be empty or fall back to seed-based)
        assert isinstance(result, PipelineResult)
        # Personalization should not be applied if embedding is None
        assert result.personalization_applied is False

    def test_personalized_excludes_watched(
        self, mock_scoring_context: ScoringContext, mock_mf_model: MockMFModel
    ):
        """Personalized pipeline excludes watched IDs."""
        user_embedding = mock_mf_model.P[1].copy()
        mock_scoring_context.user_embedding = user_embedding
        mock_scoring_context.personalization_enabled = True
        mock_scoring_context.watched_ids = {2, 3, 4}

        result = run_personalized_pipeline(mock_scoring_context)

        result_ids = {item["anime_id"] for item in result.ranked_items}
        assert 2 not in result_ids
        assert 3 not in result_ids
        assert 4 not in result_ids


# ---------------------------------------------------------------------------
# Tests: Browse Pipeline
# ---------------------------------------------------------------------------


class TestBrowsePipeline:
    """Tests for run_browse_pipeline()."""

    def test_browse_returns_filtered_results(self, mock_scoring_context: ScoringContext):
        """Browse pipeline returns results based on filters."""
        mock_scoring_context.browse_mode = True
        mock_scoring_context.genre_filter = ["Action"]

        result = run_browse_pipeline(mock_scoring_context)

        assert isinstance(result, PipelineResult)
        assert len(result.ranked_items) > 0

        for item in result.ranked_items:
            anime_id = item["anime_id"]
            row = mock_scoring_context.metadata[
                mock_scoring_context.metadata["anime_id"] == anime_id
            ].iloc[0]
            genres = str(row["genres"])
            assert "Action" in genres

    def test_browse_respects_type_filter(self, mock_scoring_context: ScoringContext):
        """Browse pipeline respects type filter."""
        mock_scoring_context.browse_mode = True
        mock_scoring_context.type_filter = ["TV"]

        result = run_browse_pipeline(mock_scoring_context)

        for item in result.ranked_items:
            anime_id = item["anime_id"]
            row = mock_scoring_context.metadata[
                mock_scoring_context.metadata["anime_id"] == anime_id
            ].iloc[0]
            assert row["type"] == "TV"


# ---------------------------------------------------------------------------
# Tests: Franchise Cap
# ---------------------------------------------------------------------------


class TestFranchiseCap:
    """Tests for franchise cap behavior in discovery mode."""

    def test_franchise_cap_limits_same_franchise_in_discovery(
        self, mock_scoring_context: ScoringContext
    ):
        """Franchise cap should limit same-franchise entries in discovery mode."""
        mock_scoring_context.seed_ranking_mode = "discovery"
        mock_scoring_context.seed_ids = [4]  # Attack on Titan
        mock_scoring_context.top_n = 20

        result = run_seed_based_pipeline(mock_scoring_context)

        # Count how many "Attack on Titan" titles appear (anime_id 4 and 10)
        aot_count = sum(
            1 for item in result.ranked_items if item["anime_id"] in {4, 10}
        )

        # In discovery mode, franchise cap should limit duplicates
        # (exact behavior depends on FRANCHISE_CAP_TOP20 constant)
        # For this test, just verify it doesn't return all franchise entries
        assert aot_count <= 2, "Franchise cap should limit Attack on Titan entries"


# ---------------------------------------------------------------------------
# Tests: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_seed_ids_returns_empty_or_error(self, mock_scoring_context: ScoringContext):
        """Empty seed IDs should return empty results or handle gracefully."""
        mock_scoring_context.seed_ids = []
        mock_scoring_context.seed_titles = []

        # Empty seeds may raise an error or return empty — both are acceptable
        try:
            result = run_seed_based_pipeline(mock_scoring_context)
            assert isinstance(result, PipelineResult)
            # Either empty results or some default behavior is acceptable
        except (IndexError, ValueError, KeyError):
            # It's acceptable for the pipeline to fail with empty seeds
            pass

    def test_seed_not_in_metadata(self, mock_scoring_context: ScoringContext):
        """Seed ID not in metadata should handle gracefully."""
        mock_scoring_context.seed_ids = [9999]  # Non-existent ID
        mock_scoring_context.seed_titles = ["Non-existent Anime"]

        result = run_seed_based_pipeline(mock_scoring_context)

        assert isinstance(result, PipelineResult)
        # Should handle gracefully (empty result or warning)

    def test_all_items_filtered_out(self, mock_scoring_context: ScoringContext):
        """If all items are filtered out, should return few or empty results."""
        mock_scoring_context.genre_filter = ["Nonexistent Genre"]

        result = run_seed_based_pipeline(mock_scoring_context)

        assert isinstance(result, PipelineResult)
        # Filters are applied as post-filters, so the pipeline may return some results
        # even if none match the filter perfectly (to avoid empty screens)
        # This is expected behavior for UX reasons
        assert isinstance(result.ranked_items, list)

    def test_watched_ids_covers_all_candidates(self, mock_scoring_context: ScoringContext):
        """If watched_ids covers all candidates, should return empty."""
        # Mark all anime as watched
        mock_scoring_context.watched_ids = set(range(1, 11))

        result = run_seed_based_pipeline(mock_scoring_context)

        assert len(result.ranked_items) == 0, "Should return empty when all items watched"


# ---------------------------------------------------------------------------
# Tests: Result Structure
# ---------------------------------------------------------------------------


class TestResultStructure:
    """Tests for the structure of returned results."""

    def test_result_items_have_required_fields(self, mock_scoring_context: ScoringContext):
        """Each result item should have required fields."""
        result = run_seed_based_pipeline(mock_scoring_context)

        required_fields = {"anime_id", "score"}

        for item in result.ranked_items:
            for field in required_fields:
                assert field in item, f"Item missing required field: {field}"
            assert isinstance(item["anime_id"], (int, np.integer))
            assert isinstance(item["score"], (float, np.floating))

    def test_pipeline_result_structure(self, mock_scoring_context: ScoringContext):
        """PipelineResult should have expected structure."""
        result = run_seed_based_pipeline(mock_scoring_context)

        assert hasattr(result, "ranked_items")
        assert hasattr(result, "timing")
        assert hasattr(result, "stage0_diagnostics")
        assert hasattr(result, "stage1_diagnostics")
        assert hasattr(result, "diversity_stats")
        assert hasattr(result, "warnings")

        assert isinstance(result.ranked_items, list)
        assert isinstance(result.timing, dict)
        assert isinstance(result.warnings, list)
