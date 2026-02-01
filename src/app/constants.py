"""Phase 5 application constants.

These values centralize reproducibility and default UI/runtime parameters.
"""

from __future__ import annotations

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
