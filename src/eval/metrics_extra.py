from __future__ import annotations

import numpy as np


def item_coverage(recommendations: dict[int, list[int]], total_items: int) -> float:
    """Fraction of catalog that appears at least once across all users' top-K lists."""
    rec_items = set()
    for items in recommendations.values():
        rec_items.update(items)
    if total_items <= 0:
        return 0.0
    return float(len(rec_items)) / float(total_items)


def gini_index(recommendations: dict[int, list[int]]) -> float:
    """Gini index over item recommendation frequencies (higher => more inequality).

    If no recommendations, return 0. Uses the standard Gini formula over positive counts.
    """
    from collections import Counter

    counts = Counter()
    for items in recommendations.values():
        counts.update(items)
    if not counts:
        return 0.0
    x = np.array(sorted(counts.values()))
    n = x.size
    if n == 0:
        return 0.0
    cum_x = np.cumsum(x)
    # Gini with mean absolute difference formulation simplified for discrete distribution
    gini = (n + 1 - 2 * np.sum(cum_x) / cum_x[-1]) / n
    return float(gini)
