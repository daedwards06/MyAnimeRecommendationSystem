"""Tests for src/eval/metrics.py and src/eval/metrics_extra.py"""
import pytest
from src.eval.metrics import (
    precision_at_k,
    recall_at_k,
    f1_at_k,
    ndcg_at_k,
    ndcg_at_k_graded,
    average_precision_at_k,
    evaluate_ranking,
)
from src.eval.metrics_extra import (
    item_coverage,
    gini_index,
)


class TestPrecisionAtK:
    """Tests for precision_at_k function."""
    
    def test_precision_perfect(self):
        """All recommendations are relevant."""
        ranked = [1, 2, 3]
        relevant = {1, 2, 3}
        assert precision_at_k(ranked, relevant, 3) == 1.0
    
    def test_precision_half(self):
        """Half of recommendations are relevant."""
        ranked = [1, 2, 3, 4]
        relevant = {1, 3}
        assert precision_at_k(ranked, relevant, 4) == 0.5
    
    def test_precision_none_relevant(self):
        """No recommendations are relevant."""
        ranked = [1, 2, 3]
        relevant = {4, 5}
        assert precision_at_k(ranked, relevant, 3) == 0.0
    
    def test_precision_k_larger_than_list(self):
        """k is larger than ranked list."""
        ranked = [1]
        relevant = {1}
        assert precision_at_k(ranked, relevant, 5) == pytest.approx(0.2)  # 1/5
    
    def test_precision_k_zero(self):
        """Edge case: k=0."""
        ranked = [1, 2, 3]
        relevant = {1, 2, 3}
        assert precision_at_k(ranked, relevant, 0) == 0.0


