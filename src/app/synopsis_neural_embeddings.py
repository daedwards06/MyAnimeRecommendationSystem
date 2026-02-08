"""Neural synopsis sentence-embedding artifact + cosine similarity utilities (Phase 5).

Goal
----
Provide a true neural semantic signal for ranked modes (seed-conditioned Stage 1
shortlist + small Stage 2 rerank), while keeping Windows runtime free of
torch/transformers dependencies.

Key constraints
---------------
- Runtime (Windows): pure NumPy (no torch/transformers).
- Build (WSL2): embeddings computed offline and serialized as a lightweight
  artifact (float32 + L2-normalized for cosine similarity).
- Deterministic: stable anime_id ordering, fixed truncation/preprocessing rules.

Text policy
-----------
- Use `synopsis` only.
- Deterministic truncation is applied during offline build and recorded in the
  artifact metadata.
- If synopsis is missing/blank: a zero vector is stored for that item.

The artifact is intentionally simple: it stores the already-normalized matrix
and a stable anime_id -> row index mapping.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Centralized constants (Phase 5 neural embeddings)
# ---------------------------------------------------------------------------

SYNOPSIS_NEURAL_EMBEDDINGS_SCHEMA: str = "synopsis_neural_embeddings_v1"

# Cosine similarity thresholds on L2-normalized sentence-transformer embeddings.
# These are intentionally conservative defaults; tune via env / evaluation.
SYNOPSIS_NEURAL_MIN_SIM: float = 0.25
SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD: float = 0.55

# Same minimum-episodes heuristic used by Phase 4 semantic gates.
SYNOPSIS_NEURAL_MIN_EPISODES: int = 12

# If admitted via HIGH_SIM override, apply a small deterministic penalty so
# same-type TV remains preferred unless similarity is genuinely strong.
SYNOPSIS_NEURAL_OFFTYPE_HIGH_SIM_PENALTY: float = 0.01

# Additive rerank coefficients (dramatically increased to make neural signal dominant).
# Phase 5 fix: previous values (0.35/0.15) were too small to compete with genre overlap.
SYNOPSIS_NEURAL_COLD_START_COEF: float = 2.5
SYNOPSIS_NEURAL_TRAINED_COEF: float = 1.5

# Conservative short-form penalty when the base gate fails.
SYNOPSIS_NEURAL_OFFTYPE_SHORT_PENALTY_BASE: float = 0.60
SYNOPSIS_NEURAL_OFFTYPE_SHORT_PENALTY_SIM_RELIEF: float = 1.0


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _embed_bonus(sim: float, *, coef: float, min_sim: float = SYNOPSIS_NEURAL_MIN_SIM) -> float:
    s = float(sim)
    if s <= float(min_sim):
        return 0.0
    # Shifted similarity so the bonus turns on smoothly at min_sim.
    return float(coef) * float(s - float(min_sim))


def synopsis_neural_bonus_for_candidate(*, sim: float, hybrid_val: float) -> float:
    coef = float(SYNOPSIS_NEURAL_COLD_START_COEF) if float(hybrid_val) == 0.0 else float(SYNOPSIS_NEURAL_TRAINED_COEF)
    return _embed_bonus(float(sim), coef=coef)


def synopsis_neural_penalty_for_candidate(*, passes_gate: bool, sim: float, candidate_episodes: Any) -> float:
    """Return a negative penalty for off-type/short candidates.

    Only applies when the candidate fails the gate AND is short-form
    (episodes < SYNOPSIS_NEURAL_MIN_EPISODES).
    """
    if bool(passes_gate):
        return 0.0

    try:
        if candidate_episodes is None:
            return 0.0
        # Avoid importing pandas at runtime; accept NaN-ish via float checks.
        if isinstance(candidate_episodes, float) and not np.isfinite(candidate_episodes):
            return 0.0
        if int(candidate_episodes) >= int(SYNOPSIS_NEURAL_MIN_EPISODES):
            return 0.0
    except Exception:
        return 0.0

    penalty = -float(SYNOPSIS_NEURAL_OFFTYPE_SHORT_PENALTY_BASE) + float(SYNOPSIS_NEURAL_OFFTYPE_SHORT_PENALTY_SIM_RELIEF) * float(sim)
    return float(min(0.0, penalty))


@dataclass(frozen=True)
class SynopsisNeuralEmbeddingsArtifact:
    schema: str
    created_utc: str

    model_name: str
    model_library_versions: dict[str, str]

    text_field: str
    text_preprocessing: dict[str, Any]

    dim: int
    normalized: bool

    embeddings: np.ndarray  # float32, shape [n_items, dim], L2-normalized (or 0 for missing)

    anime_ids: np.ndarray  # int64, aligned to embeddings rows
    anime_id_to_row: dict[int, int]

    config_hash: str
    anime_ids_hash: str


def validate_synopsis_neural_embeddings_artifact(obj: Any) -> SynopsisNeuralEmbeddingsArtifact:
    if not isinstance(obj, SynopsisNeuralEmbeddingsArtifact):
        raise TypeError("Synopsis neural embeddings artifact has unexpected type")

    if obj.schema != SYNOPSIS_NEURAL_EMBEDDINGS_SCHEMA:
        raise ValueError(f"Unsupported synopsis neural embeddings schema: {obj.schema}")

    E = obj.embeddings
    if E is None or not isinstance(E, np.ndarray) or E.ndim != 2 or E.shape[0] <= 0 or E.shape[1] <= 0:
        raise ValueError("Synopsis neural embeddings artifact has invalid embeddings matrix")
    if E.dtype != np.float32:
        raise ValueError("Synopsis neural embeddings must be float32")

    if obj.anime_ids is None or len(obj.anime_ids) != int(E.shape[0]):
        raise ValueError("Synopsis neural embeddings artifact has invalid anime_ids")
    if not isinstance(obj.anime_id_to_row, dict) or not obj.anime_id_to_row:
        raise ValueError("Synopsis neural embeddings artifact is missing anime_id_to_row mapping")

    if int(obj.dim) != int(E.shape[1]):
        raise ValueError("Synopsis neural embeddings dim does not match embeddings shape")

    if bool(obj.normalized):
        # Allow zero vectors (missing synopsis). For non-zero rows, require ~unit norm.
        sample = E[: min(256, E.shape[0])]
        norms = np.linalg.norm(sample, axis=1)
        if not np.isfinite(norms).all():
            raise ValueError("Synopsis neural embeddings have non-finite values")
        nonzero = norms > 1e-6
        if np.any(nonzero):
            if float(np.max(np.abs(norms[nonzero] - 1.0))) > 1e-2:
                raise ValueError("Synopsis neural embeddings are expected to be L2-normalized")

    return obj


def compute_seed_similarity_map(
    artifact: Any,
    *,
    seed_ids: Iterable[int],
    min_sim: float = SYNOPSIS_NEURAL_MIN_SIM,
) -> dict[int, float]:
    """Compute max cosine similarity to any seed for every item.

    Returns a dense-ish map (anime_id -> similarity). Values below min_sim are
    omitted (keeps downstream loops faster and deterministic).

    Similarity is cosine on L2-normalized embeddings: dot(E[i], E[seed]).
    """

    art = validate_synopsis_neural_embeddings_artifact(artifact)
    seeds = [int(x) for x in seed_ids]
    if not seeds:
        return {}

    seed_rows: list[int] = []
    for sid in seeds:
        r = art.anime_id_to_row.get(int(sid))
        if r is not None:
            seed_rows.append(int(r))
    if not seed_rows:
        return {}

    E = art.embeddings
    S = E[np.asarray(seed_rows, dtype=np.int32)]
    if S.ndim != 2 or S.shape[0] <= 0:
        return {}

    # Cosine on normalized vectors -> dot product.
    sims = E @ S.T  # [n_items, n_seeds]
    max_sims = np.max(sims, axis=1)

    out: dict[int, float] = {}
    thr = float(min_sim)
    for aid, s in zip(art.anime_ids.tolist(), max_sims.tolist()):
        fs = float(s)
        if fs >= thr:
            out[int(aid)] = fs
    return out


def compute_seed_topk_neighbors(
    artifact: Any,
    *,
    seed_ids: Iterable[int],
    topk: int,
) -> list[tuple[int, float]]:
    """Return [(anime_id, sim)] for the top-K neural neighbors to the seed(s).

    Similarity is cosine on L2-normalized embeddings: dot(E[i], E[seed]).

    Notes:
    - Deterministic ordering: sim desc, anime_id asc.
    - Seed items themselves are excluded from selection.
    - No min_sim threshold is applied here; callers can filter if desired.
    """

    art = validate_synopsis_neural_embeddings_artifact(artifact)
    seeds = [int(x) for x in seed_ids]
    k = max(0, int(topk))
    if not seeds or k <= 0:
        return []

    seed_rows: list[int] = []
    for sid in seeds:
        r = art.anime_id_to_row.get(int(sid))
        if r is not None:
            seed_rows.append(int(r))
    if not seed_rows:
        return []

    E = art.embeddings
    S = E[np.asarray(seed_rows, dtype=np.int32)]
    if S.ndim != 2 or S.shape[0] <= 0:
        return []

    sims = E @ S.T
    max_sims = np.max(sims, axis=1)

    # Exclude seeds from the neighbor list.
    for r in seed_rows:
        if 0 <= int(r) < int(max_sims.shape[0]):
            max_sims[int(r)] = -np.inf

    n_items = int(max_sims.shape[0])
    if n_items <= 0:
        return []

    if k >= n_items:
        idx = np.arange(n_items, dtype=np.int32)
    else:
        # Partial selection for efficiency.
        idx = np.argpartition(max_sims, -k)[-k:]

    pairs: list[tuple[int, float]] = []
    for i in idx.tolist():
        try:
            aid = int(art.anime_ids[int(i)])
            sim = float(max_sims[int(i)])
        except Exception:
            continue
        if not np.isfinite(sim):
            continue
        pairs.append((aid, sim))

    pairs.sort(key=lambda x: (-float(x[1]), int(x[0])))
    return pairs[:k]


def build_artifact_from_embeddings(
    *,
    anime_ids: np.ndarray,
    embeddings: np.ndarray,
    model_name: str,
    model_library_versions: dict[str, str],
    text_preprocessing: dict[str, Any],
    created_utc: str | None = None,
) -> SynopsisNeuralEmbeddingsArtifact:
    """Create a validated artifact from a precomputed embeddings matrix.

    This is used by the offline builder (WSL2) after computing embeddings with
    sentence-transformers.
    """

    created = created_utc or _utc_now_iso()

    ids = np.asarray(anime_ids, dtype=np.int64)
    if ids.ndim != 1 or ids.shape[0] <= 0:
        raise ValueError("anime_ids must be a non-empty 1D array")

    E = np.asarray(embeddings)
    if E.ndim != 2 or E.shape[0] != ids.shape[0] or E.shape[1] <= 0:
        raise ValueError("embeddings must be shape [N, D] aligned with anime_ids")
    if E.dtype != np.float32:
        E = E.astype(np.float32, copy=False)

    dim = int(E.shape[1])
    anime_id_to_row = {int(aid): int(i) for i, aid in enumerate(ids.tolist())}

    # Hashes for reproducibility/debug.
    cfg = {
        "schema": SYNOPSIS_NEURAL_EMBEDDINGS_SCHEMA,
        "model_name": str(model_name),
        "text_field": "synopsis",
        "text_preprocessing": text_preprocessing,
        "dim": int(dim),
        "normalized": True,
    }
    cfg_bytes = str(cfg).encode("utf-8")
    ids_bytes = ids.tobytes()

    art = SynopsisNeuralEmbeddingsArtifact(
        schema=SYNOPSIS_NEURAL_EMBEDDINGS_SCHEMA,
        created_utc=str(created),
        model_name=str(model_name),
        model_library_versions=dict(model_library_versions or {}),
        text_field="synopsis",
        text_preprocessing=dict(text_preprocessing or {}),
        dim=int(dim),
        normalized=True,
        embeddings=E,
        anime_ids=ids,
        anime_id_to_row=anime_id_to_row,
        config_hash=_sha256_hex(cfg_bytes),
        anime_ids_hash=_sha256_hex(ids_bytes),
    )

    return validate_synopsis_neural_embeddings_artifact(art)


__all__ = [
    "SYNOPSIS_NEURAL_EMBEDDINGS_SCHEMA",
    "SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD",
    "SYNOPSIS_NEURAL_MIN_SIM",
    "SYNOPSIS_NEURAL_OFFTYPE_HIGH_SIM_PENALTY",
    "SynopsisNeuralEmbeddingsArtifact",
    "build_artifact_from_embeddings",
    "compute_seed_similarity_map",
    "synopsis_neural_bonus_for_candidate",
    "synopsis_neural_penalty_for_candidate",
    "validate_synopsis_neural_embeddings_artifact",
]
