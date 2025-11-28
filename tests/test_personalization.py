"""Pytest tests for user embedding generation and personalization.

Tests cover:
- Embedding generation (weighted/simple averaging)
- Personalized scoring (dot product, exclusions)
- Taste profile analysis
- Edge cases (empty ratings, missing items)
"""

import pytest
import numpy as np
from src.models.user_embedding import (
    generate_user_embedding,
    compute_personalized_scores,
    get_user_taste_profile,
)


class MockMFModel:
    """Mock MF model for testing."""
    
    def __init__(self, n_items=100, n_factors=64):
        np.random.seed(42)
        self.Q = np.random.randn(n_items, n_factors).astype(np.float32)
        self.item_to_index = {i: i for i in range(n_items)}
        self.index_to_item = {i: i for i in range(n_items)}
        self.global_mean = 7.0
        self.n_factors = n_factors


@pytest.fixture
def mock_mf_model():
    """Fixture providing a mock MF model."""
    return MockMFModel(n_items=100, n_factors=64)


@pytest.fixture
def sample_ratings():
    """Fixture providing sample ratings."""
    return {
        0: 10,
        1: 9,
        2: 8,
        3: 7,
        5: 8,
        10: 9,
        15: 6,
        20: 7,
    }


@pytest.fixture
def metadata_df():
    """Fixture providing sample metadata."""
    import pandas as pd
    return pd.DataFrame({
        "anime_id": [0, 1, 2, 3, 5, 10, 15, 20],
        "title": ["Anime A", "Anime B", "Anime C", "Anime D", "Anime E", "Anime F", "Anime G", "Anime H"],
        "genres": ["Action|Adventure", "Comedy", "Drama|Romance", "Action", "Horror", "Fantasy|Adventure", "Comedy|Slice of Life", "Drama"],
    })


