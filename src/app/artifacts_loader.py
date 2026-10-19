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

import json
import logging
import os
import random
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .constants import (
    DEFAULT_KNN_MODEL_STEM,
    DEFAULT_LEARNED_RERANKER_STEM,
    DEFAULT_MF_MODEL_STEM,
    EXPECTED_MODEL_FAMILIES,
    METADATA_PARQUET,
    MIN_METADATA_COLUMNS,
    RANDOM_SEED,
)

logger = logging.getLogger(__name__)


ArtifactBundle = dict[str, Any]


class ArtifactContractError(RuntimeError):
    """Raised when required artifacts are missing or violate expected contracts."""

    def __init__(self, message: str, *, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


def _select_model_stem(
    models: dict[str, Any],
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
        q = mf_model.Q
        if q is None or not hasattr(q, "shape"):
            raise TypeError("Q is not an array-like matrix")
        it2i = mf_model.item_to_index
        i2it = mf_model.index_to_item
        if not isinstance(it2i, dict) or not isinstance(i2it, dict):
            raise TypeError("item_to_index/index_to_item must be dicts")
    except Exception as e:
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
            def _truncate(s: object) -> str:
                if not isinstance(s, str):
                    s = str(s) if s is not None and not (isinstance(s, float) and np.isnan(s)) else ""
                return (s[:240] + "…") if len(s) > 240 else s

            work["synopsis_snippet"] = snippet.apply(_truncate)

    # Ensure optional columns exist to avoid KeyError on selection
    for c in MIN_METADATA_COLUMNS:
        if c not in work.columns:
            work[c] = None
    return work.loc[:, MIN_METADATA_COLUMNS].copy()


def _load_models(models_dir: Path, *, skipped: dict[str, str] | None = None) -> dict[str, Any]:
    """Load every ``*.joblib`` in ``models_dir``.

    Files skipped for a missing dependency are recorded in ``skipped`` (stem -> reason).
    """
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    models: dict[str, Any] = {}
    if skipped is None:
        skipped = {}
    for f in models_dir.glob("*.joblib"):
        try:
            models[f.stem] = joblib.load(f)
        except ModuleNotFoundError as e:
            # Skip models that require unavailable dependencies (e.g. torch).
            # These are optional; the pipeline checks for their presence.
            logger.warning("Skipping model '%s' (missing dependency: %s)", f.name, e)
            skipped[f.stem] = f"missing dependency: {e}"
        except Exception as e:
            raise RuntimeError(f"Failed loading model '{f}': {e}") from e
    if not models:
        raise RuntimeError(f"No .joblib models found in {models_dir}")
    if skipped:
        logger.info("Skipped %d model(s) due to missing dependencies: %s", len(skipped), ", ".join(sorted(skipped)))
    return models


def _load_json_glob(root: Path, pattern: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in root.glob(pattern):
        try:
            with f.open("r", encoding="utf-8") as fh:
                out[f.stem] = json.load(fh)
        except Exception as e:
            # Non-critical; skip with warning semantics via logging.
            logger.warning(f"Could not load JSON artifact {f}: {e}")
    return out


# (family, stem prefixes, selection env var, label, preferred stem)
_OPTIONAL_FAMILIES: list[tuple[str, tuple[str, ...], str, str, str | None]] = [
    ("knn", ("item_knn", "knn"), "APP_KNN_MODEL_STEM", "kNN", DEFAULT_KNN_MODEL_STEM),
    ("synopsis_tfidf", ("synopsis_tfidf",), "APP_SYNOPSIS_TFIDF_STEM", "Synopsis TF-IDF", None),
    ("synopsis_embeddings", ("synopsis_embeddings",), "APP_SYNOPSIS_EMBEDDINGS_STEM", "Synopsis embeddings", None),
    (
        "synopsis_neural_embeddings",
        ("synopsis_neural_embeddings",),
        "APP_SYNOPSIS_NEURAL_EMBEDDINGS_STEM",
        "Synopsis neural embeddings",
        None,
    ),
    (
        "learned_reranker",
        ("learned_reranker",),
        "APP_LEARNED_RERANKER_STEM",
        "Learned reranker",
        DEFAULT_LEARNED_RERANKER_STEM,
    ),
]

FAMILY_LABELS: dict[str, str] = {"mf": "MF", **{f[0]: f[3] for f in _OPTIONAL_FAMILIES}}


def _family_entry(models_dir: Path, stem: str | None, reason: str | None = None) -> dict[str, Any]:
    size_mb: float | None = None
    if stem is not None:
        path = models_dir / f"{stem}.joblib"
        if path.exists():
            size_mb = round(path.stat().st_size / 1e6, 1)
    return {"loaded": reason is None and stem is not None, "stem": stem, "size_mb": size_mb, "reason": reason}


def _alias_optional_family(
    models: dict[str, Any],
    *,
    family: str,
    prefixes: tuple[str, ...],
    env_var: str,
    label: str,
    preferred_stem: str | None,
    models_dir: Path,
    skipped: dict[str, str],
    load_report: dict[str, dict[str, Any]],
) -> None:
    """Alias ``models[family]`` when its stem is unambiguous; record the outcome either way."""
    candidates = sorted(k for k in models if k.startswith(prefixes))
    try:
        stem = _select_model_stem(
            models,
            candidates=candidates,
            env_var=env_var,
            label=label,
            preferred_stem=preferred_stem,
        )
    except ArtifactContractError as e:
        skipped_here = sorted(s for s in skipped if s.startswith(prefixes))
        if not candidates and skipped_here:
            reason = f"{skipped_here[0]}.joblib skipped ({skipped[skipped_here[0]]})"
        else:
            reason = " ".join([str(e), *e.details])
        logger.warning("%s not loaded: %s", label, reason)
        load_report[family] = _family_entry(models_dir, None, reason)
        return
    models[family] = models[stem]
    models[f"_{family}_stem"] = stem
    load_report[family] = _family_entry(models_dir, stem)


def missing_expected_families(
    load_report: dict[str, dict[str, Any]] | None,
    expected: tuple[str, ...] = EXPECTED_MODEL_FAMILIES,
) -> list[str]:
    """Return the expected families that the load report does not mark as loaded."""
    report = load_report or {}
    return [f for f in expected if not report.get(f, {}).get("loaded", False)]


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
        Dictionary with keys: 'metadata', 'models', 'explanations', 'diversity', and
        'load_report' (model family -> loaded / stem / size_mb / reason).
    """
    set_determinism()

    data_dir_p = Path(data_dir)
    models_dir_p = Path(models_dir)
    reports_dir_p = Path(reports_dir)

    metadata_path = data_dir_p / METADATA_PARQUET
    metadata_raw = _safe_parquet(metadata_path)
    try:
        metadata = _prune_metadata(metadata_raw)
    except Exception as e:
        raise ArtifactContractError(
            "Failed to process metadata parquet.",
            details=[
                f"Error: {e}",
                f"Source: {metadata_path}",
                "Fix: regenerate data/processed/anime_metadata.parquet.",
            ],
        ) from e

    if "anime_id" not in metadata.columns or metadata["anime_id"].isna().all():
        raise ArtifactContractError(
            "Metadata is missing a valid 'anime_id' column; cannot proceed.",
            details=[
                f"Expected parquet: {metadata_path}",
                "Fix: regenerate processed metadata parquet (Phase 2/4 processing).",
            ],
        )

    skipped: dict[str, str] = {}
    models = _load_models(models_dir_p, skipped=skipped)

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
    load_report: dict[str, dict[str, Any]] = {
        "mf": _family_entry(models_dir_p, mf_stem),
    }

    # Compute mean-user vector for seed-based CF baseline (Phase 2, Task 2.1)
    # When no personalization is active, use the mean of all training user vectors
    # instead of a single arbitrary user (index 0). This makes CF contribution
    # represent average community preferences rather than one user's taste.
    if hasattr(mf_model, "P") and mf_model.P is not None:
        try:
            mean_user_P = np.mean(mf_model.P, axis=0)  # shape: [n_factors]
            models["mf_mean_user_vector"] = mean_user_P
            # Precompute mean-user scores for all items for efficiency
            global_mean = getattr(mf_model, "global_mean", 0.0)
            mean_user_scores = float(global_mean) + (mean_user_P @ mf_model.Q.T)  # shape: [n_items]
            models["mf_mean_user_scores"] = mean_user_scores.astype(np.float32)
        except Exception as e:
            logger.warning("Failed to precompute mean-user MF scores: %s", e)
            models["mf_mean_user_vector"] = None
            models["mf_mean_user_scores"] = None
    else:
        models["mf_mean_user_vector"] = None
        models["mf_mean_user_scores"] = None

    for family, prefixes, env_var, label, preferred in _OPTIONAL_FAMILIES:
        _alias_optional_family(
            models,
            family=family,
            prefixes=prefixes,
            env_var=env_var,
            label=label,
            preferred_stem=preferred,
            models_dir=models_dir_p,
            skipped=skipped,
            load_report=load_report,
        )

    explanations = _load_json_glob(reports_dir_p, "**/*explanations*.json")
    diversity = _load_json_glob(reports_dir_p, "**/*diversity*.json")

    return {
        "metadata": metadata,
        "models": models,
        "explanations": explanations,
        "diversity": diversity,
        "load_report": load_report,
    }


__all__ = [
    "FAMILY_LABELS",
    "ArtifactContractError",
    "build_artifacts",
    "missing_expected_families",
    "set_determinism",
]
