"""Phase 4 / Chunk A1: Golden queries + offline evaluation harness.

One command that:
  1) Computes headline offline ranking metrics (NDCG@K, MAP@K; plus optional coverage/Gini)
  2) Generates a human-readable golden-queries report (top-N per query)

Outputs:
  - experiments/metrics/phase4_eval_<ts>.json
  - experiments/metrics/summary.csv (append)
  - reports/phase4_golden_queries_<ts>.md
  - reports/artifacts/phase4_golden_queries_<ts>.json

This script is evaluation-only: it does not change training pipelines or app UX.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from joblib import load

from src.app.artifacts_loader import build_artifacts, set_determinism
from src.app.recommender import HybridComponents, HybridRecommender, choose_weights
from src.app.search import fuzzy_search
from src.app.diversity import compute_popularity_percentiles
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids
from src.app.constants import (
    FORCE_NEURAL_MIN_SIM,
    FORCE_NEURAL_TOPK,
    STAGE0_NEURAL_TOPK,
    STAGE0_POPULARITY_BACKFILL,
    STAGE0_POOL_CAP,
    STAGE0_META_MIN_GENRE_OVERLAP,
    STAGE0_META_MIN_THEME_OVERLAP,
    SEED_RANKING_MODE,
    FRANCHISE_TITLE_OVERLAP_THRESHOLD,
    FRANCHISE_CAP_TOP20,
    FRANCHISE_CAP_TOP50,
    STAGE0_ENFORCEMENT_BUFFER,
)

from src.app.why_not_scored import (
    NOT_IN_STAGE1_SHORTLIST,
    BLOCKED_LOW_SEMANTIC_SIM,
    BLOCKED_LOW_OVERLAP,
    BLOCKED_OTHER_ADMISSION,
    MISSING_SEMANTIC_VECTOR,
    DROPPED_BY_QUALITY_FILTERS,
    SCORED,
    REASONS_ORDERED,
)
from src.app.franchise_cap import apply_franchise_cap
from src.app.stage1_shortlist import (
    build_stage1_shortlist,
    force_neural_enabled,
    forced_pool_stats,
    select_forced_neural_pairs,
)
from src.app.stage0_candidates import build_stage0_seed_candidate_pool
from src.app.constants import CONTENT_FIRST_ALPHA
from src.app.stage2_overrides import (
    content_first_final_score,
    quality_prior_bonus,
    relax_off_type_penalty,
    should_relax_off_type_penalty,
    should_use_content_first,
)
from src.app.metadata_features import (
    METADATA_AFFINITY_COLD_START_COEF,
    METADATA_AFFINITY_TRAINED_COEF,
    build_seed_metadata_profile,
    compute_metadata_affinity,
    demographics_overlap_tiebreak_bonus,
    theme_stage2_tiebreak_bonus,
)
from src.app.synopsis_tfidf import (
    compute_seed_similarity_map,
    most_common_seed_type,
    synopsis_gate_passes,
    synopsis_tfidf_penalty_for_candidate,
    synopsis_tfidf_bonus_for_candidate,
    SYNOPSIS_TFIDF_MIN_SIM,
    SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD,
    SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY,
)

from src.app.synopsis_embeddings import (
    compute_seed_similarity_map as compute_seed_embedding_similarity_map,
    SYNOPSIS_EMBEDDINGS_MIN_SIM,
    SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD,
    SYNOPSIS_EMBEDDINGS_OFFTYPE_HIGH_SIM_PENALTY,
    synopsis_embeddings_bonus_for_candidate,
    synopsis_embeddings_penalty_for_candidate,
)
from src.app.synopsis_neural_embeddings import (
    compute_seed_similarity_map as compute_seed_neural_similarity_map,
    SYNOPSIS_NEURAL_MIN_SIM,
    SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD,
    SYNOPSIS_NEURAL_OFFTYPE_HIGH_SIM_PENALTY,
    synopsis_neural_bonus_for_candidate,
    synopsis_neural_penalty_for_candidate,
)

from src.app.semantic_admission import (
    STAGE1_DEMO_SHOUNEN_MIN_SIM_NEURAL,
    normalize_demographics_tokens,
    stage1_semantic_admission,
    theme_overlap_ratio,
)

from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.eval.metrics_extra import item_coverage, gini_index
from src.eval.splits import build_validation, sample_user_ids

from src.models.baselines import popularity_scores
from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, METRICS_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS, DEFAULT_HYBRID_WEIGHTS
from src.models.data_loader import load_interactions
from src.models.hybrid import weighted_blend
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.mf_sgd import FunkSVDRecommender


REPORTS_DIR = Path("reports")
REPORTS_ARTIFACTS_DIR = REPORTS_DIR / "artifacts"


def _json_default(o: Any):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)


def _stable_rank(items_to_scores: dict[int, float], *, top_k: int) -> list[int]:
    """Deterministic ranking: sort by score desc, then item id asc."""
    ranked = sorted(items_to_scores.items(), key=lambda x: (-float(x[1]), int(x[0])))
    return [int(i) for i, _ in ranked[:top_k]]


def _evaluate_recs(recommendations: dict[int, list[int]], relevant: dict[int, set[int]], k: int) -> dict[str, float]:
    ndcgs: list[float] = []
    maps: list[float] = []
    for u, recs in recommendations.items():
        rel = relevant.get(u, set())
        ndcgs.append(ndcg_at_k(recs, rel, k))
        maps.append(average_precision_at_k(recs, rel, k))
    return {
        "ndcg@k_mean": float(sum(ndcgs) / max(1, len(ndcgs))),
        "map@k_mean": float(sum(maps) / max(1, len(maps))),
    }


def _run_headline_metrics(*, k: int, sample_users: int, w_mf: float, w_knn: float, w_pop: float) -> dict[str, Any]:
    """Compute headline offline metrics for a weighted hybrid (MF + kNN + popularity).

    Uses processed interactions when available, and existing v1.0 artifacts if present.
    Falls back to fitting models if artifacts are missing.
    """

    interactions = load_interactions(DATA_PROCESSED_DIR)

    train_df, val_df = build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].astype(int).unique().tolist(), sample_users)

    # Load or fit models (offline-eval harness; not app inference)
    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"

    if knn_path.exists():
        knn_model: ItemKNNRecommender = load(knn_path)
    else:
        knn_model = ItemKNNRecommender().fit(train_df)

    if mf_path.exists():
        mf_model: FunkSVDRecommender = load(mf_path)
    else:
        mf_model = FunkSVDRecommender().fit(train_df)

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    pop_series = popularity_scores(train_df)  # item_id -> score
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    # ------------------------------------------------------------------
    # Performance note:
    # The previous implementation materialized full dicts for knn/mf/pop
    # for each user and sorted them. That is very slow for large catalogs.
    # Here we compute the blended score in a single aligned array and
    # select top-k via argpartition (deterministic tie-breaking applied).
    # ------------------------------------------------------------------

    weights = {"mf": float(w_mf), "knn": float(w_knn), "pop": float(w_pop)}

    # Build a stable global item index for all sources.
    mf_items = [int(mf_model.index_to_item[i]) for i in range(len(mf_model.index_to_item))] if mf_model.index_to_item is not None else []
    knn_items = [int(knn_model.index_to_item[i]) for i in range(len(knn_model.index_to_item))] if knn_model.index_to_item is not None else []
    global_items_sorted = sorted(set(mf_items).union(set(knn_items)).union(set(pop_scores_global.keys())))
    global_id_to_pos = {int(aid): int(idx) for idx, aid in enumerate(global_items_sorted)}

    mf_pos = np.asarray([global_id_to_pos[int(aid)] for aid in mf_items], dtype=np.int32) if mf_items else np.asarray([], dtype=np.int32)
    knn_pos = np.asarray([global_id_to_pos[int(aid)] for aid in knn_items], dtype=np.int32) if knn_items else np.asarray([], dtype=np.int32)

    pop_vec_global = np.zeros(len(global_items_sorted), dtype=np.float32)
    for aid, sc in pop_scores_global.items():
        pos = global_id_to_pos.get(int(aid))
        if pos is not None:
            pop_vec_global[int(pos)] = float(sc)

    def _knn_scores_array(user_id: int) -> np.ndarray:
        if knn_model.user_to_index is None or knn_model.item_user_matrix is None:
            return np.asarray([], dtype=np.float32)
        if user_id not in knn_model.user_to_index:
            return np.asarray([], dtype=np.float32)

        profile = knn_model._user_profile(int(user_id))
        if np.allclose(profile, 0):
            return np.asarray([], dtype=np.float32)

        denom = np.linalg.norm(profile)
        if denom == 0:
            return np.asarray([], dtype=np.float32)

        sims = (knn_model.item_user_matrix @ profile) / denom
        sims = np.asarray(sims).ravel().astype(np.float32, copy=False)
        if knn_model.item_pop is not None and float(getattr(knn_model, "popularity_weight", 0.0)) != 0.0:
            sims = sims + float(getattr(knn_model, "popularity_weight", 0.0)) * np.asarray(knn_model.item_pop, dtype=np.float32)
        return sims

    recs: dict[int, list[int]] = {}
    k_int = int(k)

    for u in users:
        u = int(u)
        seen = set(int(x) for x in train_hist.get(u, set()))

        scores = np.zeros(len(global_items_sorted), dtype=np.float32)

        # MF contribution
        if float(weights.get("mf", 0.0)) != 0.0 and mf_items:
            mf_arr = np.asarray(mf_model.predict_user(u), dtype=np.float32)
            scores[mf_pos] += float(weights["mf"]) * mf_arr

        # kNN contribution
        if float(weights.get("knn", 0.0)) != 0.0 and knn_items:
            knn_arr = _knn_scores_array(u)
            if knn_arr.size:
                scores[knn_pos] += float(weights["knn"]) * knn_arr

        # Popularity contribution
        if float(weights.get("pop", 0.0)) != 0.0:
            scores += float(weights["pop"]) * pop_vec_global

        # Exclude seen items (applies to blended score)
        if seen:
            seen_pos = [global_id_to_pos.get(int(aid)) for aid in seen]
            seen_pos = [p for p in seen_pos if p is not None]
            if seen_pos:
                scores[np.asarray(seen_pos, dtype=np.int32)] = -np.inf

        # Top-k selection (deterministic tie-breaker: score desc, then anime_id asc)
        if k_int <= 0:
            recs[u] = []
            continue
        k_eff = min(k_int, int(scores.shape[0]))
        top_idx = np.argpartition(scores, -k_eff)[-k_eff:]
        top_scores = scores[top_idx]
        top_aids = np.asarray([global_items_sorted[int(i)] for i in top_idx], dtype=np.int64)
        order = np.lexsort((top_aids, -top_scores))
        ordered_idx = top_idx[order]

        recs[u] = [int(global_items_sorted[int(i)]) for i in ordered_idx[:k_eff] if np.isfinite(scores[int(i)])]

    metrics = _evaluate_recs(recs, val_hist, k)

    total_items = int(train_df["anime_id"].nunique())
    metrics_extra = {
        "item_coverage@k": item_coverage(recs, total_items),
        "gini_index@k": gini_index(recs),
    }

    out: dict[str, Any] = {
        "model": "hybrid_weighted",
        "k": int(k),
        "users_evaluated": int(len(recs)),
        "weights": {"mf": float(w_mf), "knn": float(w_knn), "pop": float(w_pop)},
        **metrics,
        **metrics_extra,
    }
    return out


@dataclass(frozen=True)
class GoldenExpectations:
    disallow_types: tuple[str, ...]
    disallow_title_regex: str


def _parse_genres(val: Any) -> set[str]:
    if isinstance(val, str):
        return {g.strip() for g in val.split("|") if g and g.strip()}
    if hasattr(val, "__iter__") and not isinstance(val, str):
        return {str(g).strip() for g in val if g and str(g).strip()}
    return set()


def _parse_themes(val: Any) -> set[str]:
    # Keep consistent with genre parsing: tolerate pipe-delimited strings and iterables.
    if isinstance(val, str):
        return {t.strip() for t in val.split("|") if t and t.strip()}
    if hasattr(val, "__iter__") and not isinstance(val, str):
        return {str(t).strip() for t in val if t and str(t).strip()}
    return set()


def _resolve_seed_titles(
    metadata: pd.DataFrame,
    seed_titles: list[str],
    *,
    allow_fuzzy: bool = False,
) -> tuple[list[int], list[str], list[dict[str, Any]]]:
    choices = [(str(t), int(a)) for t, a in zip(metadata["title_display"].astype(str).tolist(), metadata["anime_id"].astype(int).tolist())]

    resolved_ids: list[int] = []
    resolved_titles: list[str] = []
    resolution_debug: list[dict[str, Any]] = []

    title_to_id_exact = {
        str(t): int(a)
        for t, a in zip(metadata["title_display"].astype(str).tolist(), metadata["anime_id"].astype(int).tolist())
    }

    for q in seed_titles:
        if q in title_to_id_exact:
            aid = int(title_to_id_exact[q])
            resolved_ids.append(aid)
            resolved_titles.append(q)
            resolution_debug.append({"query": q, "resolved_anime_id": aid, "matched_title": q, "method": "exact"})
            continue

        # Strict-by-default: do NOT fuzzy-resolve seeds unless explicitly allowed.
        # We may compute fuzzy suggestions for diagnostics, but we won't pick one.
        matches = fuzzy_search(q, choices, limit=5, min_score=70)
        if not allow_fuzzy:
            resolution_debug.append(
                {
                    "query": q,
                    "resolved_anime_id": None,
                    "matched_title": None,
                    "method": "blocked_fuzzy",
                    "suggestions": [
                        {"anime_id": int(aid), "matched_title": str(t), "score": float(score)}
                        for aid, score, t in matches
                    ],
                }
            )
            continue

        if not matches:
            resolution_debug.append({"query": q, "resolved_anime_id": None, "matched_title": None, "method": "none"})
            continue

        aid, score, matched_title = matches[0]
        resolved_ids.append(int(aid))
        resolved_titles.append(str(matched_title))
        resolution_debug.append({"query": q, "resolved_anime_id": int(aid), "matched_title": str(matched_title), "score": float(score), "method": "fuzzy"})

    # de-dupe while preserving order
    seen: set[int] = set()
    uniq_ids: list[int] = []
    uniq_titles: list[str] = []
    for aid, title in zip(resolved_ids, resolved_titles):
        if aid in seen:
            continue
        seen.add(aid)
        uniq_ids.append(aid)
        uniq_titles.append(title)

    return uniq_ids, uniq_titles, resolution_debug


def _build_app_like_recommender(bundle: dict[str, Any]) -> tuple[pd.DataFrame, HybridComponents, HybridRecommender, dict[int, float]]:
    metadata: pd.DataFrame = bundle["metadata"]

    mf_model = bundle.get("models", {}).get("mf")
    if mf_model is None:
        raise RuntimeError("MF model alias 'mf' not found in bundle['models']")

    for attr in ("P", "Q", "global_mean", "index_to_item"):
        if not hasattr(mf_model, attr):
            raise RuntimeError(f"MF model missing required field '{attr}' for app-like inference")

    index_to_item = mf_model.index_to_item
    n_items = len(index_to_item)
    item_ids = np.asarray([int(index_to_item[i]) for i in range(n_items)], dtype=np.int64)

    p = mf_model.P
    q = mf_model.Q
    if p is None or q is None:
        raise RuntimeError("MF model P/Q is None")
    if p.shape[0] < 1:
        raise RuntimeError("MF model has no users in P")

    demo_user_index = 0
    demo_scores = float(mf_model.global_mean) + (p[demo_user_index] @ q.T)
    mf_scores = np.asarray(demo_scores, dtype=np.float32).reshape(1, -1)

    components = HybridComponents(mf=mf_scores, knn=None, pop=None, item_ids=item_ids)

    pop_percentile_by_anime_id: dict[int, float] = {}

    # Optional: popularity prior from app-selected KNN artifact
    knn_model = bundle.get("models", {}).get("knn")
    try:
        if (
            knn_model is not None
            and hasattr(knn_model, "item_pop")
            and hasattr(knn_model, "item_to_index")
            and knn_model.item_pop is not None
            and knn_model.item_to_index is not None
        ):
            it2i = knn_model.item_to_index
            pop_arr = np.asarray(knn_model.item_pop, dtype=np.float32)

            pop_pct_arr = compute_popularity_percentiles(pop_arr)
            pop_percentile_by_anime_id = {
                int(aid): float(pop_pct_arr[int(idx)])
                for aid, idx in it2i.items()
                if idx is not None and 0 <= int(idx) < len(pop_pct_arr)
            }

            pop_vec = np.zeros(len(item_ids), dtype=np.float32)
            for j, aid in enumerate(item_ids):
                idx = it2i.get(int(aid))
                if idx is not None and 0 <= int(idx) < len(pop_arr):
                    pop_vec[j] = float(pop_arr[int(idx)])
            components.pop = pop_vec
    except Exception:
        pop_percentile_by_anime_id = {}

    recommender = HybridRecommender(components)
    return metadata, components, recommender, pop_percentile_by_anime_id


def _pop_pct(pop_pct_by_id: dict[int, float], anime_id: int) -> float:
    try:
        return float(pop_pct_by_id.get(int(anime_id), 0.5))
    except Exception:
        return 0.5


def _seed_based_scores(
    *,
    query_id: str | None = None,
    metadata: pd.DataFrame,
    components: HybridComponents,
    recommender: HybridRecommender,
    seed_ids: list[int],
    seed_titles: list[str],
    weights: dict[str, float],
    pop_pct_by_id: dict[int, float],
    top_n: int,
    exclude_ids: set[int] | None = None,
    synopsis_tfidf_artifact: Any | None = None,
    synopsis_embeddings_artifact: Any | None = None,
    synopsis_neural_embeddings_artifact: Any | None = None,
    shortlist_size: int = 600,
    seed_ranking_mode: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not seed_ids:
        return [], {
            "metadata_bonus_fired_count": 0,
            "metadata_bonus_mean": 0.0,
            "metadata_bonus_max": 0.0,
            "affinity_mean": 0.0,
            "affinity_max": 0.0,
            "synopsis_tfidf_bonus_fired_count": 0,
            "synopsis_tfidf_bonus_mean": 0.0,
            "synopsis_tfidf_bonus_max": 0.0,
            "top20_overlap_with_without_meta": 1.0,
            "top50_overlap_with_without_meta": 1.0,
            "top20_mean_abs_rank_delta": 0.0,
            "top50_mean_abs_rank_delta": 0.0,
            "top20_moved_count": 0,
            "top50_moved_count": 0,
            "top20_overlap_with_without_tfidf": 1.0,
            "top50_overlap_with_without_tfidf": 1.0,
            "top20_mean_abs_rank_delta_tfidf": 0.0,
            "top50_mean_abs_rank_delta_tfidf": 0.0,
            "top20_moved_count_tfidf": 0,
            "top50_moved_count_tfidf": 0,
            "embedding_bonus_fired_count": 0,
            "embedding_bonus_mean": 0.0,
            "embedding_bonus_max": 0.0,
            "top20_overlap_with_without_embeddings": 1.0,
            "top50_overlap_with_without_embeddings": 1.0,
            "top20_mean_abs_rank_delta_embeddings": 0.0,
            "top50_mean_abs_rank_delta_embeddings": 0.0,
            "top20_moved_count_embeddings": 0,
            "top50_moved_count_embeddings": 0,
            "neural_bonus_fired_count": 0,
            "neural_bonus_mean": 0.0,
            "neural_bonus_max": 0.0,
            "top20_overlap_with_without_neural": 1.0,
            "top50_overlap_with_without_neural": 1.0,
            "top20_mean_abs_rank_delta_neural": 0.0,
            "top50_mean_abs_rank_delta_neural": 0.0,
            "top20_moved_count_neural": 0,
            "top50_moved_count_neural": 0,
        }

    # Semantic mode:
    # - neural: Phase 5 sentence-transformer embeddings (offline-built; runtime numpy-only)
    # - embeddings: Phase 4 deterministic (local) embeddings successor
    # - tfidf: Phase 4 legacy
    # - both: embeddings + tfidf
    # - none: disable semantic
    semantic_mode = str(os.environ.get("PHASE4_SEMANTIC_MODE", "")).strip().lower()
    if semantic_mode not in {"neural", "embeddings", "tfidf", "both", "none", ""}:
        semantic_mode = ""
    if not semantic_mode:
        # Deterministic + conservative default.
        # Prefer Phase 5 neural when present; otherwise keep Phase 4 behavior.
        if synopsis_neural_embeddings_artifact is not None:
            semantic_mode = "neural"
        elif synopsis_embeddings_artifact is not None and synopsis_tfidf_artifact is not None:
            semantic_mode = "both"
        elif synopsis_embeddings_artifact is not None:
            semantic_mode = "embeddings"
        elif synopsis_tfidf_artifact is not None:
            semantic_mode = "tfidf"
        else:
            semantic_mode = "none"

    exclude_ids = set(exclude_ids or set())

    # Stable iteration order
    work = metadata.sort_values("anime_id", kind="mergesort")

    # Phase 4 / Chunk A3: seed metadata affinity profile (used as a cold-start bonus only).
    seed_meta_profile = build_seed_metadata_profile(work, seed_ids=seed_ids)

    # Phase 4/5: optional semantic similarity maps.
    synopsis_sims_by_id: dict[int, float] = {}
    embed_sims_by_id: dict[int, float] = {}
    neural_sims_by_id: dict[int, float] = {}

    try:
        seed_type_target: str | None = most_common_seed_type(work, seed_ids=seed_ids)
    except Exception:
        seed_type_target = None

    if semantic_mode in {"tfidf", "both"} and synopsis_tfidf_artifact is not None:
        try:
            synopsis_sims_by_id = compute_seed_similarity_map(synopsis_tfidf_artifact, seed_ids=seed_ids)
        except Exception:
            synopsis_sims_by_id = {}

    if semantic_mode in {"embeddings", "both"} and synopsis_embeddings_artifact is not None:
        try:
            embed_sims_by_id = compute_seed_embedding_similarity_map(synopsis_embeddings_artifact, seed_ids=seed_ids)
        except Exception:
            embed_sims_by_id = {}

    if semantic_mode == "neural" and synopsis_neural_embeddings_artifact is not None:
        try:
            min_sim_neural = float(SYNOPSIS_NEURAL_MIN_SIM)
            if bool(force_neural_enabled(semantic_mode=semantic_mode)):
                min_sim_neural = float(min(float(min_sim_neural), float(FORCE_NEURAL_MIN_SIM)))
            neural_sims_by_id = compute_seed_neural_similarity_map(
                synopsis_neural_embeddings_artifact,
                seed_ids=seed_ids,
                min_sim=float(min_sim_neural),
            )
        except Exception:
            neural_sims_by_id = {}

    # ------------------------------------------------------------------
    # Stage 0 (Phase 5 final fix): seed-conditioned candidate pool
    #
    # Constrain candidate universe BEFORE Stage 1 admission / Stage 2 scoring.
    # ------------------------------------------------------------------
    stage0_ids, stage0_flags_by_id, stage0_diag = build_stage0_seed_candidate_pool(
        metadata=work,
        seed_ids=list(seed_ids),
        ranked_hygiene_exclude_ids=set(exclude_ids),
        watched_ids=None,
        neural_artifact=synopsis_neural_embeddings_artifact,
        neural_topk=int(STAGE0_NEURAL_TOPK),
        meta_min_genre_overlap=float(STAGE0_META_MIN_GENRE_OVERLAP),
        meta_min_theme_overlap=float(STAGE0_META_MIN_THEME_OVERLAP),
        popularity_backfill=int(STAGE0_POPULARITY_BACKFILL),
        pool_cap=int(STAGE0_POOL_CAP),
        pop_item_ids=(np.asarray(components.item_ids, dtype=np.int64) if components is not None else None),
        pop_scores=(
            np.asarray(components.pop, dtype=np.float32)
            if (components is not None and components.pop is not None)
            else None
        ),
    )

    # Stage 0 enforcement: this is the ONLY candidate universe.
    candidate_ids = [int(x) for x in (stage0_ids or []) if int(x) > 0]
    candidate_id_set = {int(x) for x in candidate_ids}
    if candidate_id_set:
        try:
            candidate_df = work.loc[work["anime_id"].astype(int).isin(candidate_id_set)]
        except Exception:
            candidate_df = work
    else:
        candidate_df = work.iloc[0:0]

    seed_genre_map: dict[str, set[str]] = {}
    all_seed_genres: set[str] = set()
    genre_weights: dict[str, int] = {}

    # Deterministic seed title tokenization for franchise-like backfill.
    # (No new models; uses existing title_display strings only.)
    _TITLE_STOP = {
        "the", "and", "of", "to", "a", "an", "in", "on", "for", "with",
        "movie", "film", "tv", "ova", "ona", "special", "season", "part",
        "episode", "eps", "edition", "new",
    }

    def _title_tokens(s: str) -> set[str]:
        try:
            toks = re.findall(r"[a-z0-9]+", str(s).lower())
        except Exception:
            toks = []
        return {t for t in toks if len(t) >= 3 and t not in _TITLE_STOP}

    seed_title_token_map: dict[str, set[str]] = {}
    for st in seed_titles:
        seed_title_token_map[str(st)] = _title_tokens(str(st))

    for sid, stitle in zip(seed_ids, seed_titles):
        seed_row = work.loc[work["anime_id"].astype(int) == int(sid)].head(1)
        if seed_row.empty:
            continue
        seed_genres = _parse_genres(seed_row.iloc[0].get("genres"))
        seed_genre_map[stitle] = seed_genres
        all_seed_genres.update(seed_genres)
        for g in seed_genres:
            genre_weights[g] = genre_weights.get(g, 0) + 1

    num_seeds = max(1, len(seed_ids))

    # ------------------------------------------------------------------
    # Option A (Phase 4): Two-stage seed-conditioned ranking
    #   Stage 1: shortlist candidates using seed-conditioned signals ONLY
    #            (genre overlap, metadata affinity, synopsis TF-IDF)
    #   Stage 2: rerank only that shortlist using the existing final logic
    #            (hybrid + pop + seed-conditioned bonuses)
    # ------------------------------------------------------------------

    # --- Stage 1: shortlist -------------------------------------------------
    # Prefer embeddings (successor) and TF-IDF (legacy) neighbors first to keep
    # the shortlist seed-conditioned before allowing hybrid/MF priors in Stage 2.
    stage1_embed_pool: list[dict[str, Any]] = []
    stage1_tfidf_pool: list[dict[str, Any]] = []
    stage1_neural_pool: list[dict[str, Any]] = []
    stage1_forced_neural_pool: list[dict[str, Any]] = []
    stage1_fallback_pool: list[dict[str, Any]] = []

    seed_genres_count = int(len(all_seed_genres))
    seed_themes = getattr(seed_meta_profile, "themes", frozenset()) or frozenset()

    forced_neural_pairs: list[tuple[int, float]] = []
    forced_neural_ids: set[int] = set()
    if semantic_mode == "neural" and bool(force_neural_enabled(semantic_mode=semantic_mode)) and bool(neural_sims_by_id):
        forced_neural_pairs = select_forced_neural_pairs(
            neural_sims_by_id,
            seed_ids=seed_ids,
            exclude_ids=set(exclude_ids),
            watched_ids=None,
            topk=int(FORCE_NEURAL_TOPK),
            min_sim=float(FORCE_NEURAL_MIN_SIM),
        )
        forced_neural_ids = {int(aid) for aid, _ in forced_neural_pairs}

    # Phase 5 diagnostics: demographics-aware admission is sparse and must never
    # penalize missingness.
    seed_demo_tokens = normalize_demographics_tokens(getattr(seed_meta_profile, "demographics", frozenset()) or frozenset())
    seed_has_shounen_demo = bool("shounen" in seed_demo_tokens)

    # Diagnostics: quantify admission behavior under the adaptive two-lane policy.
    # Baseline ("old") is kept for comparability: semantic min-sim AND (overlap>0 OR title>=0.50).
    # Policy ("new"): stage1_semantic_admission(...) decision.
    embed_semantic_old_admit = 0
    embed_semantic_policy_admit = 0
    embed_semantic_blocked_by_policy = 0
    tfidf_semantic_old_admit = 0
    tfidf_semantic_policy_admit = 0

    neural_semantic_old_admit = 0
    neural_semantic_policy_admit = 0
    neural_semantic_blocked_by_policy = 0
    tfidf_semantic_blocked_by_policy = 0

    admitted_by_lane_A_count = 0
    admitted_by_lane_B_count = 0
    admitted_by_theme_override_count = 0
    admitted_by_demo_override_shounen_count = 0
    demo_override_admitted_ids: set[int] = set()
    blocked_due_to_overlap_count = 0
    blocked_due_to_low_sim_count = 0

    # Keep a small, deterministic sample of the highest-similarity blocked candidates.
    blocked_embed_top: list[dict[str, Any]] = []
    blocked_tfidf_top: list[dict[str, Any]] = []
    blocked_neural_top: list[dict[str, Any]] = []

    # Keep a small, deterministic sample of Lane A admissions.
    laneA_admitted_examples_top: list[dict[str, Any]] = []

    # For inspection: high-sim blocked candidates with overlap in {0.25, 0.333}.
    blocked_high_sim_overlap_025_0333: list[dict[str, Any]] = []

    # "False negative" hunting: blocked candidates that are *very* high similarity.
    # Defaults are intentionally conservative; override via env vars if desired.
    try:
        false_neg_embed_sim = float(os.environ.get("PHASE4_FALSE_NEG_EMB_SIM", "0.55"))
    except Exception:
        false_neg_embed_sim = 0.55
    try:
        false_neg_tfidf_sim = float(os.environ.get("PHASE4_FALSE_NEG_TFIDF_SIM", "0.08"))
    except Exception:
        false_neg_tfidf_sim = 0.08

    try:
        false_neg_neural_sim = float(
            os.environ.get("PHASE5_FALSE_NEG_NEURAL_SIM", str(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD))
        )
    except Exception:
        false_neg_neural_sim = float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD)

    embed_semantic_blocked_high_sim = 0
    tfidf_semantic_blocked_high_sim = 0
    blocked_embed_high_sim_top: list[dict[str, Any]] = []
    blocked_tfidf_high_sim_top: list[dict[str, Any]] = []
    blocked_neural_high_sim_top: list[dict[str, Any]] = []
    neural_semantic_blocked_high_sim = 0

    def _push_top_blocked(dst: list[dict[str, Any]], entry: dict[str, Any], *, max_n: int = 12) -> None:
        dst.append(entry)
        dst.sort(key=lambda x: (-float(x.get("sim", 0.0)), int(x.get("anime_id", 0))))
        if len(dst) > int(max_n):
            del dst[int(max_n) :]

    def _push_top_laneA_admit(dst: list[dict[str, Any]], entry: dict[str, Any], *, max_n: int = 12) -> None:
        dst.append(entry)
        dst.sort(key=lambda x: (-float(x.get("sim", 0.0)), int(x.get("anime_id", 0))))
        if len(dst) > int(max_n):
            del dst[int(max_n) :]

    stage1_off_type_allowed_sims: list[float] = []
    stage1_off_type_allowed_embed_sims: list[float] = []
    stage1_off_type_allowed_neural_sims: list[float] = []

    # Phase 5 diagnostics: track Stage 1 admission per Stage 0 candidate.
    stage1_admitted_any_by_id: dict[int, bool] = {}
    stage1_block_reason_by_id: dict[int, str] = {}

    def _missing_neural_vector(aid: int) -> bool:
        art = synopsis_neural_embeddings_artifact
        if art is None:
            return False
        try:
            r = art.anime_id_to_row.get(int(aid))
            if r is None:
                return True
            v = art.embeddings[int(r)]
            return bool(float(np.linalg.norm(v)) <= 1e-6)
        except Exception:
            return False

    for _, row in candidate_df.iterrows():
        aid = int(row["anime_id"])
        if aid in exclude_ids:
            continue
        if aid in seed_ids:
            continue
        # No full-catalog iteration here: candidate_df is already Stage 0 constrained.

        stage1_admitted_any_by_id[int(aid)] = False

        item_genres = _parse_genres(row.get("genres"))
        item_themes = _parse_themes(row.get("themes"))
        raw_overlap = sum(genre_weights.get(g, 0) for g in item_genres)
        max_possible_overlap = len(all_seed_genres) * num_seeds
        weighted_overlap = (raw_overlap / max_possible_overlap) if max_possible_overlap > 0 else 0.0

        themes_overlap = theme_overlap_ratio(seed_themes, item_themes)

        overlap_per_seed = {
            seed_title: int(len(seed_genres & item_genres))
            for seed_title, seed_genres in seed_genre_map.items()
        }
        num_seeds_matched = sum(1 for c in overlap_per_seed.values() if c > 0)
        seed_coverage = num_seeds_matched / num_seeds

        # Seed-conditioned metadata affinity (stage 1: treat as cold-start; no hybrid/MF).
        meta_affinity = compute_metadata_affinity(seed_meta_profile, row)
        meta_bonus_s1 = 0.0
        if meta_affinity > 0.0:
            meta_bonus_s1 = float(METADATA_AFFINITY_COLD_START_COEF) * float(meta_affinity)

        synopsis_tfidf_sim = float(synopsis_sims_by_id.get(aid, 0.0))
        synopsis_embed_sim = float(embed_sims_by_id.get(aid, 0.0))
        synopsis_neural_sim = float(neural_sims_by_id.get(aid, 0.0))

        cand_title = str(row.get("title_display") or row.get("title_primary") or "")
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
        cand_type = None if pd.isna(row.get("type")) else str(row.get("type")).strip()
        cand_eps = row.get("episodes")
        base_passes_gate = synopsis_gate_passes(
            seed_type=seed_type_target,
            candidate_type=cand_type,
            candidate_episodes=cand_eps,
        )

        high_sim_override_tfidf = (not bool(base_passes_gate)) and (float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD))
        high_sim_override_embed = (not bool(base_passes_gate)) and (float(synopsis_embed_sim) >= float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD))
        high_sim_override_neural = (not bool(base_passes_gate)) and (float(synopsis_neural_sim) >= float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD))

        base = {
            "anime_id": aid,
            "meta": {
                "title_display": str(row.get("title_display", "")),
                "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                "mal_score": None if pd.isna(row.get("mal_score")) else float(row.get("mal_score")),
                "members_count": None if pd.isna(row.get("members_count")) else int(row.get("members_count")),
                "aired_from": None if pd.isna(row.get("aired_from")) else str(row.get("aired_from")),
            },
            "_stage1": {
                "weighted_overlap": float(weighted_overlap),
                "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                "seed_coverage": float(seed_coverage),
                "metadata_affinity": float(meta_affinity),
                "title_overlap": float(title_overlap),
                "synopsis_tfidf_sim": float(synopsis_tfidf_sim),
                "synopsis_tfidf_base_gate_passed": bool(base_passes_gate),
                "synopsis_tfidf_high_sim_override": bool(high_sim_override_tfidf),
                "synopsis_embed_sim": float(synopsis_embed_sim),
                "synopsis_embed_high_sim_override": bool(high_sim_override_embed),
                "synopsis_neural_sim": float(synopsis_neural_sim),
                "synopsis_neural_high_sim_override": bool(high_sim_override_neural),
                "forced_neural": bool(aid in forced_neural_ids),
                "overlap_per_seed": overlap_per_seed,
            },
        }

        # Phase 5 refinement: force-include top-K neural neighbors into Stage 1 shortlist.
        # This bypasses only the type/episodes gate; ranked hygiene exclusions were already
        # applied via exclude_ids above.
        if (
            semantic_mode == "neural"
            and bool((base.get("_stage1") or {}).get("forced_neural"))
            and float(synopsis_neural_sim) >= float(FORCE_NEURAL_MIN_SIM)
        ):
            forced_item = dict(base)
            forced_item["stage1_score"] = float(synopsis_neural_sim)
            stage1_forced_neural_pool.append(forced_item)

            # Ensure the existing off-type admission diagnostics reflect that off-type
            # candidates can enter via the force pool (not only via HIGH_SIM overrides).
            if (not bool(base_passes_gate)) and (not bool(high_sim_override_neural)):
                stage1_off_type_allowed_neural_sims.append(float(synopsis_neural_sim))

        # Pool A0: neural sentence-transformer neighbors (gated)
        if semantic_mode == "neural":
            passes_gate_effective_neural = bool(base_passes_gate) or bool(high_sim_override_neural)

            neural_decision = stage1_semantic_admission(
                semantic_sim=float(synopsis_neural_sim),
                min_sim=float(SYNOPSIS_NEURAL_MIN_SIM),
                high_sim=float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD),
                genre_overlap=float(weighted_overlap),
                title_overlap=float(title_overlap),
                seed_genres_count=int(seed_genres_count),
                num_seeds=int(num_seeds),
                theme_overlap=themes_overlap,
                seed_demographics=getattr(seed_meta_profile, "demographics", frozenset()) or frozenset(),
                candidate_demographics=row.get("demographics"),
                demo_shounen_min_sim=float(STAGE1_DEMO_SHOUNEN_MIN_SIM_NEURAL),
            )

            if bool(passes_gate_effective_neural):
                if neural_decision.admitted:
                    if neural_decision.lane == "A":
                        admitted_by_lane_A_count += 1
                        if bool(neural_decision.used_theme_override):
                            admitted_by_theme_override_count += 1

                        laneA_entry = {
                            "anime_id": int(aid),
                            "title": str(row.get("title_display") or ""),
                            "source": "neural",
                            "sim": float(synopsis_neural_sim),
                            "weighted_overlap": float(weighted_overlap),
                            "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                            "title_overlap": float(title_overlap),
                            "low_genre_overlap": float(neural_decision.low_genre_overlap),
                            "used_theme_override": bool(neural_decision.used_theme_override),
                            "rescued_from_overlap_ge_050": bool(
                                float(weighted_overlap) < 0.50 and float(title_overlap) < 0.50
                            ),
                            "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                            "episodes": None if pd.isna(row.get("episodes")) else int(row.get("episodes")),
                        }
                        _push_top_laneA_admit(laneA_admitted_examples_top, laneA_entry, max_n=12)
                    elif neural_decision.lane == "B":
                        admitted_by_lane_B_count += 1
                    elif neural_decision.lane == "demo_shounen":
                        admitted_by_demo_override_shounen_count += 1
                        demo_override_admitted_ids.add(int(aid))
                else:
                    if neural_decision.lane == "blocked_overlap":
                        blocked_due_to_overlap_count += 1
                    elif neural_decision.lane == "blocked_low_sim":
                        blocked_due_to_low_sim_count += 1

            neural_sem_base_ok = bool(passes_gate_effective_neural) and float(synopsis_neural_sim) >= float(SYNOPSIS_NEURAL_MIN_SIM)
            neural_sem_old_ok = bool(neural_sem_base_ok) and (float(weighted_overlap) > 0.0 or float(title_overlap) >= 0.50)
            neural_sem_policy_ok = bool(neural_sem_base_ok) and bool(neural_decision.admitted)
            if bool(neural_sem_old_ok):
                neural_semantic_old_admit += 1
            if bool(neural_sem_policy_ok):
                neural_semantic_policy_admit += 1
            if bool(neural_sem_old_ok) and (not bool(neural_sem_policy_ok)):
                neural_semantic_blocked_by_policy += 1
                blocked_entry = {
                    "anime_id": int(aid),
                    "title": str(row.get("title_display") or ""),
                    "source": "neural",
                    "sim": float(synopsis_neural_sim),
                    "weighted_overlap": float(weighted_overlap),
                    "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                    "title_overlap": float(title_overlap),
                    "low_genre_overlap": float(neural_decision.low_genre_overlap),
                    "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                    "episodes": None if pd.isna(row.get("episodes")) else int(row.get("episodes")),
                }
                _push_top_blocked(blocked_neural_top, blocked_entry)
                if float(synopsis_neural_sim) >= float(false_neg_neural_sim):
                    neural_semantic_blocked_high_sim += 1
                    _push_top_blocked(blocked_neural_high_sim_top, blocked_entry, max_n=20)

            if bool(passes_gate_effective_neural) and bool(neural_decision.admitted):
                item = dict(base)
                s1 = item.get("_stage1")
                if not isinstance(s1, dict):
                    s1 = {}
                    item["_stage1"] = s1
                s1.update(
                    {
                        "neural_admission_lane": str(neural_decision.lane),
                        "neural_demo_override_shounen": bool(neural_decision.lane == "demo_shounen"),
                    }
                )
                item["stage1_score"] = float(synopsis_neural_sim)
                stage1_neural_pool.append(item)
                if bool(high_sim_override_neural):
                    stage1_off_type_allowed_neural_sims.append(float(synopsis_neural_sim))
                stage1_admitted_any_by_id[int(aid)] = True
                continue

        # Pool A0: embeddings neighbors (gated) – use similarity as the primary Stage 1 rank.
        if semantic_mode not in {"embeddings", "both"}:
            passes_gate_effective_embed = False
        else:
            passes_gate_effective_embed = bool(base_passes_gate) or bool(high_sim_override_embed)

        embed_decision = stage1_semantic_admission(
            semantic_sim=float(synopsis_embed_sim),
            min_sim=float(SYNOPSIS_EMBEDDINGS_MIN_SIM),
            high_sim=float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD),
            genre_overlap=float(weighted_overlap),
            title_overlap=float(title_overlap),
            seed_genres_count=int(seed_genres_count),
            num_seeds=int(num_seeds),
            theme_overlap=themes_overlap,
        )

        if bool(passes_gate_effective_embed):
            if embed_decision.admitted:
                if embed_decision.lane == "A":
                    admitted_by_lane_A_count += 1
                    if bool(embed_decision.used_theme_override):
                        admitted_by_theme_override_count += 1

                    laneA_entry = {
                        "anime_id": int(aid),
                        "title": str(row.get("title_display") or ""),
                        "source": "embeddings",
                        "sim": float(synopsis_embed_sim),
                        "weighted_overlap": float(weighted_overlap),
                        "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                        "title_overlap": float(title_overlap),
                        "low_genre_overlap": float(embed_decision.low_genre_overlap),
                        "used_theme_override": bool(embed_decision.used_theme_override),
                        "rescued_from_overlap_ge_050": bool(
                            float(weighted_overlap) < 0.50 and float(title_overlap) < 0.50
                        ),
                        "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                        "episodes": None if pd.isna(row.get("episodes")) else int(row.get("episodes")),
                    }
                    _push_top_laneA_admit(laneA_admitted_examples_top, laneA_entry, max_n=12)
                elif embed_decision.lane == "B":
                    admitted_by_lane_B_count += 1
            else:
                if embed_decision.lane == "blocked_overlap":
                    blocked_due_to_overlap_count += 1
                elif embed_decision.lane == "blocked_low_sim":
                    blocked_due_to_low_sim_count += 1

        embed_sem_base_ok = bool(passes_gate_effective_embed) and float(synopsis_embed_sim) >= float(SYNOPSIS_EMBEDDINGS_MIN_SIM)
        embed_sem_old_ok = bool(embed_sem_base_ok) and (float(weighted_overlap) > 0.0 or float(title_overlap) >= 0.50)
        embed_sem_policy_ok = bool(embed_sem_base_ok) and bool(embed_decision.admitted)
        if bool(embed_sem_old_ok):
            embed_semantic_old_admit += 1
        if bool(embed_sem_policy_ok):
            embed_semantic_policy_admit += 1
        if bool(embed_sem_old_ok) and (not bool(embed_sem_policy_ok)):
            embed_semantic_blocked_by_policy += 1
            blocked_entry = {
                "anime_id": int(aid),
                "title": str(row.get("title_display") or ""),
                "source": "embeddings",
                "sim": float(synopsis_embed_sim),
                "weighted_overlap": float(weighted_overlap),
                "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                "title_overlap": float(title_overlap),
                "low_genre_overlap": float(embed_decision.low_genre_overlap),
                "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                "episodes": None if pd.isna(row.get("episodes")) else int(row.get("episodes")),
            }
            _push_top_blocked(blocked_embed_top, blocked_entry)
            if float(synopsis_embed_sim) >= float(false_neg_embed_sim):
                embed_semantic_blocked_high_sim += 1
                _push_top_blocked(blocked_embed_high_sim_top, blocked_entry, max_n=20)

            if float(synopsis_embed_sim) >= float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD):
                ov = round(float(weighted_overlap), 3)
                if ov in {0.25, 0.333}:
                    _push_top_blocked(blocked_high_sim_overlap_025_0333, blocked_entry, max_n=12)

        if bool(passes_gate_effective_embed) and bool(embed_decision.admitted):
            item = dict(base)
            item["stage1_score"] = float(synopsis_embed_sim)
            stage1_embed_pool.append(item)
            if bool(high_sim_override_embed):
                stage1_off_type_allowed_embed_sims.append(float(synopsis_embed_sim))
            stage1_admitted_any_by_id[int(aid)] = True
            continue

        # Pool A: TF-IDF neighbors (gated) – use similarity as the primary Stage 1 rank.
        if semantic_mode not in {"tfidf", "both"}:
            passes_gate_effective_tfidf = False
        else:
            passes_gate_effective_tfidf = bool(base_passes_gate) or bool(high_sim_override_tfidf)

        tfidf_decision = stage1_semantic_admission(
            semantic_sim=float(synopsis_tfidf_sim),
            min_sim=float(SYNOPSIS_TFIDF_MIN_SIM),
            high_sim=float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD),
            genre_overlap=float(weighted_overlap),
            title_overlap=float(title_overlap),
            seed_genres_count=int(seed_genres_count),
            num_seeds=int(num_seeds),
            theme_overlap=themes_overlap,
        )

        if bool(passes_gate_effective_tfidf):
            if tfidf_decision.admitted:
                if tfidf_decision.lane == "A":
                    admitted_by_lane_A_count += 1
                    if bool(tfidf_decision.used_theme_override):
                        admitted_by_theme_override_count += 1

                    laneA_entry = {
                        "anime_id": int(aid),
                        "title": str(row.get("title_display") or ""),
                        "source": "tfidf",
                        "sim": float(synopsis_tfidf_sim),
                        "weighted_overlap": float(weighted_overlap),
                        "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                        "title_overlap": float(title_overlap),
                        "low_genre_overlap": float(tfidf_decision.low_genre_overlap),
                        "used_theme_override": bool(tfidf_decision.used_theme_override),
                        "rescued_from_overlap_ge_050": bool(
                            float(weighted_overlap) < 0.50 and float(title_overlap) < 0.50
                        ),
                        "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                        "episodes": None if pd.isna(row.get("episodes")) else int(row.get("episodes")),
                    }
                    _push_top_laneA_admit(laneA_admitted_examples_top, laneA_entry, max_n=12)
                elif tfidf_decision.lane == "B":
                    admitted_by_lane_B_count += 1
            else:
                if tfidf_decision.lane == "blocked_overlap":
                    blocked_due_to_overlap_count += 1
                elif tfidf_decision.lane == "blocked_low_sim":
                    blocked_due_to_low_sim_count += 1

        tfidf_sem_base_ok = bool(passes_gate_effective_tfidf) and float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_MIN_SIM)
        tfidf_sem_old_ok = bool(tfidf_sem_base_ok) and (float(weighted_overlap) > 0.0 or float(title_overlap) >= 0.50)
        tfidf_sem_policy_ok = bool(tfidf_sem_base_ok) and bool(tfidf_decision.admitted)
        if bool(tfidf_sem_old_ok):
            tfidf_semantic_old_admit += 1
        if bool(tfidf_sem_policy_ok):
            tfidf_semantic_policy_admit += 1
        if bool(tfidf_sem_old_ok) and (not bool(tfidf_sem_policy_ok)):
            tfidf_semantic_blocked_by_policy += 1
            blocked_entry = {
                "anime_id": int(aid),
                "title": str(row.get("title_display") or ""),
                "source": "tfidf",
                "sim": float(synopsis_tfidf_sim),
                "weighted_overlap": float(weighted_overlap),
                "theme_overlap": None if themes_overlap is None else float(themes_overlap),
                "title_overlap": float(title_overlap),
                "low_genre_overlap": float(tfidf_decision.low_genre_overlap),
                "type": None if pd.isna(row.get("type")) else str(row.get("type")).strip(),
                "episodes": None if pd.isna(row.get("episodes")) else int(row.get("episodes")),
            }
            _push_top_blocked(blocked_tfidf_top, blocked_entry)
            if float(synopsis_tfidf_sim) >= float(false_neg_tfidf_sim):
                tfidf_semantic_blocked_high_sim += 1
                _push_top_blocked(blocked_tfidf_high_sim_top, blocked_entry, max_n=20)

            if float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD):
                ov = round(float(weighted_overlap), 3)
                if ov in {0.25, 0.333}:
                    _push_top_blocked(blocked_high_sim_overlap_025_0333, blocked_entry, max_n=12)

        if bool(passes_gate_effective_tfidf) and bool(tfidf_decision.admitted):
            item = dict(base)
            item["stage1_score"] = float(synopsis_tfidf_sim)
            stage1_tfidf_pool.append(item)
            if bool(high_sim_override_tfidf):
                stage1_off_type_allowed_sims.append(float(synopsis_tfidf_sim))
            stage1_admitted_any_by_id[int(aid)] = True
            continue

        # Pool B: backfill candidates when TF-IDF is absent/insufficient.
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

            stage1_admitted_any_by_id[int(aid)] = True

        # If not admitted to any Stage 1 pool, assign a deterministic first block reason.
        if not bool(stage1_admitted_any_by_id.get(int(aid), False)):
            if bool(_missing_neural_vector(int(aid))):
                stage1_block_reason_by_id[int(aid)] = str(MISSING_SEMANTIC_VECTOR)
            else:
                if semantic_mode == "neural":
                    try:
                        if bool(passes_gate_effective_neural) and str(neural_decision.lane) == "blocked_low_sim":
                            stage1_block_reason_by_id[int(aid)] = str(BLOCKED_LOW_SEMANTIC_SIM)
                        elif bool(passes_gate_effective_neural) and str(neural_decision.lane) == "blocked_overlap":
                            stage1_block_reason_by_id[int(aid)] = str(BLOCKED_LOW_OVERLAP)
                        else:
                            stage1_block_reason_by_id[int(aid)] = str(BLOCKED_OTHER_ADMISSION)
                    except Exception:
                        stage1_block_reason_by_id[int(aid)] = str(BLOCKED_OTHER_ADMISSION)
                else:
                    stage1_block_reason_by_id[int(aid)] = str(BLOCKED_OTHER_ADMISSION)

    stage1_embed_pool.sort(
        key=lambda x: (
            -float((x.get("_stage1") or {}).get("synopsis_embed_sim", 0.0)),
            -float((x.get("_stage1") or {}).get("weighted_overlap", 0.0)),
            -float((x.get("_stage1") or {}).get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_tfidf_pool.sort(
        key=lambda x: (
            -float((x.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0)),
            -float((x.get("_stage1") or {}).get("weighted_overlap", 0.0)),
            -float((x.get("_stage1") or {}).get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_neural_pool.sort(
        key=lambda x: (
            -float((x.get("_stage1") or {}).get("synopsis_neural_sim", 0.0)),
            -float((x.get("_stage1") or {}).get("weighted_overlap", 0.0)),
            -float((x.get("_stage1") or {}).get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_forced_neural_pool.sort(
        key=lambda x: (-float((x.get("_stage1") or {}).get("synopsis_neural_sim", 0.0)), int(x.get("anime_id", 0)))
    )
    stage1_fallback_pool.sort(key=lambda x: (-float(x.get("stage1_score", 0.0)), int(x.get("anime_id", 0))))

    stage1_gate_blocking_diagnostics = {
        "embed_semantic_old_admit_count": int(embed_semantic_old_admit),
        "embed_semantic_policy_admit_count": int(embed_semantic_policy_admit),
        "embed_semantic_blocked_by_policy_count": int(embed_semantic_blocked_by_policy),
        "embed_semantic_blocked_by_policy_rate": float(embed_semantic_blocked_by_policy)
        / float(max(1, embed_semantic_old_admit)),
        "tfidf_semantic_old_admit_count": int(tfidf_semantic_old_admit),
        "tfidf_semantic_policy_admit_count": int(tfidf_semantic_policy_admit),
        "tfidf_semantic_blocked_by_policy_count": int(tfidf_semantic_blocked_by_policy),
        "tfidf_semantic_blocked_by_policy_rate": float(tfidf_semantic_blocked_by_policy)
        / float(max(1, tfidf_semantic_old_admit)),
        "neural_semantic_old_admit_count": int(neural_semantic_old_admit),
        "neural_semantic_policy_admit_count": int(neural_semantic_policy_admit),
        "neural_semantic_blocked_by_policy_count": int(neural_semantic_blocked_by_policy),
        "neural_semantic_blocked_by_policy_rate": float(neural_semantic_blocked_by_policy)
        / float(max(1, neural_semantic_old_admit)),
        "admitted_by_lane_A_count": int(admitted_by_lane_A_count),
        "admitted_by_lane_B_count": int(admitted_by_lane_B_count),
        "admitted_by_theme_override_count": int(admitted_by_theme_override_count),
        "admitted_by_demo_override_shounen_count": int(admitted_by_demo_override_shounen_count),
        "blocked_due_to_overlap_count": int(blocked_due_to_overlap_count),
        "blocked_due_to_low_sim_count": int(blocked_due_to_low_sim_count),
        "laneA_admitted_examples_top": list(laneA_admitted_examples_top),
        "blocked_high_sim_overlap_025_0333_top": list(blocked_high_sim_overlap_025_0333),
        "embed_semantic_blocked_top": list(blocked_embed_top),
        "tfidf_semantic_blocked_top": list(blocked_tfidf_top),
        "neural_semantic_blocked_top": list(blocked_neural_top),
        "false_neg_embed_sim_threshold": float(false_neg_embed_sim),
        "false_neg_tfidf_sim_threshold": float(false_neg_tfidf_sim),
        "false_neg_neural_sim_threshold": float(false_neg_neural_sim),
        "embed_semantic_blocked_high_sim_count": int(embed_semantic_blocked_high_sim),
        "tfidf_semantic_blocked_high_sim_count": int(tfidf_semantic_blocked_high_sim),
        "neural_semantic_blocked_high_sim_count": int(neural_semantic_blocked_high_sim),
        "embed_semantic_blocked_high_sim_top": list(blocked_embed_high_sim_top),
        "tfidf_semantic_blocked_high_sim_top": list(blocked_tfidf_high_sim_top),
        "neural_semantic_blocked_high_sim_top": list(blocked_neural_high_sim_top),
    }

    shortlist_k = max(0, int(shortlist_size))
    stage1_total_candidates = int(
        len(stage1_neural_pool) + len(stage1_embed_pool) + len(stage1_tfidf_pool) + len(stage1_fallback_pool)
    )
    # Phase 4 stabilization: Stage 1 mixture shortlist + semantic confidence gating.
    # Pool A: semantic neighbors (neural OR embeddings/tfidf; seed-conditioned)
    # Pool B: seed-conditioned metadata/genre candidates
    # Pool C: deterministic backfill if A/B are insufficient
    use_embed = semantic_mode in {"embeddings", "both"}
    use_tfidf = semantic_mode in {"tfidf", "both"}
    use_neural = semantic_mode in {"neural"}
    pool_a: list[dict[str, Any]] = []
    if bool(use_neural):
        pool_a.extend(stage1_neural_pool)
    if bool(use_embed):
        pool_a.extend(stage1_embed_pool)
    if bool(use_tfidf):
        pool_a.extend(stage1_tfidf_pool)

    pool_b: list[dict[str, Any]] = list(stage1_fallback_pool)

    def _topk_sim_stats(sim_map: dict[int, float], *, k: int = 50) -> dict[str, Any]:
        vals: list[float] = []
        for aid, s in sim_map.items():
            try:
                aid_i = int(aid)
                if aid_i in exclude_ids or aid_i in seed_ids:
                    continue
                fs = float(s)
                if fs <= 0.0:
                    continue
                vals.append(fs)
            except Exception:
                continue
        vals.sort(reverse=True)
        top = vals[: max(0, int(k))]
        if not top:
            return {"count": 0, "mean": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
        arr = np.asarray(top, dtype=np.float64)
        mean = float(arr.mean())
        p95 = float(np.percentile(arr, 95)) if int(arr.size) >= 2 else float(arr[0])
        return {"count": int(arr.size), "mean": float(mean), "p95": float(p95), "min": float(arr.min()), "max": float(arr.max())}

    def _conf_score(stats: dict[str, Any], *, min_sim: float, high_sim: float) -> float:
        denom = float(max(1e-6, float(high_sim) - float(min_sim)))
        mean_n = max(0.0, min(1.0, (float(stats.get("mean", 0.0)) - float(min_sim)) / denom))
        p95_n = max(0.0, min(1.0, (float(stats.get("p95", 0.0)) - float(min_sim)) / denom))
        return float(0.5 * (mean_n + p95_n))

    embed_stats = _topk_sim_stats(embed_sims_by_id, k=50) if bool(use_embed) else {"count": 0, "mean": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
    tfidf_stats = _topk_sim_stats(synopsis_sims_by_id, k=50) if bool(use_tfidf) else {"count": 0, "mean": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
    neural_stats = _topk_sim_stats(neural_sims_by_id, k=50) if bool(use_neural) else {"count": 0, "mean": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}

    def _neighbor_coherence(pool: list[dict[str, Any]], *, k: int = 50) -> dict[str, Any]:
        top = pool[: max(0, int(k))]
        if not top:
            return {"count": 0, "weighted_overlap_mean": 0.0, "seed_coverage_mean": 0.0, "any_genre_match_frac": 0.0}
        overlaps = [float((it.get("_stage1") or {}).get("weighted_overlap", 0.0)) for it in top]
        coverages = [float((it.get("_stage1") or {}).get("seed_coverage", 0.0)) for it in top]
        any_match = sum(1 for v in overlaps if float(v) > 0.0)
        return {
            "count": int(len(top)),
            "weighted_overlap_mean": float(sum(overlaps) / max(1, len(overlaps))),
            "seed_coverage_mean": float(sum(coverages) / max(1, len(coverages))),
            "any_genre_match_frac": float(any_match / max(1, len(overlaps))),
        }

    embed_coherence = _neighbor_coherence(stage1_embed_pool, k=50) if bool(use_embed) else {"count": 0, "weighted_overlap_mean": 0.0, "seed_coverage_mean": 0.0, "any_genre_match_frac": 0.0}
    tfidf_coherence = _neighbor_coherence(stage1_tfidf_pool, k=50) if bool(use_tfidf) else {"count": 0, "weighted_overlap_mean": 0.0, "seed_coverage_mean": 0.0, "any_genre_match_frac": 0.0}
    neural_coherence = _neighbor_coherence(stage1_neural_pool, k=50) if bool(use_neural) else {"count": 0, "weighted_overlap_mean": 0.0, "seed_coverage_mean": 0.0, "any_genre_match_frac": 0.0}

    semantic_conf_source = "none"
    semantic_conf_score = 0.0
    semantic_conf_tier = "none"

    def _coherence_score(stats: dict[str, Any]) -> float:
        # Weighted overlap is normalized in [0,1]. Seed coverage is also [0,1].
        # Scale overlap more aggressively: 0.20 mean overlap is treated as "good".
        overlap_mean = float(stats.get("weighted_overlap_mean", 0.0))
        seed_cov_mean = float(stats.get("seed_coverage_mean", 0.0))
        any_match = float(stats.get("any_genre_match_frac", 0.0))
        overlap_s = max(0.0, min(1.0, overlap_mean / 0.20))
        seedcov_s = max(0.0, min(1.0, seed_cov_mean / 0.50))
        any_s = max(0.0, min(1.0, any_match / 0.80))
        return float((overlap_s + seedcov_s + any_s) / 3.0)

    if bool(use_neural) and int(neural_stats.get("count", 0)) > 0:
        semantic_conf_source = "neural"
        sim_conf = _conf_score(neural_stats, min_sim=float(SYNOPSIS_NEURAL_MIN_SIM), high_sim=float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD))
        coh_conf = _coherence_score(neural_coherence)
        semantic_conf_score = float(0.70 * float(sim_conf) + 0.30 * float(coh_conf))
    elif bool(use_embed) and int(embed_stats.get("count", 0)) > 0:
        semantic_conf_source = "embeddings"
        sim_conf = _conf_score(embed_stats, min_sim=float(SYNOPSIS_EMBEDDINGS_MIN_SIM), high_sim=float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD))
        coh_conf = _coherence_score(embed_coherence)
        semantic_conf_score = float(0.70 * float(sim_conf) + 0.30 * float(coh_conf))
    elif bool(use_tfidf) and int(tfidf_stats.get("count", 0)) > 0:
        semantic_conf_source = "tfidf"
        sim_conf = _conf_score(tfidf_stats, min_sim=float(SYNOPSIS_TFIDF_MIN_SIM), high_sim=float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD))
        coh_conf = _coherence_score(tfidf_coherence)
        semantic_conf_score = float(0.70 * float(sim_conf) + 0.30 * float(coh_conf))

    if semantic_conf_source == "none":
        semantic_conf_tier = "none"
    elif float(semantic_conf_score) >= 0.60:
        semantic_conf_tier = "high"
    elif float(semantic_conf_score) >= 0.30:
        semantic_conf_tier = "medium"
    else:
        semantic_conf_tier = "low"

    # Deterministically allocate shortlist budget between semantic neighbors (A) and metadata/genre candidates (B).
    if shortlist_k <= 0:
        stage1_k_sem = int(len(pool_a))
        stage1_k_meta = int(len(pool_b))
        shortlist, forced_added_count = build_stage1_shortlist(
            pool_a=pool_a,
            pool_b=pool_b,
            shortlist_k=int(len(pool_a) + len(pool_b) + len(stage1_forced_neural_pool)),
            k_sem=int(stage1_k_sem),
            k_meta=int(stage1_k_meta),
            forced_first=stage1_forced_neural_pool,
        )
    else:
        # Keep a robust mixture even when semantic confidence is high.
        if semantic_conf_tier == "high":
            sem_frac = 0.50
        elif semantic_conf_tier == "medium":
            sem_frac = 0.40
        elif semantic_conf_tier == "low":
            sem_frac = 0.20
        else:
            sem_frac = 0.0

        stage1_k_sem = int(round(float(shortlist_k) * float(sem_frac)))
        stage1_k_sem = max(0, min(int(shortlist_k), int(stage1_k_sem)))
        stage1_k_meta = int(shortlist_k) - int(stage1_k_sem)

        shortlist, forced_added_count = build_stage1_shortlist(
            pool_a=pool_a,
            pool_b=pool_b,
            shortlist_k=int(shortlist_k),
            k_sem=int(stage1_k_sem),
            k_meta=int(stage1_k_meta),
            forced_first=stage1_forced_neural_pool,
        )

    # --- Stage 2: rerank shortlist using existing final scoring --------------
    try:
        blended_scores = recommender._blend(0, weights)  # pylint: disable=protected-access
    except Exception:
        blended_scores = None

    id_to_index = {int(aid): idx for idx, aid in enumerate(components.item_ids)}

    scored: list[dict[str, Any]] = []

    # Phase 5 experiment diagnostics: content-first activation and One Piece debug.
    content_first_one_piece_rows_by_neural: list[dict[str, Any]] = []

    for c in shortlist:
        aid = int(c["anime_id"])
        s1 = float(c.get("stage1_score", 0.0))

        weighted_overlap = float((c.get("_stage1") or {}).get("weighted_overlap", 0.0))
        seed_coverage = float((c.get("_stage1") or {}).get("seed_coverage", 0.0))
        meta_affinity = float((c.get("_stage1") or {}).get("metadata_affinity", 0.0))
        synopsis_tfidf_sim = float((c.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0))
        synopsis_embed_sim = float((c.get("_stage1") or {}).get("synopsis_embed_sim", 0.0))
        synopsis_neural_sim = float((c.get("_stage1") or {}).get("synopsis_neural_sim", 0.0))
        overlap_per_seed = (c.get("_stage1") or {}).get("overlap_per_seed") or {}

        pop_pct = _pop_pct(pop_pct_by_id, aid)
        popularity_boost = max(0.0, (0.5 - pop_pct) / 0.5)

        if blended_scores is not None and aid in id_to_index:
            hybrid_val = float(blended_scores[int(id_to_index[aid])])
        else:
            hybrid_val = 0.0

        # CF-only hybrid stabilizer (mf/knn only; pop excluded)
        # NOTE: We gate on this, not blended hybrid_val, because hybrid_val can be dominated by pop.
        hybrid_cf_score = 0.0
        if aid in id_to_index:
            idx = int(id_to_index[aid])
            try:
                mf_base = float(components.mf[0, idx]) if components.mf is not None else 0.0
            except Exception:
                mf_base = 0.0
            try:
                knn_base = float(components.knn[0, idx]) if components.knn is not None else 0.0
            except Exception:
                knn_base = 0.0
            hybrid_cf_score = float((0.93 * mf_base) + (0.07 * knn_base))

        content_first_active = bool(
            should_use_content_first(
                float(hybrid_cf_score),
                semantic_mode=str(semantic_mode),
                sem_conf=str(semantic_conf_tier),
                neural_sim=float(synopsis_neural_sim),
            )
        )

        meta_bonus = 0.0
        if meta_affinity > 0.0:
            coef = float(METADATA_AFFINITY_COLD_START_COEF) if hybrid_val == 0.0 else float(METADATA_AFFINITY_TRAINED_COEF)
            meta_bonus = float(coef) * float(meta_affinity)

        # Recompute TF-IDF bonus with the existing hybrid-conditioned coefficient.
        cand_type = (c.get("meta") or {}).get("type")
        cand_eps = work.loc[work["anime_id"].astype(int) == aid, "episodes"].head(1)
        cand_eps_val = None if cand_eps.empty else cand_eps.iloc[0]

        passes_gate = synopsis_gate_passes(
            seed_type=seed_type_target,
            candidate_type=cand_type,
            candidate_episodes=cand_eps_val,
        )
        high_sim_override_tfidf = (not bool(passes_gate)) and (float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD))
        high_sim_override_embed = (not bool(passes_gate)) and (float(synopsis_embed_sim) >= float(SYNOPSIS_EMBEDDINGS_HIGH_SIM_THRESHOLD))
        high_sim_override_neural = (not bool(passes_gate)) and (float(synopsis_neural_sim) >= float(SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD))
        passes_gate_effective_tfidf = bool(passes_gate) or bool(high_sim_override_tfidf)
        passes_gate_effective_embed = bool(passes_gate) or bool(high_sim_override_embed)
        passes_gate_effective_neural = bool(passes_gate) or bool(high_sim_override_neural)

        # If we admitted a candidate via the high-sim override, treat it as a
        # cold-start-ish semantic neighbor for TF-IDF coefficient selection and
        # do not let a negative hybrid value effectively veto it.
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

            # Prefer a small penalty (not exclusion) for very-high-sim off-type items.
            # Keep the existing conservative short-form penalty for all other off-gate cases.
            if bool(high_sim_override_tfidf):
                synopsis_tfidf_penalty = -float(SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY)
            else:
                synopsis_tfidf_penalty = float(
                    synopsis_tfidf_penalty_for_candidate(
                        passes_gate=passes_gate,
                        sim=synopsis_tfidf_sim,
                        candidate_episodes=cand_eps_val,
                    )
                )
            synopsis_tfidf_adjustment = float(synopsis_tfidf_bonus + synopsis_tfidf_penalty)

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
                        candidate_episodes=cand_eps_val,
                    )
                )
            synopsis_embed_adjustment = float(synopsis_embed_bonus + synopsis_embed_penalty)

        synopsis_neural_bonus = 0.0
        synopsis_neural_penalty = 0.0
        synopsis_neural_adjustment = 0.0
        synopsis_neural_penalty_before_override = 0.0
        synopsis_neural_penalty_after_override = 0.0
        high_sim_override_stage2_relaxed = False
        if semantic_mode == "neural":
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
                        candidate_episodes=cand_eps_val,
                    )
                )

            synopsis_neural_penalty_before_override = float(synopsis_neural_penalty)
            synopsis_neural_penalty = float(
                relax_off_type_penalty(
                    penalty=float(synopsis_neural_penalty),
                    neural_sim=float(synopsis_neural_sim),
                    semantic_mode=str(semantic_mode),
                    browse_mode=False,
                )
            )
            synopsis_neural_penalty_after_override = float(synopsis_neural_penalty)
            high_sim_override_stage2_relaxed = bool(
                should_relax_off_type_penalty(
                    neural_sim=float(synopsis_neural_sim),
                    semantic_mode=str(semantic_mode),
                    browse_mode=False,
                )
                and float(synopsis_neural_penalty_after_override) != float(synopsis_neural_penalty_before_override)
            )
            synopsis_neural_adjustment = float(synopsis_neural_bonus + synopsis_neural_penalty)

        # Optional tiny tie-breaker: demographics overlap (Stage 2 only; never gates).
        if "demographics" in work.columns:
            seed_demo = seed_meta_profile.demographics
            cand_demo = work.loc[work["anime_id"].astype(int) == aid, "demographics"].head(1)
            cand_demo_val = None if cand_demo.empty else cand_demo.iloc[0]
            demo_bonus = demographics_overlap_tiebreak_bonus(seed_demo, cand_demo_val)
        else:
            demo_bonus = 0.0

        # Optional tiny tie-breaker: themes overlap (Stage 2 only; never gates).
        theme_overlap = (c.get("_stage1") or {}).get("theme_overlap")
        semantic_sim_for_theme = max(float(synopsis_tfidf_sim), float(synopsis_embed_sim), float(synopsis_neural_sim))
        theme_bonus = theme_stage2_tiebreak_bonus(
            None if theme_overlap is None else float(theme_overlap),
            semantic_sim=float(semantic_sim_for_theme),
            genre_overlap=float(weighted_overlap),
        )

        # Retrieve MAL score and members count for quality scaling.
        item_mal_score = (c.get("meta") or {}).get("mal_score")
        item_members_count = (c.get("meta") or {}).get("members_count")
        if item_mal_score is not None:
            try:
                item_mal_score = float(item_mal_score)
            except Exception:
                item_mal_score = None
        if item_members_count is not None:
            try:
                item_members_count = int(item_members_count)
            except Exception:
                item_members_count = None

        # Phase 5 fix: Quality-scaled neural contribution.
        # Scale neural_sim by quality factor: MAL 5.0->0.15, 7.0->0.5, 9.0->1.0
        if item_mal_score is not None and item_mal_score > 0:
            quality_factor = max(0.15, min(1.0, (item_mal_score - 5.0) / 4.0))
        else:
            quality_factor = 0.3  # Conservative default for missing scores

        neural_contribution = 1.5 * float(synopsis_neural_sim) * quality_factor

        # Phase 5 fix: rebalanced weights to make neural similarity dominant.
        score_before = (
            (0.3 * weighted_overlap)
            + (0.1 * seed_coverage)
            + (0.15 * float(hybrid_val_for_scoring))
            + (0.05 * popularity_boost)
            + (0.10 * float(s1))
            + neural_contribution  # Quality-scaled neural contribution
            + meta_bonus
            + synopsis_tfidf_adjustment
            + synopsis_embed_adjustment
            + synopsis_neural_adjustment
            + float(demo_bonus)
            + float(theme_bonus)
        )

        # Phase 5 fix: Obscurity/quality penalty for low-quality/unknown items.
        obscurity_penalty = 0.0
        if item_members_count is not None and item_members_count < 50000:
            obscurity_penalty += 0.25  # Low member count penalty (aggressive)
        if item_mal_score is None:
            obscurity_penalty += 0.15  # Missing MAL score penalty
        elif item_mal_score < 7.0:
            # Strong penalty for low-rated items: MAL 6.0 -> 0.20, MAL 5.0 -> 0.40
            obscurity_penalty += max(0.0, 0.20 * (7.0 - item_mal_score))
        score_before = score_before - obscurity_penalty

        score_after = float(score_before)
        quality_prior = 0.0
        if bool(content_first_active):
            ms = (c.get("meta") or {}).get("mal_score")
            mc = (c.get("meta") or {}).get("members_count")
            quality_prior = float(
                quality_prior_bonus(
                    mal_score=None if ms is None else float(ms),
                    members_count=None if mc is None else int(mc),
                )
            )
            score_after = float(
                content_first_final_score(
                    score_before=float(score_before),
                    neural_sim=float(synopsis_neural_sim),
                    hybrid_cf_score=float(hybrid_cf_score),
                    mal_score=None if ms is None else float(ms),
                    members_count=None if mc is None else int(mc),
                )
            )

        score = float(score_after)
        if score <= 0.0:
            continue

        scored.append(
            {
                "anime_id": aid,
                "score": float(score),
                "meta": c.get("meta") or {},
                "signals": {
                    "stage1_score": float(s1),
                    "stage1_pool": str(((c.get("_stage1") or {}).get("pool")) or ""),
                    "forced_neural": bool((c.get("_stage1") or {}).get("forced_neural", False)),
                    "weighted_overlap": float(weighted_overlap),
                    "seed_title_overlap": float((c.get("_stage1") or {}).get("title_overlap", 0.0)),
                    "seed_coverage": float(seed_coverage),
                    "hybrid_val": float(hybrid_val),
                    "hybrid_cf_score": float(hybrid_cf_score),
                    "popularity_boost": float(popularity_boost),
                    "metadata_affinity": float(meta_affinity),
                    "metadata_bonus": float(meta_bonus),
                    "score_without_metadata_bonus": float(score - meta_bonus),
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
                    "synopsis_neural_bonus": float(synopsis_neural_bonus),
                    "synopsis_neural_penalty": float(synopsis_neural_penalty),
                    "synopsis_neural_penalty_before_override": float(synopsis_neural_penalty_before_override),
                    "synopsis_neural_penalty_after_override": float(synopsis_neural_penalty_after_override),
                    "high_sim_override_stage2_relaxed": bool(high_sim_override_stage2_relaxed),
                    "synopsis_neural_adjustment": float(synopsis_neural_adjustment),
                    "synopsis_neural_high_sim_override": bool(high_sim_override_neural),
                    "demographics_overlap_bonus": float(demo_bonus),
                    "theme_overlap": None if theme_overlap is None else float(theme_overlap),
                    "theme_stage2_bonus": float(theme_bonus),
                    "score_without_synopsis_tfidf_bonus": float(score - synopsis_tfidf_adjustment),
                    "score_without_synopsis_embeddings_bonus": float(score - synopsis_embed_adjustment),
                    "score_without_synopsis_neural_bonus": float(score - synopsis_neural_adjustment),
                    "overlap_per_seed": overlap_per_seed,

                    # Phase 5 experiment: gated content-first scoring
                    "content_first_active": bool(content_first_active),
                    "content_first_alpha": float(CONTENT_FIRST_ALPHA),
                    "content_first_quality_prior": float(quality_prior),
                    "score_before": float(score_before),
                    "score_after": float(score_after),
                },
            }
        )

    # Debug-only guardrail: once Stage 0 is enforced, we should never be scoring
    # something that resembles the full catalog.
    final_scored_candidate_count = int(len(scored))
    if __debug__:
        if int(final_scored_candidate_count) > int(STAGE0_POOL_CAP) + int(STAGE0_ENFORCEMENT_BUFFER):
            raise AssertionError(
                f"Stage0 enforcement violated: scored={final_scored_candidate_count} > cap+buf={int(STAGE0_POOL_CAP)+int(STAGE0_ENFORCEMENT_BUFFER)}"
            )

    # ------------------------------------------------------------------
    # Phase 5 diagnostics: why Stage 0 candidates did not make it to scored
    # ------------------------------------------------------------------
    stage0_universe_ids = [int(x) for x in (candidate_ids or []) if int(x) > 0]
    shortlist_ids_set = {int(c.get("anime_id", 0)) for c in (shortlist or []) if int(c.get("anime_id", 0)) > 0}
    scored_ids_set = {int(r.get("anime_id", 0)) for r in (scored or []) if int(r.get("anime_id", 0)) > 0}

    why_not_scored_counts: dict[str, int] = {
        str(NOT_IN_STAGE1_SHORTLIST): 0,
        str(BLOCKED_LOW_SEMANTIC_SIM): 0,
        str(BLOCKED_LOW_OVERLAP): 0,
        str(BLOCKED_OTHER_ADMISSION): 0,
        str(MISSING_SEMANTIC_VECTOR): 0,
        str(DROPPED_BY_QUALITY_FILTERS): 0,
        str(SCORED): 0,
    }

    def _why_reason(aid: int) -> str:
        if int(aid) in scored_ids_set:
            return str(SCORED)

        # Should be 0 in practice (Stage 0 already applied ranked hygiene), but include.
        if int(aid) in set(exclude_ids):
            return str(DROPPED_BY_QUALITY_FILTERS)

        # Shortlisted but not scored means Stage 2 produced score<=0.
        # The required buckets do not include a dedicated Stage 2 drop reason;
        # attribute to the conservative catch-all bucket.
        if int(aid) in shortlist_ids_set:
            return str(BLOCKED_OTHER_ADMISSION)

        # Not shortlisted: distinguish admitted-but-not-selected vs never admitted.
        if bool(stage1_admitted_any_by_id.get(int(aid), False)):
            return str(NOT_IN_STAGE1_SHORTLIST)

        return str(stage1_block_reason_by_id.get(int(aid), BLOCKED_OTHER_ADMISSION))

    for aid in stage0_universe_ids:
        r = _why_reason(int(aid))
        why_not_scored_counts[str(r)] = int(why_not_scored_counts.get(str(r), 0) + 1)

    # Ensure totals sum to Stage 0 universe.
    try:
        tot = int(sum(int(v) for v in why_not_scored_counts.values()))
        if tot != int(len(stage0_universe_ids)):
            why_not_scored_counts[str(BLOCKED_OTHER_ADMISSION)] = int(
                why_not_scored_counts.get(str(BLOCKED_OTHER_ADMISSION), 0) + (int(len(stage0_universe_ids)) - tot)
            )
    except Exception:
        pass

    # Compute rank movement diagnostics by comparing:
    # - with_meta: score includes metadata_bonus
    # - without_meta: score excludes metadata_bonus
    scored_with_meta = sorted(scored, key=lambda x: (-float(x["score"]), int(x["anime_id"])))

    # Phase 5 experiment diagnostics: content-first activation + averages.
    def _avg(vals: list[float]) -> float:
        if not vals:
            return 0.0
        return float(sum(vals) / max(1, len(vals)))

    def _count_cf(items: list[dict[str, Any]]) -> int:
        return int(sum(1 for r in items if bool((r.get("signals") or {}).get("content_first_active", False))))

    top20_cf_count = _count_cf(scored_with_meta[:20])
    top50_cf_count = _count_cf(scored_with_meta[:50])
    all_cf_count = _count_cf(scored_with_meta)

    avg_neural_sim_top20 = _avg([float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)) for r in scored_with_meta[:20]])
    avg_hybrid_val_top20 = _avg([float((r.get("signals") or {}).get("hybrid_val", 0.0)) for r in scored_with_meta[:20]])

    # One Piece: print top-10 items by neural_sim with before/after rank movement.
    if str(query_id or "").strip().lower() == "one_piece":
        # Rank maps under two scoring policies.
        before_ranked = sorted(scored, key=lambda x: (-float((x.get("signals") or {}).get("score_before", 0.0)), int(x["anime_id"])))
        after_ranked = scored_with_meta
        before_ranks = {int(x["anime_id"]): i for i, x in enumerate(before_ranked, start=1)}
        after_ranks = {int(x["anime_id"]): i for i, x in enumerate(after_ranked, start=1)}

        by_neural = sorted(scored, key=lambda x: (-float((x.get("signals") or {}).get("synopsis_neural_sim", 0.0)), int(x["anime_id"])))
        top10 = by_neural[:10]
        content_first_one_piece_rows_by_neural = []
        for r in top10:
            aid = int(r.get("anime_id"))
            sig = r.get("signals") or {}
            content_first_one_piece_rows_by_neural.append(
                {
                    "anime_id": aid,
                    "title": str((r.get("meta") or {}).get("title_display", "")),
                    "neural_sim": float(sig.get("synopsis_neural_sim", 0.0)),
                    "hybrid_val": float(sig.get("hybrid_val", 0.0)),
                    "score_before": float(sig.get("score_before", 0.0)),
                    "score_after": float(sig.get("score_after", 0.0)),
                    "rank_before": int(before_ranks.get(aid, 0)),
                    "rank_after": int(after_ranks.get(aid, 0)),
                }
            )
    scored_without_meta = sorted(
        scored,
        key=lambda x: (-float(x.get("signals", {}).get("score_without_metadata_bonus", 0.0)), int(x["anime_id"])),
    )
    scored_without_tfidf = sorted(
        scored,
        key=lambda x: (-float(x.get("signals", {}).get("score_without_synopsis_tfidf_bonus", 0.0)), int(x["anime_id"])),
    )
    scored_without_embeddings = sorted(
        scored,
        key=lambda x: (
            -float(x.get("signals", {}).get("score_without_synopsis_embeddings_bonus", 0.0)),
            int(x["anime_id"]),
        ),
    )
    scored_without_neural = sorted(
        scored,
        key=lambda x: (
            -float(x.get("signals", {}).get("score_without_synopsis_neural_bonus", 0.0)),
            int(x["anime_id"]),
        ),
    )

    def _top_ids(items: list[dict[str, Any]], k: int) -> list[int]:
        return [int(x.get("anime_id")) for x in items[: max(0, int(k))]]

    def _rank_map(ids: list[int]) -> dict[int, int]:
        return {int(aid): int(r) for r, aid in enumerate(ids, start=1)}

    def _overlap_ratio(a: list[int], b: list[int]) -> float:
        if not a or not b:
            return 0.0
        k = min(len(a), len(b))
        if k <= 0:
            return 0.0
        return float(len(set(a[:k]).intersection(set(b[:k]))) / float(k))

    def _rank_diagnostics(with_ids: list[int], without_ids: list[int]) -> tuple[float, int]:
        with_rank = _rank_map(with_ids)
        without_rank = _rank_map(without_ids)
        common = [aid for aid in with_ids if aid in without_rank]
        if not common:
            return 0.0, 0
        deltas = [abs(int(with_rank[aid]) - int(without_rank[aid])) for aid in common]
        moved = sum(1 for d in deltas if int(d) != 0)
        return float(sum(deltas) / float(len(deltas))), int(moved)

    with20 = _top_ids(scored_with_meta, 20)
    without20 = _top_ids(scored_without_meta, 20)
    with50 = _top_ids(scored_with_meta, 50)
    without50 = _top_ids(scored_without_meta, 50)

    without_tfidf20 = _top_ids(scored_without_tfidf, 20)
    without_tfidf50 = _top_ids(scored_without_tfidf, 50)

    without_embed20 = _top_ids(scored_without_embeddings, 20)
    without_embed50 = _top_ids(scored_without_embeddings, 50)

    without_neural20 = _top_ids(scored_without_neural, 20)
    without_neural50 = _top_ids(scored_without_neural, 50)

    top20_mean_abs_delta, top20_moved = _rank_diagnostics(with20, without20)
    top50_mean_abs_delta, top50_moved = _rank_diagnostics(with50, without50)

    top20_mean_abs_delta_tfidf, top20_moved_tfidf = _rank_diagnostics(with20, without_tfidf20)
    top50_mean_abs_delta_tfidf, top50_moved_tfidf = _rank_diagnostics(with50, without_tfidf50)

    top20_mean_abs_delta_embed, top20_moved_embed = _rank_diagnostics(with20, without_embed20)
    top50_mean_abs_delta_embed, top50_moved_embed = _rank_diagnostics(with50, without_embed50)

    top20_mean_abs_delta_neural, top20_moved_neural = _rank_diagnostics(with20, without_neural20)
    top50_mean_abs_delta_neural, top50_moved_neural = _rank_diagnostics(with50, without_neural50)

    # Phase 5 follow-up: Discovery-mode franchise cap (post-score selection only).
    # Default must preserve current behavior: completion.
    mode = str(seed_ranking_mode or SEED_RANKING_MODE).strip().lower()
    if mode not in {"completion", "discovery"}:
        mode = "completion"

    # Always compute cap diagnostics (before/after), but only apply the cap in discovery mode.
    if mode == "discovery":
        recs_top_n, cap_diag = apply_franchise_cap(
            scored_with_meta,
            n=int(top_n),
            seed_ranking_mode=str(mode),
            seed_titles=list(seed_titles or []),
            threshold=float(FRANCHISE_TITLE_OVERLAP_THRESHOLD),
            cap_top20=int(FRANCHISE_CAP_TOP20),
            cap_top50=int(FRANCHISE_CAP_TOP50),
            title_overlap=lambda r: float((r.get("signals") or {}).get("seed_title_overlap", 0.0)),
            title=lambda r: str((r.get("meta") or {}).get("title_display", "")),
            anime_id=lambda r: int(r.get("anime_id", 0)),
            neural_sim=lambda r: float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)),
        )
    else:
        recs_top_n = scored_with_meta[:top_n]
        # Still emit diagnostics with before=after and dropped=0 for clarity.
        _, cap_diag = apply_franchise_cap(
            scored_with_meta,
            n=int(top_n),
            seed_ranking_mode=str(mode),
            seed_titles=list(seed_titles or []),
            threshold=float(FRANCHISE_TITLE_OVERLAP_THRESHOLD),
            cap_top20=int(FRANCHISE_CAP_TOP20),
            cap_top50=int(FRANCHISE_CAP_TOP50),
            title_overlap=lambda r: float((r.get("signals") or {}).get("seed_title_overlap", 0.0)),
            title=lambda r: str((r.get("meta") or {}).get("title_display", "")),
            anime_id=lambda r: int(r.get("anime_id", 0)),
            neural_sim=lambda r: float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)),
        )

    # Theme tie-break diagnostics (top20/top50).
    top20_items = scored_with_meta[:20]
    top50_items = scored_with_meta[:50]

    # Phase 5 refinement diagnostics: Stage 2 high-sim override (neural).
    hs20 = [
        r
        for r in top20_items
        if bool((r.get("signals") or {}).get("high_sim_override_stage2_relaxed", False))
    ]
    hs50 = [
        r
        for r in top50_items
        if bool((r.get("signals") or {}).get("high_sim_override_stage2_relaxed", False))
    ]
    hs_all = [
        r
        for r in scored_with_meta
        if bool((r.get("signals") or {}).get("high_sim_override_stage2_relaxed", False))
    ]
    hs50_sims = [float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)) for r in hs50]
    if hs50_sims:
        hs_sim_min = float(min(hs50_sims))
        hs_sim_mean = float(sum(hs50_sims) / len(hs50_sims))
        hs_sim_max = float(max(hs50_sims))
    else:
        hs_sim_min = 0.0
        hs_sim_mean = 0.0
        hs_sim_max = 0.0

    hs_all_sims = [float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)) for r in hs_all]
    if hs_all_sims:
        hs_all_sim_min = float(min(hs_all_sims))
        hs_all_sim_mean = float(sum(hs_all_sims) / len(hs_all_sims))
        hs_all_sim_max = float(max(hs_all_sims))
    else:
        hs_all_sim_min = 0.0
        hs_all_sim_mean = 0.0
        hs_all_sim_max = 0.0

    theme_bonuses_20 = [
        float((r.get("signals") or {}).get("theme_stage2_bonus", 0.0))
        for r in top20_items
        if r.get("signals") is not None
    ]
    theme_bonuses_50 = [
        float((r.get("signals") or {}).get("theme_stage2_bonus", 0.0))
        for r in top50_items
        if r.get("signals") is not None
    ]
    theme_fired_20 = [b for b in theme_bonuses_20 if float(b) > 0.0]
    theme_fired_50 = [b for b in theme_bonuses_50 if float(b) > 0.0]

    top20_theme_overlap_count = sum(
        1
        for r in top20_items
        if (r.get("signals") is not None) and ((r.get("signals") or {}).get("theme_overlap") is not None)
    )

    top5_by_theme_bonus_top50 = sorted(
        [
            {
                "rank_in_top50": idx,
                "anime_id": int(r.get("anime_id")),
                "title_display": str(((r.get("meta") or {}).get("title_display")) or ""),
                "theme_overlap": (r.get("signals") or {}).get("theme_overlap"),
                "theme_stage2_bonus": float((r.get("signals") or {}).get("theme_stage2_bonus", 0.0)),
            }
            for idx, r in enumerate(top50_items, start=1)
        ],
        key=lambda x: (-float(x.get("theme_stage2_bonus", 0.0)), int(x.get("anime_id", 0))),
    )[:5]

    bonuses = [
        float((r.get("signals") or {}).get("metadata_bonus", 0.0))
        for r in recs_top_n
        if r.get("signals") is not None
    ]
    affinities = [
        float((r.get("signals") or {}).get("metadata_affinity", 0.0))
        for r in recs_top_n
        if r.get("signals") is not None
    ]
    fired = [b for b in bonuses if float(b) > 0.0]

    tfidf_bonuses = [
        float((r.get("signals") or {}).get("synopsis_tfidf_bonus", 0.0))
        for r in recs_top_n
        if r.get("signals") is not None
    ]
    tfidf_fired = [b for b in tfidf_bonuses if float(b) > 0.0]

    embed_bonuses = [
        float((r.get("signals") or {}).get("synopsis_embed_bonus", 0.0))
        for r in recs_top_n
        if r.get("signals") is not None
    ]
    embed_fired = [b for b in embed_bonuses if float(b) > 0.0]

    neural_bonuses = [
        float((r.get("signals") or {}).get("synopsis_neural_bonus", 0.0))
        for r in recs_top_n
        if r.get("signals") is not None
    ]
    neural_fired = [b for b in neural_bonuses if float(b) > 0.0]

    # Seed-conditioning diagnostics for Option A shortlist
    top20 = recs_top_n[:20]
    top20_pool_a = sum(1 for r in top20 if str((r.get("signals") or {}).get("stage1_pool", "")) == "A")
    top20_pool_b = sum(1 for r in top20 if str((r.get("signals") or {}).get("stage1_pool", "")) == "B")
    top20_pool_c = sum(1 for r in top20 if str((r.get("signals") or {}).get("stage1_pool", "")) == "C")
    top20_tfidf_nonzero = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_tfidf_sim", 0.0)) > 0.0)
    top20_tfidf_ge_min = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_tfidf_sim", 0.0)) >= 0.02)

    top20_embed_nonzero = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_embed_sim", 0.0)) > 0.0)
    top20_embed_ge_min = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_embed_sim", 0.0)) >= float(SYNOPSIS_EMBEDDINGS_MIN_SIM))

    top20_neural_nonzero = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)) > 0.0)
    top20_neural_ge_min = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)) >= float(SYNOPSIS_NEURAL_MIN_SIM))

    # Off-type here means: fails the conservative base gate (same type OR episodes>=min).
    top20_off_type = sum(1 for r in top20 if not bool((r.get("signals") or {}).get("synopsis_tfidf_base_gate_passed", True)))

    forced_in_shortlist_pairs: list[tuple[int, float]] = [
        (int(it.get("anime_id", 0)), float((it.get("_stage1") or {}).get("synopsis_neural_sim", 0.0)))
        for it in shortlist
        if bool((it.get("_stage1") or {}).get("forced_neural", False))
    ]
    forced_stats = forced_pool_stats(forced_in_shortlist_pairs)
    forced_in_top20 = sum(1 for r in top20 if bool((r.get("signals") or {}).get("forced_neural", False)))
    forced_in_top50 = sum(1 for r in top50_items if bool((r.get("signals") or {}).get("forced_neural", False)))

    forced_top10_rows: list[dict[str, Any]] = []
    if semantic_mode == "neural" and forced_neural_pairs:
        top20_ids = {int(r.get("anime_id", 0)) for r in top20}
        top50_ids = [int(r.get("anime_id", 0)) for r in top50_items]
        top50_rank = {int(aid): int(rank) for rank, aid in enumerate(top50_ids, start=1)}
        final_rank = {int(r.get("anime_id", 0)): int(rank) for rank, r in enumerate(scored_with_meta, start=1)}
        scored_by_id = {int(r.get("anime_id", 0)): r for r in scored_with_meta}
        shortlist_ids = {int(it.get("anime_id", 0)) for it in shortlist}

        top20_cutoff_score = float(scored_with_meta[19]["score"]) if len(scored_with_meta) >= 20 else None
        for aid, sim in forced_neural_pairs[:10]:
            m = work.loc[work["anime_id"].astype(int) == int(aid)].head(1)
            if m.empty:
                title = ""
                typ = None
            else:
                mr = m.iloc[0]
                title = str(mr.get("title_display") or mr.get("title_primary") or "")
                typ = None if pd.isna(mr.get("type")) else str(mr.get("type")).strip()

            scored_row = scored_by_id.get(int(aid))
            signals = (scored_row or {}).get("signals") or {}
            score_val = float((scored_row or {}).get("score", 0.0)) if scored_row is not None else None
            if score_val is not None and top20_cutoff_score is not None:
                delta_to_top20 = float(top20_cutoff_score) - float(score_val)
            else:
                delta_to_top20 = None

            forced_top10_rows.append(
                {
                    "anime_id": int(aid),
                    "title_display": title,
                    "type": typ,
                    "sim": float(sim),
                    "in_shortlist": bool(int(aid) in shortlist_ids),
                    "in_top20": bool(int(aid) in top20_ids),
                    "rank_in_top50": int(top50_rank[int(aid)]) if int(aid) in top50_rank else None,
                    "final_rank": int(final_rank[int(aid)]) if int(aid) in final_rank else None,
                    "score": float(score_val) if score_val is not None else None,
                    "delta_to_top20_cutoff": float(delta_to_top20) if delta_to_top20 is not None else None,
                    "hybrid_val": float(signals.get("hybrid_val", 0.0)) if scored_row is not None else None,
                    "weighted_overlap": float(signals.get("weighted_overlap", 0.0)) if scored_row is not None else None,
                    "seed_coverage": float(signals.get("seed_coverage", 0.0)) if scored_row is not None else None,
                    "metadata_bonus": float(signals.get("metadata_bonus", 0.0)) if scored_row is not None else None,
                    "synopsis_neural_bonus": float(signals.get("synopsis_neural_bonus", 0.0)) if scored_row is not None else None,
                    "was_off_type": bool(
                        not bool((scored_by_id.get(int(aid), {}).get("signals") or {}).get("synopsis_tfidf_base_gate_passed", True))
                    )
                    if int(aid) in scored_by_id
                    else None,
                    "penalty_before": float(
                        (scored_by_id.get(int(aid), {}).get("signals") or {}).get(
                            "synopsis_neural_penalty_before_override", 0.0
                        )
                    )
                    if int(aid) in scored_by_id
                    else None,
                    "penalty_after": float(
                        (scored_by_id.get(int(aid), {}).get("signals") or {}).get(
                            "synopsis_neural_penalty_after_override", 0.0
                        )
                    )
                    if int(aid) in scored_by_id
                    else None,
                    "stage2_override_relaxed": bool(
                        (scored_by_id.get(int(aid), {}).get("signals") or {}).get("high_sim_override_stage2_relaxed", False)
                    )
                    if int(aid) in scored_by_id
                    else None,
                }
            )

    if str(query_id or "").strip().lower() == "one_piece" and forced_top10_rows:
        print("\n[Phase 5] one_piece forced-neural top10 (by similarity):")
        for r in forced_top10_rows:
            print(
                f"  - {r.get('anime_id')} | sim={float(r.get('sim', 0.0)):.4f} | in_shortlist={bool(r.get('in_shortlist'))} | rank@50={r.get('rank_in_top50')} | in_top20={bool(r.get('in_top20'))} | {r.get('type')} | {r.get('title_display')}"
            )

    shortlist_from_tfidf = sum(1 for it in shortlist if float((it.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0)) >= 0.02)
    shortlist_from_embed = sum(1 for it in shortlist if float((it.get("_stage1") or {}).get("synopsis_embed_sim", 0.0)) >= float(SYNOPSIS_EMBEDDINGS_MIN_SIM))
    shortlist_from_neural = sum(1 for it in shortlist if float((it.get("_stage1") or {}).get("synopsis_neural_sim", 0.0)) >= float(SYNOPSIS_NEURAL_MIN_SIM))

    stage1_off_type_allowed_count = int(len(stage1_off_type_allowed_sims))
    if stage1_off_type_allowed_sims:
        s_min = float(min(stage1_off_type_allowed_sims))
        s_mean = float(sum(stage1_off_type_allowed_sims) / len(stage1_off_type_allowed_sims))
        s_max = float(max(stage1_off_type_allowed_sims))
    else:
        s_min = 0.0
        s_mean = 0.0
        s_max = 0.0

    stage1_off_type_allowed_embed_count = int(len(stage1_off_type_allowed_embed_sims))
    if stage1_off_type_allowed_embed_sims:
        e_min = float(min(stage1_off_type_allowed_embed_sims))
        e_mean = float(sum(stage1_off_type_allowed_embed_sims) / len(stage1_off_type_allowed_embed_sims))
        e_max = float(max(stage1_off_type_allowed_embed_sims))
    else:
        e_min = 0.0
        e_mean = 0.0
        e_max = 0.0

    stage1_off_type_allowed_neural_count = int(len(stage1_off_type_allowed_neural_sims))
    if stage1_off_type_allowed_neural_sims:
        n_min = float(min(stage1_off_type_allowed_neural_sims))
        n_mean = float(sum(stage1_off_type_allowed_neural_sims) / len(stage1_off_type_allowed_neural_sims))
        n_max = float(max(stage1_off_type_allowed_neural_sims))
    else:
        n_min = 0.0
        n_mean = 0.0
        n_max = 0.0

    top20_embed_sims = [float((r.get("signals") or {}).get("synopsis_embed_sim", 0.0)) for r in top20]
    top20_embed_sims_nz = [s for s in top20_embed_sims if float(s) > 0.0]
    if top20_embed_sims_nz:
        top20_embed_sim_min = float(min(top20_embed_sims_nz))
        top20_embed_sim_mean = float(sum(top20_embed_sims_nz) / len(top20_embed_sims_nz))
        top20_embed_sim_max = float(max(top20_embed_sims_nz))
    else:
        top20_embed_sim_min = 0.0
        top20_embed_sim_mean = 0.0
        top20_embed_sim_max = 0.0

    demo_override_admitted_count = int(len(demo_override_admitted_ids))
    demo_override_used_in_top20_count = int(
        sum(1 for r in top20 if int(r.get("anime_id", 0)) in demo_override_admitted_ids)
    )

    diagnostics = {
        "semantic_mode": semantic_mode,
        "force_neural_enabled": bool(semantic_mode == "neural" and force_neural_enabled(semantic_mode=semantic_mode)),
        "force_neural_topk": int(FORCE_NEURAL_TOPK),
        "force_neural_min_sim": float(FORCE_NEURAL_MIN_SIM),
        "forced_neural_count": int(forced_stats.forced_count),
        "forced_neural_sim_min": float(forced_stats.sim_min),
        "forced_neural_sim_mean": float(forced_stats.sim_mean),
        "forced_neural_sim_max": float(forced_stats.sim_max),
        "forced_neural_in_top20_count": int(forced_in_top20),
        "forced_neural_in_top50_count": int(forced_in_top50),
        "forced_neural_top10": list(forced_top10_rows)
        if str(query_id or "").strip().lower() == "one_piece"
        else [],

        # Phase 5 experiment: content-first gated scoring (seed-based Stage 2)
        "content_first_alpha": float(CONTENT_FIRST_ALPHA),
        "content_first_active_count_top20": int(top20_cf_count),
        "content_first_active_count_top50": int(top50_cf_count),
        "content_first_active_count_all": int(all_cf_count),
        "avg_neural_sim_top20": float(avg_neural_sim_top20),
        "avg_hybrid_val_top20": float(avg_hybrid_val_top20),
        "one_piece_top10_by_neural": list(content_first_one_piece_rows_by_neural)
        if str(query_id or "").strip().lower() == "one_piece"
        else [],

        # Phase 5 refinement: Stage 2 high-sim override (neural)
        "high_sim_override_fired_count_top20": int(len(hs20)),
        "high_sim_override_fired_count_top50": int(len(hs50)),
        "high_sim_override_fired_count_all": int(len(hs_all)),
        "high_sim_override_sim_min": float(hs_sim_min),
        "high_sim_override_sim_mean": float(hs_sim_mean),
        "high_sim_override_sim_max": float(hs_sim_max),
        "high_sim_override_sim_min_all": float(hs_all_sim_min),
        "high_sim_override_sim_mean_all": float(hs_all_sim_mean),
        "high_sim_override_sim_max_all": float(hs_all_sim_max),
        "stage1_k_sem": int(stage1_k_sem),
        "stage1_k_meta": int(stage1_k_meta),
        "semantic_confidence_source": str(semantic_conf_source),
        "semantic_confidence_score": float(semantic_conf_score),
        "semantic_confidence_tier": str(semantic_conf_tier),
        "embeddings_top50_count": int(embed_stats.get("count", 0)),
        "embeddings_top50_mean": float(embed_stats.get("mean", 0.0)),
        "embeddings_top50_p95": float(embed_stats.get("p95", 0.0)),
        "embeddings_top50_weighted_overlap_mean": float(embed_coherence.get("weighted_overlap_mean", 0.0)),
        "embeddings_top50_any_genre_match_frac": float(embed_coherence.get("any_genre_match_frac", 0.0)),
        "tfidf_top50_count": int(tfidf_stats.get("count", 0)),
        "tfidf_top50_mean": float(tfidf_stats.get("mean", 0.0)),
        "tfidf_top50_p95": float(tfidf_stats.get("p95", 0.0)),
        "tfidf_top50_weighted_overlap_mean": float(tfidf_coherence.get("weighted_overlap_mean", 0.0)),
        "tfidf_top50_any_genre_match_frac": float(tfidf_coherence.get("any_genre_match_frac", 0.0)),
        "neural_top50_count": int(neural_stats.get("count", 0)),
        "neural_top50_mean": float(neural_stats.get("mean", 0.0)),
        "neural_top50_p95": float(neural_stats.get("p95", 0.0)),
        "neural_top50_weighted_overlap_mean": float(neural_coherence.get("weighted_overlap_mean", 0.0)),
        "neural_top50_any_genre_match_frac": float(neural_coherence.get("any_genre_match_frac", 0.0)),
        "seed_has_shounen_demo": bool(seed_has_shounen_demo),
        "seed_demo_tokens": sorted(list(seed_demo_tokens)),
        "demo_override_admitted_count": int(demo_override_admitted_count),
        "demo_override_used_in_top20_count": int(demo_override_used_in_top20_count),
        "top20_poolA_count": int(top20_pool_a),
        "top20_poolB_count": int(top20_pool_b),
        "top20_poolC_count": int(top20_pool_c),
        "stage1_shortlist_target": int(shortlist_k) if shortlist_k > 0 else int(stage1_total_candidates),
        "stage1_shortlist_size": int(len(shortlist)),
        "stage1_shortlist_from_neural_count": int(shortlist_from_neural),
        "stage1_shortlist_from_embeddings_count": int(shortlist_from_embed),
        "stage1_shortlist_from_tfidf_count": int(shortlist_from_tfidf),
        "stage1_off_type_allowed_count": int(stage1_off_type_allowed_count),
        "stage1_off_type_allowed_sim_min": float(s_min),
        "stage1_off_type_allowed_sim_mean": float(s_mean),
        "stage1_off_type_allowed_sim_max": float(s_max),
        "stage1_off_type_allowed_embeddings_count": int(stage1_off_type_allowed_embed_count),
        "stage1_off_type_allowed_embeddings_sim_min": float(e_min),
        "stage1_off_type_allowed_embeddings_sim_mean": float(e_mean),
        "stage1_off_type_allowed_embeddings_sim_max": float(e_max),
        "stage1_off_type_allowed_neural_count": int(stage1_off_type_allowed_neural_count),
        "stage1_off_type_allowed_neural_sim_min": float(n_min),
        "stage1_off_type_allowed_neural_sim_mean": float(n_mean),
        "stage1_off_type_allowed_neural_sim_max": float(n_max),
        "top20_embedding_nonzero_count": int(top20_embed_nonzero),
        "top20_embedding_ge_min_sim_count": int(top20_embed_ge_min),
        "top20_embedding_sim_min": float(top20_embed_sim_min),
        "top20_embedding_sim_mean": float(top20_embed_sim_mean),
        "top20_embedding_sim_max": float(top20_embed_sim_max),
        "top20_neural_nonzero_count": int(top20_neural_nonzero),
        "top20_neural_ge_min_sim_count": int(top20_neural_ge_min),
        "top20_tfidf_nonzero_count": int(top20_tfidf_nonzero),
        "top20_tfidf_ge_min_sim_count": int(top20_tfidf_ge_min),
        "top20_off_type_count": int(top20_off_type),
        "metadata_bonus_fired_count": int(len(fired)),
        "metadata_bonus_mean": float(sum(bonuses) / max(1, len(bonuses))),
        "metadata_bonus_max": float(max(bonuses) if bonuses else 0.0),
        "affinity_mean": float(sum(affinities) / max(1, len(affinities))),
        "affinity_max": float(max(affinities) if affinities else 0.0),
        "synopsis_tfidf_bonus_fired_count": int(len(tfidf_fired)),
        "synopsis_tfidf_bonus_mean": float(sum(tfidf_bonuses) / max(1, len(tfidf_bonuses))),
        "synopsis_tfidf_bonus_max": float(max(tfidf_bonuses) if tfidf_bonuses else 0.0),
        "embedding_bonus_fired_count": int(len(embed_fired)),
        "embedding_bonus_mean": float(sum(embed_bonuses) / max(1, len(embed_bonuses))),
        "embedding_bonus_max": float(max(embed_bonuses) if embed_bonuses else 0.0),
        "neural_bonus_fired_count": int(len(neural_fired)),
        "neural_bonus_mean": float(sum(neural_bonuses) / max(1, len(neural_bonuses))),
        "neural_bonus_max": float(max(neural_bonuses) if neural_bonuses else 0.0),

        "theme_bonus_fired_count_top20": int(len(theme_fired_20)),
        "theme_bonus_mean_top20": float(sum(theme_bonuses_20) / max(1, len(theme_bonuses_20))),
        "theme_bonus_max_top20": float(max(theme_bonuses_20) if theme_bonuses_20 else 0.0),
        "theme_bonus_fired_count_top50": int(len(theme_fired_50)),
        "theme_bonus_mean_top50": float(sum(theme_bonuses_50) / max(1, len(theme_bonuses_50))),
        "theme_bonus_max_top50": float(max(theme_bonuses_50) if theme_bonuses_50 else 0.0),
        "top20_theme_overlap_count": int(top20_theme_overlap_count),
        "top5_items_by_theme_bonus_top50": list(top5_by_theme_bonus_top50),
        "top20_overlap_with_without_meta": _overlap_ratio(with20, without20),
        "top50_overlap_with_without_meta": _overlap_ratio(with50, without50),
        "top20_mean_abs_rank_delta": float(top20_mean_abs_delta),
        "top50_mean_abs_rank_delta": float(top50_mean_abs_delta),
        "top20_moved_count": int(top20_moved),
        "top50_moved_count": int(top50_moved),
        "top20_overlap_with_without_tfidf": _overlap_ratio(with20, without_tfidf20),
        "top50_overlap_with_without_tfidf": _overlap_ratio(with50, without_tfidf50),
        "top20_mean_abs_rank_delta_tfidf": float(top20_mean_abs_delta_tfidf),
        "top50_mean_abs_rank_delta_tfidf": float(top50_mean_abs_delta_tfidf),
        "top20_moved_count_tfidf": int(top20_moved_tfidf),
        "top50_moved_count_tfidf": int(top50_moved_tfidf),
        "top20_overlap_with_without_embeddings": _overlap_ratio(with20, without_embed20),
        "top50_overlap_with_without_embeddings": _overlap_ratio(with50, without_embed50),
        "top20_mean_abs_rank_delta_embeddings": float(top20_mean_abs_delta_embed),
        "top50_mean_abs_rank_delta_embeddings": float(top50_mean_abs_delta_embed),
        "top20_moved_count_embeddings": int(top20_moved_embed),
        "top50_moved_count_embeddings": int(top50_moved_embed),
        "top20_overlap_with_without_neural": _overlap_ratio(with20, without_neural20),
        "top50_overlap_with_without_neural": _overlap_ratio(with50, without_neural50),
        "top20_mean_abs_rank_delta_neural": float(top20_mean_abs_delta_neural),
        "top50_mean_abs_rank_delta_neural": float(top50_mean_abs_delta_neural),
        "top20_moved_count_neural": int(top20_moved_neural),
        "top50_moved_count_neural": int(top50_moved_neural),

        # Phase 5 upgrade: Stage 0 semantic-first candidate pool diagnostics.
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

        # Phase 5 final fix: Stage 0 downstream enforcement diagnostics.
        "stage1_candidate_universe_count": int(len(candidate_df)),
        "stage0_stage1_universe_diff": int(len(candidate_df)) - int(stage0_diag.stage0_after_cap),
        "stage0_stage1_universe_match": bool(int(len(candidate_df)) == int(stage0_diag.stage0_after_cap)),
        "shortlist_size": int(len(shortlist)),
        "final_scored_candidate_count": int(len(scored)),

        # Phase 5 diagnostics: why Stage 0 candidates are not scored.
        "why_not_scored_counts": dict(why_not_scored_counts),

        # Phase 5 follow-up: seed ranking goal mode + franchise-cap diagnostics.
        "seed_ranking_mode": str(cap_diag.seed_ranking_mode),
        "franchise_cap_threshold": float(cap_diag.franchise_cap_threshold),
        "franchise_cap_top20": int(cap_diag.franchise_cap_top20),
        "franchise_cap_top50": int(cap_diag.franchise_cap_top50),
        "top20_franchise_like_count_before": int(cap_diag.top20_franchise_like_count_before),
        "top20_franchise_like_count_after": int(cap_diag.top20_franchise_like_count_after),
        "top50_franchise_like_count_before": int(cap_diag.top50_franchise_like_count_before),
        "top50_franchise_like_count_after": int(cap_diag.top50_franchise_like_count_after),
        "franchise_items_dropped_count": int(cap_diag.franchise_items_dropped_count),
        "franchise_items_dropped_count_top20": int(cap_diag.franchise_items_dropped_count_top20),
        "franchise_items_dropped_count_top50": int(cap_diag.franchise_items_dropped_count_top50),
        "franchise_items_dropped_examples_top5": list(cap_diag.franchise_items_dropped_examples_top5),
        "franchise_seed_norm": str(cap_diag.franchise_seed_norm or ""),
        "franchise_like_examples_top10": list(cap_diag.franchise_like_examples_top10),
        "franchise_overlap_audit_top10": list(cap_diag.franchise_overlap_audit_top10),
    }

    # Convenience: strict-metadata membership count (deduped over IDs).
    try:
        meta_strict = 0
        for aid in candidate_ids:
            flags = (stage0_flags_by_id or {}).get(int(aid), {})
            if bool(flags.get("from_meta_strict")):
                meta_strict += 1
        diagnostics["stage0_from_meta_strict_count"] = int(meta_strict)
    except Exception:
        tier_counts = diagnostics.get("stage0_after_cap_counts_by_tier") or {}
        diagnostics["stage0_from_meta_strict_count"] = int(tier_counts.get("stage0_from_meta_strict", 0))

    # Enforcement: final ranked results must all come from Stage 0.
    # For top-50 enforcement, use a true top-50 list even when top_n < 50.
    try:
        top20_ids = [int(r.get("anime_id", 0)) for r in recs_top_n[:20]]

        if str(mode) == "discovery":
            recs_top50_for_enforcement, _ = apply_franchise_cap(
                scored_with_meta,
                n=50,
                seed_ranking_mode=str(mode),
                seed_titles=list(seed_titles or []),
                threshold=float(FRANCHISE_TITLE_OVERLAP_THRESHOLD),
                cap_top20=int(FRANCHISE_CAP_TOP20),
                cap_top50=int(FRANCHISE_CAP_TOP50),
                title_overlap=lambda r: float((r.get("signals") or {}).get("seed_title_overlap", 0.0)),
                title=lambda r: str((r.get("meta") or {}).get("title_display", "")),
                anime_id=lambda r: int(r.get("anime_id", 0)),
                neural_sim=lambda r: float((r.get("signals") or {}).get("synopsis_neural_sim", 0.0)),
            )
            top50_ids = [int(r.get("anime_id", 0)) for r in recs_top50_for_enforcement[:50]]
        else:
            top50_ids = [int(r.get("anime_id", 0)) for r in scored_with_meta[:50]]

        diagnostics["top20_in_stage0_count"] = int(sum(1 for aid in top20_ids if aid in candidate_id_set))
        diagnostics["top50_in_stage0_count"] = int(sum(1 for aid in top50_ids if aid in candidate_id_set))
        diagnostics["top50_available_count"] = int(len(top50_ids))
    except Exception:
        diagnostics["top20_in_stage0_count"] = 0
        diagnostics["top50_in_stage0_count"] = 0
        diagnostics["top50_available_count"] = 0

    # Provenance: % of final top-20 sourced from (A) neural neighbors and (B) strict metadata overlap.
    try:
        final_top20 = recs_top_n[:20]
        denom = max(1, len(final_top20))
        n_neural = 0
        n_meta = 0
        for r in final_top20:
            aid = int(r.get("anime_id", 0))
            flags = stage0_flags_by_id.get(int(aid), {}) if stage0_flags_by_id is not None else {}
            if bool(flags.get("from_neural")):
                n_neural += 1
            if bool(flags.get("from_meta_strict")):
                n_meta += 1
        diagnostics["top20_from_neural_frac"] = float(n_neural) / float(denom)
        diagnostics["top20_from_meta_strict_frac"] = float(n_meta) / float(denom)
    except Exception:
        diagnostics["top20_from_neural_frac"] = 0.0
        diagnostics["top20_from_meta_strict_frac"] = 0.0

    # Stage 1 semantic admission diagnostics (blocked-by-overlap rates + examples).
    try:
        diagnostics.update(stage1_gate_blocking_diagnostics)
    except Exception:
        pass

    return recs_top_n, diagnostics


def _evaluate_golden_queries(
    *,
    golden_path: Path,
    weight_mode: str,
    seed_ranking_mode: str | None = None,
) -> dict[str, Any]:
    cfg = json.loads(golden_path.read_text(encoding="utf-8"))
    defaults = cfg.get("defaults", {})

    bundle = build_artifacts()
    metadata, components, recommender, pop_pct_by_id = _build_app_like_recommender(bundle)

    synopsis_tfidf_artifact = bundle.get("models", {}).get("synopsis_tfidf")
    synopsis_embeddings_artifact = bundle.get("models", {}).get("synopsis_embeddings")
    synopsis_neural_embeddings_artifact = bundle.get("models", {}).get("synopsis_neural_embeddings")

    # Phase 4 / Chunk A2: apply app-like ranked candidate hygiene in golden harness.
    ranked_hygiene_exclude_ids = build_ranked_candidate_hygiene_exclude_ids(metadata)

    weights = choose_weights(weight_mode)

    default_expect = GoldenExpectations(
        disallow_types=tuple(str(t) for t in defaults.get("disallow_types", [])),
        disallow_title_regex=str(defaults.get("disallow_title_regex", "")),
    )
    default_top_n = int(defaults.get("top_n", 20))

    out_queries: list[dict[str, Any]] = []

    for q in cfg.get("queries", []):
        qid = str(q.get("id"))
        seed_titles = [str(x) for x in (q.get("seed_titles") or [])]
        notes = q.get("notes")

        allow_fuzzy_seeds = bool(q.get("allow_fuzzy_seeds", defaults.get("allow_fuzzy_seeds", False)))

        top_n = int(q.get("top_n", default_top_n))
        disallow_types = tuple(str(t) for t in q.get("disallow_types", default_expect.disallow_types))
        disallow_title_regex = str(q.get("disallow_title_regex", default_expect.disallow_title_regex))
        title_re = re.compile(disallow_title_regex) if disallow_title_regex else None

        seed_ids, matched_titles, resolution_debug = _resolve_seed_titles(metadata, seed_titles, allow_fuzzy=allow_fuzzy_seeds)

        # Fail loudly if any seed wasn't deterministically resolved.
        unresolved = [d for d in resolution_debug if d.get("resolved_anime_id") is None]
        if unresolved:
            unresolved_str = "; ".join([f"{d.get('query')}({d.get('method')})" for d in unresolved])
            raise RuntimeError(
                "Seed resolution failed (strict mode). "
                "Update the golden query to use an exact title_display, or set allow_fuzzy_seeds=true for that query. "
                f"Unresolved: {unresolved_str}"
            )

        recs, recs_diag = _seed_based_scores(
            query_id=qid,
            metadata=metadata,
            components=components,
            recommender=recommender,
            seed_ids=seed_ids,
            seed_titles=matched_titles,
            weights=weights,
            pop_pct_by_id=pop_pct_by_id,
            top_n=top_n,
            exclude_ids=ranked_hygiene_exclude_ids,
            synopsis_tfidf_artifact=synopsis_tfidf_artifact,
            synopsis_embeddings_artifact=synopsis_embeddings_artifact,
            synopsis_neural_embeddings_artifact=synopsis_neural_embeddings_artifact,
            seed_ranking_mode=str(seed_ranking_mode or SEED_RANKING_MODE),
        )

        violations: list[dict[str, Any]] = []
        for rank, rec in enumerate(recs, start=1):
            meta = rec.get("meta") or {}
            title = str(meta.get("title_display", ""))
            typ = meta.get("type")

            bad_type = bool(typ and typ in disallow_types)
            bad_title = bool(title_re and title_re.search(title))

            if bad_type or bad_title:
                violations.append(
                    {
                        "rank": int(rank),
                        "anime_id": int(rec.get("anime_id")),
                        "title_display": title,
                        "type": typ,
                        "bad_type": bad_type,
                        "bad_title": bad_title,
                    }
                )

        out_queries.append(
            {
                "id": qid,
                "seed_titles": seed_titles,
                "resolved_seed_ids": seed_ids,
                "resolved_seed_titles": matched_titles,
                "notes": notes,
                "weight_mode": weight_mode,
                "top_n": top_n,
                "diagnostics": recs_diag,
                "expectations": {
                    "disallow_types": list(disallow_types),
                    "disallow_title_regex": disallow_title_regex,
                },
                "seed_resolution": resolution_debug,
                "recommendations": recs,
                "violation_count": int(len(violations)),
                "violations": violations,
            }
        )

    return {
        "schema": "phase4_golden_queries",
        "golden_file": str(golden_path.as_posix()),
        "weight_mode": weight_mode,
        "queries": out_queries,
    }


def _render_markdown_report(*, golden_results: dict[str, Any], out_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Phase 4 — Golden Queries Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Weight mode: {golden_results.get('weight_mode')}")
    lines.append(f"Golden file: {golden_results.get('golden_file')}")
    lines.append("")

    for q in golden_results.get("queries", []):
        lines.append("---")
        lines.append("")
        lines.append(f"## {q.get('id')}")
        lines.append("")
        lines.append(f"Seeds (requested): {', '.join(q.get('seed_titles') or [])}")
        lines.append(f"Seeds (resolved): {', '.join(q.get('resolved_seed_titles') or [])}")
        lines.append(f"Seed IDs: {q.get('resolved_seed_ids')}")

        # Seed resolution diagnostics table (title -> id alignment)
        seed_res = q.get("seed_resolution") or []
        if seed_res:
            lines.append("")
            lines.append("Seed resolution details:")
            lines.append("")
            lines.append("| Query | Method | Resolved anime_id | Matched title | Score |")
            lines.append("|---|---|---:|---|---:|")
            for r in seed_res:
                query = str(r.get("query", ""))
                method = str(r.get("method", ""))
                rid = r.get("resolved_anime_id")
                rid_s = "" if rid is None else str(int(rid))
                mt = "" if r.get("matched_title") is None else str(r.get("matched_title"))
                score = r.get("score")
                score_s = "" if score is None else f"{float(score):.1f}"
                query = query.replace("|", "\\|")
                mt = mt.replace("|", "\\|")
                lines.append(f"| {query} | {method} | {rid_s} | {mt} | {score_s} |")
        if q.get("notes"):
            lines.append(f"Notes: {q.get('notes')}")
        lines.append(f"Top-N: {q.get('top_n')}")
        lines.append(f"Violations: {q.get('violation_count')}")

        diag = q.get("diagnostics") or {}
        if diag:
            sem_src = str(diag.get("semantic_confidence_source") or "none")
            if sem_src == "neural":
                sem_mean = float(diag.get("neural_top50_mean", 0.0))
                sem_p95 = float(diag.get("neural_top50_p95", 0.0))
                sem_ov = float(diag.get("neural_top50_weighted_overlap_mean", 0.0))
                sem_any = float(diag.get("neural_top50_any_genre_match_frac", 0.0))
            elif sem_src == "tfidf":
                sem_mean = float(diag.get("tfidf_top50_mean", 0.0))
                sem_p95 = float(diag.get("tfidf_top50_p95", 0.0))
                sem_ov = float(diag.get("tfidf_top50_weighted_overlap_mean", 0.0))
                sem_any = float(diag.get("tfidf_top50_any_genre_match_frac", 0.0))
            else:
                sem_mean = float(diag.get("embeddings_top50_mean", 0.0))
                sem_p95 = float(diag.get("embeddings_top50_p95", 0.0))
                sem_ov = float(diag.get("embeddings_top50_weighted_overlap_mean", 0.0))
                sem_any = float(diag.get("embeddings_top50_any_genre_match_frac", 0.0))

            seed_demo_tokens = diag.get("seed_demo_tokens") or []
            if isinstance(seed_demo_tokens, list):
                seed_demo_str = ",".join(str(x) for x in seed_demo_tokens)
            else:
                seed_demo_str = str(seed_demo_tokens)

            stage0_raw_by_tier = diag.get("stage0_raw_counts_by_tier") or {}
            lines.append(
                "Diagnostics: "
                f"K_sem={diag.get('stage1_k_sem')}, K_meta={diag.get('stage1_k_meta')}, "
                f"stage0_pool_raw={diag.get('stage0_pool_raw')}, "
                f"stage0_after_hygiene={diag.get('stage0_after_hygiene')}, "
                f"stage0_after_cap={diag.get('stage0_after_cap')}, "
                f"stage0_src_raw(neural/meta_strict/pop)="
                f"{stage0_raw_by_tier.get('stage0_from_neural')}/"
                f"{stage0_raw_by_tier.get('stage0_from_meta_strict')}/"
                f"{stage0_raw_by_tier.get('stage0_from_popularity')}, "
                f"stage1_universe={diag.get('stage1_candidate_universe_count')}, "
                f"universe_match={bool(diag.get('stage0_stage1_universe_match', False))}, "
                f"shortlist={diag.get('shortlist_size', diag.get('stage1_shortlist_size'))}/{diag.get('stage1_shortlist_target')}, "
                f"scored={diag.get('final_scored_candidate_count')}, "
                f"top20_in_stage0={diag.get('top20_in_stage0_count')}, "
                f"top50_in_stage0={diag.get('top50_in_stage0_count')}, "
                f"top20_from_neural={100.0 * float(diag.get('top20_from_neural_frac', 0.0)):.1f}%, "
                f"top20_from_meta_strict={100.0 * float(diag.get('top20_from_meta_strict_frac', 0.0)):.1f}%, "
                f"force_neural={bool(diag.get('force_neural_enabled', False))}, "
                f"force_topk={diag.get('force_neural_topk')}, force_min_sim={float(diag.get('force_neural_min_sim', 0.0)):.3f}, "
                f"sem_conf=({diag.get('semantic_confidence_source')}/{diag.get('semantic_confidence_tier')}) {float(diag.get('semantic_confidence_score', 0.0)):.3f}, "
                f"content_first_alpha={float(diag.get('content_first_alpha', 0.0)):.2f}, "
                f"content_first_active(top20/top50/all)={diag.get('content_first_active_count_top20')}/{diag.get('content_first_active_count_top50')}/{diag.get('content_first_active_count_all')}, "
                f"avg_neural_sim_top20={float(diag.get('avg_neural_sim_top20', 0.0)):.4f}, "
                f"avg_hybrid_val_top20={float(diag.get('avg_hybrid_val_top20', 0.0)):.4f}, "
                f"sem_top50_mean={float(sem_mean):.3f}, sem_top50_p95={float(sem_p95):.3f}, "
                f"sem_top50_overlap_mean={float(sem_ov):.3f}, sem_top50_any_match={float(sem_any):.2f}, "
                f"top20_pools(A/B/C)={diag.get('top20_poolA_count')}/{diag.get('top20_poolB_count')}/{diag.get('top20_poolC_count')}, "
                f"forced_neural_shortlist={diag.get('forced_neural_count')}, "
                f"forced_sim_min/mean/max={float(diag.get('forced_neural_sim_min', 0.0)):.3f}/{float(diag.get('forced_neural_sim_mean', 0.0)):.3f}/{float(diag.get('forced_neural_sim_max', 0.0)):.3f}, "
                f"forced_in_top20/top50={diag.get('forced_neural_in_top20_count')}/{diag.get('forced_neural_in_top50_count')}, "
                f"seed_mode={diag.get('seed_ranking_mode')}, "
                f"franchise_cap(thr/cap20/cap50)={float(diag.get('franchise_cap_threshold', 0.0)):.2f}/{diag.get('franchise_cap_top20')}/{diag.get('franchise_cap_top50')}, "
                f"top20_franchise_like(before/after)={diag.get('top20_franchise_like_count_before')}/{diag.get('top20_franchise_like_count_after')}, "
                f"top50_franchise_like(before/after)={diag.get('top50_franchise_like_count_before')}/{diag.get('top50_franchise_like_count_after')}, "
                f"dropped(top20/top50/all)={diag.get('franchise_items_dropped_count_top20')}/{diag.get('franchise_items_dropped_count_top50')}/{diag.get('franchise_items_dropped_count')}, "
                f"high_sim_override_fired(top20/top50/all)={diag.get('high_sim_override_fired_count_top20')}/{diag.get('high_sim_override_fired_count_top50')}/{diag.get('high_sim_override_fired_count_all')}, "
                f"high_sim_override_sim_min/mean/max(top50)={float(diag.get('high_sim_override_sim_min', 0.0)):.3f}/{float(diag.get('high_sim_override_sim_mean', 0.0)):.3f}/{float(diag.get('high_sim_override_sim_max', 0.0)):.3f}, "
                f"high_sim_override_sim_min/mean/max(all)={float(diag.get('high_sim_override_sim_min_all', 0.0)):.3f}/{float(diag.get('high_sim_override_sim_mean_all', 0.0)):.3f}/{float(diag.get('high_sim_override_sim_max_all', 0.0)):.3f}, "
                f"stage1_off_type_allowed={diag.get('stage1_off_type_allowed_count')}, "
                f"stage1_off_type_allowed_neural={diag.get('stage1_off_type_allowed_neural_count')}, "
                f"top20_off_type={diag.get('top20_off_type_count')}, "
                f"off_type_sim_min={float(diag.get('stage1_off_type_allowed_sim_min', 0.0)):.5f}, "
                f"off_type_sim_mean={float(diag.get('stage1_off_type_allowed_sim_mean', 0.0)):.5f}, "
                f"off_type_sim_max={float(diag.get('stage1_off_type_allowed_sim_max', 0.0)):.5f}, "
                f"top20_tfidf_nonzero={diag.get('top20_tfidf_nonzero_count')}, "
                f"embed_blocked%={100.0 * float(diag.get('embed_semantic_blocked_by_policy_rate', 0.0)):.1f}%, "
                f"tfidf_blocked%={100.0 * float(diag.get('tfidf_semantic_blocked_by_policy_rate', 0.0)):.1f}%, "
                f"laneA={diag.get('admitted_by_lane_A_count')}, laneB={diag.get('admitted_by_lane_B_count')}, "
                f"theme_override={diag.get('admitted_by_theme_override_count')}, "
                f"seed_has_shounen_demo={bool(diag.get('seed_has_shounen_demo', False))}, "
                f"seed_demo_tokens=[{seed_demo_str}], "
                f"demo_override_admitted={diag.get('demo_override_admitted_count')}, "
                f"demo_override_top20={diag.get('demo_override_used_in_top20_count')}, "
                f"blocked_overlap={diag.get('blocked_due_to_overlap_count')}, blocked_low_sim={diag.get('blocked_due_to_low_sim_count')}, "
                f"bonus_fired={diag.get('metadata_bonus_fired_count')}, "
                f"bonus_mean={float(diag.get('metadata_bonus_mean', 0.0)):.5f}, "
                f"bonus_max={float(diag.get('metadata_bonus_max', 0.0)):.5f}, "
                f"tfidf_fired={diag.get('synopsis_tfidf_bonus_fired_count')}, "
                f"tfidf_mean={float(diag.get('synopsis_tfidf_bonus_mean', 0.0)):.5f}, "
                f"theme_bonus_fired(top20/top50)={diag.get('theme_bonus_fired_count_top20')}/{diag.get('theme_bonus_fired_count_top50')}, "
                f"theme_bonus_mean(top20/top50)={float(diag.get('theme_bonus_mean_top20', 0.0)):.5f}/{float(diag.get('theme_bonus_mean_top50', 0.0)):.5f}, "
                f"theme_bonus_max(top20/top50)={float(diag.get('theme_bonus_max_top20', 0.0)):.5f}/{float(diag.get('theme_bonus_max_top50', 0.0)):.5f}, "
                f"top20_theme_overlap_count={diag.get('top20_theme_overlap_count')}, "
                f"top20_overlap_meta={float(diag.get('top20_overlap_with_without_meta', 1.0)):.3f}, "
                f"top50_overlap_meta={float(diag.get('top50_overlap_with_without_meta', 1.0)):.3f}, "
                f"top20_moved_meta={diag.get('top20_moved_count')}, "
                f"top50_moved_meta={diag.get('top50_moved_count')}, "
                f"top20_overlap_tfidf={float(diag.get('top20_overlap_with_without_tfidf', 1.0)):.3f}, "
                f"top50_overlap_tfidf={float(diag.get('top50_overlap_with_without_tfidf', 1.0)):.3f}, "
                f"top20_moved_tfidf={diag.get('top20_moved_count_tfidf')}, "
                f"top50_moved_tfidf={diag.get('top50_moved_count_tfidf')}"
            )

            # Required: short Stage 0 audit table for selected seeds.
            if str(q.get("id")) in {"cowboy_bebop", "steins_gate", "death_note"}:
                lines.append("")
                lines.append("Stage 0 audit:")
                lines.append("")
                seed_title = ", ".join(q.get("resolved_seed_titles") or q.get("seed_titles") or [])

                after = int(diag.get("stage0_after_cap", 0))
                denom = float(max(1, after))
                tier_counts_after = diag.get("stage0_after_cap_counts_by_tier") or {}
                pct_neural = 100.0 * float(tier_counts_after.get("stage0_from_neural", 0)) / denom
                pct_meta = 100.0 * float(tier_counts_after.get("stage0_from_meta_strict", 0)) / denom
                pct_pop = 100.0 * float(tier_counts_after.get("stage0_from_popularity", 0)) / denom

                lines.append("| seed title | stage0_after_cap | % neural | % meta_strict | % popularity |")
                lines.append("|---|---:|---:|---:|---:|")
                lines.append(
                    f"| {seed_title.replace('|', '\\|')} | "
                    f"{after} | {pct_neural:.1f}% | {pct_meta:.1f}% | {pct_pop:.1f}% |"
                )

                lines.append("")
                lines.append("Stage 0 details:")
                lines.append("")
                lines.append("| metric | value |")
                lines.append("|---|---:|")
                lines.append(f"| stage0_pool_raw | {int(diag.get('stage0_pool_raw', 0))} |")
                lines.append(f"| stage0_after_hygiene | {int(diag.get('stage0_after_hygiene', 0))} |")
                lines.append(f"| stage0_after_cap | {after} |")
                lines.append(
                    "| stage0_src_raw(neural/meta_strict/pop) | "
                    f"{int((diag.get('stage0_raw_counts_by_tier') or {}).get('stage0_from_neural', 0))}/"
                    f"{int((diag.get('stage0_raw_counts_by_tier') or {}).get('stage0_from_meta_strict', 0))}/"
                    f"{int((diag.get('stage0_raw_counts_by_tier') or {}).get('stage0_from_popularity', 0))} |"
                )
                lines.append(
                    "| stage0_src_after_cap(neural/meta_strict/pop) | "
                    f"{int(tier_counts_after.get('stage0_from_neural', 0))}/"
                    f"{int(tier_counts_after.get('stage0_from_meta_strict', 0))}/"
                    f"{int(tier_counts_after.get('stage0_from_popularity', 0))} |"
                )
                lines.append(f"| stage1_candidate_universe_count | {int(diag.get('stage1_candidate_universe_count', 0))} |")
                lines.append(f"| stage0_stage1_universe_match | {bool(diag.get('stage0_stage1_universe_match', False))} |")
                lines.append(f"| final_scored_candidate_count | {int(diag.get('final_scored_candidate_count', 0))} |")
                lines.append(f"| top20_in_stage0_count | {int(diag.get('top20_in_stage0_count', 0))} |")
                lines.append(f"| top50_in_stage0_count | {int(diag.get('top50_in_stage0_count', 0))} |")

            # Deterministic why-not-scored breakdown.
            why = diag.get("why_not_scored_counts") or {}
            if isinstance(why, dict) and why:
                lines.append("")
                lines.append("Why not scored (Stage 0 universe):")
                lines.append("")
                universe = int(diag.get("stage0_after_cap", 0) or diag.get("stage1_candidate_universe_count", 0) or 0)
                denom = float(max(1, universe))
                lines.append("| reason | count | % of stage0_after_cap |")
                lines.append("|---|---:|---:|")
                for reason in REASONS_ORDERED:
                    cnt = int(why.get(reason, 0))
                    lines.append(f"| {str(reason).replace('|', '\\|')} | {cnt} | {100.0 * float(cnt) / denom:.1f}% |")
                extra_reasons = [k for k in why.keys() if k not in set(REASONS_ORDERED)]
                for reason in sorted(extra_reasons):
                    cnt = int(why.get(reason, 0))
                    lines.append(f"| {str(reason).replace('|', '\\|')} | {cnt} | {100.0 * float(cnt) / denom:.1f}% |")

            dropped = diag.get("franchise_items_dropped_examples_top5") or []
            if isinstance(dropped, list) and dropped:
                lines.append("")
                lines.append("Franchise-cap dropped examples (top 5):")
                for ex in dropped[:5]:
                    try:
                        t = str(ex.get("title", ""))
                        ov = float(ex.get("title_overlap", 0.0))
                        ns = ex.get("neural_sim", None)
                        reason = str(ex.get("reason", "") or "")
                        if ns is None:
                            lines.append(f"- {t} (reason={reason}, title_overlap={ov:.2f})")
                        else:
                            lines.append(f"- {t} (reason={reason}, title_overlap={ov:.2f}, neural_sim={float(ns):.3f})")
                    except Exception:
                        continue

            fl_ex = diag.get("franchise_like_examples_top10") or []
            if isinstance(fl_ex, list) and fl_ex:
                lines.append("")
                lines.append("Franchise-like examples (top 10, pre-cap):")
                lines.append("")
                lines.append("| anime_id | Title | reason | title_overlap | neural_sim |")
                lines.append("|---:|---|---|---:|---:|")
                for ex in fl_ex[:10]:
                    try:
                        aid = int(ex.get("anime_id", 0))
                        title = str(ex.get("title", "")).replace("|", "\\|")
                        reason = str(ex.get("reason", "") or "")
                        ov = float(ex.get("title_overlap", 0.0))
                        ns = ex.get("neural_sim", None)
                        if ns is None:
                            ns_str = ""
                        else:
                            ns_str = f"{float(ns):.3f}"
                        lines.append(f"| {aid} | {title} | {reason} | {ov:.2f} | {ns_str} |")
                    except Exception:
                        continue

            if str(q.get("id")) == "one_piece":
                audit = diag.get("franchise_overlap_audit_top10") or []
                if isinstance(audit, list) and audit:
                    lines.append("")
                    lines.append("Franchise-cap audit (One Piece): top10 by title_overlap")
                    lines.append("")
                    lines.append("| anime_id | Title | title_overlap | franchise_like | reason |")
                    lines.append("|---:|---|---:|:---:|---|")
                    for it in audit[:10]:
                        try:
                            aid = int(it.get("anime_id", 0))
                            title = str(it.get("title", "")).replace("|", "\\|")
                            ov = float(it.get("title_overlap", 0.0))
                            fl = bool(it.get("franchise_like", False))
                            reason = str(it.get("reason", "") or "")
                            lines.append(f"| {aid} | {title} | {ov:.2f} | {'Y' if fl else 'N'} | {reason} |")
                        except Exception:
                            continue

                one_piece_top10_by_neural = diag.get("one_piece_top10_by_neural") or []
                if isinstance(one_piece_top10_by_neural, list) and one_piece_top10_by_neural:
                    lines.append("")
                    lines.append("Content-first audit: top10 items by neural_sim (rank movement)")
                    lines.append("")
                    lines.append("| anime_id | Title | neural_sim | hybrid_val | score_before | score_after | rank_before | rank_after |")
                    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")
                    for it in one_piece_top10_by_neural:
                        try:
                            aid = int(it.get("anime_id", 0))
                            title = str(it.get("title", "")).replace("|", "\\|")
                            ns = float(it.get("neural_sim", 0.0))
                            hv = float(it.get("hybrid_val", 0.0))
                            sb = float(it.get("score_before", 0.0))
                            sa = float(it.get("score_after", 0.0))
                            rb = int(it.get("rank_before", 0))
                            ra = int(it.get("rank_after", 0))
                        except Exception:
                            continue
                        lines.append(f"| {aid} | {title} | {ns:.4f} | {hv:.5f} | {sb:.5f} | {sa:.5f} | {rb} | {ra} |")

                forced_top10 = diag.get("forced_neural_top10") or []
                if isinstance(forced_top10, list) and forced_top10:
                    lines.append("")
                    lines.append("Forced-neural top10 neighbors (by similarity):")
                    lines.append("")
                    lines.append("| anime_id | Title | Type | sim | in_shortlist | rank@50 | in_top20 |")
                    lines.append("|---:|---|---|---:|---:|---:|---:|")
                    for it in forced_top10:
                        try:
                            aid = int(it.get("anime_id", 0))
                            title = str(it.get("title_display") or "")
                            typ = it.get("type")
                            typ_s = "" if typ is None else str(typ)
                            sim = float(it.get("sim", 0.0))
                            in_shortlist = bool(it.get("in_shortlist", False))
                            rank50 = it.get("rank_in_top50", None)
                            rank50_s = "" if rank50 is None else str(int(rank50))
                            in_top20 = bool(it.get("in_top20", False))
                        except Exception:
                            continue
                        lines.append(
                            f"| {aid} | {title} | {typ_s} | {sim:.4f} | {in_shortlist} | {rank50_s} | {in_top20} |"
                        )

                    lines.append("")
                    lines.append("Stage 2 high-sim override audit (top10 neural neighbors):")
                    lines.append("")
                    lines.append("| anime_id | sim | type | final_rank | score | Δ_to_top20_cutoff | hybrid | overlap | coverage | neural_bonus | penalty_before | penalty_after | stage2_override |")
                    lines.append("|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
                    for it in forced_top10:
                        try:
                            aid = int(it.get("anime_id", 0))
                            sim = float(it.get("sim", 0.0))
                            typ = it.get("type")
                            typ_s = "" if typ is None else str(typ)
                            fr = it.get("final_rank", None)
                            fr_s = "" if fr is None else str(int(fr))
                            score = it.get("score", None)
                            score_s = "" if score is None else f"{float(score):.5f}"
                            d20 = it.get("delta_to_top20_cutoff", None)
                            d20_s = "" if d20 is None else f"{float(d20):.5f}"
                            hv = it.get("hybrid_val", None)
                            hv_s = "" if hv is None else f"{float(hv):.5f}"
                            ov = it.get("weighted_overlap", None)
                            ov_s = "" if ov is None else f"{float(ov):.3f}"
                            cov = it.get("seed_coverage", None)
                            cov_s = "" if cov is None else f"{float(cov):.3f}"
                            nb = it.get("synopsis_neural_bonus", None)
                            nb_s = "" if nb is None else f"{float(nb):.5f}"
                            pb = it.get("penalty_before", None)
                            pa = it.get("penalty_after", None)
                            pb_s = "" if pb is None else f"{float(pb):.5f}"
                            pa_s = "" if pa is None else f"{float(pa):.5f}"
                            fired = it.get("stage2_override_relaxed", None)
                            fired_s = "" if fired is None else str(bool(fired))
                        except Exception:
                            continue
                        lines.append(
                            f"| {aid} | {sim:.4f} | {typ_s} | {fr_s} | {score_s} | {d20_s} | {hv_s} | {ov_s} | {cov_s} | {nb_s} | {pb_s} | {pa_s} | {fired_s} |"
                        )

            # Per-request: show top 5 items by theme bonus for One Piece and Tokyo Ghoul.
            if str(q.get("id")) in {"one_piece", "tokyo_ghoul"}:
                top5 = diag.get("top5_items_by_theme_bonus_top50") or []
                if isinstance(top5, list) and top5:
                    lines.append("")
                    lines.append("Top 5 items by theme_stage2_bonus (within top50):")
                    lines.append("")
                    lines.append("| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |")
                    lines.append("|---:|---:|---|---:|---:|")
                    for it in top5:
                        try:
                            r50 = int(it.get("rank_in_top50", 0))
                            aid = int(it.get("anime_id", 0))
                            title = str(it.get("title_display", "")).replace("|", "\\|")
                            to = it.get("theme_overlap")
                            to_s = "" if to is None else f"{float(to):.3f}"
                            tb = float(it.get("theme_stage2_bonus", 0.0))
                            lines.append(f"| {r50} | {aid} | {title} | {to_s} | {tb:.5f} |")
                        except Exception:
                            continue

            sample_blocked = diag.get("blocked_high_sim_overlap_025_0333_top") or []
            if isinstance(sample_blocked, list) and sample_blocked:
                lines.append("")
                lines.append("High-sim blocked candidates (overlap in {0.25, 0.333}):")
                lines.append("")
                lines.append("| Source | anime_id | Title | Sim | genre_overlap | theme_overlap |")
                lines.append("|---|---:|---|---:|---:|---:|")
                for it in sample_blocked[:10]:
                    try:
                        src = str(it.get("source", ""))
                        aid = int(it.get("anime_id"))
                        title = str(it.get("title", "")).replace("|", "\\|")
                        sim = float(it.get("sim", 0.0))
                        go = float(it.get("weighted_overlap", 0.0))
                        to = it.get("theme_overlap")
                        to_s = "" if to is None else f"{float(to):.3f}"
                        lines.append(f"| {src} | {aid} | {title} | {sim:.3f} | {go:.3f} | {to_s} |")
                    except Exception:
                        continue
        lines.append("")

        # Table header
        lines.append("| Rank | anime_id | Title | Type | MAL | Members | Flag |")
        lines.append("|---:|---:|---|---|---:|---:|---|")

        violations_by_id_rank = {(v.get("anime_id"), v.get("rank")): v for v in (q.get("violations") or [])}

        for idx, rec in enumerate(q.get("recommendations") or [], start=1):
            meta = rec.get("meta") or {}
            aid = int(rec.get("anime_id"))
            title = str(meta.get("title_display", "")).replace("|", "\\|")
            typ = meta.get("type") or ""
            mal = meta.get("mal_score")
            members = meta.get("members_count")

            flag = ""
            v = violations_by_id_rank.get((aid, idx))
            if v:
                parts: list[str] = []
                if v.get("bad_type"):
                    parts.append("bad_type")
                if v.get("bad_title"):
                    parts.append("bad_title")
                flag = ",".join(parts)

            mal_s = f"{float(mal):.2f}" if mal is not None else ""
            mem_s = f"{int(members):d}" if members is not None else ""

            lines.append(f"| {idx} | {aid} | {title} | {typ} | {mal_s} | {mem_s} | {flag} |")

        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 A1: offline metrics + golden queries")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT, help="K for offline ranking metrics")
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS, help="Users sampled for offline metrics")
    parser.add_argument("--w-mf", type=float, default=DEFAULT_HYBRID_WEIGHTS["mf"])
    parser.add_argument("--w-knn", type=float, default=DEFAULT_HYBRID_WEIGHTS["knn"])
    parser.add_argument("--w-pop", type=float, default=DEFAULT_HYBRID_WEIGHTS["pop"])
    parser.add_argument(
        "--golden",
        type=str,
        default="data/samples/golden_queries_phase4.json",
        help="Path to golden queries config JSON",
    )
    parser.add_argument(
        "--golden-weight-mode",
        type=str,
        default="Balanced",
        choices=["Balanced", "Diversity"],
        help="Use app weight preset for golden queries (seed-based scoring)",
    )
    parser.add_argument(
        "--seed-ranking-mode",
        type=str,
        default=None,
        help=(
            "Seed ranking goal mode for golden eval (completion|discovery). "
            "Defaults to env var SEED_RANKING_MODE (or completion)."
        ),
    )
    args = parser.parse_args()

    set_determinism(42)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    # 1) Headline offline metrics
    headline = _run_headline_metrics(
        k=int(args.k),
        sample_users=int(args.sample_users),
        w_mf=float(args.w_mf),
        w_knn=float(args.w_knn),
        w_pop=float(args.w_pop),
    )

    headline.update({"timestamp_utc": ts, "seed": 42})

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out_metrics_json = METRICS_DIR / f"phase4_eval_{ts}.json"
    out_metrics_json.write_text(json.dumps(headline, indent=2, default=_json_default), encoding="utf-8")

    # Append to summary.csv (stable schema: one row)
    out_summary = METRICS_DIR / "summary.csv"
    pd.DataFrame([headline]).to_csv(out_summary, mode="a", header=not out_summary.exists(), index=False)

    # 2) Golden queries report
    golden_path = Path(args.golden)
    golden_results = _evaluate_golden_queries(
        golden_path=golden_path,
        weight_mode=str(args.golden_weight_mode),
        seed_ranking_mode=(None if args.seed_ranking_mode is None else str(args.seed_ranking_mode)),
    )
    golden_results["timestamp_utc"] = ts

    REPORTS_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    out_golden_json = REPORTS_ARTIFACTS_DIR / f"phase4_golden_queries_{ts}.json"
    out_golden_json.write_text(json.dumps(golden_results, indent=2, default=_json_default), encoding="utf-8")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_md = REPORTS_DIR / f"phase4_golden_queries_{ts}.md"
    _render_markdown_report(golden_results=golden_results, out_path=out_md)

    print(json.dumps({
        "metrics_json": str(out_metrics_json.as_posix()),
        "golden_json": str(out_golden_json.as_posix()),
        "golden_md": str(out_md.as_posix()),
        "headline": headline,
    }, indent=2, default=_json_default))


if __name__ == "__main__":
    main()
