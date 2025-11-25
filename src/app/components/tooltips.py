"""Tooltip and badge explanation utilities for Phase 5 app.

Provides helper text and formatting for cold-start, popularity band, and novelty indicators.
"""

from __future__ import annotations


def explain_cold_start(is_cold_start: bool) -> str:
    """Return explanation text for cold-start badge.
    
    Parameters
    ----------
    is_cold_start : bool
        Whether the item is flagged as cold-start (no training interactions).
    
    Returns
    -------
    str
        Explanation text suitable for tooltip/expander display.
    """
    if is_cold_start:
        return (
            "**Cold-Start Item**: This anime was not present in the training dataset interactions. "
            "Recommendation is based purely on content features (genres, synopsis) and popularity priors."
        )
    return (
        "**Not Cold-Start**: This anime has historical user ratings/interactions in the training set, "
        "enabling collaborative filtering signals."
    )


def explain_popularity_band(band: str) -> str:
    """Return explanation text for popularity percentile band.
    
    Parameters
    ----------
    band : str
        Popularity band label (e.g., 'Top 25%', 'Mid 50%', 'Long-tail').
    
    Returns
    -------
    str
        Explanation text suitable for tooltip/expander display.
    """
    explanations = {
        "Top 25%": (
            "**Top 25% Popularity**: This anime is among the most popular titles in the dataset "
            "(high user engagement, many ratings). Mainstream and widely recognized."
        ),
        "Mid 50%": (
            "**Mid 50% Popularity**: This anime has moderate popularity—not obscure, but not a blockbuster. "
            "Represents a balanced mix of recognition and niche appeal."
        ),
        "Long-tail": (
            "**Long-Tail (Bottom 25%)**: This is a less commonly rated title with niche or specialized appeal. "
            "Discovering these items can broaden your taste beyond mainstream hits."
        ),
    }
    return explanations.get(
        band,
        f"**Popularity Band: {band}**: Percentile-based grouping indicating relative user engagement in the dataset."
    )


def explain_novelty_ratio(ratio: float) -> str:
    """Return explanation text for genre novelty ratio.
    
    Parameters
    ----------
    ratio : float
        Novelty ratio (0..1 scale); higher means more genre diversity vs user history.
    
    Returns
    -------
    str
        Explanation text suitable for tooltip/expander display.
    """
    if ratio >= 0.7:
        level = "High"
        desc = "introduces many genres outside your typical preferences—great for exploration!"
    elif ratio >= 0.4:
        level = "Moderate"
        desc = "balances familiar genres with some new ones."
    else:
        level = "Low"
        desc = "stays close to genres you've already enjoyed—comfort zone pick."
    
    return (
        f"**Genre Novelty: {level} ({ratio:.2f})**: This recommendation {desc} "
        f"Novelty is measured as the proportion of item genres not heavily represented in your profile."
    )


def format_badge_tooltip(badge_key: str, badge_value) -> str:
    """Dispatch badge key to appropriate explanation function.
    
    Parameters
    ----------
    badge_key : str
        Key identifying badge type ('cold_start', 'popularity_band', 'novelty_ratio').
    badge_value
        Value of the badge (bool for cold_start, str for band, float for novelty).
    
    Returns
    -------
    str
        Formatted explanation text suitable for tooltip.
    """
    if badge_key == "cold_start":
        return explain_cold_start(bool(badge_value))
    elif badge_key == "popularity_band":
        return explain_popularity_band(str(badge_value))
    elif badge_key == "novelty_ratio":
        return explain_novelty_ratio(float(badge_value))
    return f"Badge: {badge_key} = {badge_value}"


__all__ = [
    "explain_cold_start",
    "explain_popularity_band",
    "explain_novelty_ratio",
    "format_badge_tooltip",
]
