"""Pure-Python scoring pipeline for MARS recommendations.

Architecture
------------
The recommendation pipeline operates in three stages:

**Stage 0 — Candidate Generation**
    Constrains the item universe to a focused candidate pool before any
    admission or scoring.  Three deterministic tiers feed the pool:
    neural semantic neighbors (primary), strict metadata overlap (confirmer),
    and a small popularity backfill (safety).

**Stage 1 — Shortlist Construction**
    Semantic admission gates filter the Stage 0 candidates into a shortlist
    of ~600 items, split into a semantic pool (A) and a metadata pool (B).
    Forced neural neighbors bypass the type/episode gate for high-confidence
    items.

**Stage 2 — Reranking**
    A hybrid scoring formula combines collaborative filtering (MF + kNN),
    content signals (neural/TF-IDF/embedding similarity), genre/theme/studio
    overlap, popularity boost, quality scaling, and obscurity penalties into
    a final score.  Post-processing applies franchise caps, personalization
    blend, and display filters.

Design constraint
-----------------
This module is **pure computation** — it must never import ``streamlit``.
All Streamlit interaction (session state reads, widget calls, rendering)
stays in ``app/main.py``.  The pipeline communicates exclusively through
the ``ScoringContext`` input dataclass and the ``PipelineResult`` output
dataclass.
"""

from __future__ import annotations

import logging
import math
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence

import numpy as np
import pandas as pd

# Local imports — NO streamlit allowed here.
from src.app.constants import (
    CONTENT_FIRST_ALPHA,
    DEFAULT_TOP_N,
    FORCE_NEURAL_MIN_SIM,
    FORCE_NEURAL_TOPK,
    FRANCHISE_CAP_TOP20,
    FRANCHISE_CAP_TOP50,
    FRANCHISE_TITLE_OVERLAP_THRESHOLD,
    OBSCURITY_LOW_MAL_PENALTY_SCALE,
    OBSCURITY_LOW_MAL_THRESHOLD,
    OBSCURITY_LOW_MEMBERS_PENALTY,
    OBSCURITY_MEMBERS_THRESHOLD,
    OBSCURITY_MISSING_MAL_PENALTY,
    QUALITY_FACTOR_MODE,
    SEED_RANKING_MODE,
    compute_quality_factor,
    STAGE0_ENFORCEMENT_BUFFER,
    STAGE0_META_MIN_GENRE_OVERLAP,
    STAGE0_META_MIN_THEME_OVERLAP,
    STAGE0_NEURAL_TOPK,
    STAGE0_POOL_CAP,
    STAGE0_POPULARITY_BACKFILL,
    STAGE2_GENRE_OVERLAP_WEIGHT,
    STAGE2_HYBRID_CF_WEIGHT,
    STAGE2_NEURAL_SIM_WEIGHT,
    STAGE2_POPULARITY_BOOST_WEIGHT,
    STAGE2_RAW_HYBRID_CONTRIBUTION_WEIGHT,
    STAGE2_RAW_KNN_GENRE_OVERLAP_WEIGHT,
    STAGE2_RAW_KNN_SEED_COVERAGE_WEIGHT,
    STAGE2_RAW_KNN_STAGE1_WEIGHT,
    STAGE2_SEED_COVERAGE_WEIGHT,
    STAGE2_STAGE1_SCORE_WEIGHT,
    USE_MEAN_USER_CF,
    force_neural_enable_for_semantic_mode,
)
from src.app.franchise_cap import apply_franchise_cap
from src.app.metadata_features import (
    METADATA_AFFINITY_COLD_START_COEF,
    METADATA_AFFINITY_PERSONALIZED_COEF,
    METADATA_AFFINITY_TRAINED_COEF,
    build_seed_metadata_profile,
    compute_metadata_affinity,
    demographics_overlap_tiebreak_bonus,
    theme_stage2_tiebreak_bonus,
)
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids
from src.app.recommender import (
    HybridComponents,
    HybridRecommender,
    compute_component_shares,
)
from src.app.semantic_admission import (
    STAGE1_DEMO_SHOUNEN_MIN_SIM_NEURAL,
    stage1_semantic_admission,
    theme_overlap_ratio,
)
from src.app.stage0_candidates import build_stage0_seed_candidate_pool
from src.app.stage1_shortlist import (
    build_stage1_shortlist,
    force_neural_enabled,
    select_forced_neural_pairs,
)
from src.app.stage2_overrides import (
    content_first_final_score,
    relax_off_type_penalty,
    should_use_content_first,
)
from src.app.synopsis_embeddings import (
    SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD,
    SYNOPSIS_EMBEDDINGS_MIN_SIM,
    SYNOPSIS_EMBEDDINGS_OFFTYPE_HIGH_SIM_PENALTY,
    compute_seed_similarity_map as compute_seed_embedding_similarity_map,
    personalized_synopsis_embeddings_bonus_for_candidate,
    synopsis_embeddings_bonus_for_candidate,
    synopsis_embeddings_penalty_for_candidate,
)
from src.app.synopsis_neural_embeddings import (
    SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD,
    SYNOPSIS_NEURAL_MIN_SIM,
    SYNOPSIS_NEURAL_OFFTYPE_HIGH_SIM_PENALTY,
    compute_seed_similarity_map as compute_seed_neural_similarity_map,
    synopsis_neural_bonus_for_candidate,
    synopsis_neural_penalty_for_candidate,
)
from src.app.synopsis_tfidf import (
    SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD,
    SYNOPSIS_TFIDF_MIN_SIM,
    SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY,
    compute_seed_similarity_map,
    most_common_seed_type,
    personalized_synopsis_tfidf_bonus_for_candidate,
    synopsis_gate_passes,
    synopsis_tfidf_bonus_for_candidate,
    synopsis_tfidf_penalty_for_candidate,
)
from src.app.explanations import format_explanation
from src.app.badges import badge_payload
from src.models.user_embedding import compute_personalized_scores
from src.utils import parse_pipe_set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

_TITLE_STOP = {
    "the", "and", "of", "to", "a", "an", "in", "on", "for", "with",
    "movie", "film", "tv", "ova", "ona", "special", "season", "part",
    "episode", "eps", "edition", "new",
}


def _title_tokens(s: str) -> set[str]:
    """Tokenize a title for franchise-like matching."""
    raw = str(s or "").lower()
    cleaned = "".join((ch if ch.isalnum() else " ") for ch in raw)
    toks = [t for t in cleaned.split() if len(t) >= 3 and t not in _TITLE_STOP]
    return set(toks)

# Removed _parse_str_set - now using canonical version from src.utils.parsing as parse_pipe_set


@dataclass
class ScoringContext:
    """All inputs the scoring pipeline needs — replaces all st.session_state reads.

    Attributes are grouped by category.  Optional attributes default to
    ``None`` or sensible empty values so callers only need to supply what
    their mode requires.
    """

    # --- Core data -----------------------------------------------------------
    metadata: pd.DataFrame
    """Full anime metadata DataFrame (13K+ rows)."""

    # --- Model artifacts -----------------------------------------------------
    bundle: dict[str, Any]
    """The full artifact bundle (metadata, models, explanations, diversity)."""

    recommender: HybridRecommender | None = None
    """Hybrid recommender instance (None if artifacts failed to load)."""

    components: HybridComponents | None = None
    """Hybrid score components (MF, kNN, popularity arrays)."""

    # --- Seed-based mode inputs ----------------------------------------------
    seed_ids: list[int] = field(default_factory=list)
    """Selected seed anime IDs (1–5)."""

    seed_titles: list[str] = field(default_factory=list)
    """Display titles corresponding to seed_ids."""

    # --- User / personalization inputs ---------------------------------------
    user_index: int = 0
    """Demo user index for hybrid scoring (default 0)."""

    user_embedding: np.ndarray | None = None
    """User taste embedding from profile ratings (for personalized mode)."""

    personalization_enabled: bool = False
    """Whether personalization is active."""

    personalization_strength: float = 1.0
    """Blend strength 0.0–1.0 (1.0 = pure personalized)."""

    active_profile: dict[str, Any] | None = None
    """The loaded user profile dict (ratings, watched_ids, etc.)."""

    watched_ids: set[int] = field(default_factory=set)
    """Anime IDs the user has already watched (for exclusion)."""

    personalization_blocked_reason: str | None = None
    """If set, personalization cannot run (reason string)."""

    # --- Weights & mode ------------------------------------------------------
    weights: dict[str, float] = field(default_factory=lambda: {"mf": 0.93078, "knn": 0.06625, "pop": 0.00297})
    """Hybrid weight preset."""

    seed_ranking_mode: str = "completion"
    """'completion' or 'discovery' — controls franchise cap behaviour."""

    # --- Filter inputs -------------------------------------------------------
    genre_filter: list[str] = field(default_factory=list)
    """Genre filter selections."""

    type_filter: list[str] = field(default_factory=list)
    """Type filter selections."""

    year_range: tuple[int, int] = (1960, 2025)
    """(year_min, year_max) inclusive range."""

    sort_by: str = "Match score"
    """Sort criterion."""

    default_sort_for_mode: str = "Match score"
    """Default sort for the current mode (to detect user override)."""

    n_requested: int = DEFAULT_TOP_N
    """How many results to request from the pipeline (before post-filters)."""

    top_n: int = DEFAULT_TOP_N
    """Final number of results to return after filters."""

    # --- Browse mode inputs --------------------------------------------------
    browse_mode: bool = False
    """Whether we're in browse (metadata-only) mode."""

    # --- Helpers (closures / lookups) ----------------------------------------
    pop_pct_fn: Callable[[int], float] | None = None
    """Popularity percentile lookup: anime_id → float in [0, 1]."""

    is_in_training_fn: Callable[[int], bool] | None = None
    """Cold-start detector: anime_id → bool."""

    # --- MF model reference (for personalized path) --------------------------
    mf_model: Any = None
    """MF model object (for personalized recommendations)."""

    mf_stem: str | None = None
    """MF artifact stem (for cache invalidation)."""

    user_embedding_meta: dict[str, Any] = field(default_factory=dict)
    """Metadata about user embedding (mf_stem, etc.)."""

    # --- Ranked hygiene (precomputed) ----------------------------------------
    ranked_hygiene_exclude_ids: set[int] = field(default_factory=set)
    """IDs to exclude from ranked results (bad formats, recaps)."""


