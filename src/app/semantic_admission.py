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

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal

STAGE1_TITLE_OVERLAP_ALWAYS_ADMIT: float = 0.50

# Keep the existing Phase 4 stabilization default.
STAGE1_HIGH_GENRE_OVERLAP: float = 0.50

# Avoid admitting totally off-theme items when |Gseed| is large.
STAGE1_MIN_GENRE_FLOOR: float = 0.20

# Theme overlap can relax genre requirement only in Lane A.
# Start at 1-of-3 themes.
STAGE1_THEME_MIN_OVERLAP: float = 0.33

# ---------------------------------------------------------------------------
# Phase 5 (targeted): demographic-aware semantic admission override
# ---------------------------------------------------------------------------
#
# Problem: For some long-running shounen seeds, seed-conditioned genre overlap
# gates can prevent semantic neighbors from entering the Stage 1 shortlist,
# making the neural semantic signal appear inert.
#
# Constraints:
# - Deterministic and sparse: only applies when BOTH seed and candidate have
#   non-empty demographics.
# - Never penalize missing demographics.
# - Experiment scope: shounen only.
#
# NOTE: This override does NOT bypass global Stage 1 hygiene/type gates; callers
# must still enforce those separately (as they already do).
STAGE1_DEMO_SHOUNEN_TOKEN: str = "shounen"

# Conservative starting point for neural sentence-transformer similarity.
# If diagnostics still show the neural semantic pool is empty/inert for shounen
# seeds, consider lowering to ~0.15.
STAGE1_DEMO_SHOUNEN_MIN_SIM_NEURAL: float = 0.20


AdmissionLane = Literal[
    "title",
    "B",
    "A",
    "demo_shounen",
    "blocked_low_sim",
    "blocked_overlap",
]


@dataclass(frozen=True)
class Stage1AdmissionDecision:
    admitted: bool
    lane: AdmissionLane
    used_theme_override: bool
    low_genre_overlap: float


def normalize_demographics_tokens(val: Any) -> set[str]:
    """Return a normalized set of demographic tokens.

    Handles:
      - list/tuple/set-like
      - pipe-delimited strings
      - scalars/NA

    Normalization:
      - case-fold to lowercase
      - trim whitespace
      - unicode normalize (NFKD) and drop combining marks

    The override experiment matches only the canonical token
    `STAGE1_DEMO_SHOUNEN_TOKEN`.
    """
    if val is None:
        return set()

    # Avoid importing pandas here; handle common NA spellings defensively.
    try:
        if isinstance(val, float) and val != val:  # NaN
            return set()
    except Exception:
        pass

    def _norm_one(x: Any) -> str | None:
        if x is None:
            return None
        s = str(x).strip()
        if not s or s.lower() in {"nan", "none", "null"}:
            return None

        # Fold diacritics deterministically.
        try:
            s_nfkd = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s_nfkd if not unicodedata.combining(ch))
        except Exception:
            pass

        s = " ".join(s.split()).lower()

        # Canonicalize common romanizations.
        if s in {"shounen", "shonen"}:
            return STAGE1_DEMO_SHOUNEN_TOKEN
        if s in {"shoujo", "shojo"}:
            return "shoujo"
        if s == "seinen":
            return "seinen"
        if s == "josei":
            return "josei"
        return s

    # Strings: allow pipe-delimited format.
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return set()
        parts: Iterable[Any]
        if "|" in s:
            parts = [p for p in s.split("|")]
        else:
            parts = [s]
        out: set[str] = set()
        for p in parts:
            n = _norm_one(p)
            if n:
                out.add(n)
        return out

    # Iterables (including numpy arrays via .tolist())
    if isinstance(val, (list, tuple, set, frozenset)):
        it: Iterable[Any] = val
    else:
        try:
            tolist = getattr(val, "tolist", None)
            it = tolist() if callable(tolist) else None  # type: ignore[assignment]
        except Exception:
            it = None  # type: ignore[assignment]

    if it is not None:
        out: set[str] = set()
        for x in it:
            n = _norm_one(x)
            if n:
                out.add(n)
        return out

    # Fallback scalar
    n = _norm_one(val)
    return {n} if n else set()


def adaptive_low_genre_overlap(seed_genres_count: int, *, min_floor: float = STAGE1_MIN_GENRE_FLOOR) -> float:
    if int(seed_genres_count) <= 0:
        return float(min_floor)
    return float(max(1.0 / float(seed_genres_count), float(min_floor)))


def theme_overlap_ratio(
    seed_themes: frozenset[str] | set[str],
    candidate_themes: set[str],
) -> float | None:
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
    theme_overlap: float | None,
    seed_demographics: Any = None,
    candidate_demographics: Any = None,
    demo_shounen_min_sim: float | None = None,
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

    # Phase 5 targeted override: shounen↔shounen semantic admission.
    #
    # Important: This override uses its own similarity threshold (and may
    # therefore admit candidates even when below the global min_sim), because
    # the failure mode we are addressing is that strict global gates can make
    # the neural semantic signal inert for long-running shounen seeds.
    if demo_shounen_min_sim is not None:
        seed_demo = normalize_demographics_tokens(seed_demographics)
        cand_demo = normalize_demographics_tokens(candidate_demographics)
        if (
            (STAGE1_DEMO_SHOUNEN_TOKEN in seed_demo)
            and (STAGE1_DEMO_SHOUNEN_TOKEN in cand_demo)
            and (fsim >= float(demo_shounen_min_sim))
        ):
            low_genre = float(high_genre_overlap)
            if int(num_seeds) == 1:
                low_genre = adaptive_low_genre_overlap(int(seed_genres_count))
            return Stage1AdmissionDecision(
                admitted=True,
                lane="demo_shounen",
                used_theme_override=False,
                low_genre_overlap=float(low_genre),
            )

    # Too low similarity for either standard lane.
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
