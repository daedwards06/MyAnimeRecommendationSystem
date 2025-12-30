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

    sims: dict[str, Optional[float]] = {
        "studios": _binary_overlap(profile.studios, cand_studios),
        "themes": _binary_overlap(profile.themes, cand_themes),
        "year": _year_similarity(profile.seed_year_mean, cand_year),
    }

    # Conservative gating: require at least one categorical overlap signal.
    # This prevents year-only proximity from introducing unrelated items.
    if sims.get("studios") != 1.0 and sims.get("themes") != 1.0:
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
    "METADATA_AFFINITY_COLD_START_COEF",
    "METADATA_AFFINITY_TRAINED_COEF",
    "METADATA_AFFINITY_PERSONALIZED_COEF",
    "build_seed_metadata_profile",
    "compute_metadata_affinity",
]