class TestRecallAtK:
    """Tests for recall_at_k function."""
    
    def test_recall_perfect(self):
        """All relevant items are retrieved."""
        ranked = [1, 2, 3]
        relevant = {1, 2, 3}
        assert recall_at_k(ranked, relevant, 3) == 1.0
    
    def test_recall_partial(self):
        """Only some relevant items are retrieved."""
        ranked = [1, 2]
        relevant = {1, 2, 3}
        assert recall_at_k(ranked, relevant, 2) == pytest.approx(2.0 / 3.0)
    
    def test_recall_empty_relevant(self):
        """No relevant items exist."""
        ranked = [1, 2, 3]
        relevant = set()
        assert recall_at_k(ranked, relevant, 3) == 0.0
    
    def test_recall_k_larger_than_relevant(self):
        """k is larger than number of relevant items."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 3}
        assert recall_at_k(ranked, relevant, 5) == 1.0


class TestF1AtK:
    """Tests for f1_at_k function."""
    
    def test_f1_consistency(self):
        """Verify F1 = 2*P*R/(P+R) for several inputs."""
        ranked = [1, 2, 3, 4]
        relevant = {1, 3}
        k = 4
        
        p = precision_at_k(ranked, relevant, k)
        r = recall_at_k(ranked, relevant, k)
        expected_f1 = 2 * p * r / (p + r)
        
        assert f1_at_k(ranked, relevant, k) == pytest.approx(expected_f1)
    
    def test_f1_zero_precision_and_recall(self):
        """When P and R are both 0, F1 should be 0."""
        ranked = [1, 2, 3]
        relevant = {4, 5, 6}
        assert f1_at_k(ranked, relevant, 3) == 0.0
    
    def test_f1_perfect(self):
        """Perfect precision and recall → F1 = 1.0."""
        ranked = [1, 2, 3]
        relevant = {1, 2, 3}
        assert f1_at_k(ranked, relevant, 3) == 1.0


class TestNDCGAtK:
    """Tests for binary NDCG@K."""
    
    def test_ndcg_perfect(self):
        """Ideal ordering → NDCG = 1.0."""
        ranked = [1, 2, 3]
        relevant = {1, 2, 3}
        assert ndcg_at_k(ranked, relevant, 3) == 1.0
    
    def test_ndcg_reversed(self):
        """Worst ordering → NDCG < 1.0 but > 0.0."""
        ranked = [4, 5, 1, 2, 3]  # Relevant items at the end
        relevant = {1, 2, 3}
        score = ndcg_at_k(ranked, relevant, 5)
        assert 0.0 < score < 1.0
    
    def test_ndcg_no_relevant(self):
        """No relevant items → NDCG = 0.0."""
        ranked = [1, 2, 3]
        relevant = {4, 5, 6}
        assert ndcg_at_k(ranked, relevant, 3) == 0.0
    
    def test_ndcg_empty_relevant_set(self):
        """Empty relevant set → NDCG = 0.0."""
        ranked = [1, 2, 3]
        relevant = set()
        assert ndcg_at_k(ranked, relevant, 3) == 0.0


class TestNDCGGraded:
    """Tests for graded NDCG@K with explicit ratings."""
    
    def test_ndcg_graded_perfect_ranking(self):
        """Items ordered by rating → NDCG = 1.0."""
        ranked = [1, 2, 3, 4]
        ratings = {1: 10.0, 2: 8.0, 3: 6.0, 4: 4.0}
        assert ndcg_at_k_graded(ranked, ratings, 4) == 1.0
    
    def test_ndcg_graded_reversed_ranking(self):
        """Items in reverse order → NDCG < 1.0."""
        ranked = [4, 3, 2, 1]
        ratings = {1: 10.0, 2: 8.0, 3: 6.0, 4: 4.0}
        score = ndcg_at_k_graded(ranked, ratings, 4)
        assert 0.0 < score < 1.0
    
    def test_ndcg_graded_no_relevant(self):
        """All items unrated → NDCG = 0.0."""
        ranked = [1, 2, 3]
        ratings = {4: 10.0, 5: 8.0}  # Ratings for items not in ranked list
        # All gains will be 0.0
        assert ndcg_at_k_graded(ranked, ratings, 3) == 0.0
    
    def test_ndcg_graded_at_k_1(self):
        """Only top-1 matters for K=1."""
        ranked = [1, 2, 3]
        ratings = {1: 10.0, 2: 10.0, 3: 10.0}
        assert ndcg_at_k_graded(ranked, ratings, 1) == 1.0
        
        # If best item is not first among the full set, but K=1,
        # NDCG@1 still equals 1.0 because it normalizes by the ideal
        # ordering of the items in the ranking (not all possible items)
        ranked2 = [2, 1, 3]
        ratings2 = {1: 10.0, 2: 5.0, 3: 5.0}
        # At K=1, we only look at item 2, and the ideal is also [2]
        score = ndcg_at_k_graded(ranked2, ratings2, 1)
        assert score == 1.0
        
        # To see degradation, need to compare at K where ordering matters
        score_k3 = ndcg_at_k_graded(ranked2, ratings2, 3)
        assert score_k3 < 1.0  # Because item 1 (rating 10) is not first
    
    def test_ndcg_graded_linear_vs_exponential(self):
        """Verify different gain functions produce different values."""
        ranked = [1, 2, 3]
        ratings = {1: 10.0, 2: 5.0, 3: 1.0}
        
        linear = ndcg_at_k_graded(ranked, ratings, 3, gain_fn="linear")
        exponential = ndcg_at_k_graded(ranked, ratings, 3, gain_fn="exponential")
        
        # Both should be 1.0 for perfect ranking, but the absolute DCG values differ
        assert linear == 1.0
        assert exponential == 1.0
        
        # For imperfect ranking, they should differ
        ranked_imperfect = [2, 1, 3]
        linear_imp = ndcg_at_k_graded(ranked_imperfect, ratings, 3, gain_fn="linear")
        exp_imp = ndcg_at_k_graded(ranked_imperfect, ratings, 3, gain_fn="exponential")
        
        # Exponential emphasizes high ratings more, so imperfect ranking hurts more
        assert linear_imp != exp_imp
    
    def test_ndcg_graded_matches_binary_for_uniform_ratings(self):
        """When all ratings are equal, graded NDCG should equal binary NDCG."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3}
        ratings = {1: 5.0, 2: 5.0, 3: 5.0}  # All relevant items have same rating
        
        # Binary NDCG treats all relevant items as gain=1
        binary_ndcg = ndcg_at_k(ranked, relevant, 5)
        
        # Graded with uniform ratings should behave similarly
        # (not exactly equal due to different gain functions, but close)
        graded_ndcg = ndcg_at_k_graded(ranked, ratings, 5, gain_fn="linear")
        
        # Both should be 1.0 since relevant items are at top
        assert binary_ndcg == 1.0
        assert graded_ndcg == 1.0
    
    def test_ndcg_graded_empty_ratings(self):
        """Empty ratings dict → NDCG = 0.0."""
        ranked = [1, 2, 3]
        ratings = {}
        assert ndcg_at_k_graded(ranked, ratings, 3) == 0.0
    
    def test_ndcg_graded_invalid_gain_function(self):
        """Invalid gain function → raises ValueError."""
        ranked = [1, 2, 3]
        ratings = {1: 10.0}
        with pytest.raises(ValueError, match="Unknown gain_fn"):
            ndcg_at_k_graded(ranked, ratings, 3, gain_fn="invalid")


