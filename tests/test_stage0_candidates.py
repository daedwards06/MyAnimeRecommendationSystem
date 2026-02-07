from __future__ import annotations

import numpy as np
import pandas as pd

from src.app.stage0_candidates import build_stage0_seed_candidate_pool


def test_stage0_pool_union_dedupe_and_cap() -> None:
    metadata = pd.DataFrame(
        {
            "anime_id": [1, 2, 3, 4, 5, 6],
            "genres": [
                "Action|Sci-Fi",  # seed
                "Action",  # genre match
                "Drama",  # no match
                "Sci-Fi",  # genre match
                "",  # missing-ish
                "Action",  # genre match but excluded by hygiene
            ],
            "themes": [
                "Space",  # seed
                "",  # no theme match
                "Space",  # theme match
                "",  # no theme match
                "Space",  # theme match
                "",  # no theme match
            ],
        }
    )

    # Neural neighbors: include some that also match genre/theme.
    class _DummyNeural:
        pass

    def _fake_topk(_artifact, *, seed_ids, topk):
        # Deterministic order.
        return [(2, 0.9), (3, 0.8), (5, 0.7)]

    # Monkeypatch by importing module attribute directly.
    import src.app.stage0_candidates as s0

    orig = s0.compute_seed_topk_neighbors
    s0.compute_seed_topk_neighbors = _fake_topk  # type: ignore[assignment]
    try:
        pop_item_ids = np.asarray([1, 2, 3, 4, 5, 6], dtype=np.int64)
        pop_scores = np.asarray([0.1, 0.2, 0.3, 0.4, 0.5, 0.99], dtype=np.float32)

        stage0_ids, flags, diag = build_stage0_seed_candidate_pool(
            metadata=metadata,
            seed_ids=[1],
            ranked_hygiene_exclude_ids={6},
            watched_ids=set(),
            neural_artifact=_DummyNeural(),
            neural_topk=10,
            meta_min_genre_overlap=0.50,
            meta_min_theme_overlap=0.50,
            popularity_backfill=2,
            pool_cap=4,
            pop_item_ids=pop_item_ids,
            pop_scores=pop_scores,
        )

        # Cap enforced.
        assert len(stage0_ids) == 4

        # Seed and hygiene exclusions applied.
        assert 1 not in stage0_ids
        assert 6 not in stage0_ids

        # Neural are first in stable order.
        assert stage0_ids[0:3] == [2, 3, 5]

        # Flags present for sources.
        assert flags[2]["from_neural"] is True
        assert flags[3]["from_neural"] is True
        assert flags[5]["from_neural"] is True

        # Strict metadata overlap can contribute.
        assert flags[2]["from_meta_strict"] is True
        assert flags[3]["from_meta_strict"] is True
        assert flags[5]["from_meta_strict"] is True

        # Diagnostics: after_hygiene is the actual Stage 0 universe (before cap).
        assert diag.stage0_after_hygiene == 4
        assert diag.stage0_after_cap == 4
        assert diag.stage0_from_neural_raw == 3
        assert diag.stage0_from_neural == 3

    finally:
        s0.compute_seed_topk_neighbors = orig  # type: ignore[assignment]
