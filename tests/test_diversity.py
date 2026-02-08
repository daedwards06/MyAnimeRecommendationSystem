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
    genre_exposure_ratio,
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
