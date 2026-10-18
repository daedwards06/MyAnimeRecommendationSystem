import numpy as np
import pytest

from src.eval.bootstrap import bootstrap_mean_ci, paired_bootstrap_diff_ci


def _ndcg_like(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    hits = rng.random(n) < 0.08
    return np.where(hits, 1.0 / np.log2(rng.integers(2, 12, n)), 0.0)


def test_bootstrap_is_deterministic_with_a_seed():
    values = _ndcg_like(500, 1)
    assert bootstrap_mean_ci(values, seed=7) == bootstrap_mean_ci(values, seed=7)
    assert bootstrap_mean_ci(values, seed=7) != bootstrap_mean_ci(values, seed=8)


def test_bootstrap_brackets_the_point_estimate():
    values = _ndcg_like(1000, 2)
    mean, low, high = bootstrap_mean_ci(values)
    assert mean == pytest.approx(values.mean())
    assert low < mean < high


def test_paired_diff_brackets_the_point_estimate_and_is_tighter_than_unpaired():
    base = _ndcg_like(1000, 3)
    noise = np.where(np.random.default_rng(4).random(1000) < 0.05, 0.3, 0.0)
    better = base + noise
    diff, low, high = paired_bootstrap_diff_ci(better, base)
    assert diff == pytest.approx(better.mean() - base.mean())
    assert low < diff < high
    _, b_low, b_high = bootstrap_mean_ci(better)
    _, a_low, a_high = bootstrap_mean_ci(base)
    assert (high - low) < (b_high - b_low) + (a_high - a_low)


def test_paired_diff_of_a_model_with_itself_is_exactly_zero():
    values = _ndcg_like(200, 5)
    assert paired_bootstrap_diff_ci(values, values) == (0.0, 0.0, 0.0)


def test_paired_diff_rejects_unaligned_vectors():
    with pytest.raises(ValueError, match="differ in length"):
        paired_bootstrap_diff_ci([0.1, 0.2], [0.1])