class TestAveragePrecisionAtK:
    """Tests for MAP@K."""
    
    def test_map_perfect(self):
        """All relevant items at top → MAP = 1.0."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3}
        assert average_precision_at_k(ranked, relevant, 5) == 1.0
    
    def test_map_single_relevant(self):
        """Single relevant item - verify formula manually."""
        ranked = [1, 2, 3]
        relevant = {2}
        # AP = (1/2) / min(1, 3) = 0.5 / 1 = 0.5
        assert average_precision_at_k(ranked, relevant, 3) == 0.5
    
    def test_map_no_relevant(self):
        """No relevant items → MAP = 0.0."""
        ranked = [1, 2, 3]
        relevant = {4, 5}
        assert average_precision_at_k(ranked, relevant, 3) == 0.0
    
    def test_map_empty_relevant(self):
        """Empty relevant set → MAP = 0.0."""
        ranked = [1, 2, 3]
        relevant = set()
        assert average_precision_at_k(ranked, relevant, 3) == 0.0


class TestEvaluateRanking:
    """Tests for evaluate_ranking aggregation function."""
    
    def test_evaluate_ranking_returns_all_metrics(self):
        """Check that all expected metric keys are present."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 3}
        k_values = [3, 5]
        
        result = evaluate_ranking(ranked, relevant, k_values)
        
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result
        assert "ndcg" in result
        assert "map" in result
        
        # Each metric should have values for both k values
        for metric in ["precision", "recall", "f1", "ndcg", "map"]:
            assert 3 in result[metric]
            assert 5 in result[metric]
    
    def test_evaluate_ranking_multiple_k(self):
        """Check multiple K values are correctly evaluated."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3}
        k_values = [1, 3, 5]
        
        result = evaluate_ranking(ranked, relevant, k_values)
        
        # Precision should decrease or stay same as k increases (for this case)
        assert result["precision"][1] >= result["precision"][3] >= result["precision"][5]
        
        # Recall should increase or stay same as k increases
        assert result["recall"][1] <= result["recall"][3] <= result["recall"][5]
    
    def test_evaluate_ranking_with_graded_ndcg(self):
        """Check that graded NDCG is computed when ratings provided."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3}
        ratings = {1: 10.0, 2: 8.0, 3: 6.0}
        k_values = [3, 5]
        
        result = evaluate_ranking(ranked, relevant, k_values, item_ratings=ratings)
        
        # Should include ndcg_graded
        assert "ndcg_graded" in result
        assert 3 in result["ndcg_graded"]
        assert 5 in result["ndcg_graded"]
        
        # Graded NDCG should be 1.0 for perfect ranking
        assert result["ndcg_graded"][3] == 1.0
        assert result["ndcg_graded"][5] == 1.0
    
    def test_evaluate_ranking_without_graded_ndcg(self):
        """Check that graded NDCG is not computed when ratings not provided."""
        ranked = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3}
        k_values = [3, 5]
        
        result = evaluate_ranking(ranked, relevant, k_values)
        
        # Should NOT include ndcg_graded
        assert "ndcg_graded" not in result
    
    def test_evaluate_ranking_consistency(self):
        """Check that metrics are consistent with individual functions."""
        ranked = [1, 2, 3, 4]
        relevant = {1, 3}
        k_values = [2, 4]
        
        result = evaluate_ranking(ranked, relevant, k_values)
        
        # Verify against direct function calls
        assert result["precision"][2] == precision_at_k(ranked, relevant, 2)
        assert result["recall"][4] == recall_at_k(ranked, relevant, 4)
        assert result["f1"][2] == f1_at_k(ranked, relevant, 2)
        assert result["ndcg"][4] == ndcg_at_k(ranked, relevant, 4)
        assert result["map"][2] == average_precision_at_k(ranked, relevant, 2)


