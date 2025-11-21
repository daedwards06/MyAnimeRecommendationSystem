from __future__ import annotations
import numpy as np
from typing import Sequence, Iterable, Dict, Set


def precision_at_k(recommended: Sequence[int], relevant: Set[int], k: int) -> float:
    """Precision@k for a single user."""
    top = recommended[:k]
    hit = sum(1 for i in top if i in relevant)
    return hit / max(k, 1)


def recall_at_k(recommended: Sequence[int], relevant: Set[int], k: int) -> float:
    """Recall@k for a single user."""
    if not relevant:
        return 0.0
    top = recommended[:k]
    hit = sum(1 for i in top if i in relevant)
    return hit / len(relevant)


def f1_at_k(recommended: Sequence[int], relevant: Set[int], k: int) -> float:
    """F1@k from precision and recall."""
    p = precision_at_k(recommended, relevant, k)
    r = recall_at_k(recommended, relevant, k)
    return 0.0 if (p + r) == 0 else 2 * p * r / (p + r)


def _dcg(scores: Sequence[float]) -> float:
    return float(sum(s / np.log2(i + 2) for i, s in enumerate(scores)))


def ndcg_at_k(recommended: Sequence[int], relevant: Set[int], k: int) -> float:
    """NDCG@k where each relevant item has gain 1, irrelevance 0."""
    gains = [1.0 if i in relevant else 0.0 for i in recommended[:k]]
    ideal = sorted(gains, reverse=True)
    denom = _dcg(ideal)
    return 0.0 if denom == 0 else _dcg(gains) / denom


def average_precision_at_k(recommended: Sequence[int], relevant: Set[int], k: int) -> float:
    """AP@k for a single user."""
    ap, hits = 0.0, 0
    for idx, item in enumerate(recommended[:k], start=1):
        if item in relevant:
            hits += 1
            ap += hits / idx
    return 0.0 if not relevant else ap / min(len(relevant), k)


def evaluate_ranking(recommended: Sequence[int], relevant: Set[int], k_values: Iterable[int]) -> Dict[str, Dict[int, float]]:
    """Return a dictionary with metrics over the provided k values."""
    out: Dict[str, Dict[int, float]] = {"precision": {}, "recall": {}, "f1": {}, "ndcg": {}, "map": {}}
    for k in k_values:
        out["precision"][k] = precision_at_k(recommended, relevant, k)
        out["recall"][k] = recall_at_k(recommended, relevant, k)
        out["f1"][k] = f1_at_k(recommended, relevant, k)
        out["ndcg"][k] = ndcg_at_k(recommended, relevant, k)
        out["map"][k] = average_precision_at_k(recommended, relevant, k)
    return out
