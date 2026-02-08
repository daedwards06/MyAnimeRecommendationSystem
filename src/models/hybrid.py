from __future__ import annotations

from collections.abc import Sequence


def weighted_blend(score_dicts: dict[str, dict[int, float]], weights: dict[str, float], top_k: int) -> list[int]:
    """Blend multiple score dictionaries by source with provided weights."""
    agg: dict[int, float] = {}
    for source, scores in score_dicts.items():
        w = float(weights.get(source, 0.0))
        for item, sc in scores.items():
            agg[item] = agg.get(item, 0.0) + w * float(sc)
    ranked = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]


def reciprocal_rank_fusion(rankings: dict[str, Sequence[int]], top_k: int, k: int = 60) -> list[int]:
    """RRF: sum over sources of 1 / (k + rank)."""
    scores: dict[int, float] = {}
    for ranking in rankings.values():
        for r, item in enumerate(ranking):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + r + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]


def borda_count(rankings: dict[str, Sequence[int]], top_k: int) -> list[int]:
    """Borda Count rank aggregation."""
    scores: dict[int, int] = {}
    for ranking in rankings.values():
        n = len(ranking)
        for r, item in enumerate(ranking):
            scores[item] = scores.get(item, 0) + (n - r)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]
