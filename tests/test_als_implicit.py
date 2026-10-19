"""Tests for the implicit-feedback ALS model used by the Task 2.1 MF diagnostic."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.als_implicit import ImplicitALSRecommender


@pytest.fixture
def two_taste_groups() -> pd.DataFrame:
    """Users 0-9 watch items 0-4, users 10-19 watch items 5-9; user 0 has not watched item 4.

    Ratings are deliberately mixed, including 0 (watched, unrated): the model must ignore them.
    """
    rng = np.random.default_rng(0)
    rows = []
    for u in range(20):
        group = range(0, 5) if u < 10 else range(5, 10)
        for i in group:
            if (u, i) != (0, 4):
                rows.append((u, i, float(rng.choice([0, 3, 8, 10]))))
    return pd.DataFrame(rows, columns=["user_id", "anime_id", "rating"])


def test_recommends_the_unwatched_item_from_the_users_group(two_taste_groups: pd.DataFrame):
    model = ImplicitALSRecommender(n_factors=4, n_iters=8).fit(two_taste_groups)
    seen = {0, 1, 2, 3}

    assert model.recommend(0, top_k=1, exclude=seen) == [4]
    assert not seen & set(model.recommend(0, top_k=10, exclude=seen))


def test_ratings_do_not_change_the_fit(two_taste_groups: pd.DataFrame):
    rescored = two_taste_groups.assign(rating=1.0)
    a = ImplicitALSRecommender(n_factors=4, n_iters=3).fit(two_taste_groups)
    b = ImplicitALSRecommender(n_factors=4, n_iters=3).fit(rescored)

    np.testing.assert_allclose(a.predict_user(0), b.predict_user(0))


def test_unknown_user_scores_zero(two_taste_groups: pd.DataFrame):
    model = ImplicitALSRecommender(n_factors=4, n_iters=2).fit(two_taste_groups)

    assert not model.predict_user(999).any()


def test_unknown_user_gets_no_recommendations(two_taste_groups: pd.DataFrame):
    """All-zero scores must not come back in index order as an accidental popularity list."""
    model = ImplicitALSRecommender(n_factors=4, n_iters=2).fit(two_taste_groups)

    assert model.recommend(999, top_k=5) == []
