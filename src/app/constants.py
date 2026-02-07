"""Phase 5 application constants.

These values centralize reproducibility and default UI/runtime parameters.
"""

from __future__ import annotations

import os

RANDOM_SEED: int = 42

# Default UI parameters
DEFAULT_TOP_N: int = 10
MAX_TOP_N: int = 50

# Hybrid weight presets (normalized). Diversified preset illustrative; may be tuned later.
BALANCED_WEIGHTS = {"mf": 0.93078, "knn": 0.06625, "pop": 0.00297}
DIVERSITY_EMPHASIZED_WEIGHTS = {"mf": 0.80, "knn": 0.18, "pop": 0.02}

# Caching & performance targets
EMBEDDING_TTL_SECONDS: int = 24 * 3600  # 24h
MAX_INFERENCE_LATENCY_MS: int = 250
INTERACTIVE_UPDATE_LATENCY_MS: int = 500
MEMORY_BUDGET_MB: int = 512

# Metadata columns required by UI (pruned to keep memory low)
MIN_METADATA_COLUMNS = [
    "anime_id",
    "title_display",
    "title_english",
    "title_primary",
    "title",
    "title_japanese",
    "genres",
    "themes",
    "demographics",
    "synopsis",
    "synopsis_snippet",
    "poster_thumb_url",
    "streaming",
    "mal_score",
    "episodes",
    "status",
    "aired_from",
    "studios",
    "source_material",
    "type",  # Added for type filter functionality
]

# Filenames / paths (central references)
METADATA_PARQUET = "anime_metadata.parquet"
PERSONAS_JSON = "data/samples/personas.json"

# Default artifact stems (used when multiple candidates exist and env vars are not set).
# Override at runtime with APP_MF_MODEL_STEM / APP_KNN_MODEL_STEM.
DEFAULT_MF_MODEL_STEM = "mf_sgd_v2025.11.21_202756"
DEFAULT_KNN_MODEL_STEM = "item_knn_sklearn_v2025.11.21_202756"


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None or str(val).strip() == "":
        return bool(default)
    s = str(val).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if val is None or str(val).strip() == "":
        return int(default)
    try:
        return int(float(str(val).strip()))
    except Exception:
        return int(default)


def _env_float(name: str, default: float) -> float:
    val = os.environ.get(name)
    if val is None or str(val).strip() == "":
        return float(default)
    try:
        return float(str(val).strip())
    except Exception:
        return float(default)


def _env_str(name: str, default: str) -> str:
    val = os.environ.get(name)
    if val is None:
        return str(default)
    s = str(val)
    return s if s.strip() != "" else str(default)


def _normalize_seed_ranking_mode(val: str) -> str:
    s = str(val or "").strip().lower()
    if s in {"completion", "discover", "discovery"}:
        return "discovery" if s != "completion" else "completion"
    return "completion"


# ---------------------------------------------------------------------------
# Phase 5 refinement: Force-include top-K neural neighbors into Stage 1 shortlist
#
# Motivation:
# - Long-running franchises (e.g., One Piece) have very strong neural neighbors
#   that are often Movies/OVAs with episodes=1.
# - Conservative type/episodes gates can exclude these before Stage 2 rerank.
#
# Contract:
# - Only affects ranked paths when semantic_mode includes neural.
# - Must not weaken existing ranked hygiene; use it as-is.
# - Deterministic: stable sort, tie-break by anime_id.
# ---------------------------------------------------------------------------

FORCE_NEURAL_TOPK: int = _env_int("FORCE_NEURAL_TOPK", 300)
FORCE_NEURAL_MIN_SIM: float = _env_float("FORCE_NEURAL_MIN_SIM", 0.20)


# ---------------------------------------------------------------------------
# Phase 5 refinement: Stage 2 high-similarity override (neural)
#
# Motivation:
# - In ranked modes with neural semantics, extremely high cosine similarity
#   (e.g., franchise-adjacent Movies/OVAs) is a strong signal of relevance.
# - Format-based penalties (off-type / short-form) can dominate final ranking
#   and suppress these very high-confidence neighbors.
#
# Contract:
# - Ranked modes only.
# - Only when neural semantic_mode is active.
# - Does NOT bypass ranked hygiene filters.
# - Does NOT add an explicit bonus; it only relaxes a penalty term.
# ---------------------------------------------------------------------------

HIGH_SIM_OVERRIDE_THRESHOLD: float = _env_float("HIGH_SIM_OVERRIDE_THRESHOLD", 0.60)
HIGH_SIM_OVERRIDE_MODE: str = str(os.environ.get("HIGH_SIM_OVERRIDE_MODE", "relax_off_type_penalty")).strip().lower()


# ---------------------------------------------------------------------------
# Phase 5 experiment: Seed-based Stage 2 gated content-first ranking (neural)
#
# Motivation:
# - In seed-based "similar to X" mode, collaborative/hybrid coverage can be
#   missing or effectively zero for many candidates (e.g., cold-start or items
#   outside MF/KNN training alignment).
# - When that happens and neural semantic confidence is high, neural similarity
#   should lead ranking; CF signals act as a secondary stabilizer.
#
# Contract (conservative default):
# - Applies only in ranked seed-based Stage 2.
# - Activates only when semantic_mode is neural AND semantic confidence tier is
#   "high" AND hybrid_val is near-zero (<= CONTENT_FIRST_HYBRID_EPS).
# - Personalized ranking is unaffected.
#
# Notes on values:
# - CONTENT_FIRST_ALPHA=0.7 biases toward neural similarity while preserving a
#   small CF stabilizer.
# - QUALITY_PRIOR_COEF is intentionally tiny (<= 0.05) and capped; it is a
#   guardrail against obscure/low-quality items winning purely on text match.
# ---------------------------------------------------------------------------