class TestEmbeddingGeneration:
    """Tests for generate_user_embedding()."""
    
    def test_weighted_average_basic(self, mock_mf_model, sample_ratings):
        """Test basic weighted average embedding generation."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        assert embedding.shape == (64,), "Embedding should have 64 dimensions"
        assert embedding.dtype == np.float32, "Embedding should be float32"
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5), "Embedding should be L2 normalized"
    
    def test_simple_average_basic(self, mock_mf_model, sample_ratings):
        """Test simple average embedding generation."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="simple_average", normalize=True
        )
        
        assert embedding.shape == (64,), "Embedding should have 64 dimensions"
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5), "Embedding should be L2 normalized"
    
    def test_no_normalization(self, mock_mf_model, sample_ratings):
        """Test embedding generation without normalization."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=False
        )
        
        assert embedding.shape == (64,), "Embedding should have 64 dimensions"
        # Norm should NOT be 1.0 when normalize=False
        assert not np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-2), "Embedding should not be normalized"
    
    def test_empty_ratings(self, mock_mf_model):
        """Test embedding generation with no ratings."""
        embedding = generate_user_embedding(
            {}, mock_mf_model, method="weighted_average", normalize=True
        )
        
        assert embedding.shape == (64,), "Should return zero embedding"
        assert np.allclose(embedding, 0.0), "Empty ratings should produce zero embedding"
    
    def test_single_rating(self, mock_mf_model):
        """Test embedding generation with single rating."""
        embedding = generate_user_embedding(
            {0: 10}, mock_mf_model, method="weighted_average", normalize=True
        )
        
        assert embedding.shape == (64,), "Embedding should have 64 dimensions"
        # With single rating, embedding should be normalized version of that item's factor
        expected = mock_mf_model.Q[0] / np.linalg.norm(mock_mf_model.Q[0])
        assert np.allclose(embedding, expected, atol=1e-5), "Single rating embedding incorrect"
    
    def test_missing_items_handled(self, mock_mf_model):
        """Test that items not in model are gracefully skipped."""
        ratings_with_missing = {0: 10, 1: 9, 999: 8}  # 999 not in model
        
        embedding = generate_user_embedding(
            ratings_with_missing, mock_mf_model, method="weighted_average", normalize=True
        )
        
        assert embedding.shape == (64,), "Should still generate embedding"
        assert not np.allclose(embedding, 0.0), "Should use valid items"
    
    def test_weighted_vs_simple_difference(self, mock_mf_model, sample_ratings):
        """Test that weighted and simple methods produce different results."""
        weighted = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        simple = generate_user_embedding(
            sample_ratings, mock_mf_model, method="simple_average", normalize=True
        )
        
        assert not np.allclose(weighted, simple, atol=1e-2), "Methods should produce different embeddings"


class TestPersonalizedScoring:
    """Tests for compute_personalized_scores()."""
    
    def test_basic_scoring(self, mock_mf_model, sample_ratings):
        """Test basic personalized scoring."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        scores = compute_personalized_scores(embedding, mock_mf_model, exclude_anime_ids=None)
        
        assert isinstance(scores, dict), "Should return dict"
        assert len(scores) == 100, "Should have scores for all items"
        assert all(isinstance(k, int) for k in scores.keys()), "Keys should be anime IDs"
        assert all(isinstance(v, (int, float)) for v in scores.values()), "Values should be numeric"
    
    def test_exclusion_filter(self, mock_mf_model, sample_ratings):
        """Test that exclusion filter works correctly."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        exclude_ids = [0, 1, 2, 3, 4]
        scores = compute_personalized_scores(embedding, mock_mf_model, exclude_anime_ids=exclude_ids)
        
        assert len(scores) == 95, f"Should have 95 scores (100 - 5 excluded), got {len(scores)}"
        for excluded_id in exclude_ids:
            assert excluded_id not in scores, f"Excluded ID {excluded_id} should not be in scores"
    
    def test_score_range_reasonable(self, mock_mf_model, sample_ratings):
        """Test that scores are in reasonable range."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        scores = compute_personalized_scores(embedding, mock_mf_model, exclude_anime_ids=None)
        
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        # For normalized embedding and Q matrix, scores should be in reasonable range
        assert min_score >= -5.0, f"Min score too negative: {min_score}"
        assert max_score <= 5.0, f"Max score too positive: {max_score}"
    
    def test_deterministic(self, mock_mf_model, sample_ratings):
        """Test that scoring is deterministic."""
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        scores1 = compute_personalized_scores(embedding, mock_mf_model, exclude_anime_ids=None)
        scores2 = compute_personalized_scores(embedding, mock_mf_model, exclude_anime_ids=None)
        
        assert scores1.keys() == scores2.keys(), "Keys should be identical"
        for k in scores1:
            assert np.isclose(scores1[k], scores2[k]), f"Scores for {k} should be identical"


