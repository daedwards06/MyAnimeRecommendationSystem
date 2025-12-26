"""Formatting utilities for per-item hybrid contribution explanations."""

from __future__ import annotations

from typing import Dict, Any


def format_explanation(contributions: Dict[str, Any]) -> str:
    """Format explanation dict to human-readable string.
    
    Handles both single-seed and multi-seed explanations.
    """
    parts = []
    
    # Hybrid model contributions (MF, kNN, Popularity)
    used = contributions.get("_used")
    if isinstance(used, (list, tuple)) and used:
        keys = [k for k in ("mf", "knn", "pop") if k in set(used)]
    else:
        keys = ["mf", "knn", "pop"]

    for key in keys:
        val = contributions.get(key, 0.0) * 100.0
        parts.append(f"{key} {val:.1f}%")
    
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
