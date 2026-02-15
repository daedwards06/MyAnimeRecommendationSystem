"""Tests for diversity & novelty summary helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.app.badges import novelty_ratio
from src.app.diversity import (
    average_novelty,
    build_user_genre_hist,
    compute_popularity_percentiles,
    coverage,
    embedding_cosine_similarity,
    genre_exposure_ratio,
    genre_jaccard_similarity,
    mmr_rerank,
)


def test_compute_popularity_percentiles_ordering():
    pop = np.array([10.0, 8.0, 5.0, 1.0])  # higher = more popular
    pct = compute_popularity_percentiles(pop)
    # Most popular gets 0 percentile
    assert pct[np.argmax(pop)] == 0.0
    # Least popular gets 1.0 when len-1 denominator
    assert pct[np.argmin(pop)] == 1.0


def test_coverage():
    recs = [{"anime_id": 1}, {"anime_id": 2}, {"anime_id": 2}]
    assert coverage(recs) == 2 / 3


def test_genre_exposure_ratio():
    metadata = pd.DataFrame({"anime_id": [1, 2, 3], "genres": ["action|drama", "comedy", "fantasy|action"]})
    recs = [{"anime_id": 1}, {"anime_id": 2}]
    val = genre_exposure_ratio(recs, metadata)
    # catalog unique genres = action, drama, comedy, fantasy (4); rec genres include action, drama, comedy (3)
    assert abs(val - 3 / 4) < 1e-6


def test_average_novelty():
    recs = [
        {"anime_id": 1, "badges": {"novelty_ratio": 0.5}},
        {"anime_id": 2, "badges": {"novelty_ratio": 0.25}},
    ]
    assert average_novelty(recs) == 0.375


def test_novelty_uses_user_history_and_na_without_history():
    metadata = pd.DataFrame(
        {
            "anime_id": [1, 2, 3],
            "genres": ["action|comedy", "drama", "action|fantasy"],
        }
    )

    # User A has seen action/comedy; fantasy is new => novelty 0.5
    hist_a = build_user_genre_hist({"1": 9.0}, metadata)
    assert hist_a["action"] >= 1
    assert hist_a["comedy"] >= 1
    assert novelty_ratio(hist_a, ["action", "fantasy"]) == 0.5
    assert novelty_ratio(hist_a, ["Action", "Fantasy"]) == 0.5

    # User B has only seen drama; action+fantasy are new => novelty 1.0
    hist_b = build_user_genre_hist({"2": 8.0}, metadata)
    assert novelty_ratio(hist_b, ["action", "fantasy"]) == 1.0

    # No user history => NA (None), not a misleading numeric value
    assert novelty_ratio({}, ["action", "fantasy"]) is None


# ── MMR tests ────────────────────────────────────────────────────────────────


def test_genre_jaccard_similarity_basic():
    """Test basic Jaccard similarity on genre sets."""
    a = {"genres": "Action|Adventure|Fantasy"}
    b = {"genres": "Action|Fantasy|Drama"}

    # Intersection: {action, adventure, fantasy} ∩ {action, fantasy, drama} = {action, fantasy}
    # Union: {action, adventure, fantasy, drama}
    # Jaccard = 2/4 = 0.5
    sim = genre_jaccard_similarity(a, b)
    assert abs(sim - 0.5) < 1e-6


def test_genre_jaccard_similarity_identical():
    """Test that identical genres give similarity 1.0."""
    a = {"genres": "Action|Comedy"}
    b = {"genres": "Action|Comedy"}

    sim = genre_jaccard_similarity(a, b)
    assert abs(sim - 1.0) < 1e-6


def test_genre_jaccard_similarity_disjoint():
    """Test that disjoint genres give similarity 0.0."""
    a = {"genres": "Action|Adventure"}
    b = {"genres": "Romance|Slice of Life"}

    sim = genre_jaccard_similarity(a, b)
    assert abs(sim - 0.0) < 1e-6


def test_genre_jaccard_similarity_case_insensitive():
    """Test that genre matching is case-insensitive."""
    a = {"genres": "ACTION|comedy"}
    b = {"genres": "action|COMEDY"}

    sim = genre_jaccard_similarity(a, b)
    assert abs(sim - 1.0) < 1e-6


def test_genre_jaccard_similarity_with_metadata():
    """Test genre lookup from metadata DataFrame."""
    metadata = pd.DataFrame({
        "anime_id": [1, 2],
        "genres": ["Action|Comedy", "Action|Drama"]
    })

    a = {"anime_id": 1}
    b = {"anime_id": 2}

    sim = genre_jaccard_similarity(a, b, metadata=metadata)
    # Genres: {action, comedy} ∩ {action, drama} = {action}
    # Union: {action, comedy, drama}
    # Jaccard = 1/3
    assert abs(sim - 1/3) < 1e-6


def test_embedding_cosine_similarity_basic():
    """Test cosine similarity with simple embeddings."""
    a = {"_synopsis_embedding": np.array([1.0, 0.0, 0.0])}
    b = {"_synopsis_embedding": np.array([1.0, 0.0, 0.0])}

    sim = embedding_cosine_similarity(a, b)
    assert abs(sim - 1.0) < 1e-6


def test_embedding_cosine_similarity_orthogonal():
    """Test that orthogonal embeddings give similarity 0.0."""
    a = {"_synopsis_embedding": np.array([1.0, 0.0])}
    b = {"_synopsis_embedding": np.array([0.0, 1.0])}

    sim = embedding_cosine_similarity(a, b)
    assert abs(sim - 0.0) < 1e-6


def test_embedding_cosine_similarity_missing():
    """Test that missing embeddings return 0.0."""
    a = {"anime_id": 1}
    b = {"anime_id": 2}

    sim = embedding_cosine_similarity(a, b)
    assert sim == 0.0


def test_mmr_empty_candidates():
    """Test that MMR handles empty candidate list."""
    def dummy_sim(a, b):
        return 0.0

    result = mmr_rerank([], dummy_sim, lambda_param=0.5, top_n=10)
    assert result == []


def test_mmr_fewer_than_top_n():
    """Test that MMR returns all candidates when fewer than top_n."""
    candidates = [
        {"anime_id": 1, "score": 9.0, "genres": "Action"},
        {"anime_id": 2, "score": 8.0, "genres": "Comedy"},
        {"anime_id": 3, "score": 7.0, "genres": "Drama"},
    ]

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    result = mmr_rerank(candidates, genre_sim, lambda_param=0.5, top_n=10)
    assert len(result) == 3
    assert result[0]["anime_id"] == 1  # Highest score selected first


def test_mmr_lambda_1_preserves_relevance_order():
    """Test that λ=1.0 (pure relevance) preserves original ranking."""
    candidates = [
        {"anime_id": 1, "score": 9.0, "genres": "Action|Adventure"},
        {"anime_id": 2, "score": 8.5, "genres": "Action|Fantasy"},  # Very similar to #1
        {"anime_id": 3, "score": 8.0, "genres": "Action|Shounen"},  # Very similar to #1
        {"anime_id": 4, "score": 7.0, "genres": "Romance|Drama"},   # Diverse
        {"anime_id": 5, "score": 6.0, "genres": "Comedy|Slice of Life"},  # Diverse
    ]

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    result = mmr_rerank(candidates, genre_sim, lambda_param=1.0, top_n=5)

    # Should preserve original order since λ=1.0 ignores diversity
    assert [r["anime_id"] for r in result] == [1, 2, 3, 4, 5]


def test_mmr_lambda_0_maximizes_diversity():
    """Test that λ=0.0 (pure diversity) spreads out genres."""
    candidates = [
        {"anime_id": 1, "score": 9.0, "genres": "Action|Adventure"},
        {"anime_id": 2, "score": 8.5, "genres": "Action|Fantasy"},  # Very similar to #1
        {"anime_id": 3, "score": 8.0, "genres": "Action|Shounen"},  # Very similar to #1
        {"anime_id": 4, "score": 7.0, "genres": "Romance|Drama"},   # Diverse
        {"anime_id": 5, "score": 6.0, "genres": "Comedy|Slice of Life"},  # Diverse
    ]

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    result = mmr_rerank(candidates, genre_sim, lambda_param=0.0, top_n=3)

    # First item should still be highest relevance (1)
    assert result[0]["anime_id"] == 1

    # Second item should NOT be the second-highest relevance (#2) because it's too similar
    # It should pick a more diverse item (#4 or #5)
    assert result[1]["anime_id"] in [4, 5]

    # All selected items should be diverse
    selected_ids = {r["anime_id"] for r in result}

    # Should NOT select both #2 and #3 (both very similar to #1)
    assert not (2 in selected_ids and 3 in selected_ids)


def test_mmr_lambda_intermediate_balances():
    """Test that intermediate λ balances relevance and diversity."""
    candidates = [
        {"anime_id": 1, "score": 9.0, "genres": "Action"},
        {"anime_id": 2, "score": 8.9, "genres": "Action"},  # High relevance, low diversity
        {"anime_id": 3, "score": 5.0, "genres": "Romance"},  # Low relevance, high diversity
    ]

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    result = mmr_rerank(candidates, genre_sim, lambda_param=0.5, top_n=2)

    # First should still be highest relevance
    assert result[0]["anime_id"] == 1

    # With λ=0.5, the second pick depends on the trade-off:
    # - #2 has higher relevance (8.9) but 100% similarity to #1
    # - #3 has lower relevance (5.0) but 0% similarity to #1
    # MMR score for #2 = 0.5 * 8.9 - 0.5 * 1.0 = 4.45 - 0.5 = 3.95
    # MMR score for #3 = 0.5 * 5.0 - 0.5 * 0.0 = 2.5
    # So #2 should still win, but it's closer than pure relevance
    assert result[1]["anime_id"] == 2


def test_mmr_selects_correct_count():
    """Test that MMR returns exactly top_n items."""
    candidates = [
        {"anime_id": i, "score": 10.0 - i * 0.1, "genres": f"Genre{i % 3}"}
        for i in range(20)
    ]

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    for top_n in [5, 10, 15]:
        result = mmr_rerank(candidates, genre_sim, lambda_param=0.3, top_n=top_n)
        assert len(result) == top_n


def test_mmr_genre_distribution_improves():
    """Integration test: verify that MMR improves genre distribution."""
    # Create candidates with skewed genres (many Action, few others)
    candidates = [
        {"anime_id": 1, "score": 9.0, "genres": "Action|Shounen"},
        {"anime_id": 2, "score": 8.9, "genres": "Action|Shounen"},
        {"anime_id": 3, "score": 8.8, "genres": "Action|Adventure"},
        {"anime_id": 4, "score": 8.7, "genres": "Action|Fantasy"},
        {"anime_id": 5, "score": 8.6, "genres": "Action|Mecha"},
        {"anime_id": 6, "score": 8.5, "genres": "Romance|Drama"},
        {"anime_id": 7, "score": 8.4, "genres": "Comedy|Slice of Life"},
        {"anime_id": 8, "score": 8.3, "genres": "Mystery|Thriller"},
        {"anime_id": 9, "score": 8.2, "genres": "Horror|Supernatural"},
        {"anime_id": 10, "score": 8.1, "genres": "Sports|School"},
    ]

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    # Pure relevance (λ≈1.0): top-5 will be dominated by Action
    top5_relevance = mmr_rerank(candidates, genre_sim, lambda_param=0.99, top_n=5)
    action_count_relevance = sum(
        1 for r in top5_relevance if "Action" in r.get("genres", "")
    )

    # With diversity (λ=0.3): top-5 should have fewer Action anime
    top5_diverse = mmr_rerank(candidates, genre_sim, lambda_param=0.3, top_n=5)
    action_count_diverse = sum(
        1 for r in top5_diverse if "Action" in r.get("genres", "")
    )

    # MMR should reduce Action concentration
    assert action_count_diverse < action_count_relevance

    # Count unique primary genres in diverse results
    diverse_genres = set()
    for r in top5_diverse:
        genres = r.get("genres", "").split("|")
        if genres:
            diverse_genres.add(genres[0])

    # Should have at least 3 different primary genres
    assert len(diverse_genres) >= 3


def test_mmr_handles_similarity_errors():
    """Test that MMR gracefully handles errors in similarity computation."""
    candidates = [
        {"anime_id": 1, "score": 9.0},
        {"anime_id": 2, "score": 8.0},
        {"anime_id": 3, "score": 7.0},
    ]

    def buggy_sim(a, b):
        # Simulate a function that sometimes raises exceptions
        if a["anime_id"] == 1 and b["anime_id"] == 2:
            raise ValueError("Simulated error")
        return 0.5

    # Should not crash, should fall back to 0 similarity on error
    result = mmr_rerank(candidates, buggy_sim, lambda_param=0.5, top_n=3)
    assert len(result) == 3


def test_mmr_integration_with_realistic_anime_dataset():
    """Integration test: MMR improves diversity across multiple random seed selections.

    This test validates that MMR consistently improves genre diversity when tested
    with realistic anime data and multiple random seed selections.
    """
    # Create a realistic dataset with 50 anime covering various genres
    # Simulate a scenario where many high-scoring anime share similar genres
    np.random.seed(42)

    anime_data = []
    genres_pool = [
        "Action|Shounen|Adventure",
        "Action|Shounen|Fantasy",
        "Action|Shounen|Mecha",
        "Action|Shounen|Supernatural",
        "Action|Military|Sci-Fi",
        "Romance|Drama|School",
        "Romance|Comedy|Slice of Life",
        "Comedy|Slice of Life|School",
        "Mystery|Thriller|Psychological",
        "Horror|Supernatural|Thriller",
        "Sports|School|Drama",
        "Music|Drama|School",
        "Fantasy|Adventure|Magic",
        "Sci-Fi|Space|Mecha",
        "Historical|Drama|Samurai",
    ]

    # First 20 anime: High scores but dominated by Action/Shounen (realistic popularity bias)
    for i in range(20):
        anime_data.append({
            "anime_id": i + 1,
            "score": 9.5 - i * 0.05,  # Scores from 9.5 down to 8.55
            "genres": genres_pool[i % 5],  # Mostly Action/Shounen genres
        })

    # Next 30 anime: Lower scores but more diverse genres
    for i in range(30):
        anime_data.append({
            "anime_id": i + 21,
            "score": 8.5 - i * 0.02,  # Scores from 8.5 down to 7.92
            "genres": genres_pool[5 + (i % 10)],  # More diverse genres
        })

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    # Test with 5 different random seed selections
    diversity_improvements = 0
    total_tests = 5

    for test_run in range(total_tests):
        # Randomly select 3 seed anime from top 10 (simulating user picks)
        seed_indices = np.random.choice(10, 3, replace=False)
        test_seeds = [anime_data[i] for i in seed_indices]

        # Simulate scoring: boost scores for anime similar to seeds
        # This creates a realistic scenario where similar anime cluster at the top
        scored_candidates = []
        for anime in anime_data:
            base_score = anime["score"]
            # Add similarity boost to seeds (realistic pipeline behavior)
            similarity_boost = 0
            for seed in test_seeds:
                sim = genre_jaccard_similarity(anime, seed)
                similarity_boost += sim * 0.5  # Boost similar items

            scored_candidates.append({
                "anime_id": anime["anime_id"],
                "score": base_score + similarity_boost,
                "genres": anime["genres"],
            })

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: -x["score"])

        # Test 1: Pure relevance (no MMR)
        top10_relevance = scored_candidates[:10]

        # Test 2: With MMR diversity (λ=0.3)
        top10_mmr = mmr_rerank(
            candidates=scored_candidates,
            similarity_fn=genre_sim,
            lambda_param=0.3,
            top_n=10,
        )

        # Measure diversity: count unique primary genres
        def count_unique_primary_genres(results):
            primary_genres = set()
            for r in results:
                genres = r.get("genres", "").split("|")
                if genres:
                    primary_genres.add(genres[0])
            return len(primary_genres)

        unique_genres_relevance = count_unique_primary_genres(top10_relevance)
        unique_genres_mmr = count_unique_primary_genres(top10_mmr)

        # MMR should increase genre diversity in most cases
        if unique_genres_mmr > unique_genres_relevance:
            diversity_improvements += 1

    # MMR should improve diversity in at least 60% of test runs
    # (Not 100% because sometimes the top results are already diverse)
    improvement_rate = diversity_improvements / total_tests
    assert improvement_rate >= 0.6, (
        f"MMR should improve diversity in most cases, but only improved in "
        f"{diversity_improvements}/{total_tests} runs ({improvement_rate:.1%})"
    )


def test_mmr_integration_genre_distribution_metrics():
    """Integration test: Validate that MMR measurably improves genre distribution.

    This test uses entropy as a quantitative measure of genre diversity.
    Higher entropy = more even distribution across genres.
    """
    np.random.seed(123)

    # Create a dataset where top candidates are heavily skewed toward Action
    candidates = []

    # Top 20 candidates: 15 Action, 5 diverse
    action_subgenres = ["Shounen", "Adventure", "Fantasy", "Military", "Mecha"]
    for i in range(15):
        candidates.append({
            "anime_id": i + 1,
            "score": 9.0 - i * 0.03,
            "genres": f"Action|{action_subgenres[i % 5]}",
        })

    diverse_genres = [
        "Romance|Drama", "Comedy|Slice of Life", "Mystery|Thriller",
        "Horror|Supernatural", "Sports|School"
    ]
    for i in range(5):
        candidates.append({
            "anime_id": i + 16,
            "score": 8.5 - i * 0.05,
            "genres": diverse_genres[i],
        })

    def genre_sim(a, b):
        return genre_jaccard_similarity(a, b)

    # Get top-10 with pure relevance
    top10_relevance = candidates[:10]

    # Get top-10 with MMR (λ=0.3)
    top10_mmr = mmr_rerank(
        candidates=candidates,
        similarity_fn=genre_sim,
        lambda_param=0.3,
        top_n=10,
    )

    def compute_genre_entropy(results):
        """Compute Shannon entropy of primary genre distribution."""
        import math
        from collections import Counter

        primary_genres = []
        for r in results:
            genres = r.get("genres", "").split("|")
            if genres and genres[0]:
                primary_genres.append(genres[0])

        if not primary_genres:
            return 0.0

        # Count genre occurrences
        counts = Counter(primary_genres)
        total = len(primary_genres)

        # Compute Shannon entropy: -Σ(p * log2(p))
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    entropy_relevance = compute_genre_entropy(top10_relevance)
    entropy_mmr = compute_genre_entropy(top10_mmr)

    # MMR should increase entropy (more diverse genre distribution)
    assert entropy_mmr > entropy_relevance, (
        f"MMR should increase genre entropy, but got: "
        f"relevance={entropy_relevance:.3f}, MMR={entropy_mmr:.3f}"
    )

    # Also verify: MMR should include at least one non-Action anime in top-5
    top5_mmr = top10_mmr[:5]
    non_action_in_top5 = any(
        not r.get("genres", "").startswith("Action")
        for r in top5_mmr
    )
    assert non_action_in_top5, (
        "MMR should diversify top-5 to include non-Action genres"
    )

