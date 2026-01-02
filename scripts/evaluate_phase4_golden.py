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
from src.app.metadata_features import (
    METADATA_AFFINITY_COLD_START_COEF,
    METADATA_AFFINITY_TRAINED_COEF,
    build_seed_metadata_profile,
    compute_metadata_affinity,
    demographics_overlap_tiebreak_bonus,
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

from src.app.semantic_admission import stage1_semantic_admission, theme_overlap_ratio

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
    shortlist_size: int = 600,
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
        }

    # Semantic mode: embeddings (successor), tfidf (legacy), both, none.
    # Default is deterministic and conservative: use BOTH when available so
    # embeddings can help without regressing cases where TF-IDF still helps.
    semantic_mode = str(os.environ.get("PHASE4_SEMANTIC_MODE", "")).strip().lower()
    if semantic_mode not in {"embeddings", "tfidf", "both", "none", ""}:
        semantic_mode = ""
    if not semantic_mode:
        if synopsis_embeddings_artifact is not None and synopsis_tfidf_artifact is not None:
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

    # Phase 4: optional semantic similarity maps (TF-IDF legacy; embeddings successor).
    synopsis_sims_by_id: dict[int, float] = {}
    embed_sims_by_id: dict[int, float] = {}
    seed_type_target: str | None = None
    try:
        seed_type_target = most_common_seed_type(work, seed_ids)
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
    stage1_fallback_pool: list[dict[str, Any]] = []

    seed_genres_count = int(len(all_seed_genres))
    seed_themes = getattr(seed_meta_profile, "themes", frozenset()) or frozenset()

    # Diagnostics: quantify admission behavior under the adaptive two-lane policy.
    # Baseline ("old") is kept for comparability: semantic min-sim AND (overlap>0 OR title>=0.50).
    # Policy ("new"): stage1_semantic_admission(...) decision.
    embed_semantic_old_admit = 0
    embed_semantic_policy_admit = 0
    embed_semantic_blocked_by_policy = 0
    tfidf_semantic_old_admit = 0
    tfidf_semantic_policy_admit = 0
    tfidf_semantic_blocked_by_policy = 0

    admitted_by_lane_A_count = 0
    admitted_by_lane_B_count = 0
    admitted_by_theme_override_count = 0
    blocked_due_to_overlap_count = 0
    blocked_due_to_low_sim_count = 0

    # Keep a small, deterministic sample of the highest-similarity blocked candidates.
    blocked_embed_top: list[dict[str, Any]] = []
    blocked_tfidf_top: list[dict[str, Any]] = []

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

    embed_semantic_blocked_high_sim = 0
    tfidf_semantic_blocked_high_sim = 0
    blocked_embed_high_sim_top: list[dict[str, Any]] = []
    blocked_tfidf_high_sim_top: list[dict[str, Any]] = []

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

    for _, row in work.iterrows():
        aid = int(row["anime_id"])
        if aid in exclude_ids:
            continue
        if aid in seed_ids:
            continue

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
                "overlap_per_seed": overlap_per_seed,
            },
        }

        # Pool A0: embeddings neighbors (gated) – use similarity as the primary Stage 1 rank.
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
            continue

        # Pool A: TF-IDF neighbors (gated) – use similarity as the primary Stage 1 rank.
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
        "admitted_by_lane_A_count": int(admitted_by_lane_A_count),
        "admitted_by_lane_B_count": int(admitted_by_lane_B_count),
        "admitted_by_theme_override_count": int(admitted_by_theme_override_count),
        "blocked_due_to_overlap_count": int(blocked_due_to_overlap_count),
        "blocked_due_to_low_sim_count": int(blocked_due_to_low_sim_count),
        "laneA_admitted_examples_top": list(laneA_admitted_examples_top),
        "blocked_high_sim_overlap_025_0333_top": list(blocked_high_sim_overlap_025_0333),
        "embed_semantic_blocked_top": list(blocked_embed_top),
        "tfidf_semantic_blocked_top": list(blocked_tfidf_top),
        "false_neg_embed_sim_threshold": float(false_neg_embed_sim),
        "false_neg_tfidf_sim_threshold": float(false_neg_tfidf_sim),
        "embed_semantic_blocked_high_sim_count": int(embed_semantic_blocked_high_sim),
        "tfidf_semantic_blocked_high_sim_count": int(tfidf_semantic_blocked_high_sim),
        "embed_semantic_blocked_high_sim_top": list(blocked_embed_high_sim_top),
        "tfidf_semantic_blocked_high_sim_top": list(blocked_tfidf_high_sim_top),
    }

    shortlist_k = max(0, int(shortlist_size))
    stage1_total_candidates = int(len(stage1_embed_pool) + len(stage1_tfidf_pool) + len(stage1_fallback_pool))
    # Phase 4 stabilization: Stage 1 mixture shortlist + semantic confidence gating.
    # Pool A: semantic neighbors (embeddings and/or TF-IDF; seed-conditioned)
    # Pool B: seed-conditioned metadata/genre candidates
    # Pool C: deterministic backfill if A/B are insufficient
    use_embed = semantic_mode in {"embeddings", "both"}
    use_tfidf = semantic_mode in {"tfidf", "both"}

    pool_a: list[dict[str, Any]] = []
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

    if bool(use_embed) and int(embed_stats.get("count", 0)) > 0:
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
        shortlist = pool_a + pool_b
        stage1_k_sem = int(len(pool_a))
        stage1_k_meta = int(len(pool_b))
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

        shortlist = []
        seen_ids = set()
        a_taken = 0
        b_taken = 0
        c_taken = 0

        a_i = 0
        while a_i < len(pool_a) and a_taken < int(stage1_k_sem) and len(shortlist) < int(shortlist_k):
            it = pool_a[a_i]
            a_i += 1
            aid = int(it.get("anime_id", 0))
            if aid in seen_ids:
                continue
            (it.get("_stage1") or {}).update({"pool": "A"})
            shortlist.append(it)
            seen_ids.add(aid)
            a_taken += 1

        b_i = 0
        while b_i < len(pool_b) and b_taken < int(stage1_k_meta) and len(shortlist) < int(shortlist_k):
            it = pool_b[b_i]
            b_i += 1
            aid = int(it.get("anime_id", 0))
            if aid in seen_ids:
                continue
            (it.get("_stage1") or {}).update({"pool": "B"})
            shortlist.append(it)
            seen_ids.add(aid)
            b_taken += 1

        # Pool C: deterministic backfill (prefer meta pool first to avoid semantic dominance when confidence is low).
        while b_i < len(pool_b) and len(shortlist) < int(shortlist_k):
            it = pool_b[b_i]
            b_i += 1
            aid = int(it.get("anime_id", 0))
            if aid in seen_ids:
                continue
            (it.get("_stage1") or {}).update({"pool": "C"})
            shortlist.append(it)
            seen_ids.add(aid)
            c_taken += 1

        while a_i < len(pool_a) and len(shortlist) < int(shortlist_k):
            it = pool_a[a_i]
            a_i += 1
            aid = int(it.get("anime_id", 0))
            if aid in seen_ids:
                continue
            (it.get("_stage1") or {}).update({"pool": "C"})
            shortlist.append(it)
            seen_ids.add(aid)
            c_taken += 1

    # --- Stage 2: rerank shortlist using existing final scoring --------------
    try:
        blended_scores = recommender._blend(0, weights)  # pylint: disable=protected-access
    except Exception:
        blended_scores = None

    id_to_index = {int(aid): idx for idx, aid in enumerate(components.item_ids)}

    scored: list[dict[str, Any]] = []

    for c in shortlist:
        aid = int(c["anime_id"])
        s1 = float(c.get("stage1_score", 0.0))

        weighted_overlap = float((c.get("_stage1") or {}).get("weighted_overlap", 0.0))
        seed_coverage = float((c.get("_stage1") or {}).get("seed_coverage", 0.0))
        meta_affinity = float((c.get("_stage1") or {}).get("metadata_affinity", 0.0))
        synopsis_tfidf_sim = float((c.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0))
        synopsis_embed_sim = float((c.get("_stage1") or {}).get("synopsis_embed_sim", 0.0))
        overlap_per_seed = (c.get("_stage1") or {}).get("overlap_per_seed") or {}

        pop_pct = _pop_pct(pop_pct_by_id, aid)
        popularity_boost = max(0.0, (0.5 - pop_pct) / 0.5)

        if blended_scores is not None and aid in id_to_index:
            hybrid_val = float(blended_scores[int(id_to_index[aid])])
        else:
            hybrid_val = 0.0

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
        passes_gate_effective_tfidf = bool(passes_gate) or bool(high_sim_override_tfidf)
        passes_gate_effective_embed = bool(passes_gate) or bool(high_sim_override_embed)

        # If we admitted a candidate via the high-sim override, treat it as a
        # cold-start-ish semantic neighbor for TF-IDF coefficient selection and
        # do not let a negative hybrid value effectively veto it.
        hybrid_val_for_scoring = float(hybrid_val)
        hybrid_val_for_tfidf = float(hybrid_val)
        hybrid_val_for_embed = float(hybrid_val)
        if bool(high_sim_override_tfidf) or bool(high_sim_override_embed):
            hybrid_val_for_scoring = max(0.0, float(hybrid_val))
        if bool(high_sim_override_tfidf):
            hybrid_val_for_tfidf = 0.0
        if bool(high_sim_override_embed):
            hybrid_val_for_embed = 0.0

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

        # Optional tiny tie-breaker: demographics overlap (Stage 2 only; never gates).
        if "demographics" in work.columns:
            seed_demo = seed_meta_profile.demographics
            cand_demo = work.loc[work["anime_id"].astype(int) == aid, "demographics"].head(1)
            cand_demo_val = None if cand_demo.empty else cand_demo.iloc[0]
            demo_bonus = demographics_overlap_tiebreak_bonus(seed_demo, cand_demo_val)
        else:
            demo_bonus = 0.0

        score = (
            (0.5 * weighted_overlap)
            + (0.2 * seed_coverage)
            + (0.25 * float(hybrid_val_for_scoring))
            + (0.05 * popularity_boost)
            + (0.10 * float(s1))
            + meta_bonus
            + synopsis_tfidf_adjustment
            + synopsis_embed_adjustment
            + float(demo_bonus)
        )
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
                    "weighted_overlap": float(weighted_overlap),
                    "seed_title_overlap": float((c.get("_stage1") or {}).get("title_overlap", 0.0)),
                    "seed_coverage": float(seed_coverage),
                    "hybrid_val": float(hybrid_val),
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
                    "demographics_overlap_bonus": float(demo_bonus),
                    "score_without_synopsis_tfidf_bonus": float(score - synopsis_tfidf_adjustment),
                    "score_without_synopsis_embeddings_bonus": float(score - synopsis_embed_adjustment),
                    "overlap_per_seed": overlap_per_seed,
                },
            }
        )

    # Compute rank movement diagnostics by comparing:
    # - with_meta: score includes metadata_bonus
    # - without_meta: score excludes metadata_bonus
    scored_with_meta = sorted(scored, key=lambda x: (-float(x["score"]), int(x["anime_id"])))
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

    top20_mean_abs_delta, top20_moved = _rank_diagnostics(with20, without20)
    top50_mean_abs_delta, top50_moved = _rank_diagnostics(with50, without50)

    top20_mean_abs_delta_tfidf, top20_moved_tfidf = _rank_diagnostics(with20, without_tfidf20)
    top50_mean_abs_delta_tfidf, top50_moved_tfidf = _rank_diagnostics(with50, without_tfidf50)

    top20_mean_abs_delta_embed, top20_moved_embed = _rank_diagnostics(with20, without_embed20)
    top50_mean_abs_delta_embed, top50_moved_embed = _rank_diagnostics(with50, without_embed50)

    recs_top_n = scored_with_meta[:top_n]

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

    # Seed-conditioning diagnostics for Option A shortlist
    top20 = recs_top_n[:20]
    top20_pool_a = sum(1 for r in top20 if str((r.get("signals") or {}).get("stage1_pool", "")) == "A")
    top20_pool_b = sum(1 for r in top20 if str((r.get("signals") or {}).get("stage1_pool", "")) == "B")
    top20_pool_c = sum(1 for r in top20 if str((r.get("signals") or {}).get("stage1_pool", "")) == "C")
    top20_tfidf_nonzero = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_tfidf_sim", 0.0)) > 0.0)
    top20_tfidf_ge_min = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_tfidf_sim", 0.0)) >= 0.02)

    top20_embed_nonzero = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_embed_sim", 0.0)) > 0.0)
    top20_embed_ge_min = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_embed_sim", 0.0)) >= float(SYNOPSIS_EMBEDDINGS_MIN_SIM))

    # Off-type here means: fails the conservative base gate (same type OR episodes>=min).
    top20_off_type = sum(1 for r in top20 if not bool((r.get("signals") or {}).get("synopsis_tfidf_base_gate_passed", True)))

    shortlist_from_tfidf = sum(1 for it in shortlist if float((it.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0)) >= 0.02)
    shortlist_from_embed = sum(1 for it in shortlist if float((it.get("_stage1") or {}).get("synopsis_embed_sim", 0.0)) >= float(SYNOPSIS_EMBEDDINGS_MIN_SIM))

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

    diagnostics = {
        "semantic_mode": semantic_mode,
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
        "top20_poolA_count": int(top20_pool_a),
        "top20_poolB_count": int(top20_pool_b),
        "top20_poolC_count": int(top20_pool_c),
        "stage1_shortlist_target": int(shortlist_k) if shortlist_k > 0 else int(stage1_total_candidates),
        "stage1_shortlist_size": int(len(shortlist)),
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
        "top20_embedding_nonzero_count": int(top20_embed_nonzero),
        "top20_embedding_ge_min_sim_count": int(top20_embed_ge_min),
        "top20_embedding_sim_min": float(top20_embed_sim_min),
        "top20_embedding_sim_mean": float(top20_embed_sim_mean),
        "top20_embedding_sim_max": float(top20_embed_sim_max),
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
    }

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
) -> dict[str, Any]:
    cfg = json.loads(golden_path.read_text(encoding="utf-8"))
    defaults = cfg.get("defaults", {})

    bundle = build_artifacts()
    metadata, components, recommender, pop_pct_by_id = _build_app_like_recommender(bundle)

    synopsis_tfidf_artifact = bundle.get("models", {}).get("synopsis_tfidf")
    synopsis_embeddings_artifact = bundle.get("models", {}).get("synopsis_embeddings")

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
            lines.append(
                "Diagnostics: "
                f"K_sem={diag.get('stage1_k_sem')}, K_meta={diag.get('stage1_k_meta')}, "
                f"sem_conf=({diag.get('semantic_confidence_source')}/{diag.get('semantic_confidence_tier')}) {float(diag.get('semantic_confidence_score', 0.0)):.3f}, "
                f"emb_top50_mean={float(diag.get('embeddings_top50_mean', 0.0)):.3f}, emb_top50_p95={float(diag.get('embeddings_top50_p95', 0.0)):.3f}, "
                f"emb_top50_overlap_mean={float(diag.get('embeddings_top50_weighted_overlap_mean', 0.0)):.3f}, emb_top50_any_match={float(diag.get('embeddings_top50_any_genre_match_frac', 0.0)):.2f}, "
                f"top20_pools(A/B/C)={diag.get('top20_poolA_count')}/{diag.get('top20_poolB_count')}/{diag.get('top20_poolC_count')}, "
                f"shortlist={diag.get('stage1_shortlist_size')}/{diag.get('stage1_shortlist_target')}, "
                f"stage1_off_type_allowed={diag.get('stage1_off_type_allowed_count')}, "
                f"top20_off_type={diag.get('top20_off_type_count')}, "
                f"off_type_sim_min={float(diag.get('stage1_off_type_allowed_sim_min', 0.0)):.5f}, "
                f"off_type_sim_mean={float(diag.get('stage1_off_type_allowed_sim_mean', 0.0)):.5f}, "
                f"off_type_sim_max={float(diag.get('stage1_off_type_allowed_sim_max', 0.0)):.5f}, "
                f"top20_tfidf_nonzero={diag.get('top20_tfidf_nonzero_count')}, "
                f"embed_blocked%={100.0 * float(diag.get('embed_semantic_blocked_by_policy_rate', 0.0)):.1f}%, "
                f"tfidf_blocked%={100.0 * float(diag.get('tfidf_semantic_blocked_by_policy_rate', 0.0)):.1f}%, "
                f"laneA={diag.get('admitted_by_lane_A_count')}, laneB={diag.get('admitted_by_lane_B_count')}, "
                f"theme_override={diag.get('admitted_by_theme_override_count')}, "
                f"blocked_overlap={diag.get('blocked_due_to_overlap_count')}, blocked_low_sim={diag.get('blocked_due_to_low_sim_count')}, "
                f"bonus_fired={diag.get('metadata_bonus_fired_count')}, "
                f"bonus_mean={float(diag.get('metadata_bonus_mean', 0.0)):.5f}, "
                f"bonus_max={float(diag.get('metadata_bonus_max', 0.0)):.5f}, "
                f"tfidf_fired={diag.get('synopsis_tfidf_bonus_fired_count')}, "
                f"tfidf_mean={float(diag.get('synopsis_tfidf_bonus_mean', 0.0)):.5f}, "
                f"top20_overlap_meta={float(diag.get('top20_overlap_with_without_meta', 1.0)):.3f}, "
                f"top50_overlap_meta={float(diag.get('top50_overlap_with_without_meta', 1.0)):.3f}, "
                f"top20_moved_meta={diag.get('top20_moved_count')}, "
                f"top50_moved_meta={diag.get('top50_moved_count')}, "
                f"top20_overlap_tfidf={float(diag.get('top20_overlap_with_without_tfidf', 1.0)):.3f}, "
                f"top50_overlap_tfidf={float(diag.get('top50_overlap_with_without_tfidf', 1.0)):.3f}, "
                f"top20_moved_tfidf={diag.get('top20_moved_count_tfidf')}, "
                f"top50_moved_tfidf={diag.get('top50_moved_count_tfidf')}"
            )

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
    golden_results = _evaluate_golden_queries(golden_path=golden_path, weight_mode=str(args.golden_weight_mode))
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
