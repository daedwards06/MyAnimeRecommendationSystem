"""Formatting utilities for per-item recommendation explanations.

Two outputs per card:

- ``explain_in_words`` — the plain-language sentence shown on the card.
- ``format_explanation`` — the truthful-shares "signal breakdown" line, shown
  under "More details".

User-facing labels
------------------
- ``mf``      → **Matrix factorization** — FunkSVD collaborative filtering
- ``knn``     → **Similar-item CF** — item-kNN collaborative filtering over the
  user-item matrix (an item-item signal, not a content one)
- ``content`` → **Content** — genre/theme overlap, seed coverage, metadata
  affinity and synopsis similarity from the seed-based reranker
- ``pop``     → **Popularity** — popularity boost signal
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.app.synopsis_neural_embeddings import SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD
from src.app.synopsis_tfidf import SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD

_DISPLAY_LABELS: dict[str, str] = {
    "mf": "Matrix factorization",
    "knn": "Similar-item CF",
    "content": "Content",
    "pop": "Popularity",
}
_COMPONENT_ORDER: tuple[str, ...] = ("mf", "knn", "content", "pop")

# Popularity percentile is 0 = most popular (see src/app/badges.py).
_WELL_KNOWN_MAX_PCT = 0.10
_HIDDEN_GEM_MIN_PCT = 0.50


def format_explanation(contributions: dict[str, Any]) -> str:
    """Format the per-component share line (the "signal breakdown").

    Handles both single-seed and multi-seed explanations.
    """
    parts = []

    used = contributions.get("_used")
    if isinstance(used, (list, tuple)) and used:
        keys = [k for k in _COMPONENT_ORDER if k in set(used)]
    else:
        keys = [k for k in _COMPONENT_ORDER if k in contributions]

    for key in keys:
        val = contributions.get(key, 0.0) * 100.0
        label = _DISPLAY_LABELS.get(key, key)
        parts.append(f"{label} {val:.1f}%")

    base_explanation = " | ".join(parts)

    if "seed_titles" in contributions and len(contributions.get("seed_titles", [])) > 1:
        num_matched = contributions.get("seeds_matched", 0)
        total_seeds = len(contributions["seed_titles"])
        seed_info = f" | Matches {num_matched}/{total_seeds} seeds"
        return base_explanation + seed_info

    return base_explanation


def _share(contributions: dict[str, Any], key: str) -> float:
    """Share of ``key``; 0 when the component was not used for this item."""
    used = contributions.get("_used")
    if isinstance(used, (list, tuple)) and key not in used:
        return 0.0
    try:
        return float(contributions.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _join_and(items: Sequence[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def _genre_clause(
    contributions: dict[str, Any], seed_titles: Sequence[str], item_genres: Sequence[str]
) -> str | None:
    seed_genres = contributions.get("seed_genres")
    if not isinstance(seed_genres, dict) or not item_genres:
        return None
    best_title, best_shared = None, []
    for title in seed_titles:
        genres = seed_genres.get(title) or ()
        shared = [g for g in item_genres if g in genres]
        if len(shared) > len(best_shared):
            best_title, best_shared = title, shared
    if not best_shared:
        return None
    return f"shares {_join_and(best_shared[:2])} with {best_title}"


def _story_clause(contributions: dict[str, Any]) -> str | None:
    neural = float(contributions.get("synopsis_neural_sim", 0.0) or 0.0)
    tfidf = float(contributions.get("synopsis_tfidf_sim", 0.0) or 0.0)
    if neural >= SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD or tfidf >= SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD:
        return "very similar story"
    return None


def _cf_clause(contributions: dict[str, Any], seed_titles: Sequence[str]) -> str | None:
    mf, knn = _share(contributions, "mf"), _share(contributions, "knn")
    if max(mf, knn) <= 0.0:
        return None
    if knn >= mf:
        if not seed_titles:
            return "fans of anime you rated highly also rate it highly"
        who = _join_and(list(seed_titles)) if len(seed_titles) <= 2 else "your seeds"
        return f"fans of {who} also rate it highly"
    # The MF term is a profile or mean-user vector; it never depends on the seeds.
    if contributions.get("has_profile"):
        return "matches the taste of viewers who rate like you"
    return "rated well by MAL viewers overall"


def _popularity_clause(contributions: dict[str, Any]) -> str | None:
    pct = contributions.get("popularity_pct")
    if pct is None:
        return None
    pct = float(pct)
    if pct < _WELL_KNOWN_MAX_PCT and _share(contributions, "pop") > 0.0:
        return "a well-known pick"
    # Describes the item rather than crediting the popularity signal, so no share gate.
    if pct >= _HIDDEN_GEM_MIN_PCT:
        return "a hidden gem"
    return None


def explain_in_words(
    contributions: dict[str, Any],
    seed_titles: Sequence[str] | None,
    item_genres: Sequence[str] | None,
) -> str:
    """Plain-language reason for a recommendation, e.g.
    "Shares Sci-Fi and Suspense with Steins;Gate · very similar story · fans of
    Steins;Gate also rate it highly".

    Up to three clauses, in a fixed priority order (genres, story, collaborative,
    popularity). Content clauses need a non-zero content share; the collaborative
    clause names whichever of MF / similar-item CF has the larger share. Multi-seed
    runs append "Matches N of M seeds". Returns "" when nothing applies.
    """
    seeds = [str(t) for t in (seed_titles or [])]
    genres = [str(g) for g in (item_genres or [])]

    candidates: list[str | None] = []
    if _share(contributions, "content") > 0.0:
        candidates.append(_genre_clause(contributions, seeds, genres))
        candidates.append(_story_clause(contributions))
    candidates.append(_cf_clause(contributions, seeds))
    candidates.append(_popularity_clause(contributions))

    clauses = [c for c in candidates if c][:3]
    if len(seeds) > 1:
        matched = int(contributions.get("seeds_matched", 0) or 0)
        clauses.append(f"Matches {matched} of {len(seeds)} seeds")
    if not clauses:
        return ""
    sentence = " · ".join(clauses)
    return sentence[0].upper() + sentence[1:]


def format_seed_explanation(contributions: dict[str, Any]) -> str:
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


__all__ = ["explain_in_words", "format_explanation", "format_seed_explanation"]
