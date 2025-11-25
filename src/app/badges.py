"""Badge logic for cold-start, popularity band, and genre novelty."""

from __future__ import annotations

from typing import Dict, List, Any


def cold_start_flag(is_in_training: bool) -> bool:
    return not is_in_training


def popularity_band(pop_percentile: float) -> str:
    """Map popularity percentile (0=most popular) to label."""
    if pop_percentile < 0.10:
        return "Top 10%"
    if pop_percentile < 0.25:
        return "Top 25%"
    if pop_percentile < 0.50:
        return "Mid"
    return "Long Tail"


def novelty_ratio(user_genre_hist: Dict[str, int], item_genres: List[str]) -> float:
    if not item_genres:
        return 0.0
    unseen = sum(1 for g in item_genres if g not in user_genre_hist)
    return unseen / len(item_genres)


def badge_payload(
    is_in_training: bool,
    pop_percentile: float,
    user_genre_hist: Dict[str, int],
    item_genres: List[str],
) -> Dict[str, Any]:
    return {
        "cold_start": cold_start_flag(is_in_training),
        "popularity_band": popularity_band(pop_percentile),
        "novelty_ratio": novelty_ratio(user_genre_hist, item_genres),
    }


__all__ = [
    "cold_start_flag",
    "popularity_band",
    "novelty_ratio",
    "badge_payload",
]
