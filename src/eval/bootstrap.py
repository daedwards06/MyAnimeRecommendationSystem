"""Percentile bootstrap intervals over per-user metric vectors.

Users are the resampling unit. Every model in the ablation is scored on the same cohort, so a
comparison between two models resamples users jointly (`paired_bootstrap_diff_ci`): the
between-user variance that both models share cancels, and the interval is much tighter than
the gap between two independent intervals would suggest.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from src.models.constants import RANDOM_SEED

N_RESAMPLES = 1000
CONFIDENCE = 0.95


def _resample_indices(n: int, n_resamples: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, size=(n_resamples, n))


def _percentile_interval(stats: np.ndarray, confidence: float) -> tuple[float, float]:
    tail = (1.0 - confidence) / 2.0 * 100.0
    low, high = np.percentile(stats, [tail, 100.0 - tail])
    return float(low), float(high)


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    n_resamples: int = N_RESAMPLES,
    confidence: float = CONFIDENCE,
    seed: int = RANDOM_SEED,
) -> tuple[float, float, float]:
    """Return (mean, low, high) for the mean of `values`."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("bootstrap_mean_ci needs at least one value")
    idx = _resample_indices(arr.size, n_resamples, seed)
    low, high = _percentile_interval(arr[idx].mean(axis=1), confidence)
    return float(arr.mean()), low, high


def paired_bootstrap_diff_ci(
    a: Sequence[float],
    b: Sequence[float],
    *,
    n_resamples: int = N_RESAMPLES,
    confidence: float = CONFIDENCE,
    seed: int = RANDOM_SEED,
) -> tuple[float, float, float]:
    """Return (mean(a) - mean(b), low, high), resampling the same users for both.

    `a[i]` and `b[i]` must be the same user's metric under two models.
    """
    arr_a = np.asarray(a, dtype=np.float64)
    arr_b = np.asarray(b, dtype=np.float64)
    if arr_a.shape != arr_b.shape:
        raise ValueError(f"paired vectors differ in length: {arr_a.shape} vs {arr_b.shape}")
    return bootstrap_mean_ci(arr_a - arr_b, n_resamples=n_resamples, confidence=confidence, seed=seed)


__all__ = ["CONFIDENCE", "N_RESAMPLES", "bootstrap_mean_ci", "paired_bootstrap_diff_ci"]
