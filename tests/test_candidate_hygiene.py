from __future__ import annotations

import pandas as pd

from src.app.quality_filters import (
    RANKED_HYGIENE_BAD_TITLE_REGEX,
    RANKED_HYGIENE_DISALLOW_TYPES,
    build_ranked_candidate_hygiene_exclude_ids,
)


def test_build_ranked_candidate_hygiene_exclude_ids_type_and_title():
    df = pd.DataFrame(
        [
            {"anime_id": 1, "title_display": "Some Show", "type": "TV"},
            {"anime_id": 2, "title_display": "Cool Special", "type": "Special"},
            {"anime_id": 3, "title_display": "Recap Digest", "type": "TV"},
            {"anime_id": 4, "title_display": "Music Video", "type": "Music"},
            {"anime_id": 5, "title_display": None, "type": None},
        ]
    )

    out = build_ranked_candidate_hygiene_exclude_ids(
        df,
        disallow_types=RANKED_HYGIENE_DISALLOW_TYPES,
        bad_title_regex=RANKED_HYGIENE_BAD_TITLE_REGEX,
    )

    assert 1 not in out
    assert 2 in out  # disallowed type
    assert 3 in out  # title regex
    assert 4 in out  # disallowed type
    assert 5 not in out