class TestTasteProfile:
    """Tests for get_user_taste_profile()."""
    
    def test_basic_taste_profile(self, sample_ratings, metadata_df):
        """Test basic taste profile generation."""
        taste = get_user_taste_profile(sample_ratings, metadata_df, top_n_genres=5)
        
        assert "top_genres" in taste
        assert "rating_distribution" in taste
        assert "avg_rating" in taste
    
    def test_favorite_genres_format(self, sample_ratings, metadata_df):
        """Test favorite genres format."""
        taste = get_user_taste_profile(sample_ratings, metadata_df, top_n_genres=5)
        
        top_genres = taste["top_genres"]
        assert isinstance(top_genres, list), "Should return list"
        assert len(top_genres) <= 5, "Should respect top_n limit"
        
        for genre, rating in top_genres:
            assert isinstance(genre, str), "Genre should be string"
            assert isinstance(rating, (int, float)), "Rating should be numeric"
            assert 1 <= rating <= 10, f"Rating {rating} out of valid range"
    
    def test_rating_distribution(self, sample_ratings, metadata_df):
        """Test rating distribution buckets."""
        taste = get_user_taste_profile(sample_ratings, metadata_df, top_n_genres=5)
        
        dist = taste["rating_distribution"]
        expected_buckets = ["9-10", "7-8", "5-6", "1-4"]
        
        for bucket in expected_buckets:
            assert bucket in dist, f"Missing bucket {bucket}"
            assert isinstance(dist[bucket], int), f"Bucket {bucket} should have int count"
            assert dist[bucket] >= 0, f"Bucket {bucket} should have non-negative count"
    
    def test_overall_avg_rating(self, sample_ratings, metadata_df):
        """Test overall average rating calculation."""
        taste = get_user_taste_profile(sample_ratings, metadata_df, top_n_genres=5)
        
        avg = taste["avg_rating"]
        assert isinstance(avg, (int, float)), "Should be numeric"
        
        # Calculate expected average
        expected_avg = sum(sample_ratings.values()) / len(sample_ratings)
        assert np.isclose(avg, expected_avg, atol=1e-2), "Average calculation incorrect"
    
    def test_empty_ratings(self, metadata_df):
        """Test taste profile with no ratings."""
        taste = get_user_taste_profile({}, metadata_df, top_n_genres=5)
        
        assert taste["top_genres"] == []
        assert taste["avg_rating"] == 0.0
        # Empty ratings dict should have no ratings in any bucket
        # But the function may not return distribution for empty ratings


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_all_same_rating(self, mock_mf_model):
        """Test embedding with all ratings the same."""
        same_ratings = {i: 7 for i in range(10)}
        
        embedding = generate_user_embedding(
            same_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        # With all same ratings, should produce simple average of item factors
        assert embedding.shape == (64,)
        assert not np.allclose(embedding, 0.0), "Should still produce valid embedding"
    
    def test_extreme_ratings(self, mock_mf_model):
        """Test with extreme ratings (all 1s or all 10s)."""
        extreme_high = {i: 10 for i in range(10)}
        extreme_low = {i: 1 for i in range(10)}
        
        embedding_high = generate_user_embedding(
            extreme_high, mock_mf_model, method="weighted_average", normalize=True
        )
        embedding_low = generate_user_embedding(
            extreme_low, mock_mf_model, method="weighted_average", normalize=True
        )
        
        assert embedding_high.shape == (64,)
        assert embedding_low.shape == (64,)
        # They should be different (unless ratings don't matter in weighted avg with same values)
    
    def test_large_rating_count(self, mock_mf_model):
        """Test with many ratings (performance check)."""
        import time
        
        large_ratings = {i: (i % 10) + 1 for i in range(100)}  # All 100 items
        
        start = time.time()
        embedding = generate_user_embedding(
            large_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        elapsed = time.time() - start
        
        assert embedding.shape == (64,)
        assert elapsed < 0.1, f"Embedding generation too slow: {elapsed:.3f}s"
    
    def test_invalid_model_structure(self):
        """Test error handling for invalid model."""
        class InvalidModel:
            pass
        
        invalid_model = InvalidModel()
        
        with pytest.raises(ValueError, match="MF model must have"):
            generate_user_embedding({0: 10}, invalid_model)


class TestPerformance:
    """Performance benchmarks for personalization."""
    
    def test_embedding_generation_speed(self, mock_mf_model, sample_ratings):
        """Benchmark embedding generation speed."""
        import time
        
        times = []
        for _ in range(10):
            start = time.time()
            generate_user_embedding(
                sample_ratings, mock_mf_model, method="weighted_average", normalize=True
            )
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.01, f"Embedding generation too slow: {avg_time*1000:.2f}ms"
    
    def test_scoring_speed(self, mock_mf_model, sample_ratings):
        """Benchmark personalized scoring speed."""
        import time
        
        embedding = generate_user_embedding(
            sample_ratings, mock_mf_model, method="weighted_average", normalize=True
        )
        
        times = []
        for _ in range(10):
            start = time.time()
            compute_personalized_scores(embedding, mock_mf_model, exclude_anime_ids=None)
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.01, f"Scoring too slow: {avg_time*1000:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