CONTENT_FIRST_ALPHA: float = _env_float("CONTENT_FIRST_ALPHA", 0.70)
CONTENT_FIRST_HYBRID_EPS: float = _env_float("CONTENT_FIRST_HYBRID_EPS", 0.0)

# Minimum neural similarity for enabling content-first.
# Phase 5 fix: lowered from 0.55 to 0.30 so content-first fires more often.
CONTENT_FIRST_NEURAL_MIN_SIM: float = _env_float("CONTENT_FIRST_NEURAL_MIN_SIM", 0.30)

# Small stability prior (must remain tiny). Uses existing metadata signals.
QUALITY_PRIOR_COEF: float = min(0.05, max(0.0, _env_float("QUALITY_PRIOR_COEF", 0.03)))


# ---------------------------------------------------------------------------
# Phase 5 follow-up: Seed-based ranking goal mode (Completion vs Discovery)
#
# Motivation:
# - Completion: allow sequels/spin-offs to surface prominently.
# - Discovery: limit franchise-dominance deterministically using `title_overlap`.
#
# Contract:
# - Default must preserve current behavior: completion.
# - Configurable via env var SEED_RANKING_MODE (completion|discovery).
# - Discovery mode applies a post-score selection cap; it does not change scores.
# ---------------------------------------------------------------------------

SEED_RANKING_MODE: str = _normalize_seed_ranking_mode(_env_str("SEED_RANKING_MODE", "completion"))

# Define "franchise-like" based on existing title overlap heuristic.
FRANCHISE_TITLE_OVERLAP_THRESHOLD: float = _env_float("FRANCHISE_TITLE_OVERLAP_THRESHOLD", 0.50)

# Phase 5 follow-up: Discovery-mode franchise classifier upgrade.
#
# Strong match is intentionally high-precision: it uses normalized phrase
# containment (e.g., "one piece" in "one piece film z").
# Safety gates:
# - Can be disabled.
# - Disabled for very short seeds to avoid false positives.
FRANCHISE_STRONG_MATCH_ENABLED: bool = _env_bool("FRANCHISE_STRONG_MATCH_ENABLED", True)
FRANCHISE_STRONG_MATCH_MIN_SEED_LEN: int = _env_int("FRANCHISE_STRONG_MATCH_MIN_SEED_LEN", 5)

# Caps apply to the *output prefix*.
FRANCHISE_CAP_TOP20: int = _env_int("FRANCHISE_CAP_TOP20", 6)

# Optional: only meaningful when selecting/reporting top-50.
FRANCHISE_CAP_TOP50: int = _env_int("FRANCHISE_CAP_TOP50", 15)


# ---------------------------------------------------------------------------
# Phase 5 final quality fix: Stage 0 seed-conditioned candidate generation
#
# Motivation:
# - Seed-based ranked results can be dominated by off-theme catalog noise when
#   later ranking stages operate over the full catalog.
# - Stage 0 constrains the candidate universe to items plausibly related to the
#   seed before any Stage 1 admission or Stage 2 scoring runs.
#
# Contract:
# - Seed-based ranked paths only (Streamlit + golden harness).
# - Browse mode must bypass Stage 0 entirely.
# - Deterministic: stable ordering within each source and stable truncation.
# - Hygiene filters still apply (Stage 0 applies ranked hygiene exclusions).
# ---------------------------------------------------------------------------

STAGE0_NEURAL_TOPK: int = _env_int("STAGE0_NEURAL_TOPK", 1500)
STAGE0_POOL_CAP: int = _env_int("STAGE0_POOL_CAP", 3000)
STAGE0_POPULARITY_BACKFILL: int = _env_int("STAGE0_POPULARITY_BACKFILL", 100)

# Phase 5 upgrade: Stage 0 strict metadata overlap (semantic-first candidate generation).
# IMPORTANT: this replaces the previous permissive "shares >=1 genre" admission.
STAGE0_META_MIN_GENRE_OVERLAP: float = _env_float("STAGE0_META_MIN_GENRE_OVERLAP", 0.50)
STAGE0_META_MIN_THEME_OVERLAP: float = _env_float("STAGE0_META_MIN_THEME_OVERLAP", 0.50)

# Debug-only enforcement buffer: scored/shortlisted candidate counts should never
# exceed Stage 0 cap by more than this (once Stage 0 is enforced as the universe).
STAGE0_ENFORCEMENT_BUFFER: int = _env_int("STAGE0_ENFORCEMENT_BUFFER", 25)


def force_neural_enable_for_semantic_mode(semantic_mode: str) -> bool:
    """Return whether forced neural neighbors should be enabled.

    Default behavior is conservative:
      - Enabled only for neural semantic_mode.
      - Can be overridden with FORCE_NEURAL_ENABLE=[0/1].
    """

    sem = str(semantic_mode or "").strip().lower()
    default = bool(sem == "neural")
    return _env_bool("FORCE_NEURAL_ENABLE", default)
