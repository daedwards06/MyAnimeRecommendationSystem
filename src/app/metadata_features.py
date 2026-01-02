"""Lightweight metadata feature signals for ranked scoring (Phase 4 / Chunk A3).

Goal
----
Improve ranked recommendation quality (especially cold-start and "weird match" reduction)
by adding a deterministic, easy-to-reason-about metadata affinity term derived from
columns already present in `data/processed/anime_metadata.parquet`.

Design constraints
------------------
- Ranked modes only (Seed-based + Personalized); Browse mode remains metadata-only.
- Conservative: only applies a bonus to candidates when the collaborative signal is
  absent (cold-start in MF index order), unless explicitly used elsewhere.
- Deterministic: no randomness; stable parsing.
- Minimal: no new heavy dependencies; uses existing metadata columns only.

The affinity term is intentionally *weak* and only computed from columns that are
usually present for cold-start-ish titles:
- studios (strong)
- themes (moderate)
- demographics (moderate)
- producers (weak; often many-to-many)
- aired_from year proximity (weak)

We avoid using genres here to prevent double-counting since seed-based scoring already
uses genre overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Centralized weights (keep these conservative; easy to reason about).
# ---------------------------------------------------------------------------

# Per-feature contribution weights *within* the affinity score.
# Only features with data for both seed profile and candidate participate.
#
# NOTE: demographics/producers were intentionally dropped as weighted signals because
# they are often too broad (e.g., "Shounen", "Aniplex") and can introduce false
# positives in top-N. Studios + themes are more selective and easier to justify.
METADATA_AFFINITY_WEIGHTS: dict[str, float] = {
    "studios": 0.55,
    "themes": 0.35,
    "year": 0.10,
}

# Themes graded similarity guardrails.
#
# Rationale: themes can be noisy/generic; we require *both* a minimum overlap count
# and a minimum graded similarity before themes contribute any positive affinity.
# This prevents a single generic theme from triggering a full bonus.
#
# Similarity definition: overlap ratio = |A∩B| / min(|A|, |B|)
METADATA_AFFINITY_THEMES_MIN_OVERLAP_COUNT: int = 2
METADATA_AFFINITY_THEMES_MIN_OVERLAP_RATIO: float = 0.34

# Back-compat export: older sessions referenced a Jaccard threshold.
# Keep the constant name to avoid churn; it now mirrors the overlap-ratio threshold.
METADATA_AFFINITY_THEMES_MIN_JACCARD: float = METADATA_AFFINITY_THEMES_MIN_OVERLAP_RATIO

# Year proximity window: similarity = max(0, 1 - |year-seed_year|/window).
METADATA_AFFINITY_YEAR_WINDOW: int = 10

# Overall coefficient added to the existing seed-based score for cold-start candidates
# (those without a hybrid/MF-aligned score in the current scoring path).
METADATA_AFFINITY_COLD_START_COEF: float = 0.08

# Much smaller coefficient for candidates that already have a hybrid/MF-aligned score.
# This is intended as a gentle rerank to reduce occasional "weird match" items.
METADATA_AFFINITY_TRAINED_COEF: float = 0.01

# Optional: if used to nudge MF-personalized rankings toward selected seeds.
METADATA_AFFINITY_PERSONALIZED_COEF: float = 0.02

# Phase 4 Option A refinement (2025-12-31): tiny demographics overlap tie-break.
#
# Constraints:
# - Never use demographics for filtering/shortlisting (missingness is high).
# - Never penalize missing demographics.
# - Apply only when BOTH seed and candidate have non-empty demographics.
#
# Rationale:
# - Demographics are often missing, especially for non-TV types.
# - When present for both items, overlap (e.g., "Shounen") can be a safe, tiny
#   deterministic tie-breaker in Stage 2 rerank.
METADATA_DEMOGRAPHICS_OVERLAP_TIEBREAK_BONUS: float = 0.002

# Phase 4 ranked scoring polish (2026-01-01): tiny themes tie-break bonus (Stage 2 only).
#
# Constraints:
# - No candidate admission changes (Stage 1 unchanged).
# - Never penalize missing themes.
# - Only compute when BOTH seed and candidate have non-empty themes.
#
# Theme overlap definition (directional): |themes_seed ∩ themes_candidate| / |themes_seed|
# We cap overlap contribution to avoid overweighting generic theme matches.
THEME_STAGE2_COEF: float = 0.004
THEME_STAGE2_CAP: float = 0.50

# Optional safety gate: only allow theme tie-break if the candidate is already
# plausibly related via semantic similarity OR via the genre-overlap gate.
THEME_STAGE2_MIN_SEM_SIM: float = 0.10
THEME_STAGE2_GENRE_GATE_OVERLAP: float = 0.50


@dataclass(frozen=True)
class SeedMetadataProfile:
    studios: frozenset[str]
    themes: frozenset[str]
    demographics: frozenset[str]
    producers: frozenset[str]
    seed_year_mean: Optional[float]


def _coerce_str_set(val: Any) -> set[str]:
    """Coerce metadata values to a normalized set of strings.

    Handles:
      - numpy arrays / lists
      - pipe-delimited strings
      - scalars
    """
    if val is None:
        return set()

    # pandas NA / numpy nan
    try:
        if pd.isna(val):
            return set()
    except Exception:
        pass

    # Strings: allow pipe-delimited format.
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return set()
        if "|" in s:
            return {x.strip() for x in s.split("|") if x and x.strip()}
        return {s}

    # Iterables (including numpy arrays)
    if isinstance(val, (list, tuple, set)):
        it: Iterable[Any] = val
    else:
        # numpy arrays expose .tolist(); treat anything iterable-but-not-string as a list
        try:
            tolist = getattr(val, "tolist", None)
            if callable(tolist):
                it = tolist()
            else:
                it = None  # type: ignore[assignment]
        except Exception:
            it = None  # type: ignore[assignment]

    if it is not None:
        out: set[str] = set()
        for x in it:
            if x is None:
                continue
            sx = str(x).strip()
            if sx:
                out.add(sx)
        return out

    # Fallback scalar
    sx = str(val).strip()
    return {sx} if sx else set()


def _coerce_year(val: Any) -> Optional[int]:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass

    # Common in this repo: ISO string like '2017-07-07T00:00:00+00:00'
    if isinstance(val, str):
        s = val.strip()
        if len(s) >= 4 and s[:4].isdigit():
            return int(s[:4])
        return None

    # pandas Timestamp / datetime
    try:
        ts = pd.to_datetime(val, errors="coerce")
        if pd.isna(ts):
            return None
        return int(ts.year)
    except Exception:
        return None


def build_seed_metadata_profile(metadata: pd.DataFrame, *, seed_ids: list[int]) -> SeedMetadataProfile:
    """Aggregate seed metadata into a simple profile.

    Missing columns are treated as empty.
    """
    if metadata is None or metadata.empty or not seed_ids or "anime_id" not in metadata.columns:
        return SeedMetadataProfile(
            studios=frozenset(),
            themes=frozenset(),
            demographics=frozenset(),
            producers=frozenset(),
            seed_year_mean=None,
        )

    seed_set = {int(x) for x in seed_ids}

    studios: set[str] = set()
    themes: set[str] = set()
    demographics: set[str] = set()
    producers: set[str] = set()
    years: list[int] = []

    # Stable order for determinism.
    work = metadata.loc[metadata["anime_id"].astype(int).isin(seed_set)].sort_values("anime_id", kind="mergesort")

    for _, row in work.iterrows():
        if "studios" in work.columns:
            studios.update(_coerce_str_set(row.get("studios")))
        if "themes" in work.columns:
            themes.update(_coerce_str_set(row.get("themes")))
        if "demographics" in work.columns:
            demographics.update(_coerce_str_set(row.get("demographics")))
        if "producers" in work.columns:
            producers.update(_coerce_str_set(row.get("producers")))
        if "aired_from" in work.columns:
            y = _coerce_year(row.get("aired_from"))
            if y is not None:
                years.append(int(y))

    seed_year_mean: Optional[float]
    if years:
        seed_year_mean = float(sum(years) / len(years))
    else:
        seed_year_mean = None

    return SeedMetadataProfile(
        studios=frozenset(studios),
        themes=frozenset(themes),
        demographics=frozenset(demographics),
        producers=frozenset(producers),
        seed_year_mean=seed_year_mean,
    )


def demographics_overlap_tiebreak_bonus(
    seed_demographics: Any,
    candidate_demographics: Any,
    *,
    bonus: float = METADATA_DEMOGRAPHICS_OVERLAP_TIEBREAK_BONUS,
) -> float:
    """Return a tiny bonus if demographics overlap and BOTH sides are non-empty.

    This is a tie-breaker only. Missing demographics never incur a penalty.
    """
    seed_set = _coerce_str_set(seed_demographics)
    cand_set = _coerce_str_set(candidate_demographics)
    if not seed_set or not cand_set:
        return 0.0
    if seed_set.isdisjoint(cand_set):
        return 0.0
    return float(bonus)


def theme_stage2_tiebreak_bonus(
    theme_overlap: Optional[float],
    *,
    semantic_sim: float,
    genre_overlap: float,
    coef: float = THEME_STAGE2_COEF,
    cap: float = THEME_STAGE2_CAP,
    min_sem_sim: float = THEME_STAGE2_MIN_SEM_SIM,
    genre_gate_overlap: float = THEME_STAGE2_GENRE_GATE_OVERLAP,
) -> float:
    """Return a tiny Stage 2 additive bonus based on theme overlap.

    This is a tie-breaker only. Missing themes never incur a penalty.

    Args:
        theme_overlap: Directional overlap ratio, defined as
            |themes_seed ∩ themes_candidate| / |themes_seed|.
            Should be None when seed or candidate themes are missing/empty.
        semantic_sim: Candidate's semantic similarity to the seed (used only as an
            optional safety gate).
        genre_overlap: Candidate's genre overlap with seed profile (used only as an
            optional safety gate).
    """
    if theme_overlap is None:
        return 0.0

    try:
        ov = float(theme_overlap)
    except Exception:
        return 0.0

    if ov <= 0.0:
        return 0.0

    # Optional safety: only boost if semantic similarity is non-trivial OR the
    # candidate already passed the genre overlap gate.
    try:
        sem_ok = float(semantic_sim) >= float(min_sem_sim)
    except Exception:
        sem_ok = False
    try:
        genre_ok = float(genre_overlap) >= float(genre_gate_overlap)
    except Exception:
        genre_ok = False

    if not (sem_ok or genre_ok):
        return 0.0

    capped = min(float(ov), float(cap))
    if capped <= 0.0:
        return 0.0
    return float(coef) * float(capped)


def _binary_overlap(a: frozenset[str], b: set[str]) -> Optional[float]:
    if not a or not b:
        return None
    return 1.0 if (a.intersection(b)) else 0.0


def _weak_overlap_ratio(a: frozenset[str], b: set[str]) -> Optional[float]:
    """Overlap ratio: |A∩B| / min(|A|, |B|)."""
    if not a or not b:
        return None
    denom = min(len(a), len(b))
    if denom <= 0:
        return None
    return float(len(a.intersection(b)) / denom)


def _jaccard(a: frozenset[str], b: set[str]) -> tuple[Optional[float], int]:
    """Jaccard similarity and raw overlap count.

    Returns:
      (similarity, overlap_count)
    """
    if not a or not b:
        return None, 0
    inter = a.intersection(b)
    overlap = int(len(inter))
    if overlap <= 0:
        return 0.0, 0
    union = len(a.union(b))
    if union <= 0:
        return None, overlap
    return float(overlap / union), overlap


def _year_similarity(seed_year_mean: Optional[float], candidate_year: Optional[int]) -> Optional[float]:
    if seed_year_mean is None or candidate_year is None:
        return None
    window = float(METADATA_AFFINITY_YEAR_WINDOW)
    if window <= 0:
        return None
    diff = abs(float(candidate_year) - float(seed_year_mean))
    return max(0.0, 1.0 - (diff / window))


def compute_metadata_affinity(profile: SeedMetadataProfile, candidate_row: Mapping[str, Any]) -> float:
    """Compute 0..1 affinity of a candidate to the seed metadata profile.

    Only features with data for both sides participate (no penalty for missing data).
    """
    cand_studios = _coerce_str_set(candidate_row.get("studios"))
    cand_themes = _coerce_str_set(candidate_row.get("themes"))
    cand_year = _coerce_year(candidate_row.get("aired_from"))

    studios_sim = _binary_overlap(profile.studios, cand_studios)

    # Themes: graded similarity with conservative thresholding.
    themes_sim_raw = _weak_overlap_ratio(profile.themes, cand_themes)
    themes_overlap = int(len(profile.themes.intersection(cand_themes))) if profile.themes and cand_themes else 0
    themes_sim: Optional[float]
    if themes_sim_raw is None:
        themes_sim = None
    else:
        # Conservative: themes only contribute when similarity is meaningful.
        if themes_overlap < int(METADATA_AFFINITY_THEMES_MIN_OVERLAP_COUNT):
            themes_sim = 0.0
        elif float(themes_sim_raw) < float(METADATA_AFFINITY_THEMES_MIN_OVERLAP_RATIO):
            themes_sim = 0.0
        else:
            themes_sim = float(themes_sim_raw)

    sims: dict[str, Optional[float]] = {
        "studios": studios_sim,
        "themes": themes_sim,
        "year": _year_similarity(profile.seed_year_mean, cand_year),
    }

    # Conservative categorical gate.
    # - Studios is the strong binary gate.
    # - Themes can also pass the gate, but only when they clear the min-overlap + min-sim thresholds.
    # - Year proximity may contribute only after a categorical gate passes.
    studios_pass = sims.get("studios") == 1.0
    themes_pass = (themes_sim is not None) and (float(themes_sim) > 0.0)
    if not (studios_pass or themes_pass):
        return 0.0

    total_w = 0.0
    total = 0.0
    for k, sim in sims.items():
        if sim is None:
            continue
        w = float(METADATA_AFFINITY_WEIGHTS.get(k, 0.0))
        if w <= 0.0:
            continue
        total_w += w
        total += w * float(sim)

    if total_w <= 0.0:
        return 0.0

    # Clamp defensively.
    out = total / total_w
    if out < 0.0:
        return 0.0
    if out > 1.0:
        return 1.0
    return float(out)


__all__ = [
    "SeedMetadataProfile",
    "METADATA_AFFINITY_WEIGHTS",
    "METADATA_AFFINITY_YEAR_WINDOW",
    "METADATA_AFFINITY_THEMES_MIN_OVERLAP_COUNT",
    "METADATA_AFFINITY_THEMES_MIN_OVERLAP_RATIO",
    "METADATA_AFFINITY_THEMES_MIN_JACCARD",
    "METADATA_AFFINITY_COLD_START_COEF",
    "METADATA_AFFINITY_TRAINED_COEF",
    "METADATA_AFFINITY_PERSONALIZED_COEF",
    "METADATA_DEMOGRAPHICS_OVERLAP_TIEBREAK_BONUS",
    "THEME_STAGE2_COEF",
    "THEME_STAGE2_CAP",
    "THEME_STAGE2_MIN_SEM_SIM",
    "THEME_STAGE2_GENRE_GATE_OVERLAP",
    "build_seed_metadata_profile",
    "demographics_overlap_tiebreak_bonus",
    "theme_stage2_tiebreak_bonus",
    "compute_metadata_affinity",
]
