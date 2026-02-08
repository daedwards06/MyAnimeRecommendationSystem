"""Formatting utilities for per-item hybrid contribution explanations.

User-facing labels
------------------
Internal component keys map to display labels as follows:

- ``mf``  → **CF** — collaborative filtering (FunkSVD matrix factorization)
- ``knn`` → **Content** — content-based signals (genre/theme overlap,
  metadata affinity, synopsis similarity, seed coverage, plus a small
  item-kNN collaborative contribution)
- ``pop`` → **Popularity** — popularity boost signal

The ``knn`` bucket aggregates both item-kNN collaborative scores and the
majority of content/metadata signals in the Stage 2 reranking formula.
Labeling it "Content" is more accurate for the user-facing explanation
because content signals dominate this component (~75%+ of its value).
"""

from __future__ import annotations

from typing import Dict, Any

# User-facing display labels for internal component keys.
# Keep internal keys unchanged for backward compatibility with tests,
# serialized explanations, and the recommender module.
_DISPLAY_LABELS: Dict[str, str] = {
    "mf": "CF",
    "knn": "Content",
    "pop": "Popularity",
}


def format_explanation(contributions: Dict[str, Any]) -> str:
    """Format explanation dict to human-readable string.
    
    Handles both single-seed and multi-seed explanations.
    """
    parts = []
    
    # Hybrid model contributions (CF, Content, Popularity)
    used = contributions.get("_used")
    if isinstance(used, (list, tuple)) and used:
        keys = [k for k in ("mf", "knn", "pop") if k in set(used)]
    else:
        keys = ["mf", "knn", "pop"]

    for key in keys:
        val = contributions.get(key, 0.0) * 100.0
        label = _DISPLAY_LABELS.get(key, key)
        parts.append(f"{label} {val:.1f}%")
    
    base_explanation = " | ".join(parts)
    
    # Multi-seed specific info
    if "seed_titles" in contributions and len(contributions.get("seed_titles", [])) > 1:
        num_matched = contributions.get("seeds_matched", 0)
        total_seeds = len(contributions["seed_titles"])
        seed_info = f" | Matches {num_matched}/{total_seeds} seeds"
        return base_explanation + seed_info
    
    return base_explanation


def format_seed_explanation(contributions: Dict[str, Any]) -> str:
    """Format detailed seed-specific explanation for multi-seed recommendations."""
    if "overlap_per_seed" not in contributions:
        return ""
    
    overlap = contributions["overlap_per_seed"]
    lines = []
    for seed_title, count in overlap.items():
        if count > 0:
            lines.append(f"• {seed_title}: {count} genre{'s' if count > 1 else ''} match")
    
    if not lines:
        return "No direct genre overlap"
    
    return "\n".join(lines)


__all__ = ["format_explanation", "format_seed_explanation"]