@dataclass
class PipelineResult:
    """All outputs from a pipeline run.

    This replaces the scattered variables and st.session_state writes that
    previously lived inline in app/main.py.
    """

    ranked_items: list[dict[str, Any]] = field(default_factory=list)
    """Final ranked recommendation list (each dict has anime_id, score, explanation, etc.)."""

    # --- Diagnostics ---------------------------------------------------------
    stage0_diagnostics: dict[str, Any] = field(default_factory=dict)
    """Stage 0 candidate generation diagnostics."""

    stage1_diagnostics: dict[str, Any] = field(default_factory=dict)
    """Stage 1 shortlist construction diagnostics."""

    stage0_enforcement: dict[str, Any] = field(default_factory=dict)
    """Stage 0 enforcement diagnostics (scored count vs cap)."""

    franchise_cap_diagnostics: dict[str, Any] = field(default_factory=dict)
    """Discovery-mode franchise cap diagnostics."""

    diversity_stats: dict[str, Any] = field(default_factory=dict)
    """Beyond-accuracy diversity metrics (genre coverage, Gini index, etc.)."""

    # --- State flags ---------------------------------------------------------
    personalization_applied: bool = False
    """Whether personalization was actually applied."""

    personalization_blocked_reason: str | None = None
    """If personalization could not run, the reason."""

    active_scoring_path: str = ""
    """Human-readable description of the scoring path used."""

    # --- Timing --------------------------------------------------------------
    timing: dict[str, float] = field(default_factory=dict)
    """Timing measurements in seconds for major pipeline stages."""

    # --- Warnings / messages -------------------------------------------------
    warnings: list[str] = field(default_factory=list)
    """Non-fatal warnings generated during the pipeline run."""


# ---------------------------------------------------------------------------
# Internal helpers (pure functions migrated from app/main.py)
# ---------------------------------------------------------------------------

def _topk_sim_stats(
    sim_map: dict[int, float],
    k: int,
    exclude_ids: set[int],
    seed_ids: set[int],
    watched_ids: set[int],
) -> dict:
    """Compute mean/p95 of top-K similarity values for confidence gating."""
    vals: list[float] = []
    for aid, s in (sim_map or {}).items():
        try:
            aid_i = int(aid)
            if aid_i in exclude_ids or aid_i in seed_ids or aid_i in watched_ids:
                continue
            fs = float(s)
            if fs <= 0.0:
                continue
            vals.append(fs)
        except Exception:
            continue
    vals.sort(reverse=True)
    top = vals[:max(0, int(k))]
    if not top:
        return {"count": 0, "mean": 0.0, "p95": 0.0}
    arr = np.asarray(top, dtype=np.float64)
    mean = float(arr.mean())
    p95 = float(np.percentile(arr, 95)) if int(arr.size) >= 2 else float(arr[0])
    return {"count": int(arr.size), "mean": float(mean), "p95": float(p95)}


def _conf_score(stats: dict, min_sim: float, high_sim: float) -> float:
    """Normalized confidence score from similarity stats."""
    denom = float(max(1e-6, float(high_sim) - float(min_sim)))
    mean_n = max(0.0, min(1.0, (float(stats.get("mean", 0.0)) - float(min_sim)) / denom))
    p95_n = max(0.0, min(1.0, (float(stats.get("p95", 0.0)) - float(min_sim)) / denom))
    return float(0.5 * (mean_n + p95_n))


def _neighbor_coherence(pool: list[dict], k: int = 50) -> dict:
    """Compute neighborhood coherence statistics for confidence gating."""
    top = pool[:max(0, int(k))]
    if not top:
        return {"count": 0, "weighted_overlap_mean": 0.0, "seed_coverage_mean": 0.0, "any_genre_match_frac": 0.0}
    overlaps = [float(it.get("weighted_overlap", 0.0)) for it in top]
    coverages = [float(it.get("seed_coverage", 0.0)) for it in top]
    any_match = sum(1 for v in overlaps if float(v) > 0.0)
    return {
        "count": int(len(top)),
        "weighted_overlap_mean": float(sum(overlaps) / max(1, len(overlaps))),
        "seed_coverage_mean": float(sum(coverages) / max(1, len(coverages))),
        "any_genre_match_frac": float(any_match / max(1, len(overlaps))),
    }


def _coherence_score(stats: dict) -> float:
    """Scalar coherence score from neighborhood coherence stats."""
    overlap_mean = float(stats.get("weighted_overlap_mean", 0.0))
    seed_cov_mean = float(stats.get("seed_coverage_mean", 0.0))
    any_match = float(stats.get("any_genre_match_frac", 0.0))
    overlap_s = max(0.0, min(1.0, overlap_mean / 0.20))
    seedcov_s = max(0.0, min(1.0, seed_cov_mean / 0.50))
    any_s = max(0.0, min(1.0, any_match / 0.80))
    return float((overlap_s + seedcov_s + any_s) / 3.0)


# ---------------------------------------------------------------------------
# Browse pipeline
# ---------------------------------------------------------------------------

def run_browse_pipeline(ctx: ScoringContext) -> PipelineResult:
    """Browse-by-genre mode — metadata-only, no ranking model involved.

    Filters the catalog by genre, type, and year, then sorts by the chosen
    criterion.  Returns items with ``score=None`` and ``explanation=None``.
    """
    t0 = time.monotonic()
    result = PipelineResult(active_scoring_path="Browse")
    metadata = ctx.metadata

    if not ctx.genre_filter:
        # No genre selected → empty result with guidance
        result.timing["total"] = time.monotonic() - t0
        return result

    browse_results: list[dict[str, Any]] = []
    pop_pct_fn = ctx.pop_pct_fn or (lambda _aid: 0.5)

    for _, row in metadata.iterrows():
        anime_id = int(row["anime_id"])
        row_genres_val = row.get("genres")

        # Parse genres
        item_genres: set[str] = set()
        if isinstance(row_genres_val, str):
            item_genres = {g.strip() for g in row_genres_val.split("|") if g.strip()}
        elif hasattr(row_genres_val, "__iter__") and not isinstance(row_genres_val, str):
            item_genres = {str(g).strip() for g in row_genres_val if g}

        # Genre match
        if not any(gf in item_genres for gf in ctx.genre_filter):
            continue

        # Exclude watched
        if ctx.watched_ids and anime_id in ctx.watched_ids:
            continue

        # Type filter
        include = True
        if ctx.type_filter and "type" in metadata.columns:
            item_type = row.get("type")
            if pd.notna(item_type):
                type_str = str(item_type).strip()
                if type_str not in ctx.type_filter:
                    include = False
            else:
                include = False

        # Year filter
        if include and (ctx.year_range[0] > 1960 or ctx.year_range[1] < 2025):
            aired_from = row.get("aired_from")
            if aired_from and isinstance(aired_from, str):
                try:
                    year = int(aired_from[:4])
                    if not (ctx.year_range[0] <= year <= ctx.year_range[1]):
                        include = False
                except Exception:
                    include = False
            else:
                include = False

        if not include:
            continue

        rec: dict[str, Any] = {
            "anime_id": anime_id,
            "score": None,
            "explanation": None,
            "_mal_score": float(row.get("mal_score", 0) if pd.notna(row.get("mal_score")) else 0),
            "_year": 0,
            "_popularity": pop_pct_fn(anime_id),
        }
        aired_from = row.get("aired_from")
        if aired_from and isinstance(aired_from, str):
            try:
                rec["_year"] = int(aired_from[:4])
            except Exception:
                pass
        browse_results.append(rec)

    # Sort
    sort_by = ctx.sort_by
    if sort_by == "MAL Score":
        browse_results.sort(key=lambda x: x["_mal_score"], reverse=True)
    elif sort_by == "Year (Newest)":
        browse_results.sort(key=lambda x: x["_year"], reverse=True)
    elif sort_by == "Year (Oldest)":
        browse_results.sort(key=lambda x: x["_year"], reverse=False)
    elif sort_by == "Popularity":
        browse_results.sort(key=lambda x: x["_popularity"], reverse=False)
    else:
        browse_results.sort(key=lambda x: x["_mal_score"], reverse=True)

    result.ranked_items = browse_results[:min(ctx.top_n, len(browse_results))]
    result.timing["total"] = time.monotonic() - t0
    return result


# ---------------------------------------------------------------------------
# Seed-based pipeline
# ---------------------------------------------------------------------------

