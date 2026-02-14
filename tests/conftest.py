"""PyTest configuration: shared fixtures and test utilities.

This module provides:
- Project root path setup for `import src`
- Shared fixtures for models, metadata, and test data
- Factory fixtures for creating test instances
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Mock Model Classes
# ---------------------------------------------------------------------------


class MockMFModel:
    """Mock matrix factorization model for testing.

    Provides realistic attributes required by the recommendation pipeline:
    - P: user factors matrix
    - Q: item factors matrix
    - item_to_index, index_to_item: item ID mappings
    - global_mean: baseline rating
    - n_factors: embedding dimension
    """

    def __init__(self, n_users: int = 5, n_items: int = 10, n_factors: int = 8):
        np.random.seed(42)
        self.P = np.random.randn(n_users, n_factors).astype(np.float32) * 0.1
        self.Q = np.random.randn(n_items, n_factors).astype(np.float32) * 0.1
        self.item_to_index = {i: i for i in range(n_items)}
        self.index_to_item = {i: i for i in range(n_items)}
        self.global_mean = 7.0
        self.n_factors = n_factors

    def predict_for_user(self, user_index: int, item_indices: list[int]) -> np.ndarray:
        """Predict scores for a user and list of item indices."""
        scores = self.global_mean + self.P[user_index] @ self.Q[item_indices].T
        return scores

    @property
    def mf_stem(self) -> str:
        """Return a mock stem for artifact versioning."""
        return "mock_v1.0"


class MockKNNModel:
    """Mock k-nearest neighbors model for testing.

    Minimal implementation - the pipeline handles knn=None gracefully.
    """

    def __init__(self, n_items: int = 10):
        np.random.seed(43)
        self.model = None  # Pipeline doesn't directly access this


# ---------------------------------------------------------------------------
# Shared Data Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_metadata() -> pd.DataFrame:
    """Comprehensive metadata DataFrame with 10 diverse anime for testing.

    Covers:
    - Popular titles (FMA, Steins;Gate, Attack on Titan)
    - Different types (TV, Movie)
    - Genre diversity (Action, Drama, Sci-Fi, Romance, Psychological)
    - Score range (6.8-9.1)
    - Era diversity (1998-2017)
    - Franchise relationships (Attack on Titan S1/S2)
    """
    return pd.DataFrame(
        [
            {
                "anime_id": 1,
                "title_display": "Fullmetal Alchemist: Brotherhood",
                "title_english": "Fullmetal Alchemist: Brotherhood",
                "title_primary": "Fullmetal Alchemist: Brotherhood",
                "title": "Fullmetal Alchemist: Brotherhood",
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
                "title_english": "Steins;Gate",
                "title_primary": "Steins;Gate",
                "title": "Steins;Gate",
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
                "title_english": "Hunter x Hunter",
                "title_primary": "Hunter x Hunter (2011)",
                "title": "Hunter x Hunter (2011)",
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
                "title_english": "Attack on Titan",
                "title_primary": "Attack on Titan",
                "title": "Shingeki no Kyojin",
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
                "title_english": "Death Note",
                "title_primary": "Death Note",
                "title": "Death Note",
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
                "title_english": "Cowboy Bebop",
                "title_primary": "Cowboy Bebop",
                "title": "Cowboy Bebop",
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
                "title_english": "Code Geass: Lelouch of the Rebellion",
                "title_primary": "Code Geass",
                "title": "Code Geass: Hangyaku no Lelouch",
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
                "title_english": "Your Name",
                "title_primary": "Your Name",
                "title": "Kimi no Na wa",
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
                "title_english": "Niche Psychological Thriller",
                "title_primary": "Niche Psychological Thriller",
                "title": "Niche Psychological Thriller",
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
                "title_english": "Attack on Titan Season 2",
                "title_primary": "Attack on Titan Season 2",
                "title": "Shingeki no Kyojin Season 2",
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
def sample_ratings() -> dict[int, float]:
    """Sample user ratings for 8 anime (IDs 0-20).

    Mix of high ratings (9-10) and moderate ratings (6-8) to test
    weighted averaging and personalization.
    """
    return {
        0: 10.0,
        1: 9.0,
        2: 8.0,
        3: 7.0,
        5: 8.0,
        10: 9.0,
        15: 6.0,
        20: 7.0,
    }


@pytest.fixture
def sample_seeds() -> list[int]:
    """Default seed anime IDs for testing seed-based recommendations.

    Uses popular well-connected anime (FMA:B, Steins;Gate, HxH).
    """
    return [1, 2, 3]


# ---------------------------------------------------------------------------
# Model Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mf_model() -> MockMFModel:
    """Mock MF model with 5 users, 10 items, 8 factors."""
    return MockMFModel(n_users=5, n_items=10, n_factors=8)


@pytest.fixture
def mock_knn_model() -> MockKNNModel | None:
    """Mock kNN model (returns None by default - pipeline handles this)."""
    return None


# ---------------------------------------------------------------------------
# Bundle & Component Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bundle(mock_mf_model: MockMFModel, sample_metadata: pd.DataFrame) -> dict:
    """Mock artifact bundle with models and metadata.

    Structure matches the return value of build_artifacts().
    """
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
def mock_components(mock_mf_model: MockMFModel):
    """Mock HybridComponents for HybridRecommender.

    Precomputes MF scores for all user-item pairs.
    Requires HybridComponents to be imported (deferred import to avoid circular deps).
    """
    from src.app.recommender import HybridComponents

    # Precompute MF scores for all users and items
    mf_scores_2d = np.zeros((5, 10), dtype=np.float32)
    for user_idx in range(5):
        mf_scores_2d[user_idx] = mock_mf_model.predict_for_user(user_idx, list(range(10)))

    return HybridComponents(
        mf=mf_scores_2d,  # 2D array (n_users, n_items)
        knn=None,
        pop=np.random.rand(10).astype(np.float32) * 0.1,  # Small popularity scores
        item_ids=np.arange(1, 11, dtype=np.int64),  # anime_ids 1-10
    )


@pytest.fixture
def mock_recommender(mock_components):
    """Mock HybridRecommender instance ready for testing."""
    from src.app.recommender import HybridRecommender

    return HybridRecommender(mock_components)
