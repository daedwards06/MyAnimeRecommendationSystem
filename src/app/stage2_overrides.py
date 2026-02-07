"""Stage 2 ranking overrides (Phase 5 refinement).

These overrides are intentionally narrow and deterministic.

Current override:
- High-similarity override (neural): when semantic confidence is extremely high,
  relax the *format-based* (off-type / short-form) penalty so strong neighbors
  can compete in final ranking.

Important:
- Does NOT bypass ranked hygiene filters.
- Does NOT add a bonus; only removes (or clamps) a penalty term.
- Applies only in ranked paths when semantic_mode is neural.
"""

from __future__ import annotations

import math

from src.app.constants import (
    CONTENT_FIRST_ALPHA,
    CONTENT_FIRST_HYBRID_EPS,
    CONTENT_FIRST_NEURAL_MIN_SIM,
    HIGH_SIM_OVERRIDE_MODE,
    HIGH_SIM_OVERRIDE_THRESHOLD,
    QUALITY_PRIOR_COEF,
)


def should_relax_off_type_penalty(*, neural_sim: float, semantic_mode: str, browse_mode: bool = False) -> bool:
    """Return True if we should relax the off-type/episode penalty in Stage 2.

    This is a strict gate:
    - browse_mode must be False
    - semantic_mode must be "neural"
    - neural_sim must be finite and >= HIGH_SIM_OVERRIDE_THRESHOLD
    - HIGH_SIM_OVERRIDE_MODE must be "relax_off_type_penalty"
    """

    if bool(browse_mode):
        return False

    sem = str(semantic_mode or "").strip().lower()
    if sem != "neural":
        return False

    if str(HIGH_SIM_OVERRIDE_MODE or "").strip().lower() != "relax_off_type_penalty":
        return False

    try:
        s = float(neural_sim)
    except Exception:
        return False

    if not math.isfinite(s):
        return False

    return bool(s >= float(HIGH_SIM_OVERRIDE_THRESHOLD))


def relax_off_type_penalty(*, penalty: float, neural_sim: float, semantic_mode: str, browse_mode: bool = False) -> float:
    """Relax ONLY the off-type/episode penalty term.

    Minimal policy: if the override condition is met, zero out negative penalties.
    This never increases the score beyond removing a demotion.
    """

    try:
        p = float(penalty)
    except Exception:
        p = 0.0

    if not should_relax_off_type_penalty(neural_sim=neural_sim, semantic_mode=semantic_mode, browse_mode=browse_mode):
        return float(p)

    if float(p) < 0.0:
        return 0.0

    return float(p)


def should_use_content_first(hybrid_val: float, semantic_mode: str, sem_conf: str, neural_sim: float) -> bool:
    """Return True if seed-based Stage 2 should use content-first scoring.

    Conservative default (per Phase 5 experiment spec):
    - semantic_mode must include neural (implemented as semantic_mode == "neural")
    - semantic confidence tier must be "high"
    - hybrid_val must be near-zero (<= CONTENT_FIRST_HYBRID_EPS)
    - neural_sim must be >= CONTENT_FIRST_NEURAL_MIN_SIM
    """

    sem = str(semantic_mode or "").strip().lower()
    if sem != "neural":
        return False

    tier = str(sem_conf or "").strip().lower()
    if tier != "high":
        return False

    try:
        hv = float(hybrid_val)
    except Exception:
        return False

    if not math.isfinite(hv):
        return False

    eps = float(CONTENT_FIRST_HYBRID_EPS)
    # Use abs() to avoid tiny negative/positive float noise.
    if not bool(abs(hv) <= eps):
        return False

    try:
        ns = float(neural_sim)
    except Exception:
        return False
    if not math.isfinite(ns):
        return False

    return bool(ns >= float(CONTENT_FIRST_NEURAL_MIN_SIM))


def quality_prior_bonus(*, mal_score: float | None, members_count: int | None = None) -> float:
    """Return a tiny additive quality prior (guardrail) for content-first ranking.

    Uses already-available metadata signals and is capped to QUALITY_PRIOR_COEF.
    """

    coef = float(QUALITY_PRIOR_COEF)
    if coef <= 0.0:
        return 0.0

    ms = 0.0
    try:
        if mal_score is not None:
            ms = float(mal_score)
    except Exception:
        ms = 0.0

    mal_n = 0.0
    if math.isfinite(ms) and ms > 0.0:
        # MAL scores are roughly 0..10.
        mal_n = max(0.0, min(1.0, ms / 10.0))

    mem_n = 0.0
    try:
        if members_count is not None:
            mc = int(members_count)
            if mc > 0:
                # Normalize log-members to [0,1] with a gentle scale.
                mem_n = max(0.0, min(1.0, math.log10(mc + 1) / 7.0))
    except Exception:
        mem_n = 0.0

    # Prefer MAL score; members is a weak secondary stabilizer.
    prior_n = float(0.75 * mal_n + 0.25 * mem_n)
    return float(min(coef, max(0.0, coef * prior_n)))


def content_first_final_score(
    *,
    score_before: float,
    neural_sim: float,
    hybrid_cf_score: float,
    mal_score: float | None,
    members_count: int | None = None,
) -> float:
    """Compute content-first final score (seed-based Stage 2 only).

    IMPORTANT: This policy must not regress results when it triggers.

    Therefore, we apply a *positive-only* additive delta on top of the existing
    Stage 2 score rather than replacing the whole formula.

    score_after = score_before + alpha * max(0, neural_sim - hybrid_cf_score) + quality_prior
    """

    try:
        alpha = float(CONTENT_FIRST_ALPHA)
    except Exception:
        alpha = 0.70
    alpha = max(0.0, min(1.0, alpha))

    try:
        sb = float(score_before)
    except Exception:
        sb = 0.0

    ns = float(neural_sim)
    hcf = float(hybrid_cf_score)

    # Positive-only delta: avoid decreasing a candidate that already scores well.
    delta = float(alpha * max(0.0, ns - hcf))
    delta += float(quality_prior_bonus(mal_score=mal_score, members_count=members_count))

    return float(sb + delta)


__all__ = [
    "should_relax_off_type_penalty",
    "relax_off_type_penalty",
    "should_use_content_first",
    "quality_prior_bonus",
    "content_first_final_score",
]