class TestItemCoverage:
    """Tests for item_coverage function from metrics_extra."""
    
    def test_coverage_full(self):
        """All catalog items recommended → coverage = 1.0."""
        recommendations = {
            1: [10, 20, 30],
            2: [40, 50],
        }
        total_items = 5  # Items 10, 20, 30, 40, 50
        assert item_coverage(recommendations, total_items) == 1.0
    
    def test_coverage_partial(self):
        """Half of catalog recommended → coverage = 0.5."""
        recommendations = {
            1: [1, 2],
            2: [3, 4],
        }
        total_items = 8
        assert item_coverage(recommendations, total_items) == 0.5
    
    def test_coverage_empty_recommendations(self):
        """No recommendations → coverage = 0.0."""
        recommendations = {}
        total_items = 100
        assert item_coverage(recommendations, total_items) == 0.0
    
    def test_coverage_zero_catalog(self):
        """Edge case: zero total items → coverage = 0.0."""
        recommendations = {1: [1, 2, 3]}
        total_items = 0
        assert item_coverage(recommendations, total_items) == 0.0
    
    def test_coverage_duplicate_items(self):
        """Duplicate items across users count once."""
        recommendations = {
            1: [1, 2, 3],
            2: [2, 3, 4],
            3: [3, 4, 5],
        }
        # Unique items: {1, 2, 3, 4, 5} = 5 items
        total_items = 10
        assert item_coverage(recommendations, total_items) == 0.5
    
    def test_coverage_single_user(self):
        """Single user recommendations."""
        recommendations = {1: [10, 20, 30, 40]}
        total_items = 10
        assert item_coverage(recommendations, total_items) == 0.4


class TestGiniIndex:
    """Tests for gini_index function from metrics_extra."""
    
    def test_gini_uniform(self):
        """All items recommended equally → Gini ≈ 0.0."""
        recommendations = {
            1: [1, 2, 3],
            2: [1, 2, 3],
            3: [1, 2, 3],
        }
        # Each item appears 3 times - perfectly uniform
        gini = gini_index(recommendations)
        assert gini == pytest.approx(0.0, abs=1e-6)
    
    def test_gini_concentrated(self):
        """One item dominates → Gini > 0.0 indicating concentration."""
        recommendations = {
            1: [1, 1, 1, 1, 1],
            2: [1, 1, 1, 1, 1],
            3: [1, 1, 1, 1, 2],
        }
        # Item 1 appears 14 times, item 2 appears 1 time
        gini = gini_index(recommendations)
        assert gini > 0.3  # Significant concentration
    
    def test_gini_empty_recommendations(self):
        """No recommendations → Gini = 0.0."""
        recommendations = {}
        assert gini_index(recommendations) == 0.0
    
    def test_gini_single_item(self):
        """Single item recommended → Gini = 0.0 (perfect equality for 1 item)."""
        recommendations = {
            1: [5],
            2: [5],
            3: [5],
        }
        gini = gini_index(recommendations)
        assert gini == pytest.approx(0.0, abs=1e-6)
    
    def test_gini_two_items_equal(self):
        """Two items with equal frequency → Gini = 0.0."""
        recommendations = {
            1: [1, 2],
            2: [1, 2],
            3: [1, 2],
        }
        gini = gini_index(recommendations)
        assert gini == pytest.approx(0.0, abs=1e-6)
    
    def test_gini_two_items_unequal(self):
        """Two items with unequal frequency → 0 < Gini < 1."""
        recommendations = {
            1: [1, 1, 1, 2],
            2: [1, 1, 1, 2],
        }
        # Item 1 appears 6 times, item 2 appears 2 times
        gini = gini_index(recommendations)
        assert 0.0 < gini < 1.0
    
    def test_gini_range(self):
        """Gini index should always be in [0, 1]."""
        # Test various distributions
        test_cases = [
            {1: [1, 2, 3, 4, 5]},
            {1: [1], 2: [2], 3: [3]},
            {1: [1, 1, 2, 3, 4]},
            {1: list(range(100))},  # Many different items
        ]
        for recs in test_cases:
            gini = gini_index(recs)
            assert 0.0 <= gini <= 1.0
    
    def test_gini_perfect_inequality(self):
        """Single item gets everything, many others get one each."""
        recommendations = {
            1: [1] * 100 + [2, 3, 4, 5, 6],
        }
        # Item 1 appears 100 times, others appear 1 time each
        gini = gini_index(recommendations)
        assert gini > 0.7  # Very high inequality

