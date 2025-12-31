"""Deterministic synopsis TF-IDF artifact + lightweight rerank utilities.

Phase 4 (A3 → early A4 experiment): add a semantic rerank signal based on
synopsis/synopsis_snippet similarity.

Design constraints
------------------
- Deterministic: stable ordering, fixed preprocessing, no randomness.
- Lightweight: scikit-learn TF-IDF only; sparse matrix stored via joblib.
- Ranked modes only: seed-based first; personalized only when seeds exist.
- Conservative gating: prefer same `type` OR minimum `episodes` threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer


# ---------------------------------------------------------------------------
# Centralized, conservative TF-IDF settings (deterministic).
# ---------------------------------------------------------------------------

SYNOPSIS_TFIDF_SCHEMA: str = "synopsis_tfidf_v1"

SYNOPSIS_TFIDF_MAX_FEATURES: int = 30000
SYNOPSIS_TFIDF_NGRAM_RANGE: tuple[int, int] = (1, 2)
SYNOPSIS_TFIDF_MIN_DF: int = 2
SYNOPSIS_TFIDF_MAX_DF: float = 0.90
SYNOPSIS_TFIDF_STOP_WORDS: str = "english"
SYNOPSIS_TFIDF_TOKEN_PATTERN: str = r"(?u)\b[a-zA-Z][a-zA-Z]+\b"

# Rerank constants (additive + interpretable; keep small).
SYNOPSIS_TFIDF_MIN_SIM: float = 0.02
SYNOPSIS_TFIDF_MIN_EPISODES: int = 12

# Phase 4 Option A refinement (2025-12-31):
# High-similarity override for Stage 1 TF-IDF candidate gating.
#
# Rationale:
# - Some long-running franchises (e.g., One Piece) have their strongest synopsis
#   TF-IDF neighbors in Movies / TV Specials / OVAs (often with episodes=1).
# - A strict same-type / min-episodes gate can exclude these, forcing generic
#   TV matches.
#
# We keep the existing conservative gate for most candidates, but allow an
# override only at very high cosine similarity. This threshold is intentionally
# conservative (near the extreme tail of the similarity distribution) to avoid
# admitting short-form noise.
SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD: float = 0.12

# If a candidate is admitted via the HIGH_SIM_THRESHOLD override (i.e., it fails
# the base gate), apply a small deterministic penalty so same-type TV remains
# preferred unless similarity is genuinely strong.
SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY: float = 0.001

SYNOPSIS_TFIDF_COLD_START_COEF: float = 2.00
SYNOPSIS_TFIDF_TRAINED_COEF: float = 0.50
SYNOPSIS_TFIDF_PERSONALIZED_COEF: float = 0.50

# Optional conservative penalty: if a candidate fails the type/episodes gate and is
# short-form (episodes < min), demote it. Similarity can partially offset the penalty,
# but the adjustment never becomes positive.
SYNOPSIS_TFIDF_OFFTYPE_SHORT_PENALTY_BASE: float = 0.75
SYNOPSIS_TFIDF_OFFTYPE_SHORT_PENALTY_SIM_RELIEF: float = 1.0


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


def choose_synopsis_text(row: Mapping[str, Any]) -> str:
    """Prefer full synopsis; fall back to snippet.

    Only uses existing fields: `synopsis` or `synopsis_snippet`.
    """
    for key in ("synopsis", "synopsis_snippet"):
        if key in row and not _is_blank_text(row.get(key)):
            return str(row.get(key)).strip()
    return ""


def _most_common_type(metadata: pd.DataFrame, seed_ids: Iterable[int]) -> Optional[str]:
    if metadata is None or metadata.empty or "anime_id" not in metadata.columns:
        return None
    if "type" not in metadata.columns:
        return None

    seed_set = {int(x) for x in seed_ids}
    work = metadata.loc[metadata["anime_id"].astype(int).isin(seed_set), ["anime_id", "type"]].copy()
    if work.empty:
        return None

    # Stable + conservative: take the mode; tie-break by lexicographic sort.
    types: list[str] = []
    for _, r in work.sort_values("anime_id", kind="mergesort").iterrows():
        t = r.get("type")
        if _is_blank_text(t):
            continue
        types.append(str(t).strip())
    if not types:
        return None

    counts: dict[str, int] = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    return sorted(counts.items(), key=lambda x: (-int(x[1]), str(x[0])))[0][0]


def synopsis_gate_passes(
    *,
    seed_type: Optional[str],
    candidate_type: Optional[str],
    candidate_episodes: Any,
    min_episodes: int = SYNOPSIS_TFIDF_MIN_EPISODES,
) -> bool:
    """Conservative gate: same type OR episodes >= threshold (if episodes available)."""
    same_type = False
    if seed_type and candidate_type:
        same_type = str(seed_type).strip() == str(candidate_type).strip()

    eps_ok = False
    try:
        if candidate_episodes is not None and not pd.isna(candidate_episodes):
            eps_ok = int(candidate_episodes) >= int(min_episodes)
    except Exception:
        eps_ok = False

    return bool(same_type or eps_ok)


def synopsis_tfidf_penalty_for_candidate(*, passes_gate: bool, sim: float, candidate_episodes: Any) -> float:
    """Return a negative penalty for off-type/short candidates.

    Only applies when the candidate fails the gate AND is short-form
    (episodes < SYNOPSIS_TFIDF_MIN_EPISODES).
    """
    if bool(passes_gate):
        return 0.0
    try:
        if candidate_episodes is None or pd.isna(candidate_episodes):
            return 0.0
        if int(candidate_episodes) >= int(SYNOPSIS_TFIDF_MIN_EPISODES):
            return 0.0
    except Exception:
        return 0.0

    penalty = -float(SYNOPSIS_TFIDF_OFFTYPE_SHORT_PENALTY_BASE) + float(SYNOPSIS_TFIDF_OFFTYPE_SHORT_PENALTY_SIM_RELIEF) * float(sim)
    return float(min(0.0, penalty))


def _tfidf_bonus(sim: float, *, coef: float, min_sim: float = SYNOPSIS_TFIDF_MIN_SIM) -> float:
    s = float(sim)
    if s <= float(min_sim):
        return 0.0
    # Keep additive term interpretable: gated cosine similarity scaled by a small coefficient.
    return float(coef) * float(s)


@dataclass(frozen=True)
class SynopsisTfidfArtifact:
    schema: str
    created_utc: str
    text_field: str

    vectorizer: TfidfVectorizer
    tfidf_matrix: Any  # scipy.sparse csr_matrix

    anime_ids: np.ndarray  # aligned to tfidf_matrix rows
    anime_id_to_row: dict[int, int]

    vocab_size: int
    vectorizer_params: dict[str, Any]


def validate_synopsis_tfidf_artifact(obj: Any) -> SynopsisTfidfArtifact:
    if isinstance(obj, SynopsisTfidfArtifact):
        art = obj
    else:
        raise TypeError("Synopsis TF-IDF artifact has unexpected type")

    if art.schema != SYNOPSIS_TFIDF_SCHEMA:
        raise ValueError(f"Unsupported synopsis TF-IDF schema: {art.schema}")
    if art.anime_ids is None or len(art.anime_ids) <= 0:
        raise ValueError("Synopsis TF-IDF artifact has empty anime_ids")
    if art.tfidf_matrix is None:
        raise ValueError("Synopsis TF-IDF artifact is missing tfidf_matrix")
    if not isinstance(art.anime_id_to_row, dict) or not art.anime_id_to_row:
        raise ValueError("Synopsis TF-IDF artifact is missing anime_id_to_row mapping")
    if int(art.vocab_size) <= 0:
        raise ValueError("Synopsis TF-IDF artifact has empty vocabulary")

    return art


def build_synopsis_tfidf_artifact(
    metadata: pd.DataFrame,
    *,
    id_col: str = "anime_id",
) -> SynopsisTfidfArtifact:
    if metadata is None or metadata.empty:
        raise ValueError("Cannot build synopsis TF-IDF: metadata is empty")
    if id_col not in metadata.columns:
        raise ValueError(f"Cannot build synopsis TF-IDF: missing '{id_col}'")

    work = metadata.copy()
    work[id_col] = pd.to_numeric(work[id_col], errors="coerce").astype("Int64")
    work = work.dropna(subset=[id_col]).copy()
    work[id_col] = work[id_col].astype(int)

    # Stable order for determinism.
    work = work.sort_values(id_col, kind="mergesort")

    texts = work.apply(lambda r: choose_synopsis_text(r), axis=1).astype(str).fillna("")

    # Avoid empty vocabulary errors by checking at least one non-empty doc.
    if not texts.str.len().gt(0).any():
        raise ValueError("Cannot build synopsis TF-IDF: no non-empty synopsis texts found")

    vec = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words=SYNOPSIS_TFIDF_STOP_WORDS,
        max_features=int(SYNOPSIS_TFIDF_MAX_FEATURES),
        ngram_range=SYNOPSIS_TFIDF_NGRAM_RANGE,
        min_df=int(SYNOPSIS_TFIDF_MIN_DF),
        max_df=float(SYNOPSIS_TFIDF_MAX_DF),
        token_pattern=SYNOPSIS_TFIDF_TOKEN_PATTERN,
        sublinear_tf=True,
        norm="l2",
    )

    X = vec.fit_transform(texts.tolist())

    anime_ids = work[id_col].astype(int).to_numpy(dtype=np.int64, copy=True)
    anime_id_to_row = {int(aid): int(i) for i, aid in enumerate(anime_ids.tolist())}

    params = {
        "lowercase": True,
        "strip_accents": "unicode",
        "stop_words": SYNOPSIS_TFIDF_STOP_WORDS,
        "max_features": int(SYNOPSIS_TFIDF_MAX_FEATURES),
        "ngram_range": SYNOPSIS_TFIDF_NGRAM_RANGE,
        "min_df": int(SYNOPSIS_TFIDF_MIN_DF),
        "max_df": float(SYNOPSIS_TFIDF_MAX_DF),
        "token_pattern": SYNOPSIS_TFIDF_TOKEN_PATTERN,
        "sublinear_tf": True,
        "norm": "l2",
    }

    return SynopsisTfidfArtifact(
        schema=SYNOPSIS_TFIDF_SCHEMA,
        created_utc=_utc_now_iso(),
        text_field="synopsis|synopsis_snippet",
        vectorizer=vec,
        tfidf_matrix=X,
        anime_ids=anime_ids,
        anime_id_to_row=anime_id_to_row,
        vocab_size=int(len(vec.get_feature_names_out())),
        vectorizer_params=params,
    )


def compute_seed_similarity_map(
    artifact: Any,
    *,
    seed_ids: list[int],
) -> dict[int, float]:
    """Compute max cosine similarity of each item to any seed.

    Returns dict: anime_id -> similarity (0..1). Items absent from the artifact are omitted.
    """
    art = validate_synopsis_tfidf_artifact(artifact)

    seed_rows: list[int] = []
    for sid in seed_ids:
        idx = art.anime_id_to_row.get(int(sid))
        if idx is not None:
            seed_rows.append(int(idx))

    if not seed_rows:
        return {}

    X = art.tfidf_matrix
    X_t = X.T

    sims = np.zeros(len(art.anime_ids), dtype=np.float32)
    for r in seed_rows:
        q = X[int(r)]
        try:
            s = q.dot(X_t).toarray().ravel()
        except Exception:
            # Fallback: avoid hard failure in ranked modes.
            continue
        sims = np.maximum(sims, np.asarray(s, dtype=np.float32))

    return {int(aid): float(sims[i]) for i, aid in enumerate(art.anime_ids.tolist())}


def apply_synopsis_tfidf_bonus(
    *,
    metadata: pd.DataFrame,
    synopsis_tfidf_artifact: Any,
    seed_ids: list[int],
    scored_rows: Iterable[Mapping[str, Any]],
    score_key: str = "score",
    hybrid_val_key: str = "hybrid_val",
    type_key: str = "type",
    episodes_key: str = "episodes",
    out_sim_key: str = "synopsis_tfidf_sim",
    out_bonus_key: str = "synopsis_tfidf_bonus",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Add TF-IDF bonus to a scored iterable.

    This helper is intentionally simple and primarily used by evaluation.
    """
    sims_by_id = compute_seed_similarity_map(synopsis_tfidf_artifact, seed_ids=seed_ids)
    seed_type = _most_common_type(metadata, seed_ids)

    out: list[dict[str, Any]] = []
    fired = 0

    for row in scored_rows:
        item = dict(row)
        aid = int(item.get("anime_id"))
        sim = float(sims_by_id.get(aid, 0.0))

        passes = synopsis_gate_passes(
            seed_type=seed_type,
            candidate_type=item.get(type_key),
            candidate_episodes=item.get(episodes_key),
        )

        hybrid_val = float(item.get(hybrid_val_key, 0.0) or 0.0)
        coef = float(SYNOPSIS_TFIDF_COLD_START_COEF) if hybrid_val == 0.0 else float(SYNOPSIS_TFIDF_TRAINED_COEF)
        bonus = _tfidf_bonus(sim, coef=coef)
        if not passes:
            bonus = 0.0

        item[out_sim_key] = float(sim)
        item[out_bonus_key] = float(bonus)
        item[score_key] = float(item.get(score_key, 0.0)) + float(bonus)
        if bonus > 0.0:
            fired += 1

        out.append(item)

    diagnostics = {
        "synopsis_tfidf_bonus_fired_count": int(fired),
    }
    return out, diagnostics


