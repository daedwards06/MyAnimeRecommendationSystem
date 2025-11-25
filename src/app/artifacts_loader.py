"""Artifact loading utilities for Phase 5 Streamlit app.

Responsibilities:
  - Deterministic seeding for reproducibility.
  - Load & prune item metadata to minimal UI-required columns.
  - Load serialized model artifacts (joblib format).
  - Load optional explanation & diversity/novelty JSON artifacts.
  - Provide a single `build_artifacts()` entry returning a dict-like bundle.

Design Notes:
  - Heavy artifacts should be cached at the Streamlit layer via `st.cache_resource`.
  - This module stays pure (no Streamlit imports) to keep testability.
  - Errors are explicit; missing critical files raises with actionable messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import random
import numpy as np
import pandas as pd
import joblib

from .constants import (
    RANDOM_SEED,
    MIN_METADATA_COLUMNS,
    METADATA_PARQUET,
)


ArtifactBundle = Dict[str, Any]


def set_determinism(seed: int = RANDOM_SEED) -> None:
    """Set seeds for reproducibility (Python + NumPy).

    Parameters
    ----------
    seed : int
        Seed value applied to Python's `random` and NumPy RNGs.
    """
    random.seed(seed)
    np.random.seed(seed)


def _safe_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Metadata parquet not found: {path}. Ensure Phase 2/4 processing generated it."
        )
    return pd.read_parquet(path)


def _prune_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Return a pruned metadata frame with required display columns.

    Falls back gracefully when canonical columns are absent by deriving:
      - title_display: first available among common title fields.
      - genres: join list-like genre fields if needed.
      - synopsis_snippet: truncated synopsis/description if snippet missing.
    """
    work = df.copy()

    # Title fallback (row-wise): ensure non-empty display title.
    title_candidates = [
        "title_display",
        "title_primary",
        "title",
        "title_english",
        "title_romaji",
        "title_japanese",
    ]
    # Ensure all candidate columns exist (to simplify row-wise fill)
    for c in title_candidates:
        if c not in work.columns:
            work[c] = None
    def _choose_title(row: pd.Series) -> str:
        for c in title_candidates:
            val = row.get(c)
            if isinstance(val, str) and val.strip() and val.strip().lower() not in {"nan", "none", "null"}:
                return val.strip()
        # Fallback to anime_id when available
        aid = row.get("anime_id")
        return f"Anime {int(aid)}" if pd.notna(aid) else "Anime"
    work["title_display"] = work.apply(_choose_title, axis=1)

    # Genres fallback: ensure pipe-delimited string
    if "genres" not in work.columns:
        genre_candidates = ["genre", "genre_list", "genres_list", "genres_raw"]
        for c in genre_candidates:
            if c in work.columns:
                val = work[c]
                if val.dtype == object:
                    work["genres"] = val.apply(
                        lambda x: "|".join(x) if isinstance(x, (list, tuple, set)) else str(x)
                    )
                else:
                    work["genres"] = val.astype(str)
                break
        if "genres" not in work.columns:
            work["genres"] = ""

    # Synopsis snippet fallback
    if "synopsis_snippet" not in work.columns:
        synopsis_candidates = [
            "synopsis_snippet",
            "synopsis",
            "synopsis_text",
            "description",
            "title_synopsis",
        ]
        snippet = None
        for c in synopsis_candidates:
            if c in work.columns:
                snippet = work[c].astype(str)
                break
        if snippet is None:
            work["synopsis_snippet"] = ""
        else:
            work["synopsis_snippet"] = snippet.apply(lambda s: (s[:240] + "…") if len(s) > 240 else s)

    # Ensure optional columns exist to avoid KeyError on selection
    for c in MIN_METADATA_COLUMNS:
        if c not in work.columns:
            work[c] = None
    return work.loc[:, MIN_METADATA_COLUMNS].copy()


def _load_models(models_dir: Path) -> Dict[str, Any]:
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    models: Dict[str, Any] = {}
    for f in models_dir.glob("*.joblib"):
        try:
            models[f.stem] = joblib.load(f)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Failed loading model '{f}': {e}") from e
    if not models:
        raise RuntimeError(f"No .joblib models found in {models_dir}")
    return models


def _load_json_glob(root: Path, pattern: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for f in root.glob(pattern):
        try:
            with f.open("r", encoding="utf-8") as fh:
                out[f.stem] = json.load(fh)
        except Exception as e:  # noqa: BLE001
            # Non-critical; skip with warning semantics via print.
            print(f"[WARN] Could not load JSON artifact {f}: {e}")
    return out


def build_artifacts(
    data_dir: str | Path = "data/processed",
    models_dir: str | Path = "models",
    reports_dir: str | Path = "reports",
) -> ArtifactBundle:
    """Load and assemble artifacts required by the Streamlit app.

    Parameters
    ----------
    data_dir : str | Path
        Directory containing processed data artifacts.
    models_dir : str | Path
        Directory containing serialized model artifacts (.joblib).
    reports_dir : str | Path
        Directory containing evaluation/explanation/diversity JSON files.

    Returns
    -------
    ArtifactBundle
        Dictionary with keys: 'metadata', 'models', 'explanations', 'diversity'.
    """
    set_determinism()

    data_dir_p = Path(data_dir)
    models_dir_p = Path(models_dir)
    reports_dir_p = Path(reports_dir)

    metadata_path = data_dir_p / METADATA_PARQUET
    metadata_raw = _safe_parquet(metadata_path)
    metadata = _prune_metadata(metadata_raw)

    models = _load_models(models_dir_p)
    explanations = _load_json_glob(reports_dir_p, "**/*explanations*.json")
    diversity = _load_json_glob(reports_dir_p, "**/*diversity*.json")

    return {
        "metadata": metadata,
        "models": models,
        "explanations": explanations,
        "diversity": diversity,
    }


__all__ = ["build_artifacts", "set_determinism"]
