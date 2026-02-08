"""Hybrid recommendation explanation utilities for Phase 4 & app integration."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_hybrid_contributions(
    component_scores: dict[str, float],
    weights: dict[str, float],
) -> dict[str, float]:
    """Convert component scores and weights into normalized contribution shares.

    Parameters
    ----------
    component_scores : dict
        Raw scores from each source (e.g., mf, knn, pop, content).
    weights : dict
        Blending weights (same keys as component_scores subset).

    Returns
    -------
    Dict[str, float]
        Component -> percentage share of final hybrid score (sums to ~1.0).
    """
    weighted = {
        k: component_scores.get(k, 0.0) * weights.get(k, 0.0)
        for k in component_scores
    }
    total = sum(weighted.values())
    if total == 0:
        return {k: 0.0 for k in weighted}
    return {k: v / total for k, v in weighted.items()}


def format_explanation(item_id: int, contributions: dict[str, float]) -> str:
    """Human-readable summary of component shares."""
    parts = [
        f"{src}: {pct:.1%}" for src, pct in sorted(contributions.items(), key=lambda x: -x[1])
    ]
    return f"Item {item_id} hybrid contribution breakdown -> " + ", ".join(parts)


def build_examples(
    recommendations: list[tuple[int, dict[str, float]]],
    weights: dict[str, float],
    top_n: int = 3,
) -> list[dict[str, str]]:
    """Build explanation examples for the top-N recommendations.

    Parameters
    ----------
    recommendations : list of (item_id, component_score_dict)
        Each component_score_dict maps component name to its raw score.
    weights : dict
        Hybrid blending weights.
    top_n : int, default=3
        Number of top recommendations to explain.

    Returns
    -------
    List[Dict[str, str]]
        Each dict contains item_id, shares (component -> float) and text summary.
    """
    examples = []
    for item_id, comp_scores in recommendations[:top_n]:
        shares = compute_hybrid_contributions(comp_scores, weights)
        examples.append(
            {
                "item_id": str(item_id),
                "shares": {k: round(v, 4) for k, v in shares.items()},
                "text": format_explanation(item_id, shares),
            }
        )
    return examples


if __name__ == "__main__":  # Simple self-test
    demo_recs = [
        (123, {"mf": 0.82, "knn": 0.05, "pop": 0.01, "content": 0.20}),
        (456, {"mf": 0.77, "knn": 0.08, "pop": 0.02, "content": 0.25}),
        (789, {"mf": 0.65, "knn": 0.11, "pop": 0.03, "content": 0.30}),
    ]
    weights_demo = {"mf": 0.93078, "knn": 0.06625, "pop": 0.00297, "content": 0.0}
    for ex in build_examples(demo_recs, weights_demo):
        logger.debug(ex["text"])  # Smoke output for self-test