def most_common_seed_type(metadata: pd.DataFrame, seed_ids: list[int]) -> Optional[str]:
    return _most_common_type(metadata, seed_ids)


def synopsis_tfidf_bonus_for_candidate(
    *,
    sim: float,
    hybrid_val: float,
) -> float:
    coef = float(SYNOPSIS_TFIDF_COLD_START_COEF) if float(hybrid_val) == 0.0 else float(SYNOPSIS_TFIDF_TRAINED_COEF)
    return _tfidf_bonus(float(sim), coef=coef)


def personalized_synopsis_tfidf_bonus_for_candidate(sim: float) -> float:
    return _tfidf_bonus(float(sim), coef=float(SYNOPSIS_TFIDF_PERSONALIZED_COEF))


__all__ = [
    "SYNOPSIS_TFIDF_SCHEMA",
    "SYNOPSIS_TFIDF_MAX_FEATURES",
    "SYNOPSIS_TFIDF_NGRAM_RANGE",
    "SYNOPSIS_TFIDF_MIN_DF",
    "SYNOPSIS_TFIDF_MAX_DF",
    "SYNOPSIS_TFIDF_STOP_WORDS",
    "SYNOPSIS_TFIDF_TOKEN_PATTERN",
    "SYNOPSIS_TFIDF_MIN_SIM",
    "SYNOPSIS_TFIDF_MIN_EPISODES",
    "SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD",
    "SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY",
    "SYNOPSIS_TFIDF_COLD_START_COEF",
    "SYNOPSIS_TFIDF_TRAINED_COEF",
    "SYNOPSIS_TFIDF_PERSONALIZED_COEF",
    "SYNOPSIS_TFIDF_OFFTYPE_SHORT_PENALTY_BASE",
    "SYNOPSIS_TFIDF_OFFTYPE_SHORT_PENALTY_SIM_RELIEF",
    "SynopsisTfidfArtifact",
    "build_synopsis_tfidf_artifact",
    "validate_synopsis_tfidf_artifact",
    "choose_synopsis_text",
    "compute_seed_similarity_map",
    "most_common_seed_type",
    "synopsis_gate_passes",
    "synopsis_tfidf_penalty_for_candidate",
    "synopsis_tfidf_bonus_for_candidate",
    "personalized_synopsis_tfidf_bonus_for_candidate",
]
