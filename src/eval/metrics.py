from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np


def precision_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """Precision@k for a single user."""
    top = recommended[:k]
    hit = sum(1 for i in top if i in relevant)
    return hit / max(k, 1)


def recall_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """Recall@k for a single user."""
    if not relevant:
        return 0.0
    top = recommended[:k]
    hit = sum(1 for i in top if i in relevant)
    return hit / len(relevant)


def f1_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """F1@k from precision and recall."""
    p = precision_at_k(recommended, relevant, k)
    r = recall_at_k(recommended, relevant, k)
    return 0.0 if (p + r) == 0 else 2 * p * r / (p + r)


def _dcg(scores: Sequence[float]) -> float:
    return float(sum(s / np.log2(i + 2) for i, s in enumerate(scores)))


def ndcg_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """NDCG@k where each relevant item has gain 1, irrelevance 0."""
    gains = [1.0 if i in relevant else 0.0 for i in recommended[:k]]
    ideal = sorted(gains, reverse=True)
    denom = _dcg(ideal)
    return 0.0 if denom == 0 else _dcg(gains) / denom


def ndcg_at_k_graded(
    ranked_list: Sequence[int],
    item_ratings: dict[int, float],
    k: int,
    gain_fn: str = "exponential",
) -> float:
    """NDCG@K with graded relevance from explicit ratings.

    Args:
        ranked_list: Ordered list of recommended item IDs
        item_ratings: Dict mapping item_id -> rating (e.g., 1-10 scale)
        k: Cutoff position
        gain_fn: "exponential" for 2^rating - 1, "linear" for raw rating

    Returns:
        NDCG@K score in [0, 1]

    Notes:
        Exponential gain (2^r - 1) is the standard in RecSys literature
        as it emphasizes highly-rated items more strongly than linear gain.
    """
    if not item_ratings:
        return 0.0

    # Compute gains for recommended items
    if gain_fn == "exponential":
        gains = [2.0 ** item_ratings.get(item, 0.0) - 1.0 for item in ranked_list[:k]]
    elif gain_fn == "linear":
        gains = [item_ratings.get(item, 0.0) for item in ranked_list[:k]]
    else:
        raise ValueError(f"Unknown gain_fn: {gain_fn}. Use 'exponential' or 'linear'.")

    # Compute ideal DCG (sorted by rating descending)
    ideal_gains = sorted(gains, reverse=True)
    ideal_dcg = _dcg(ideal_gains)

    if ideal_dcg == 0.0:
        return 0.0

    # Compute actual DCG
    actual_dcg = _dcg(gains)

    return actual_dcg / ideal_dcg


def average_precision_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """AP@k for a single user."""
    ap, hits = 0.0, 0
    for idx, item in enumerate(recommended[:k], start=1):
        if item in relevant:
            hits += 1
            ap += hits / idx
    return 0.0 if not relevant else ap / min(len(relevant), k)


def evaluate_ranking(
    recommended: Sequence[int],
    relevant: set[int],
    k_values: Iterable[int],
    item_ratings: dict[int, float] | None = None,
    gain_fn: str = "exponential",
) -> dict[str, dict[int, float]]:
    """Return a dictionary with metrics over the provided k values.

    Args:
        recommended: Ordered list of recommended item IDs
        relevant: Set of relevant item IDs (for binary metrics)
        k_values: List of K values to evaluate at
        item_ratings: Optional dict mapping item_id -> rating for graded NDCG
        gain_fn: Gain function for graded NDCG ("exponential" or "linear")

    Returns:
        Dict with keys: "precision", "recall", "f1", "ndcg", "map"
        If item_ratings provided, also includes "ndcg_graded"
    """
    out: dict[str, dict[int, float]] = {"precision": {}, "recall": {}, "f1": {}, "ndcg": {}, "map": {}}

    # Add graded NDCG dict if ratings provided
    if item_ratings is not None:
        out["ndcg_graded"] = {}

    for k in k_values:
        out["precision"][k] = precision_at_k(recommended, relevant, k)
        out["recall"][k] = recall_at_k(recommended, relevant, k)
        out["f1"][k] = f1_at_k(recommended, relevant, k)
        out["ndcg"][k] = ndcg_at_k(recommended, relevant, k)
        out["map"][k] = average_precision_at_k(recommended, relevant, k)

        # Compute graded NDCG if ratings provided
        if item_ratings is not None:
            out["ndcg_graded"][k] = ndcg_at_k_graded(recommended, item_ratings, k, gain_fn)

    return out
