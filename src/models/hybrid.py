from __future__ import annotations
from typing import Dict, List, Sequence


def weighted_blend(score_dicts: Dict[str, Dict[int, float]], weights: Dict[str, float], top_k: int) -> List[int]:
    """Blend multiple score dictionaries by source with provided weights."""
    agg: Dict[int, float] = {}
    for source, scores in score_dicts.items():
        w = float(weights.get(source, 0.0))
        for item, sc in scores.items():
            agg[item] = agg.get(item, 0.0) + w * float(sc)
    ranked = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]


def reciprocal_rank_fusion(rankings: Dict[str, Sequence[int]], top_k: int, k: int = 60) -> List[int]:
    """RRF: sum over sources of 1 / (k + rank)."""
    scores: Dict[int, float] = {}
    for ranking in rankings.values():
        for r, item in enumerate(ranking):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + r + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]


def borda_count(rankings: Dict[str, Sequence[int]], top_k: int) -> List[int]:
    """Borda Count rank aggregation."""
    scores: Dict[int, int] = {}
    for ranking in rankings.values():
        n = len(ranking)
        for r, item in enumerate(ranking):
            scores[item] = scores.get(item, 0) + (n - r)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]