def run_seed_based_pipeline(ctx: ScoringContext) -> PipelineResult:
    """Full Stage 0 → Stage 1 → Stage 2 → post-processing pipeline.

    This is the core seed-based recommendation path.  It requires at least
    one seed ID and a working recommender/components pair.

    Returns a ``PipelineResult`` with ranked items, diagnostics, and timing.
    """
    t0 = time.monotonic()
    result = PipelineResult()
    timing: dict[str, float] = {}

    metadata = ctx.metadata
    selected_seed_ids = ctx.seed_ids
    selected_seed_titles = ctx.seed_titles
    recommender = ctx.recommender
    components = ctx.components
    user_index = ctx.user_index
    weights = ctx.weights
    n_requested = ctx.n_requested
    ranked_hygiene_exclude_ids = ctx.ranked_hygiene_exclude_ids
    watched_ids_set = ctx.watched_ids
    pop_pct_fn = ctx.pop_pct_fn or (lambda _aid: 0.5)

    if not selected_seed_ids:
        result.active_scoring_path = "Seedless"
        if recommender is not None:
            recs = recommender.get_top_n_for_user(
                user_index,
                n=n_requested,
                weights=weights,
                exclude_item_ids=sorted(ranked_hygiene_exclude_ids),
            )
            result.ranked_items = recs
        result.timing["total"] = time.monotonic() - t0
        return result

    result.active_scoring_path = "Seed-based" if len(selected_seed_ids) == 1 else "Multi-seed"

    # ------------------------------------------------------------------
    # Build seed genre map and aggregates
    # ------------------------------------------------------------------
    t_prep = time.monotonic()
    seed_genre_map: dict[str, set[str]] = {}
    all_seed_genres: set[str] = set()
    genre_weights: dict[str, int] = {}

    # Create indexed lookup for O(1) access (performance optimization)
    metadata_by_id = metadata.set_index("anime_id", drop=False)

    for seed_id, seed_title in zip(selected_seed_ids, selected_seed_titles):
        try:
            seed_row = metadata_by_id.loc[seed_id]
            row_genres = seed_row.get("genres") if isinstance(seed_row, pd.Series) else None
        except KeyError:
            continue
        
        if row_genres is not None:
            if isinstance(row_genres, str):
                seed_genres = {g.strip() for g in row_genres.split("|") if g.strip()}
            elif hasattr(row_genres, "__iter__") and not isinstance(row_genres, str):
                seed_genres = {str(g).strip() for g in row_genres if g}
            else:
                seed_genres = set()

            seed_genre_map[seed_title] = seed_genres
            all_seed_genres.update(seed_genres)
            for genre in seed_genres:
                genre_weights[genre] = genre_weights.get(genre, 0) + 1

    seed_title_token_map: dict[str, set[str]] = {
        str(t): _title_tokens(str(t)) for t in (selected_seed_titles or [])
    }

    seed_meta_profile = build_seed_metadata_profile(metadata, seed_ids=selected_seed_ids)

    # ------------------------------------------------------------------
    # Semantic rerank artifacts
    # ------------------------------------------------------------------
    synopsis_tfidf_artifact = ctx.bundle.get("models", {}).get("synopsis_tfidf")
    synopsis_embeddings_artifact = ctx.bundle.get("models", {}).get("synopsis_embeddings")
    synopsis_neural_artifact = ctx.bundle.get("models", {}).get("synopsis_neural_embeddings")

    semantic_mode = str(os.environ.get("PHASE4_SEMANTIC_MODE", "")).strip().lower()
    if semantic_mode not in {"neural", "embeddings", "tfidf", "both", "none", ""}:
        semantic_mode = ""
    if not semantic_mode:
        if synopsis_neural_artifact is not None:
            semantic_mode = "neural"
        elif synopsis_embeddings_artifact is not None and synopsis_tfidf_artifact is not None:
            semantic_mode = "both"
        elif synopsis_embeddings_artifact is not None:
            semantic_mode = "embeddings"
        elif synopsis_tfidf_artifact is not None:
            semantic_mode = "tfidf"
        else:
            semantic_mode = "none"

    synopsis_sims_by_id: dict[int, float] = {}
    embed_sims_by_id: dict[int, float] = {}
    neural_sims_by_id: dict[int, float] = {}
    seed_type_target: str | None = None

    try:
        seed_type_target = most_common_seed_type(metadata, selected_seed_ids)
    except Exception:
        seed_type_target = None

    if semantic_mode in {"tfidf", "both"} and synopsis_tfidf_artifact is not None:
        try:
            synopsis_sims_by_id = compute_seed_similarity_map(
                synopsis_tfidf_artifact, seed_ids=selected_seed_ids
            )
        except Exception:
            synopsis_sims_by_id = {}

    if semantic_mode in {"embeddings", "both"} and synopsis_embeddings_artifact is not None:
        try:
            embed_sims_by_id = compute_seed_embedding_similarity_map(
                synopsis_embeddings_artifact, seed_ids=selected_seed_ids
            )
        except Exception:
            embed_sims_by_id = {}

    if semantic_mode in {"neural"} and synopsis_neural_artifact is not None:
        try:
            min_sim_neural = float(SYNOPSIS_NEURAL_MIN_SIM)
            if bool(force_neural_enabled(semantic_mode=semantic_mode)):
                min_sim_neural = float(min(float(min_sim_neural), float(FORCE_NEURAL_MIN_SIM)))
            neural_sims_by_id = compute_seed_neural_similarity_map(
                synopsis_neural_artifact,
                seed_ids=selected_seed_ids,
                min_sim=float(min_sim_neural),
            )
        except Exception:
            neural_sims_by_id = {}

    num_seeds = len(selected_seed_ids)
    seed_shortlist_size = 600
    timing["prep"] = time.monotonic() - t_prep

    # ------------------------------------------------------------------
    # Stage 0: Seed-conditioned candidate pool
    # ------------------------------------------------------------------
    t_s0 = time.monotonic()
    stage0_ids, stage0_flags_by_id, stage0_diag = build_stage0_seed_candidate_pool(
        metadata=metadata,
        seed_ids=list(selected_seed_ids),
        ranked_hygiene_exclude_ids=set(ranked_hygiene_exclude_ids),
        watched_ids=set(watched_ids_set),
        neural_artifact=synopsis_neural_artifact,
        neural_topk=int(STAGE0_NEURAL_TOPK),
        meta_min_genre_overlap=float(STAGE0_META_MIN_GENRE_OVERLAP),
        meta_min_theme_overlap=float(STAGE0_META_MIN_THEME_OVERLAP),
        popularity_backfill=int(STAGE0_POPULARITY_BACKFILL),
        pool_cap=int(STAGE0_POOL_CAP),
        pop_item_ids=(components.item_ids if components is not None else None),
        pop_scores=(components.pop if components is not None else None),
    )

    result.stage0_diagnostics = {
        "stage0_pool_raw": int(stage0_diag.stage0_pool_raw),
        "stage0_raw_counts_by_tier": {
            "stage0_from_neural": int(stage0_diag.stage0_from_neural_raw),
            "stage0_from_meta_strict": int(stage0_diag.stage0_from_meta_strict_raw),
            "stage0_from_popularity": int(stage0_diag.stage0_from_popularity_raw),
        },
        "stage0_after_hygiene": int(stage0_diag.stage0_after_hygiene),
        "stage0_after_cap": int(stage0_diag.stage0_after_cap),
        "stage0_after_cap_counts_by_tier": {
            "stage0_from_neural": int(stage0_diag.stage0_from_neural),
            "stage0_from_meta_strict": int(stage0_diag.stage0_from_meta_strict),
            "stage0_from_popularity": int(stage0_diag.stage0_from_popularity),
        },
        "stage0_overlap_counts": {
            "stage0_neural_only": int(stage0_diag.stage0_neural_only),
            "stage0_meta_only": int(stage0_diag.stage0_meta_only),
            "stage0_pop_only": int(stage0_diag.stage0_pop_only),
            "stage0_neural_and_meta": int(stage0_diag.stage0_neural_and_meta),
        },
    }

    candidate_ids = [int(x) for x in (stage0_ids or []) if int(x) > 0]
    candidate_id_set = {int(x) for x in candidate_ids}

    if candidate_id_set:
        try:
            candidate_df = metadata.loc[metadata["anime_id"].astype(int).isin(candidate_id_set)]
        except Exception:
            candidate_df = metadata
    else:
        candidate_df = metadata.iloc[0:0]

    logger.info(
        "Stage0(seed-based) pool_raw=%s after_hygiene=%s after_cap=%s "
        "src_raw(neural/meta_strict/pop)=%s/%s/%s "
        "overlap(neural_only/meta_only/pop_only/neural_and_meta)=%s/%s/%s/%s",
        int(stage0_diag.stage0_pool_raw),
        int(stage0_diag.stage0_after_hygiene),
        int(stage0_diag.stage0_after_cap),
        int(stage0_diag.stage0_from_neural_raw),
        int(stage0_diag.stage0_from_meta_strict_raw),
        int(stage0_diag.stage0_from_popularity_raw),
        int(stage0_diag.stage0_neural_only),
        int(stage0_diag.stage0_meta_only),
        int(stage0_diag.stage0_pop_only),
        int(stage0_diag.stage0_neural_and_meta),
    )
    timing["stage0"] = time.monotonic() - t_s0

    # ------------------------------------------------------------------
    # Stage 1: Shortlist construction
    # ------------------------------------------------------------------
    t_s1 = time.monotonic()
    stage1_embed_pool: list[dict] = []
    stage1_tfidf_pool: list[dict] = []
    stage1_neural_pool: list[dict] = []
    stage1_forced_neural_pool: list[dict] = []
    stage1_fallback_pool: list[dict] = []

    seed_genres_count = int(len(all_seed_genres))
    seed_themes = getattr(seed_meta_profile, "themes", frozenset()) or frozenset()

    forced_neural_pairs: list[tuple[int, float]] = []
    forced_neural_ids: set[int] = set()
    if (
        semantic_mode in {"neural"}
        and synopsis_neural_artifact is not None
        and bool(force_neural_enabled(semantic_mode=semantic_mode))
        and bool(neural_sims_by_id)
    ):
        forced_neural_pairs = select_forced_neural_pairs(
            neural_sims_by_id,
            seed_ids=selected_seed_ids,
            exclude_ids=set(ranked_hygiene_exclude_ids),
            watched_ids=set(watched_ids_set),
            topk=int(FORCE_NEURAL_TOPK),
            min_sim=float(FORCE_NEURAL_MIN_SIM),
        )
        forced_neural_ids = {int(aid) for aid, _ in forced_neural_pairs}

    # Stage 1 operates ONLY over Stage 0 candidates.
    for _, mrow in candidate_df.iterrows():
        aid = int(mrow["anime_id"])
        if aid in selected_seed_ids:
            continue
        if aid in ranked_hygiene_exclude_ids:
            continue
        if aid in watched_ids_set:
            continue

        row_genres = mrow.get("genres")
        if isinstance(row_genres, str):
            item_genres = {g.strip() for g in row_genres.split("|") if g.strip()}
        elif hasattr(row_genres, "__iter__") and not isinstance(row_genres, str):
            item_genres = {str(g).strip() for g in row_genres if g}
        else:
            item_genres = set()

        item_themes = parse_pipe_set(mrow.get("themes"))

        raw_overlap = sum(genre_weights.get(g, 0) for g in item_genres)
        max_possible_overlap = len(all_seed_genres) * num_seeds
        weighted_overlap = raw_overlap / max_possible_overlap if max_possible_overlap > 0 else 0.0

        overlap_per_seed = {
            seed_title: len(seed_genres & item_genres)
            for seed_title, seed_genres in seed_genre_map.items()
        }
        num_seeds_matched = sum(1 for count in overlap_per_seed.values() if count > 0)
        seed_coverage = num_seeds_matched / num_seeds

        meta_affinity = compute_metadata_affinity(seed_meta_profile, mrow)
        meta_bonus_s1 = 0.0
        if meta_affinity > 0.0:
            meta_bonus_s1 = float(METADATA_AFFINITY_COLD_START_COEF) * float(meta_affinity)

        synopsis_tfidf_sim = float(synopsis_sims_by_id.get(aid, 0.0))
        synopsis_embed_sim = float(embed_sims_by_id.get(aid, 0.0))
        synopsis_neural_sim = float(neural_sims_by_id.get(aid, 0.0))

        cand_title = str(mrow.get("title_display") or mrow.get("title_primary") or "")
        cand_tokens = _title_tokens(cand_title)
        title_overlap = 0.0
        for _, stoks in seed_title_token_map.items():
            if not stoks:
                continue
            try:
                title_overlap = max(title_overlap, float(len(stoks & cand_tokens)) / float(len(stoks)))
            except Exception:
                continue
        title_bonus_s1 = 0.40 * float(title_overlap)
        cand_type = None if pd.isna(mrow.get("type")) else str(mrow.get("type")).strip()
        cand_eps = mrow.get("episodes")
        base_passes_gate = synopsis_gate_passes(
            seed_type=seed_type_target,
            candidate_type=cand_type,
            candidate_episodes=cand_eps,
        )

        high_sim_override_tfidf = (not bool(base_passes_gate)) and (
            float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD)
        )
        high_sim_override_embed = (not bool(base_passes_gate)) and (
            float(synopsis_embed_sim) >= float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD)
        )
        high_sim_override_neural = (not bool(base_passes_gate)) and (
            float(synopsis_neural_sim) >= float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD)
        )

        base = {
            "anime_id": aid,
            "mrow": mrow,
            "item_genres": item_genres,
            "weighted_overlap": float(weighted_overlap),
            "theme_overlap": theme_overlap_ratio(seed_themes, item_themes),
            "seed_coverage": float(seed_coverage),
            "overlap_per_seed": overlap_per_seed,
            "seeds_matched": int(num_seeds_matched),
            "metadata_affinity": float(meta_affinity),
            "title_overlap": float(title_overlap),
            "synopsis_tfidf_sim": float(synopsis_tfidf_sim),
            "synopsis_embed_sim": float(synopsis_embed_sim),
            "synopsis_neural_sim": float(synopsis_neural_sim),
            "passes_gate": bool(base_passes_gate),
            "synopsis_tfidf_high_sim_override": bool(high_sim_override_tfidf),
            "synopsis_embed_high_sim_override": bool(high_sim_override_embed),
            "synopsis_neural_high_sim_override": bool(high_sim_override_neural),
            "cand_type": cand_type,
            "cand_eps": cand_eps,
            "forced_neural": bool(aid in forced_neural_ids),
        }

        # Force-include top-K neural neighbors into Stage 1 shortlist.
        if bool(base.get("forced_neural")) and float(synopsis_neural_sim) >= float(FORCE_NEURAL_MIN_SIM):
            forced_item = dict(base)
            forced_item["stage1_score"] = float(synopsis_neural_sim)
            stage1_forced_neural_pool.append(forced_item)

        # Neural-first pool (gated)
        passes_gate_effective_neural = bool(base_passes_gate) or bool(high_sim_override_neural)
        if semantic_mode in {"neural"} and bool(passes_gate_effective_neural):
            neural_decision = stage1_semantic_admission(
                semantic_sim=float(synopsis_neural_sim),
                min_sim=float(SYNOPSIS_NEURAL_MIN_SIM),
                high_sim=float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD),
                genre_overlap=float(weighted_overlap),
                title_overlap=float(title_overlap),
                seed_genres_count=int(seed_genres_count),
                num_seeds=int(num_seeds),
                theme_overlap=theme_overlap_ratio(seed_themes, item_themes),
                seed_demographics=getattr(seed_meta_profile, "demographics", frozenset()) or frozenset(),
                candidate_demographics=mrow.get("demographics"),
                demo_shounen_min_sim=float(STAGE1_DEMO_SHOUNEN_MIN_SIM_NEURAL),
            )
            if bool(neural_decision.admitted):
                item = dict(base)
                item["stage1_score"] = float(synopsis_neural_sim)
                stage1_neural_pool.append(item)
                continue

        # Embeddings-first pool (gated)
        passes_gate_effective_embed = bool(base_passes_gate) or bool(high_sim_override_embed)
        if (
            semantic_mode in {"embeddings", "both"}
            and bool(passes_gate_effective_embed)
            and bool(
                stage1_semantic_admission(
                    semantic_sim=float(synopsis_embed_sim),
                    min_sim=float(SYNOPSIS_EMBEDDINGS_MIN_SIM),
                    high_sim=float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD),
                    genre_overlap=float(weighted_overlap),
                    title_overlap=float(title_overlap),
                    seed_genres_count=int(seed_genres_count),
                    num_seeds=int(num_seeds),
                    theme_overlap=theme_overlap_ratio(seed_themes, item_themes),
                ).admitted
            )
        ):
            item = dict(base)
            item["stage1_score"] = float(synopsis_embed_sim)
            stage1_embed_pool.append(item)
            continue

        # TF-IDF-first pool (gated)
        passes_gate_effective_tfidf = bool(base_passes_gate) or bool(high_sim_override_tfidf)
        if (
            semantic_mode in {"tfidf", "both"}
            and bool(passes_gate_effective_tfidf)
            and bool(
                stage1_semantic_admission(
                    semantic_sim=float(synopsis_tfidf_sim),
                    min_sim=float(SYNOPSIS_TFIDF_MIN_SIM),
                    high_sim=float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD),
                    genre_overlap=float(weighted_overlap),
                    title_overlap=float(title_overlap),
                    seed_genres_count=int(seed_genres_count),
                    num_seeds=int(num_seeds),
                    theme_overlap=theme_overlap_ratio(seed_themes, item_themes),
                ).admitted
            )
        ):
            item = dict(base)
            item["stage1_score"] = float(synopsis_tfidf_sim)
            stage1_tfidf_pool.append(item)
            continue

        # Backfill pool
        fallback_score = (
            (0.5 * float(weighted_overlap))
            + (0.2 * float(seed_coverage))
            + float(meta_bonus_s1)
            + float(title_bonus_s1)
        )
        if float(fallback_score) > 0.0:
            item = dict(base)
            item["stage1_score"] = float(fallback_score)
            stage1_fallback_pool.append(item)

    # Sort pools
    stage1_embed_pool.sort(
        key=lambda x: (
            -float(x.get("synopsis_embed_sim", 0.0)),
            -float(x.get("weighted_overlap", 0.0)),
            -float(x.get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_tfidf_pool.sort(
        key=lambda x: (
            -float(x.get("synopsis_tfidf_sim", 0.0)),
            -float(x.get("weighted_overlap", 0.0)),
            -float(x.get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_neural_pool.sort(
        key=lambda x: (
            -float(x.get("synopsis_neural_sim", 0.0)),
            -float(x.get("weighted_overlap", 0.0)),
            -float(x.get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_forced_neural_pool.sort(
        key=lambda x: (-float(x.get("synopsis_neural_sim", 0.0)), int(x.get("anime_id", 0)))
    )
    stage1_fallback_pool.sort(
        key=lambda x: (-float(x.get("stage1_score", 0.0)), int(x.get("anime_id", 0)))
    )

    # Confidence gating
    pool_a: list[dict] = []
    pool_a.extend(stage1_neural_pool)
    pool_a.extend(stage1_embed_pool)
    pool_a.extend(stage1_tfidf_pool)
    pool_b: list[dict] = list(stage1_fallback_pool)

    seed_ids_set = set(selected_seed_ids)

    semantic_conf_tier = "none"
    semantic_conf_score = 0.0
    if semantic_mode in {"embeddings", "both"} and synopsis_embeddings_artifact is not None and embed_sims_by_id:
        stats = _topk_sim_stats(embed_sims_by_id, k=50, exclude_ids=ranked_hygiene_exclude_ids, seed_ids=seed_ids_set, watched_ids=watched_ids_set)
        if int(stats.get("count", 0)) > 0:
            sim_conf = _conf_score(stats, float(SYNOPSIS_EMBEDDINGS_MIN_SIM), float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD))
            coh_conf = _coherence_score(_neighbor_coherence(stage1_embed_pool, k=50))
            semantic_conf_score = float(0.70 * float(sim_conf) + 0.30 * float(coh_conf))
    elif semantic_mode in {"tfidf", "both"} and synopsis_tfidf_artifact is not None and synopsis_sims_by_id:
        stats = _topk_sim_stats(synopsis_sims_by_id, k=50, exclude_ids=ranked_hygiene_exclude_ids, seed_ids=seed_ids_set, watched_ids=watched_ids_set)
        if int(stats.get("count", 0)) > 0:
            sim_conf = _conf_score(stats, float(SYNOPSIS_TFIDF_MIN_SIM), float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD))
            coh_conf = _coherence_score(_neighbor_coherence(stage1_tfidf_pool, k=50))
            semantic_conf_score = float(0.70 * float(sim_conf) + 0.30 * float(coh_conf))

    if semantic_conf_score <= 0.0:
        semantic_conf_tier = "none"
    elif float(semantic_conf_score) >= 0.60:
        semantic_conf_tier = "high"
    elif float(semantic_conf_score) >= 0.30:
        semantic_conf_tier = "medium"
    else:
        semantic_conf_tier = "low"

    if semantic_conf_tier == "high":
        sem_frac = 0.50
    elif semantic_conf_tier == "medium":
        sem_frac = 0.40
    elif semantic_conf_tier == "low":
        sem_frac = 0.20
    else:
        sem_frac = 0.0

    k_sem = int(round(float(seed_shortlist_size) * float(sem_frac)))
    k_sem = max(0, min(int(seed_shortlist_size), int(k_sem)))
    k_meta = int(seed_shortlist_size) - int(k_sem)

    shortlist, _forced_added = build_stage1_shortlist(
        pool_a=pool_a,
        pool_b=pool_b,
        shortlist_k=int(seed_shortlist_size),
        k_sem=int(k_sem),
        k_meta=int(k_meta),
        forced_first=stage1_forced_neural_pool,
    )

    result.stage1_diagnostics = {
        "stage1_iterated_candidate_count": int(len(candidate_df)),
        "shortlist_size": int(len(shortlist)),
        "semantic_conf_tier": semantic_conf_tier,
        "semantic_conf_score": float(semantic_conf_score),
        "pool_a_size": len(pool_a),
        "pool_b_size": len(pool_b),
        "k_sem": k_sem,
        "k_meta": k_meta,
    }

    result.stage0_enforcement = {
        "stage0_after_hygiene_size": int(stage0_diag.stage0_after_hygiene),
        "stage1_iterated_candidate_count": int(len(candidate_df)),
        "shortlist_size": int(len(shortlist)),
    }
    timing["stage1"] = time.monotonic() - t_s1

    # ------------------------------------------------------------------
    # Stage 2: Rerank shortlist
    # ------------------------------------------------------------------
    t_s2 = time.monotonic()
    
    # Determine which user vector to use for CF scoring (Phase 2, Task 2.1)
    # If personalization is disabled and USE_MEAN_USER_CF is True, use mean-user scores
    # to represent community preferences instead of one arbitrary training user.
    use_mean_user = bool(USE_MEAN_USER_CF) and not ctx.personalization_enabled
    mf_mean_user_scores = ctx.bundle.get("models", {}).get("mf_mean_user_scores")
    
    # Personalized MF scores array (built once, reused for blended_scores
    # and per-item hybrid_cf_score when personalization is enabled).
    _pers_mf_array: np.ndarray | None = None
    _pers_strength = float(ctx.personalization_strength) if ctx.personalization_enabled else 0.0
    if (
        ctx.personalization_enabled
        and ctx.user_embedding is not None
        and ctx.mf_model is not None
        and _pers_strength > 0.01
    ):
        try:
            _pers_scores_dict = compute_personalized_scores(ctx.user_embedding, ctx.mf_model)
            _pers_mf_array = np.zeros(components.num_items, dtype=np.float32)
            for _pi, _pid in enumerate(components.item_ids):
                if int(_pid) in _pers_scores_dict:
                    _pers_mf_array[_pi] = _pers_scores_dict[int(_pid)]
        except Exception:
            _pers_mf_array = None

    try:
        if use_mean_user and mf_mean_user_scores is not None:
            # Build hybrid scores using mean-user MF component
            blended_scores = np.zeros(components.num_items, dtype=np.float32)
            
            # MF component: use precomputed mean-user scores
            if components.mf is not None:
                w_mf = weights.get("mf", 0.0)
                blended_scores += w_mf * mf_mean_user_scores
            
            # kNN component: still uses user_index (typically 0 for seed-based)
            if components.knn is not None:
                w_knn = weights.get("knn", 0.0)
                blended_scores += w_knn * components.knn[user_index]
            
            # Popularity component: broadcast across items
            if components.pop is not None:
                w_pop = weights.get("pop", 0.0)
                blended_scores += w_pop * components.pop
        else:
            # Use standard blend with user_index (preserves current behavior)
            blended_scores = recommender._blend(user_index, weights)  # pylint: disable=protected-access
    except Exception:
        blended_scores = None

    # When personalization is enabled with seeds, blend personal MF scores
    # into the hybrid CF component. Seeds shape the candidate pool (Stage 0/1),
    # personal taste re-ranks within that pool via the CF signal.
    if _pers_mf_array is not None and blended_scores is not None:
        _pers_blended = np.zeros(components.num_items, dtype=np.float32)
        _pers_blended += float(weights.get("mf", 0.0)) * _pers_mf_array
        if components.knn is not None:
            _pers_blended += float(weights.get("knn", 0.0)) * components.knn[user_index]
        if components.pop is not None:
            _pers_blended += float(weights.get("pop", 0.0)) * components.pop
        blended_scores = _pers_strength * _pers_blended + (1.0 - _pers_strength) * blended_scores

    id_to_index = {int(aid): idx for idx, aid in enumerate(components.item_ids)}
    scored: list[dict] = []

    for c in shortlist:
        aid = int(c["anime_id"])
        mrow = c["mrow"]
        item_genres = c["item_genres"]
        weighted_overlap = float(c["weighted_overlap"])
        seed_coverage = float(c["seed_coverage"])
        overlap_per_seed = c["overlap_per_seed"]
        num_seeds_matched = int(c["seeds_matched"])

        pop_pct = pop_pct_fn(aid)
        popularity_boost = max(0.0, (0.5 - pop_pct) / 0.5)

        if blended_scores is not None and aid in id_to_index:
            hybrid_val = float(blended_scores[id_to_index[aid]])
        else:
            hybrid_val = 0.0

        # CF-only hybrid score (mf/knn only; pop excluded) for content-first blend.
        hybrid_cf_score = 0.0
        if aid in id_to_index:
            idx = int(id_to_index[aid])
            try:
                # Use mean-user MF scores if enabled, otherwise use user_index
                if use_mean_user and mf_mean_user_scores is not None:
                    mf_base = float(mf_mean_user_scores[idx]) if idx < len(mf_mean_user_scores) else 0.0
                else:
                    mf_base = float(components.mf[user_index, idx]) if components.mf is not None else 0.0
            except Exception:
                mf_base = 0.0
            # Blend personalized MF into mf_base when available
            if _pers_mf_array is not None:
                try:
                    mf_base_pers = float(_pers_mf_array[idx])
                    mf_base = _pers_strength * mf_base_pers + (1.0 - _pers_strength) * mf_base
                except Exception:
                    pass
            try:
                knn_base = float(components.knn[user_index, idx]) if components.knn is not None else 0.0
            except Exception:
                knn_base = 0.0
            hybrid_cf_score = float((0.93 * mf_base) + (0.07 * knn_base))

        # Gated content-first scoring
        synopsis_neural_sim = float(c.get("synopsis_neural_sim", 0.0))
        content_first_active = bool(
            should_use_content_first(
                float(hybrid_cf_score),
                semantic_mode=str(semantic_mode),
                sem_conf=str(semantic_conf_tier),
                neural_sim=float(synopsis_neural_sim),
            )
        )

        meta_affinity = float(c.get("metadata_affinity", 0.0))
        meta_bonus = 0.0
        if meta_affinity > 0.0:
            coef = float(METADATA_AFFINITY_COLD_START_COEF) if hybrid_val == 0.0 else float(METADATA_AFFINITY_TRAINED_COEF)
            meta_bonus = float(coef) * float(meta_affinity)

        synopsis_tfidf_sim = float(c.get("synopsis_tfidf_sim", 0.0))
        synopsis_embed_sim = float(c.get("synopsis_embed_sim", 0.0))
        passes_gate = bool(c.get("passes_gate", False))
        high_sim_override_tfidf = (not bool(passes_gate)) and (
            float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD)
        )
        high_sim_override_embed = (not bool(passes_gate)) and (
            float(synopsis_embed_sim) >= float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD)
        )
        high_sim_override_neural = (not bool(passes_gate)) and (
            float(synopsis_neural_sim) >= float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD)
        )
        passes_gate_effective_tfidf = bool(passes_gate) or bool(high_sim_override_tfidf)
        passes_gate_effective_embed = bool(passes_gate) or bool(high_sim_override_embed)
        passes_gate_effective_neural = bool(passes_gate) or bool(high_sim_override_neural)
        cand_eps = c.get("cand_eps")

        # Hybrid value adjustments for high-sim overrides.
        hybrid_val_for_scoring = float(hybrid_val)
        hybrid_val_for_tfidf = float(hybrid_val)
        hybrid_val_for_embed = float(hybrid_val)
        hybrid_val_for_neural = float(hybrid_val)
        if bool(high_sim_override_tfidf) or bool(high_sim_override_embed) or bool(high_sim_override_neural):
            hybrid_val_for_scoring = max(0.0, float(hybrid_val))
        if bool(high_sim_override_tfidf):
            hybrid_val_for_tfidf = 0.0
        if bool(high_sim_override_embed):
            hybrid_val_for_embed = 0.0
        if bool(high_sim_override_neural):
            hybrid_val_for_neural = 0.0

        # TF-IDF synopsis adjustment
        synopsis_tfidf_bonus = 0.0
        synopsis_tfidf_penalty = 0.0
        synopsis_tfidf_adjustment = 0.0
        if semantic_mode in {"tfidf", "both"}:
            if bool(passes_gate_effective_tfidf):
                synopsis_tfidf_bonus = float(
                    synopsis_tfidf_bonus_for_candidate(
                        sim=synopsis_tfidf_sim,
                        hybrid_val=hybrid_val_for_tfidf,
                    )
                )
            if bool(high_sim_override_tfidf):
                synopsis_tfidf_penalty = -float(SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY)
            else:
                synopsis_tfidf_penalty = float(
                    synopsis_tfidf_penalty_for_candidate(
                        passes_gate=passes_gate,
                        sim=synopsis_tfidf_sim,
                        candidate_episodes=cand_eps,
                    )
                )
            synopsis_tfidf_adjustment = float(synopsis_tfidf_bonus + synopsis_tfidf_penalty)

        # Embeddings synopsis adjustment
        synopsis_embed_bonus = 0.0
        synopsis_embed_penalty = 0.0
        synopsis_embed_adjustment = 0.0
        if semantic_mode in {"embeddings", "both"}:
            if bool(passes_gate_effective_embed):
                synopsis_embed_bonus = float(
                    synopsis_embeddings_bonus_for_candidate(
                        sim=synopsis_embed_sim,
                        hybrid_val=hybrid_val_for_embed,
                    )
                )
            if bool(high_sim_override_embed):
                synopsis_embed_penalty = -float(SYNOPSIS_EMBEDDINGS_OFFTYPE_HIGH_SIM_PENALTY)
            else:
                synopsis_embed_penalty = float(
                    synopsis_embeddings_penalty_for_candidate(
                        passes_gate=passes_gate,
                        sim=synopsis_embed_sim,
                        candidate_episodes=cand_eps,
                    )
                )
            synopsis_embed_adjustment = float(synopsis_embed_bonus + synopsis_embed_penalty)

        # Neural synopsis adjustment
        synopsis_neural_bonus = 0.0
        synopsis_neural_penalty = 0.0
        synopsis_neural_adjustment = 0.0
        if semantic_mode in {"neural"}:
            if bool(passes_gate_effective_neural):
                synopsis_neural_bonus = float(
                    synopsis_neural_bonus_for_candidate(
                        sim=synopsis_neural_sim,
                        hybrid_val=hybrid_val_for_neural,
                    )
                )
            if bool(high_sim_override_neural):
                synopsis_neural_penalty = -float(SYNOPSIS_NEURAL_OFFTYPE_HIGH_SIM_PENALTY)
            else:
                synopsis_neural_penalty = float(
                    synopsis_neural_penalty_for_candidate(
                        passes_gate=passes_gate,
                        sim=synopsis_neural_sim,
                        candidate_episodes=cand_eps,
                    )
                )
            synopsis_neural_penalty = float(
                relax_off_type_penalty(
                    penalty=float(synopsis_neural_penalty),
                    neural_sim=float(synopsis_neural_sim),
                    semantic_mode=str(semantic_mode),
                    browse_mode=False,
                )
            )
            synopsis_neural_adjustment = float(synopsis_neural_bonus + synopsis_neural_penalty)

        # Tie-breakers
        if "demographics" in metadata.columns:
            demo_bonus = demographics_overlap_tiebreak_bonus(
                seed_meta_profile.demographics,
                mrow.get("demographics"),
            )
        else:
            demo_bonus = 0.0

        theme_overlap = c.get("theme_overlap")
        semantic_sim_for_theme = max(float(synopsis_tfidf_sim), float(synopsis_embed_sim), float(synopsis_neural_sim))
        theme_bonus = theme_stage2_tiebreak_bonus(
            None if theme_overlap is None else float(theme_overlap),
            semantic_sim=float(semantic_sim_for_theme),
            genre_overlap=float(weighted_overlap),
        )

        s1 = float(c.get("stage1_score", 0.0))

        # Quality scaling
        try:
            item_mal_score = None if pd.isna(mrow.get("mal_score")) else float(mrow.get("mal_score"))
        except Exception:
            item_mal_score = None
        try:
            item_members_count = None if pd.isna(mrow.get("members_count")) else int(mrow.get("members_count"))
        except Exception:
            item_members_count = None

        # Compute quality factor using configurable mode
        quality_factor = compute_quality_factor(item_mal_score, mode=QUALITY_FACTOR_MODE)

        neural_contribution = STAGE2_NEURAL_SIM_WEIGHT * float(synopsis_neural_sim) * quality_factor

        # Final score formula
        score_before = (
            (STAGE2_GENRE_OVERLAP_WEIGHT * weighted_overlap)
            + (STAGE2_SEED_COVERAGE_WEIGHT * seed_coverage)
            + (STAGE2_HYBRID_CF_WEIGHT * float(hybrid_val_for_scoring))
            + (STAGE2_POPULARITY_BOOST_WEIGHT * popularity_boost)
            + (STAGE2_STAGE1_SCORE_WEIGHT * float(s1))
            + neural_contribution
            + meta_bonus
            + synopsis_tfidf_adjustment
            + synopsis_embed_adjustment
            + synopsis_neural_adjustment
            + float(demo_bonus)
            + float(theme_bonus)
        )

        # Obscurity/quality penalty
        obscurity_penalty = 0.0
        if item_members_count is not None and item_members_count < OBSCURITY_MEMBERS_THRESHOLD:
            obscurity_penalty += OBSCURITY_LOW_MEMBERS_PENALTY
        if item_mal_score is None:
            obscurity_penalty += OBSCURITY_MISSING_MAL_PENALTY
        elif item_mal_score < OBSCURITY_LOW_MAL_THRESHOLD:
            obscurity_penalty += max(
                0.0, OBSCURITY_LOW_MAL_PENALTY_SCALE * (OBSCURITY_LOW_MAL_THRESHOLD - item_mal_score)
            )
        score_before = score_before - obscurity_penalty

        score_after = float(score_before)
        if bool(content_first_active):
            score_after = float(
                content_first_final_score(
                    score_before=float(score_before),
                    neural_sim=float(synopsis_neural_sim),
                    hybrid_cf_score=float(hybrid_cf_score),
                    mal_score=item_mal_score,
                    members_count=item_members_count,
                )
            )

        score = float(score_after)
        if score <= 0:
            continue

        raw_mf = 0.0
        raw_knn = (
            (STAGE2_RAW_KNN_GENRE_OVERLAP_WEIGHT * weighted_overlap)
            + (STAGE2_RAW_KNN_SEED_COVERAGE_WEIGHT * seed_coverage)
            + (STAGE2_RAW_KNN_STAGE1_WEIGHT * float(s1))
            + meta_bonus
            + synopsis_tfidf_adjustment
            + synopsis_embed_adjustment
            + float(demo_bonus)
            + float(theme_bonus)
        )
        raw_pop = (STAGE2_POPULARITY_BOOST_WEIGHT * popularity_boost)
        used_components: list[str] = ["knn", "pop"]
        if aid in id_to_index:
            idx = id_to_index[aid]
            try:
                raw_hybrid = recommender.raw_components_for_item(user_index, idx, weights)
            except Exception:
                raw_hybrid = {"mf": 0.0, "knn": 0.0, "pop": 0.0}
            raw_mf += STAGE2_RAW_HYBRID_CONTRIBUTION_WEIGHT * float(raw_hybrid.get("mf", 0.0))
            raw_knn += STAGE2_RAW_HYBRID_CONTRIBUTION_WEIGHT * float(raw_hybrid.get("knn", 0.0))
            raw_pop += STAGE2_RAW_HYBRID_CONTRIBUTION_WEIGHT * float(raw_hybrid.get("pop", 0.0))

            used_components = sorted(
                set(used_components) | set(recommender.used_components_for_weights(weights)),
                key=lambda k: {"mf": 0, "knn": 1, "pop": 2}.get(k, 99),
            )

        raw_components = {"mf": raw_mf, "knn": raw_knn, "pop": raw_pop}
        shares = compute_component_shares(raw_components, used_components=used_components)

        explanation = {
            "seed_titles": selected_seed_titles,
            "overlap_per_seed": overlap_per_seed,
            "weighted_overlap": weighted_overlap,
            "seeds_matched": num_seeds_matched,
            "seed_coverage": seed_coverage,
            "common_genres": list(all_seed_genres & item_genres),
            "metadata_affinity": float(meta_affinity),
            "metadata_bonus": float(meta_bonus),
            "title_overlap": float(c.get("title_overlap", 0.0)),
            "synopsis_tfidf_sim": float(synopsis_tfidf_sim),
            "synopsis_tfidf_bonus": float(synopsis_tfidf_bonus),
            "synopsis_tfidf_penalty": float(synopsis_tfidf_penalty),
            "synopsis_tfidf_adjustment": float(synopsis_tfidf_adjustment),
            "synopsis_tfidf_base_gate_passed": bool(passes_gate),
            "synopsis_tfidf_high_sim_override": bool(high_sim_override_tfidf),
            "synopsis_embed_sim": float(synopsis_embed_sim),
            "synopsis_embed_bonus": float(synopsis_embed_bonus),
            "synopsis_embed_penalty": float(synopsis_embed_penalty),
            "synopsis_embed_adjustment": float(synopsis_embed_adjustment),
            "synopsis_embed_high_sim_override": bool(high_sim_override_embed),
            "synopsis_neural_sim": float(synopsis_neural_sim),
            "demographics_overlap_bonus": float(demo_bonus),
            "theme_overlap": None if theme_overlap is None else float(theme_overlap),
            "theme_stage2_bonus": float(theme_bonus),
            "stage1_score": float(s1),
            "shortlist_size": int(len(shortlist)),
            "content_first_active": bool(content_first_active),
            "content_first_alpha": float(CONTENT_FIRST_ALPHA),
            "content_first_hybrid_cf_score": float(hybrid_cf_score),
            "hybrid_val": float(hybrid_val),
            "score_before": float(score_before),
            "score_after": float(score_after),
        }
        explanation.update(shares)

        scored.append({
            "anime_id": aid,
            "score": score,
            "explanation": explanation,
            "_title_display": str(mrow.get("title_display") or mrow.get("title_primary") or ""),
            "_title_overlap": float(c.get("title_overlap", 0.0)),
            "_synopsis_neural_sim": float(synopsis_neural_sim),
            "_raw_components": raw_components,
            "_used_components": used_components,
            "_explanation_meta": {
                "seed_titles": selected_seed_titles,
                "seeds_matched": num_seeds_matched,
            },
        })

    scored.sort(key=lambda x: (-float(x.get("score", 0.0)), int(x.get("anime_id", 0))))

    # Stage 0 enforcement guardrail
    final_scored_candidate_count = int(len(scored))
    if __debug__:
        if int(final_scored_candidate_count) > int(STAGE0_POOL_CAP) + int(STAGE0_ENFORCEMENT_BUFFER):
            logger.warning(
                "Stage0 enforcement violated: scored=%s > cap+buf=%s (cap=%s buf=%s)",
                int(final_scored_candidate_count),
                int(int(STAGE0_POOL_CAP) + int(STAGE0_ENFORCEMENT_BUFFER)),
                int(STAGE0_POOL_CAP),
                int(STAGE0_ENFORCEMENT_BUFFER),
            )

    # Discovery mode franchise cap
    seed_ranking_mode = str(ctx.seed_ranking_mode or SEED_RANKING_MODE).strip().lower()
    if seed_ranking_mode == "discovery":
        scored_capped, cap_diag = apply_franchise_cap(
            scored,
            n=int(n_requested),
            seed_ranking_mode=str(seed_ranking_mode),
            seed_titles=list(selected_seed_titles or []),
            threshold=float(FRANCHISE_TITLE_OVERLAP_THRESHOLD),
            cap_top20=int(FRANCHISE_CAP_TOP20),
            cap_top50=int(FRANCHISE_CAP_TOP50),
            title_overlap=lambda r: float(r.get("_title_overlap", 0.0)),
            title=lambda r: str(r.get("_title_display", "")),
            anime_id=lambda r: int(r.get("anime_id", 0)),
            neural_sim=lambda r: float(r.get("_synopsis_neural_sim", 0.0)),
        )
        result.franchise_cap_diagnostics = {
            "seed_ranking_mode": cap_diag.seed_ranking_mode,
            "franchise_cap_threshold": cap_diag.franchise_cap_threshold,
            "franchise_cap_top20": cap_diag.franchise_cap_top20,
            "franchise_cap_top50": cap_diag.franchise_cap_top50,
            "top20_franchise_like_count_before": cap_diag.top20_franchise_like_count_before,
            "top20_franchise_like_count_after": cap_diag.top20_franchise_like_count_after,
            "top50_franchise_like_count_before": cap_diag.top50_franchise_like_count_before,
            "top50_franchise_like_count_after": cap_diag.top50_franchise_like_count_after,
            "franchise_items_dropped_count": cap_diag.franchise_items_dropped_count,
            "franchise_items_dropped_count_top20": cap_diag.franchise_items_dropped_count_top20,
            "franchise_items_dropped_count_top50": cap_diag.franchise_items_dropped_count_top50,
            "franchise_items_dropped_examples_top5": cap_diag.franchise_items_dropped_examples_top5,
        }
        recs = scored_capped
    else:
        recs = scored[:n_requested]

    # Downstream enforcement diagnostics
    try:
        top20 = recs[:20]
        top50 = recs[:50]
        top20_in_stage0 = sum(1 for r in top20 if int(r.get("anime_id", 0)) in candidate_id_set)
        top50_in_stage0 = sum(1 for r in top50 if int(r.get("anime_id", 0)) in candidate_id_set)
    except Exception:
        top20_in_stage0 = 0
        top50_in_stage0 = 0

    try:
        result.stage0_enforcement.update({
            "final_scored_candidate_count": int(final_scored_candidate_count),
            "top20_in_stage0_count": int(top20_in_stage0),
            "top50_in_stage0_count": int(top50_in_stage0),
        })
    except Exception:
        pass

    timing["stage2"] = time.monotonic() - t_s2
    timing["total"] = time.monotonic() - t0
    result.timing = timing
    result.ranked_items = recs
    return result


# ---------------------------------------------------------------------------
# Personalized pipeline
# ---------------------------------------------------------------------------

def run_personalized_pipeline(ctx: ScoringContext) -> PipelineResult:
    """Personalized recommendation path using user embedding.

    If seeds are also selected, this blends personalized MF scores with
    seed-based metadata affinity nudges and synopsis signals.

    Depending on ``personalization_strength``:
    - 1.0: pure personalized
    - 0.01–0.99: blended with seed-based results
    - ≤0.01: seed-based only (personalization skipped)
    """
    t0 = time.monotonic()
    result = PipelineResult()

    metadata = ctx.metadata
    recommender = ctx.recommender
    weights = ctx.weights
    mf_model = ctx.mf_model
    user_embedding = ctx.user_embedding
    personalization_strength = ctx.personalization_strength
    n_requested = ctx.n_requested
    ranked_hygiene_exclude_ids = ctx.ranked_hygiene_exclude_ids
    selected_seed_ids = ctx.seed_ids
    selected_seed_titles = ctx.seed_titles

    # --- Validate personalization prerequisites ---
    mf_stem = ctx.mf_stem
    cached_meta = ctx.user_embedding_meta or {}

    if mf_model is None:
        result.personalization_blocked_reason = "MF model is not available (artifact load/selection failed)."
    elif user_embedding is None:
        result.personalization_blocked_reason = "User embedding is not available."
    elif cached_meta.get("mf_stem") != mf_stem:
        result.personalization_blocked_reason = "User embedding was generated from a different MF artifact; rerun to refresh."
    elif ctx.personalization_blocked_reason:
        result.personalization_blocked_reason = ctx.personalization_blocked_reason

    if result.personalization_blocked_reason is not None:
        # Fall through — personalization cannot run, return seed-based results unchanged.
        result.timing["total"] = time.monotonic() - t0
        return result

    # Get watched anime IDs for exclusion
    watched_ids_list = list(ctx.watched_ids)
    exclude_ranked_ids = sorted(set(watched_ids_list) | set(ranked_hygiene_exclude_ids))

    personalization_applied = False
    personalized_recs: list[dict] = []

    try:
        if personalization_strength >= 0.99:
            # Pure personalized recommendations (100% strength)
            personalized_recs = recommender.get_personalized_recommendations(
                user_embedding=user_embedding,
                mf_model=mf_model,
                n=n_requested,
                weights=weights,
                exclude_item_ids=exclude_ranked_ids,
            )
            if not personalized_recs:
                result.personalization_blocked_reason = (
                    "MF personalization returned no results (likely no overlap with MF items)."
                )
            else:
                # Metadata affinity nudge when seeds are selected
                if selected_seed_ids:
                    seed_meta_profile = build_seed_metadata_profile(metadata, seed_ids=selected_seed_ids)
                    synopsis_tfidf_artifact = ctx.bundle.get("models", {}).get("synopsis_tfidf")
                    synopsis_sims_by_id: dict[int, float] = {}
                    seed_type_target: str | None = None
                    if synopsis_tfidf_artifact is not None:
                        try:
                            synopsis_sims_by_id = compute_seed_similarity_map(
                                synopsis_tfidf_artifact, seed_ids=selected_seed_ids
                            )
                            seed_type_target = most_common_seed_type(metadata, selected_seed_ids)
                        except Exception:
                            synopsis_sims_by_id = {}
                            seed_type_target = None

                    # Build metadata lookup for O(1) access
                    metadata_by_id = metadata.set_index("anime_id")

                    for rec in personalized_recs:
                        aid = int(rec.get("anime_id"))
                        try:
                            row_data = metadata_by_id.loc[aid]
                        except KeyError:
                            continue
                        affinity = compute_metadata_affinity(seed_meta_profile, row_data)
                        bonus = float(METADATA_AFFINITY_PERSONALIZED_COEF) * float(affinity)
                        if bonus > 0.0:
                            rec["score"] = float(rec.get("score", 0.0)) + bonus
                            raw = rec.get("_raw_components")
                            if isinstance(raw, dict):
                                raw["knn"] = float(raw.get("knn", 0.0)) + bonus
                            else:
                                rec["_raw_components"] = {"mf": 0.0, "knn": bonus, "pop": 0.0}
                            used = rec.get("_used_components")
                            if isinstance(used, list) and "knn" not in used:
                                used.append("knn")

                        # Synopsis TF-IDF nudge in personalized mode
                        if synopsis_sims_by_id:
                            sim = float(synopsis_sims_by_id.get(aid, 0.0))
                            if sim > 0.0:
                                cand_type = None
                                try:
                                    cand_type_val = row_data.get("type") if isinstance(row_data, pd.Series) else None
                                    cand_type = None if pd.isna(cand_type_val) else str(cand_type_val).strip()
                                except Exception:
                                    cand_type = None
                                cand_eps = row_data.get("episodes") if isinstance(row_data, pd.Series) else None
                                if synopsis_gate_passes(
                                    seed_type=seed_type_target,
                                    candidate_type=cand_type,
                                    candidate_episodes=cand_eps,
                                ):
                                    tfidf_bonus = float(personalized_synopsis_tfidf_bonus_for_candidate(sim))
                                    if tfidf_bonus > 0.0:
                                        rec["score"] = float(rec.get("score", 0.0)) + tfidf_bonus
                                        raw = rec.get("_raw_components")
                                        if isinstance(raw, dict):
                                            raw["knn"] = float(raw.get("knn", 0.0)) + tfidf_bonus
                                        else:
                                            rec["_raw_components"] = {"mf": 0.0, "knn": tfidf_bonus, "pop": 0.0}
                                        used = rec.get("_used_components")
                                        if isinstance(used, list) and "knn" not in used:
                                            used.append("knn")

                personalized_recs.sort(key=lambda x: (-float(x.get("score", 0.0)), int(x.get("anime_id", 0))))
                personalized_recs = personalized_recs[:n_requested]
                result.ranked_items = personalized_recs
                personalization_applied = True

        elif personalization_strength > 0.01:
            # Blend personalized and seed-based
            personalized_recs = recommender.get_personalized_recommendations(
                user_embedding=user_embedding,
                mf_model=mf_model,
                n=n_requested,
                weights=weights,
                exclude_item_ids=exclude_ranked_ids,
            )
            if not personalized_recs:
                result.personalization_blocked_reason = (
                    "MF personalization returned no results (likely no overlap with MF items)."
                )
            else:
                result.ranked_items = personalized_recs
                personalization_applied = True
    except Exception as e:  # noqa: BLE001
        result.personalization_blocked_reason = f"Personalization failed at scoring time: {e}"

    result.personalization_applied = personalization_applied
    result.timing["total"] = time.monotonic() - t0
    return result


def blend_personalized_and_seed(
    personalized_recs: list[dict],
    seed_recs: list[dict],
    personalization_strength: float,
    n_requested: int,
    ranked_hygiene_exclude_ids: set[int],
) -> list[dict]:
    """Blend personalized and seed-based recommendation lists.

    Returns the blended, sorted, and truncated result.
    """
    personalized_scores = {rec["anime_id"]: rec["score"] for rec in personalized_recs}
    seed_scores = {rec["anime_id"]: rec["score"] for rec in seed_recs}

    personalized_raw = {
        rec["anime_id"]: rec.get("_raw_components", {"mf": 0.0, "knn": 0.0, "pop": 0.0})
        for rec in personalized_recs
    }
    seed_raw = {
        rec["anime_id"]: rec.get("_raw_components", {"mf": 0.0, "knn": 0.0, "pop": 0.0})
        for rec in seed_recs
    }
    personalized_used = {
        rec["anime_id"]: rec.get("_used_components", []) for rec in personalized_recs
    }
    seed_used = {rec["anime_id"]: rec.get("_used_components", []) for rec in seed_recs}

    all_anime_ids = set(personalized_scores.keys()) | set(seed_scores.keys())

    blended: list[dict] = []
    for aid in all_anime_ids:
        if aid in ranked_hygiene_exclude_ids:
            continue
        p_score = personalized_scores.get(aid, 0.0)
        s_score = seed_scores.get(aid, 0.0)

        final_score = (personalization_strength * p_score) + ((1 - personalization_strength) * s_score)

        pr = personalized_raw.get(aid, {"mf": 0.0, "knn": 0.0, "pop": 0.0})
        sr = seed_raw.get(aid, {"mf": 0.0, "knn": 0.0, "pop": 0.0})
        raw_components = {
            "mf": (personalization_strength * float(pr.get("mf", 0.0)))
            + ((1 - personalization_strength) * float(sr.get("mf", 0.0))),
            "knn": (personalization_strength * float(pr.get("knn", 0.0)))
            + ((1 - personalization_strength) * float(sr.get("knn", 0.0))),
            "pop": (personalization_strength * float(pr.get("pop", 0.0)))
            + ((1 - personalization_strength) * float(sr.get("pop", 0.0))),
        }
        used_components = sorted(
            set(personalized_used.get(aid, [])) | set(seed_used.get(aid, [])),
            key=lambda k: {"mf": 0, "knn": 1, "pop": 2}.get(k, 99),
        )

        blended.append({
            "anime_id": aid,
            "score": final_score,
            "_raw_components": raw_components,
            "_used_components": used_components,
        })

    blended.sort(key=lambda x: x["score"], reverse=True)
    return blended[:n_requested]


# ---------------------------------------------------------------------------
# Post-pipeline filters & explanation formatting
# ---------------------------------------------------------------------------

def apply_post_filters(
    recs: list[dict],
    ctx: ScoringContext,
) -> list[dict]:
    """Apply genre, type, year, and sort filters to the recommendation list.

    This consolidates the post-scoring filter logic that was previously
    inline in app/main.py.  Uses O(1) metadata lookups.
    """
    metadata = ctx.metadata
    pop_pct_fn = ctx.pop_pct_fn or (lambda _aid: 0.5)

    if not recs:
        return recs

    # Build O(1) metadata lookup
    metadata_by_id = metadata.set_index("anime_id")

    # Genre filter
    if ctx.genre_filter:
        filtered: list[dict] = []
        for rec in recs:
            aid = rec["anime_id"]
            try:
                row = metadata_by_id.loc[aid]
            except KeyError:
                continue
            row_genres_val = row.get("genres", "") if isinstance(row, pd.Series) else ""
            item_genres: set[str] = set()
            if isinstance(row_genres_val, str):
                item_genres = {g.strip() for g in row_genres_val.split("|") if g.strip()}
            elif hasattr(row_genres_val, "__iter__") and not isinstance(row_genres_val, str):
                item_genres = {str(g).strip() for g in row_genres_val if g}
            if any(gf in item_genres for gf in ctx.genre_filter):
                filtered.append(rec)
        recs = filtered

    # Type filter
    if ctx.type_filter and "type" in metadata.columns:
        filtered = []
        for rec in recs:
            aid = rec["anime_id"]
            try:
                row = metadata_by_id.loc[aid]
            except KeyError:
                continue
            item_type = row.get("type") if isinstance(row, pd.Series) else None
            if pd.notna(item_type) and str(item_type).strip() in ctx.type_filter:
                filtered.append(rec)
        recs = filtered

    # Year range filter
    if ctx.year_range[0] > 1960 or ctx.year_range[1] < 2025:
        filtered = []
        for rec in recs:
            aid = rec["anime_id"]
            try:
                row = metadata_by_id.loc[aid]
            except KeyError:
                continue
            aired_from = row.get("aired_from") if isinstance(row, pd.Series) else None
            if aired_from and isinstance(aired_from, str):
                try:
                    year = int(aired_from[:4])
                    if ctx.year_range[0] <= year <= ctx.year_range[1]:
                        filtered.append(rec)
                except Exception:
                    pass
        recs = filtered

    # Sort (only when user has changed from default)
    if ctx.sort_by != ctx.default_sort_for_mode:
        enriched: list[dict] = []
        for rec in recs:
            aid = rec["anime_id"]
            try:
                row = metadata_by_id.loc[aid]
            except KeyError:
                continue
            rec_copy = rec.copy()
            rec_copy["_mal_score"] = float(row.get("mal_score")) if isinstance(row, pd.Series) and pd.notna(row.get("mal_score")) else 0
            rec_copy["_year"] = 0
            aired_from = row.get("aired_from") if isinstance(row, pd.Series) else None
            if aired_from and isinstance(aired_from, str):
                try:
                    rec_copy["_year"] = int(aired_from[:4])
                except Exception:
                    pass
            rec_copy["_popularity"] = pop_pct_fn(int(aid))
            enriched.append(rec_copy)

        if ctx.sort_by == "MAL Score":
            enriched.sort(key=lambda x: x["_mal_score"], reverse=True)
        elif ctx.sort_by == "Year (Newest)":
            enriched.sort(key=lambda x: x["_year"], reverse=True)
        elif ctx.sort_by == "Year (Oldest)":
            enriched.sort(key=lambda x: x["_year"], reverse=False)
        elif ctx.sort_by == "Popularity":
            enriched.sort(key=lambda x: x["_popularity"], reverse=False)
        recs = enriched

    # Final trim to requested top_n
    recs = recs[:ctx.top_n]
    return recs


def finalize_explanation_shares(
    recs: list[dict],
) -> list[dict]:
    """Recompute truthful MF/kNN/Pop shares and format explanation text.

    This runs after optional personalized explanation text generation so we
    can append truthful share percentages.
    """
    for rec in recs:
        raw = rec.get("_raw_components")
        used = rec.get("_used_components")
        if not isinstance(raw, dict) or not isinstance(used, list) or not used:
            continue
        shares = compute_component_shares(raw, used_components=used)

        contributions = {
            "mf": shares.get("mf", 0.0),
            "knn": shares.get("knn", 0.0),
            "pop": shares.get("pop", 0.0),
            "_used": shares.get("_used", used),
        }
        meta = rec.get("_explanation_meta")
        if isinstance(meta, dict):
            contributions.update(meta)
        share_text = format_explanation(contributions)

        existing = rec.get("explanation")
        if isinstance(existing, str) and existing.strip():
            rec["explanation"] = f"{existing} • {share_text}"
        else:
            rec["explanation"] = share_text
    return recs


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------

__all__ = [
    "ScoringContext",
    "PipelineResult",
    "run_seed_based_pipeline",
    "run_personalized_pipeline",
    "run_browse_pipeline",
    "blend_personalized_and_seed",
    "apply_post_filters",
    "finalize_explanation_shares",
]
