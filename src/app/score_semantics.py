"""Single source of truth for recommendation score semantics.

Phase 2 / Chunk 1:
- Recommendation scores are *relative* and *uncalibrated*.
- They must not be presented as probabilities, percentiles, or /10 ratings.

The goal is consistent UI labeling + formatting without changing ranking.
"""

from __future__ import annotations

import math
from typing import Optional


SCORE_SEMANTIC_NAME: str = "Match score (relative)"
SCORE_LABEL_SHORT: str = "Match score"
SCORE_HELP_TEXT: str = (
    "Relative, uncalibrated ranking signal. Higher means a better match. "
    "Compare within the current run (not a probability or /10 rating)."
)


def has_match_score(value: Optional[float]) -> bool:
    if value is None:
        return False
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def format_match_score(value: Optional[float], *, decimals: int = 3) -> str:
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


__all__ = [
    "SCORE_SEMANTIC_NAME",
    "SCORE_LABEL_SHORT",
    "SCORE_HELP_TEXT",
    "has_match_score",
    "format_match_score",
]
