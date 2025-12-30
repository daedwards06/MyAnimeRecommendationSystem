from __future__ import annotations

import pandas as pd

from src.app.metadata_features import (
    METADATA_AFFINITY_COLD_START_COEF,
    METADATA_AFFINITY_YEAR_WINDOW,
    build_seed_metadata_profile,
    compute_metadata_affinity,
)


def test_build_seed_metadata_profile_and_affinity_overlap():
    df = pd.DataFrame(
        [
            {
                "anime_id": 10,
                "studios": ["A-1 Pictures"],
                "themes": ["Gore"],
                "demographics": ["Seinen"],
                "producers": ["Aniplex", "Fuji TV"],
                "aired_from": "2017-01-01T00:00:00+00:00",
            },
            {
                "anime_id": 20,
                "studios": ["A-1 Pictures"],
                "themes": ["Gore", "Psychological"],
                "demographics": ["Seinen"],
                "producers": ["Aniplex"],
                "aired_from": "2018-01-01T00:00:00+00:00",
            },
        ]
    )

    profile = build_seed_metadata_profile(df, seed_ids=[10])
    assert "A-1 Pictures" in profile.studios
    assert "Gore" in profile.themes
    assert "Seinen" in profile.demographics
    assert "Aniplex" in profile.producers
    assert profile.seed_year_mean is not None

    affinity = compute_metadata_affinity(profile, df.loc[df["anime_id"] == 20].iloc[0])
    assert 0.0 <= affinity <= 1.0
    assert affinity > 0.0


def test_affinity_year_window_behavior():
    df = pd.DataFrame(
        [
            {"anime_id": 1, "aired_from": "2010-01-01T00:00:00+00:00"},
            {"anime_id": 2, "aired_from": f"{2010 + METADATA_AFFINITY_YEAR_WINDOW}-01-01T00:00:00+00:00"},
        ]
    )
    profile = build_seed_metadata_profile(df, seed_ids=[1])

    # At exactly +window years away, similarity clamps to 0.
    affinity = compute_metadata_affinity(profile, df.loc[df["anime_id"] == 2].iloc[0])
    # With no categorical overlap signals, affinity should stay at 0 (conservative gating).
    assert affinity == 0.0


def test_affinity_missing_metadata_is_safe():
    df = pd.DataFrame(
        [
            {"anime_id": 1, "title_display": "Seed", "genres": "Action"},
            {"anime_id": 2, "title_display": "Candidate", "genres": "Action"},
        ]
    )
    profile = build_seed_metadata_profile(df, seed_ids=[1])
    affinity = compute_metadata_affinity(profile, df.loc[df["anime_id"] == 2].iloc[0])

    # No relevant metadata columns => affinity defaults to 0.
    assert affinity == 0.0


def test_cold_start_coef_is_conservative():
    # Coef should remain small relative to existing seed-based scoring terms.
    assert 0.0 < float(METADATA_AFFINITY_COLD_START_COEF) <= 0.2
