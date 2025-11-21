from __future__ import annotations
from typing import Dict, List


def blend_explanations(
    top_items: List[int],
    sources: Dict[str, Dict[int, float]],
    weights: Dict[str, float],
) -> Dict[int, Dict[str, float]]:
    """Return per-item contribution breakdown for a blended recommendation list.

    For each item in top_items, compute contribution = weight[source] * source_score[item].
    Missing scores default to 0.
    """
    out: Dict[int, Dict[str, float]] = {}
    for it in top_items:
        contrib = {}
        total = 0.0
        for src, scores in sources.items():
            w = float(weights.get(src, 0.0))
            sc = float(scores.get(it, 0.0))
            val = w * sc
            contrib[src] = val
            total += val
        # optionally include normalized shares to aid readability
        shares = {f"{k}_share": (v / total if total != 0 else 0.0) for k, v in contrib.items()}
        out[it] = {**contrib, **shares, "total": total}
    return out
