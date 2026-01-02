"""Stage 1 semantic admission policy (Phase 4 refinement).

Goal
----
Preserve Tokyo Ghoul improvements (avoid off-theme semantic neighbors dominating
shortlists) while reducing false negatives on other seeds.

Design constraints
------------------
- Deterministic: no randomness, stable thresholds.
- Themes are never a hard gate and never penalize missingness.
- Themes may only act as an optional confirmer in the *high semantic confidence*
  lane.

Policy
------
Always admit if title_overlap >= STAGE1_TITLE_OVERLAP_ALWAYS_ADMIT.

Lane B (standard): admit if semantic_sim >= min_sim and genre_overlap >= HIGH.

Lane A (precision rescue): if Lane B fails, admit if semantic_sim >= high_sim
and (genre_overlap >= adaptive_low_genre_overlap OR theme_overlap >= THEME_MIN).

For single-seed queries:
  adaptive_low_genre_overlap = max(1 / |Gseed|, MIN_GENRE_FLOOR)

For multi-seed queries, adaptive_low_genre_overlap defaults to HIGH.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal

STAGE1_TITLE_OVERLAP_ALWAYS_ADMIT: float = 0.50

# Keep the existing Phase 4 stabilization default.
STAGE1_HIGH_GENRE_OVERLAP: float = 0.50

# Avoid admitting totally off-theme items when |Gseed| is large.
STAGE1_MIN_GENRE_FLOOR: float = 0.20

# Theme overlap can relax genre requirement only in Lane A.
# Start at 1-of-3 themes.
STAGE1_THEME_MIN_OVERLAP: float = 0.33


AdmissionLane = Literal[
    "title",
    "B",
    "A",
    "blocked_low_sim",
    "blocked_overlap",
]


@dataclass(frozen=True)
class Stage1AdmissionDecision:
    admitted: bool
    lane: AdmissionLane
    used_theme_override: bool
    low_genre_overlap: float


def adaptive_low_genre_overlap(seed_genres_count: int, *, min_floor: float = STAGE1_MIN_GENRE_FLOOR) -> float:
    if int(seed_genres_count) <= 0:
        return float(min_floor)
    return float(max(1.0 / float(seed_genres_count), float(min_floor)))


def theme_overlap_ratio(
    seed_themes: frozenset[str] | set[str],
    candidate_themes: set[str],
) -> Optional[float]:
    if not seed_themes or not candidate_themes:
        return None
    denom = len(seed_themes)
    if denom <= 0:
        return None
    return float(len(set(seed_themes) & set(candidate_themes)) / float(denom))


def stage1_semantic_admission(
    *,
    semantic_sim: float,
    min_sim: float,
    high_sim: float,
    genre_overlap: float,
    title_overlap: float,
    seed_genres_count: int,
    num_seeds: int,
    theme_overlap: Optional[float],
    high_genre_overlap: float = STAGE1_HIGH_GENRE_OVERLAP,
    theme_min_overlap: float = STAGE1_THEME_MIN_OVERLAP,
    title_always_admit: float = STAGE1_TITLE_OVERLAP_ALWAYS_ADMIT,
) -> Stage1AdmissionDecision:
    # Always admit franchise/self-title neighbors.
    if float(title_overlap) >= float(title_always_admit):
        return Stage1AdmissionDecision(
            admitted=True,
            lane="title",
            used_theme_override=False,
            low_genre_overlap=float(high_genre_overlap),
        )

    fsim = float(semantic_sim)
    fmin = float(min_sim)
    fhigh = float(high_sim)
    fgenre = float(genre_overlap)

    # Standard admission first.
    if fsim >= fmin and fgenre >= float(high_genre_overlap):
        return Stage1AdmissionDecision(
            admitted=True,
            lane="B",
            used_theme_override=False,
            low_genre_overlap=float(high_genre_overlap),
        )

    # Too low similarity for either lane.
    if fsim < fmin:
        return Stage1AdmissionDecision(
            admitted=False,
            lane="blocked_low_sim",
            used_theme_override=False,
            low_genre_overlap=float(high_genre_overlap),
        )

    # Lane A rescue: only when semantic confidence is high.
    low_genre = float(high_genre_overlap)
    if int(num_seeds) == 1:
        low_genre = adaptive_low_genre_overlap(int(seed_genres_count))

    theme_ok = (theme_overlap is not None) and (float(theme_overlap) >= float(theme_min_overlap))
    genre_ok_low = fgenre >= low_genre

    if fsim >= fhigh and (genre_ok_low or theme_ok):
        return Stage1AdmissionDecision(
            admitted=True,
            lane="A",
            used_theme_override=bool(theme_ok and (not genre_ok_low)),
            low_genre_overlap=float(low_genre),
        )

    return Stage1AdmissionDecision(
        admitted=False,
        lane="blocked_overlap",
        used_theme_override=False,
        low_genre_overlap=float(low_genre),
    )
