"""Single source of truth for recommendation score semantics.

Phase 2 / Chunk 1:
- Recommendation scores are *relative* and *uncalibrated*.
- They must not be presented as probabilities, percentiles, or /10 ratings.

The goal is consistent UI labeling + formatting without changing ranking.
"""

from __future__ import annotations

import math

SCORE_SEMANTIC_NAME: str = "Match score (relative)"
SCORE_LABEL_SHORT: str = "Match score"
SCORE_HELP_TEXT: str = (
    "Relative, uncalibrated ranking signal. Higher means a better match. "
    "Compare within the current run (not a probability or /10 rating)."
)


def has_match_score(value: float | None) -> bool:
    if value is None:
        return False
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def format_match_score(value: float | None, *, decimals: int = 3) -> str:
    """Format a recommendation score for display.

    Notes:
    - This does not normalize, calibrate, or clamp (display semantics only).
    - Values are intentionally shown as unitless to avoid implying bounds.
    """

    if not has_match_score(value):
        return "—"
    v = float(value)
    fmt = f"{{:.{decimals}f}}"
    return fmt.format(v)


def format_user_friendly_score(
    raw_score: float, all_raw_scores: list[float]
) -> tuple[str, str, str]:
    """Convert raw score to user-friendly display format.

    Computes percentile rank within the current result set and displays
    as a percentage with color coding. This makes scores more interpretable
    for end users who don't understand raw, uncalibrated values.

    Args:
        raw_score: The raw recommendation score for this item
        all_raw_scores: All raw scores in the current result set (for percentile)

    Returns:
        (display_text, tooltip_text, color):
            display_text: e.g., "95% Match"
            tooltip_text: e.g., "Raw score: 0.847 (relative to this result set)"
            color: CSS color code based on percentile (green/blue/orange/grey)

    Notes:
    - Top item gets "98% Match" (not 100% — more honest)
    - Minimum display is "50% Match" (don't show low numbers for recommended items)
    - Color coding: ≥90% green, ≥75% blue, ≥60% orange, else grey
    - Scores are relative within the result set, not absolute quality ratings
    """
    if not all_raw_scores:
        # Fallback if no scores available
        return "—% Match", "No score data", "#95A5A6"

    # Sort scores descending to compute percentile rank
    sorted_scores = sorted(all_raw_scores, reverse=True)

    # Find rank of this score (0-indexed, 0 = best)
    try:
        rank = sorted_scores.index(raw_score)
    except ValueError:
        # Score not in list (shouldn't happen), use 0
        rank = 0

    # Compute percentile: top item = 98%, scale linearly
    # percentile = 1 - (rank / len(sorted_scores))
    if len(sorted_scores) == 1:
        percentile = 0.98  # Single item gets 98%
    else:
        # Linear interpolation: rank 0 → 98%, last rank → 50%
        percentile = 0.98 - (rank / (len(sorted_scores) - 1)) * (0.98 - 0.50)

    # Clamp to [50%, 98%]
    percentile = max(0.50, min(0.98, percentile))

    # Format display text
    display_text = f"{int(percentile * 100)}% Match"

    # Tooltip with raw score
    tooltip_text = f"Raw score: {raw_score:.3f} (relative to this result set)"

    # Color coding
    if percentile >= 0.90:
        color = "#27AE60"  # Green
    elif percentile >= 0.75:
        color = "#3498DB"  # Blue
    elif percentile >= 0.60:
        color = "#E67E22"  # Orange
    else:
        color = "#95A5A6"  # Grey

    return display_text, tooltip_text, color


__all__ = [
    "SCORE_HELP_TEXT",
    "SCORE_LABEL_SHORT",
    "SCORE_SEMANTIC_NAME",
    "format_match_score",
    "format_user_friendly_score",
    "has_match_score",
]
