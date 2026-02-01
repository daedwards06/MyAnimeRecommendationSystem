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


def force_neural_enable_for_semantic_mode(semantic_mode: str) -> bool:
    """Return whether forced neural neighbors should be enabled.

    Default behavior is conservative:
      - Enabled only for neural semantic_mode.
      - Can be overridden with FORCE_NEURAL_ENABLE=[0/1].
    """

    sem = str(semantic_mode or "").strip().lower()
    default = bool(sem == "neural")
    return _env_bool("FORCE_NEURAL_ENABLE", default)
