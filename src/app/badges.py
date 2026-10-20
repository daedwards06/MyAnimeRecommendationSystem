"""Badge logic for cold-start, popularity band, and genre novelty."""

from __future__ import annotations

from typing import Any


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


# The one visitor-facing name per band (audit F8); popularity_band values stay the badge contract.
BAND_LABELS: dict[str, str] = {
    "Top 10%": "Popular",
    "Top 25%": "Popular",
    "Mid": "Mid-range",
    "Long Tail": "Hidden gem",
}


def band_label(band: str) -> str:
    return BAND_LABELS.get(band, band)


def band_counts(bands: list[str]) -> tuple[int, int, int]:
    """(popular, mid-range, hidden gem) counts from popularity_band values."""
    labels = [band_label(b) for b in bands]
    return labels.count("Popular"), labels.count("Mid-range"), labels.count("Hidden gem")


def novelty_ratio(user_genre_hist: dict[str, int], item_genres: list[str]) -> float | None:
    """Compute novelty ratio for an item relative to a user's genre history.

    Returns None when there is no user history to compare against (i.e., not
    personalized). This prevents displaying misleading novelty values.
    """
    if not user_genre_hist:
        return None
    if not item_genres:
        return None
    # Compare case-insensitively; history keys are expected to be normalized.
    unseen = 0
    denom = 0
    for g in item_genres:
        gg = str(g).strip().lower()
        if not gg:
            continue
        denom += 1
        if gg not in user_genre_hist:
            unseen += 1
    if denom <= 0:
        return None
    return unseen / denom


def badge_payload(
    is_in_training: bool,
    pop_percentile: float,
    user_genre_hist: dict[str, int],
    item_genres: list[str],
) -> dict[str, Any]:
    return {
        "cold_start": cold_start_flag(is_in_training),
        "popularity_band": popularity_band(pop_percentile),
        "novelty_ratio": novelty_ratio(user_genre_hist, item_genres),
    }


__all__ = [
    "BAND_LABELS",
    "badge_payload",
    "band_counts",
    "band_label",
    "cold_start_flag",
    "novelty_ratio",
    "popularity_band",
]
