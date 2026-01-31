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
import os
import random
import numpy as np
import pandas as pd
import joblib

from .constants import (
    RANDOM_SEED,
    MIN_METADATA_COLUMNS,
    METADATA_PARQUET,
    DEFAULT_MF_MODEL_STEM,
    DEFAULT_KNN_MODEL_STEM,
)


ArtifactBundle = Dict[str, Any]


class ArtifactContractError(RuntimeError):
    """Raised when required artifacts are missing or violate expected contracts."""

    def __init__(self, message: str, *, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


def _select_model_stem(
    models: Dict[str, Any],
    *,
    candidates: list[str],
    env_var: str,
    label: str,
    preferred_stem: str | None = None,
) -> str:
    selected = os.environ.get(env_var)
    if selected:
        if selected not in models:
            raise ArtifactContractError(
                f"{label} artifact '{selected}' was requested via {env_var}, but was not found in loaded models.",
                details=[
                    f"Set {env_var} to one of: {', '.join(sorted(candidates))}" if candidates else "No candidates found.",
                ],
            )
        return selected

    if len(candidates) == 1:
        return candidates[0]

    if preferred_stem and preferred_stem in models:
        return preferred_stem

    if len(candidates) == 0:
        raise ArtifactContractError(
            f"No {label} artifacts were found.",
            details=[
                "Expected at least one .joblib file matching the naming convention.",
                f"If you have multiple artifacts, set {env_var} to choose one.",
            ],
        )

    raise ArtifactContractError(
        f"Multiple {label} artifacts were found; selection is ambiguous.",
        details=[
            f"Found: {', '.join(sorted(candidates))}",
            f"Set {env_var} to the desired artifact stem.",
        ],
    )


def _validate_mf_model(mf_model: Any, *, stem: str, models_dir: Path) -> None:
    missing: list[str] = []
    for attr in ("Q", "item_to_index", "index_to_item"):
        if not hasattr(mf_model, attr):
            missing.append(attr)
    if missing:
        raise ArtifactContractError(
            f"MF artifact '{stem}' is missing required attributes and cannot be used for inference.",
            details=[
                f"Missing attributes: {', '.join(missing)}",
                f"Expected in: {models_dir}",
                "Fix: re-export the MF model artifact with these fields (see Phase 1 / MF model contract).",
            ],
        )

    # Basic sanity checks (non-exhaustive)
    try:
        q = getattr(mf_model, "Q")
        if q is None or not hasattr(q, "shape"):
            raise TypeError("Q is not an array-like matrix")
        it2i = getattr(mf_model, "item_to_index")
        i2it = getattr(mf_model, "index_to_item")
        if not isinstance(it2i, dict) or not isinstance(i2it, dict):
            raise TypeError("item_to_index/index_to_item must be dicts")
    except Exception as e:  # noqa: BLE001
        raise ArtifactContractError(
            f"MF artifact '{stem}' failed basic contract validation.",
            details=[
                f"Error: {e}",
                f"Expected in: {models_dir}",
            ],
        ) from e


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

    if "anime_id" not in metadata.columns or metadata["anime_id"].isna().all():
        raise ArtifactContractError(
            "Metadata is missing a valid 'anime_id' column; cannot proceed.",
            details=[
                f"Expected parquet: {metadata_path}",
                "Fix: regenerate processed metadata parquet (Phase 2/4 processing).",
            ],
        )

    models = _load_models(models_dir_p)

    # --- Required: MF model selection + validation ------------------------
    mf_candidates = sorted([k for k in models.keys() if k.startswith("mf_") or k.startswith("mf")])
    mf_stem = _select_model_stem(
        models,
        candidates=mf_candidates,
        env_var="APP_MF_MODEL_STEM",
        label="MF",
        preferred_stem=DEFAULT_MF_MODEL_STEM,
    )
    mf_model = models[mf_stem]
    _validate_mf_model(mf_model, stem=mf_stem, models_dir=models_dir_p)
    models["mf"] = mf_model
    models["_mf_stem"] = mf_stem

    # Optional: kNN model alias (only if unambiguous or explicitly chosen)
    knn_candidates = sorted([k for k in models.keys() if k.startswith("item_knn") or k.startswith("knn")])
    try:
        knn_stem = _select_model_stem(
            models,
            candidates=knn_candidates,
            env_var="APP_KNN_MODEL_STEM",
            label="kNN",
            preferred_stem=DEFAULT_KNN_MODEL_STEM,
        )
        models["knn"] = models[knn_stem]
        models["_knn_stem"] = knn_stem
    except ArtifactContractError:
        # kNN is optional for Phase 1; do not block app startup.
        pass

    # Optional: synopsis TF-IDF artifact (Phase 4 semantic rerank experiment).
    # Only alias when unambiguous or explicitly chosen.
    synopsis_tfidf_candidates = sorted([k for k in models.keys() if k.startswith("synopsis_tfidf")])
    try:
        synopsis_tfidf_stem = _select_model_stem(
            models,
            candidates=synopsis_tfidf_candidates,
            env_var="APP_SYNOPSIS_TFIDF_STEM",
            label="Synopsis TF-IDF",
            preferred_stem=None,
        )
        models["synopsis_tfidf"] = models[synopsis_tfidf_stem]
        models["_synopsis_tfidf_stem"] = synopsis_tfidf_stem
    except ArtifactContractError:
        # TF-IDF is optional; do not block app startup.
        pass

    # Optional: synopsis embeddings artifact (Phase 4 semantic rerank experiment; successor to TF-IDF).
    # Only alias when unambiguous or explicitly chosen.
    synopsis_embeddings_candidates = sorted([k for k in models.keys() if k.startswith("synopsis_embeddings")])
    try:
        synopsis_embeddings_stem = _select_model_stem(
            models,
            candidates=synopsis_embeddings_candidates,
            env_var="APP_SYNOPSIS_EMBEDDINGS_STEM",
            label="Synopsis embeddings",
            preferred_stem=None,
        )
        models["synopsis_embeddings"] = models[synopsis_embeddings_stem]
        models["_synopsis_embeddings_stem"] = synopsis_embeddings_stem
    except ArtifactContractError:
        # Embeddings are optional; do not block app startup.
        pass

    # Optional: synopsis neural embeddings artifact (Phase 5 semantic generalization).
    # Built offline in WSL2; Windows runtime only loads the serialized arrays.
    synopsis_neural_candidates = sorted([k for k in models.keys() if k.startswith("synopsis_neural_embeddings")])
    try:
        synopsis_neural_stem = _select_model_stem(
            models,
            candidates=synopsis_neural_candidates,
            env_var="APP_SYNOPSIS_NEURAL_EMBEDDINGS_STEM",
            label="Synopsis neural embeddings",
            preferred_stem=None,
        )
        models["synopsis_neural_embeddings"] = models[synopsis_neural_stem]
        models["_synopsis_neural_embeddings_stem"] = synopsis_neural_stem
    except ArtifactContractError:
        # Neural embeddings are optional; do not block app startup.
        pass

    explanations = _load_json_glob(reports_dir_p, "**/*explanations*.json")
    diversity = _load_json_glob(reports_dir_p, "**/*diversity*.json")

    return {
        "metadata": metadata,
        "models": models,
        "explanations": explanations,
        "diversity": diversity,
    }


__all__ = ["build_artifacts", "set_determinism", "ArtifactContractError"]
