"""Deterministic synopsis embeddings artifact + cosine similarity utilities.

Phase 4 (A4 experiment): successor to TF-IDF synopsis similarity.

Design constraints
------------------
- Deterministic: stable item ordering (anime_id mergesort), fixed preprocessing,
  CPU inference, stable tie-breaking in downstream ranking.
- Ranked modes only: seed-conditioned signal for Stage 1 shortlist + Stage 2 rerank.
- Lightweight artifact: float32, L2-normalized embeddings for cosine similarity.

Text policy
-----------
Uses existing text fields only.
- Prefer `synopsis_snippet` *only if* it matches the deterministic truncation of
  `synopsis` (when synopsis exists).
- Otherwise use the deterministic truncation of `synopsis`.

Deterministic truncation rule (mirrors `src.app.artifacts_loader` fallback):
- max_chars=240
- if len(text) > max_chars: text[:max_chars] + "…"
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Centralized constants (Phase 4 embeddings experiment)
# ---------------------------------------------------------------------------

SYNOPSIS_EMBEDDINGS_SCHEMA: str = "synopsis_embeddings_v1"

# Rerank thresholds (cosine similarity on L2-normalized embeddings).
#
# Notes:
# - With the local TF-IDF+SVD embedding backend, cosine similarities tend to be
#   lower than sentence-transformer cosines.
# - Keep this conservative, but low enough to actually activate in practice.
SYNOPSIS_EMBEDDINGS_MIN_SIM: float = 0.10

# Dual-threshold override: allow off-type/short candidates only at very high
# similarity; otherwise rely on the conservative gate + penalties.
SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD: float = 0.35

# Keep the same minimum-episodes heuristic as TF-IDF for consistency.
SYNOPSIS_EMBEDDINGS_MIN_EPISODES: int = 12

# If admitted via HIGH_SIM_THRESHOLD override, apply a small deterministic penalty
# so same-type TV remains preferred unless similarity is genuinely strong.
SYNOPSIS_EMBEDDINGS_OFFTYPE_HIGH_SIM_PENALTY: float = 0.01

# Additive rerank coefficients (kept small; Stage 1 shortlist is the main effect).
SYNOPSIS_EMBEDDINGS_COLD_START_COEF: float = 0.80
SYNOPSIS_EMBEDDINGS_TRAINED_COEF: float = 0.25
SYNOPSIS_EMBEDDINGS_PERSONALIZED_COEF: float = 0.25

# Conservative short-form penalty when the base gate fails.
SYNOPSIS_EMBEDDINGS_OFFTYPE_SHORT_PENALTY_BASE: float = 0.60
SYNOPSIS_EMBEDDINGS_OFFTYPE_SHORT_PENALTY_SIM_RELIEF: float = 1.0

# Deterministic truncation to limit compute and control noise.
SYNOPSIS_EMBEDDINGS_MAX_CHARS: int = 240
SYNOPSIS_EMBEDDINGS_TRUNC_SUFFIX: str = "…"

# Default local embedding pipeline identifier.
#
# We intentionally avoid torch/sentence-transformers here to keep builds
# deterministic and dependency-light across Windows environments.
DEFAULT_SENTENCE_TRANSFORMERS_MODEL: str = "tfidf_svd_256"

# Local embedding pipeline params.
SYNOPSIS_EMBEDDINGS_TFIDF_MAX_FEATURES: int = 40000
SYNOPSIS_EMBEDDINGS_TFIDF_NGRAM_RANGE: tuple[int, int] = (1, 2)
SYNOPSIS_EMBEDDINGS_TFIDF_MIN_DF: int = 2
SYNOPSIS_EMBEDDINGS_TFIDF_MAX_DF: float = 0.90
SYNOPSIS_EMBEDDINGS_TFIDF_STOP_WORDS: str = "english"
SYNOPSIS_EMBEDDINGS_TFIDF_TOKEN_PATTERN: str = r"(?u)\b[a-zA-Z][a-zA-Z]+\b"

SYNOPSIS_EMBEDDINGS_SVD_DIM: int = 256
SYNOPSIS_EMBEDDINGS_SVD_RANDOM_STATE: int = 42
SYNOPSIS_EMBEDDINGS_SVD_N_ITER: int = 7


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _is_blank_text(val: Any) -> bool:
    if val is None:
        return True
    try:
        if pd.isna(val):
            return True
    except Exception:
        pass
    s = str(val).strip()
    if not s:
        return True
    if s.lower() in {"nan", "none", "null"}:
        return True
    return False


def truncate_synopsis(text: str, *, max_chars: int = SYNOPSIS_EMBEDDINGS_MAX_CHARS, suffix: str = SYNOPSIS_EMBEDDINGS_TRUNC_SUFFIX) -> str:
    s = str(text or "")
    if len(s) > int(max_chars):
        return s[: int(max_chars)] + str(suffix)
    return s


def choose_embedding_text(row: Mapping[str, Any]) -> str:
    """Choose deterministic embedding text using existing metadata fields."""
    synopsis = "" if _is_blank_text(row.get("synopsis")) else str(row.get("synopsis")).strip()
    snippet = "" if _is_blank_text(row.get("synopsis_snippet")) else str(row.get("synopsis_snippet")).strip()

    if synopsis:
        trunc = truncate_synopsis(synopsis)
        # Prefer snippet only when it matches the truncation rule.
        if snippet and snippet == trunc:
            return snippet
        return trunc

    # No synopsis available; fall back to snippet as-is.
    return snippet


def _sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def synopsis_embeddings_penalty_for_candidate(*, passes_gate: bool, sim: float, candidate_episodes: Any) -> float:
    """Return a negative penalty for off-type/short candidates.

    Only applies when the candidate fails the gate AND is short-form
    (episodes < SYNOPSIS_EMBEDDINGS_MIN_EPISODES).
    """
    if bool(passes_gate):
        return 0.0
    try:
        if candidate_episodes is None or pd.isna(candidate_episodes):
            return 0.0
        if int(candidate_episodes) >= int(SYNOPSIS_EMBEDDINGS_MIN_EPISODES):
            return 0.0
    except Exception:
        return 0.0

    penalty = -float(SYNOPSIS_EMBEDDINGS_OFFTYPE_SHORT_PENALTY_BASE) + float(SYNOPSIS_EMBEDDINGS_OFFTYPE_SHORT_PENALTY_SIM_RELIEF) * float(sim)
    return float(min(0.0, penalty))


def _embed_bonus(sim: float, *, coef: float, min_sim: float = SYNOPSIS_EMBEDDINGS_MIN_SIM) -> float:
    s = float(sim)
    if s <= float(min_sim):
        return 0.0
    # Use a shifted similarity so the bonus turns on smoothly at min_sim.
    return float(coef) * float(s - float(min_sim))


def synopsis_embeddings_bonus_for_candidate(*, sim: float, hybrid_val: float) -> float:
    coef = float(SYNOPSIS_EMBEDDINGS_COLD_START_COEF) if float(hybrid_val) == 0.0 else float(SYNOPSIS_EMBEDDINGS_TRAINED_COEF)
    return _embed_bonus(float(sim), coef=coef)


def personalized_synopsis_embeddings_bonus_for_candidate(sim: float) -> float:
    return _embed_bonus(float(sim), coef=float(SYNOPSIS_EMBEDDINGS_PERSONALIZED_COEF))


@dataclass(frozen=True)
class SynopsisEmbeddingsArtifact:
    schema: str
    created_utc: str

    model_name: str
    model_library_versions: dict[str, str]

    text_field: str
    text_preprocessing: dict[str, Any]

    dim: int
    normalized: bool

    embeddings: np.ndarray  # float32, shape [n_items, dim], L2-normalized

    anime_ids: np.ndarray  # int64, aligned to embeddings rows
    anime_id_to_row: dict[int, int]

    config_hash: str
    anime_ids_hash: str


def validate_synopsis_embeddings_artifact(obj: Any) -> SynopsisEmbeddingsArtifact:
    if not isinstance(obj, SynopsisEmbeddingsArtifact):
        raise TypeError("Synopsis embeddings artifact has unexpected type")

    if obj.schema != SYNOPSIS_EMBEDDINGS_SCHEMA:
        raise ValueError(f"Unsupported synopsis embeddings schema: {obj.schema}")

    E = obj.embeddings
    if E is None or not isinstance(E, np.ndarray) or E.ndim != 2 or E.shape[0] <= 0 or E.shape[1] <= 0:
        raise ValueError("Synopsis embeddings artifact has invalid embeddings matrix")
    if E.dtype != np.float32:
        raise ValueError("Synopsis embeddings must be float32")

    if obj.anime_ids is None or len(obj.anime_ids) != int(E.shape[0]):
        raise ValueError("Synopsis embeddings artifact has invalid anime_ids")
    if not isinstance(obj.anime_id_to_row, dict) or not obj.anime_id_to_row:
        raise ValueError("Synopsis embeddings artifact is missing anime_id_to_row mapping")

    if int(obj.dim) != int(E.shape[1]):
        raise ValueError("Synopsis embeddings artifact dim does not match embeddings shape")

    if bool(obj.normalized):
        # Spot-check normalization (tolerant; avoids false positives from fp32 rounding).
        norms = np.linalg.norm(E[: min(256, E.shape[0])], axis=1)
        if not np.isfinite(norms).all():
            raise ValueError("Synopsis embeddings have non-finite values")
        if float(np.max(np.abs(norms - 1.0))) > 1e-2:
            raise ValueError("Synopsis embeddings are expected to be L2-normalized")

    return obj


def build_synopsis_embeddings_artifact(
    metadata: pd.DataFrame,
    *,
    id_col: str = "anime_id",
    model_name: str = DEFAULT_SENTENCE_TRANSFORMERS_MODEL,
    batch_size: int = 64,
) -> SynopsisEmbeddingsArtifact:
    if metadata is None or metadata.empty:
        raise ValueError("Cannot build synopsis embeddings: metadata is empty")
    if id_col not in metadata.columns:
        raise ValueError(f"Cannot build synopsis embeddings: missing '{id_col}'")

    # NOTE: batch_size is accepted for interface parity with the earlier
    # sentence-transformers plan, but is not used by the local SVD pipeline.
    _ = batch_size

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    import sklearn  # type: ignore

    work = metadata.copy()
    work[id_col] = pd.to_numeric(work[id_col], errors="coerce").astype("Int64")
    work = work.dropna(subset=[id_col]).copy()
    work[id_col] = work[id_col].astype(int)

    # Stable order for determinism.
    work = work.sort_values(id_col, kind="mergesort")

    texts = work.apply(lambda r: choose_embedding_text(r), axis=1).astype(str).fillna("")

    # Deterministic config hash (does not depend on build time).
    preprocess = {
        "policy": "prefer_snippet_if_matches_trunc_else_trunc_synopsis",
        "max_chars": int(SYNOPSIS_EMBEDDINGS_MAX_CHARS),
        "suffix": str(SYNOPSIS_EMBEDDINGS_TRUNC_SUFFIX),
        "strip": True,
        "blank_policy": "empty_string",
    }
    config_hash = _sha256_hex(
        (
            SYNOPSIS_EMBEDDINGS_SCHEMA
            + "|" + str(model_name)
            + "|" + str(sorted(preprocess.items()))
        ).encode("utf-8")
    )

    anime_ids = work[id_col].astype(int).to_numpy(dtype=np.int64, copy=True)
    anime_id_to_row = {int(aid): int(i) for i, aid in enumerate(anime_ids.tolist())}
    anime_ids_hash = _sha256_hex(anime_ids.tobytes())

    # Local deterministic embedding pipeline:
    #   1) TF-IDF (sparse) over deterministic synopsis text
    #   2) TruncatedSVD to dense semantic components
    #   3) L2 normalize for cosine similarity
    vec = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words=SYNOPSIS_EMBEDDINGS_TFIDF_STOP_WORDS,
        max_features=int(SYNOPSIS_EMBEDDINGS_TFIDF_MAX_FEATURES),
        ngram_range=SYNOPSIS_EMBEDDINGS_TFIDF_NGRAM_RANGE,
        min_df=int(SYNOPSIS_EMBEDDINGS_TFIDF_MIN_DF),
        max_df=float(SYNOPSIS_EMBEDDINGS_TFIDF_MAX_DF),
        token_pattern=SYNOPSIS_EMBEDDINGS_TFIDF_TOKEN_PATTERN,
        sublinear_tf=True,
        norm="l2",
    )
    X = vec.fit_transform(texts.tolist())

    svd = TruncatedSVD(
        n_components=int(SYNOPSIS_EMBEDDINGS_SVD_DIM),
        n_iter=int(SYNOPSIS_EMBEDDINGS_SVD_N_ITER),
        random_state=int(SYNOPSIS_EMBEDDINGS_SVD_RANDOM_STATE),
    )
    E = svd.fit_transform(X)
    E = np.asarray(E, dtype=np.float32)

    # Ensure finite and normalized.
    E = np.nan_to_num(E, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32, copy=False)
    norms = np.linalg.norm(E, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, 1.0, norms)
    E = (E / norms).astype(np.float32, copy=False)

    versions = {
        "sklearn": str(getattr(sklearn, "__version__", "")),
        "numpy": str(getattr(np, "__version__", "")),
    }

    return SynopsisEmbeddingsArtifact(
        schema=SYNOPSIS_EMBEDDINGS_SCHEMA,
        created_utc=_utc_now_iso(),
        model_name=str(model_name),
        model_library_versions=versions,
        text_field="synopsis_snippet|synopsis_trunc240",
        text_preprocessing=preprocess,
        dim=int(E.shape[1]),
        normalized=True,
        embeddings=E,
        anime_ids=anime_ids,
        anime_id_to_row=anime_id_to_row,
        config_hash=config_hash,
        anime_ids_hash=anime_ids_hash,
    )


def compute_seed_similarity_map(
    artifact: Any,
    *,
    seed_ids: list[int],
) -> dict[int, float]:
    """Compute max cosine similarity of each item to any seed.

    Returns dict: anime_id -> similarity (0..1). Items absent from the artifact are omitted.
    """
    art = validate_synopsis_embeddings_artifact(artifact)

    seed_rows: list[int] = []
    for sid in seed_ids:
        idx = art.anime_id_to_row.get(int(sid))
        if idx is not None:
            seed_rows.append(int(idx))

    if not seed_rows:
        return {}

    E = art.embeddings

    sims = np.zeros(len(art.anime_ids), dtype=np.float32)
    for r in seed_rows:
        q = E[int(r)]
        try:
            s = E @ q
        except Exception:
            continue
        sims = np.maximum(sims, np.asarray(s, dtype=np.float32))

    return {int(aid): float(sims[i]) for i, aid in enumerate(art.anime_ids.tolist())}


__all__ = [
    "SYNOPSIS_EMBEDDINGS_SCHEMA",
    "SYNOPSIS_EMBEDDINGS_MIN_SIM",
    "SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD",
    "SYNOPSIS_EMBEDDINGS_MIN_EPISODES",
    "SYNOPSIS_EMBEDDINGS_OFFTYPE_HIGH_SIM_PENALTY",
    "SYNOPSIS_EMBEDDINGS_COLD_START_COEF",
    "SYNOPSIS_EMBEDDINGS_TRAINED_COEF",
    "SYNOPSIS_EMBEDDINGS_PERSONALIZED_COEF",
    "SYNOPSIS_EMBEDDINGS_OFFTYPE_SHORT_PENALTY_BASE",
    "SYNOPSIS_EMBEDDINGS_OFFTYPE_SHORT_PENALTY_SIM_RELIEF",
    "SYNOPSIS_EMBEDDINGS_MAX_CHARS",
    "SYNOPSIS_EMBEDDINGS_TRUNC_SUFFIX",
    "DEFAULT_SENTENCE_TRANSFORMERS_MODEL",
    "SynopsisEmbeddingsArtifact",
    "validate_synopsis_embeddings_artifact",
    "truncate_synopsis",
    "choose_embedding_text",
    "synopsis_embeddings_bonus_for_candidate",
    "synopsis_embeddings_penalty_for_candidate",
    "personalized_synopsis_embeddings_bonus_for_candidate",
    "build_synopsis_embeddings_artifact",
    "compute_seed_similarity_map",
]
