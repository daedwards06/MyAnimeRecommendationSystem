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


MATCH_TIERS: tuple[tuple[str, str], ...] = (
    ("Top match", "#27AE60"),
    ("Strong match", "#3498DB"),
    ("Good match", "#E67E22"),
    ("Worth a look", "#95A5A6"),
)


def match_rank(raw_score: float, all_raw_scores: list[float]) -> int:
    """1-based rank of ``raw_score`` within the run (ties share the best rank)."""
    sorted_scores = sorted(all_raw_scores, reverse=True)
    try:
        return sorted_scores.index(raw_score) + 1
    except ValueError:
        return 1


def format_user_friendly_score(
    raw_score: float, all_raw_scores: list[float]
) -> tuple[str, str, str]:
    """Convert a raw score to a tiered match label for display.

    The tier is the within-run rank quartile: the first quarter of the run is
    "Top match", then "Strong match", "Good match", and "Worth a look". Scores are
    uncalibrated, so no percentage is shown; the tooltip carries the rank and the
    raw score.

    Returns:
        (display_text, tooltip_text, color)
    """
    if not all_raw_scores:
        return "—", "No score data", "#95A5A6"

    n = len(all_raw_scores)
    rank = match_rank(raw_score, all_raw_scores)
    tier = min(len(MATCH_TIERS) - 1, ((rank - 1) * len(MATCH_TIERS)) // n)
    label, color = MATCH_TIERS[tier]
    tooltip = f"Rank {rank} of {n} in this run, raw score {raw_score:.3f} (relative, not a probability)"
    return label, tooltip, color


__all__ = [
    "MATCH_TIERS",
    "SCORE_HELP_TEXT",
    "SCORE_LABEL_SHORT",
    "SCORE_SEMANTIC_NAME",
    "format_match_score",
    "format_user_friendly_score",
    "has_match_score",
    "match_rank",
]
