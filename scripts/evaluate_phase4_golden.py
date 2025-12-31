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

    recs: dict[int, list[int]] = {}

    weights = {"mf": float(w_mf), "knn": float(w_knn), "pop": float(w_pop)}

    for u in users:
        u = int(u)
        seen = set(train_hist.get(u, set()))

        knn_scores = knn_model.score_all(u, exclude_seen=True)

        # MF scores (mask seen)
        mf_scores_arr = mf_model.predict_user(u)
        if mf_model.item_to_index is not None:
            for it in seen:
                idx = mf_model.item_to_index.get(int(it))
                if idx is not None and 0 <= int(idx) < len(mf_scores_arr):
                    mf_scores_arr[int(idx)] = -np.inf
        mf_scores = {
            int(mf_model.index_to_item[i]): float(s)
            for i, s in enumerate(mf_scores_arr)
            if np.isfinite(s)
        }

        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}

        # Deterministic weighted blend
        agg: dict[int, float] = {}
        for source, scores in (("mf", mf_scores), ("knn", knn_scores), ("pop", pop_scores)):
            w = float(weights.get(source, 0.0))
            if w == 0.0:
                continue
            for item_id, sc in scores.items():
                agg[int(item_id)] = agg.get(int(item_id), 0.0) + w * float(sc)

        recs[u] = _stable_rank(agg, top_k=k)

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
        }

    exclude_ids = set(exclude_ids or set())

    # Stable iteration order
    work = metadata.sort_values("anime_id", kind="mergesort")

    # Phase 4 / Chunk A3: seed metadata affinity profile (used as a cold-start bonus only).
    seed_meta_profile = build_seed_metadata_profile(work, seed_ids=seed_ids)

    # Phase 4 (A3 → early A4): optional synopsis TF-IDF similarity map for semantic rerank.
    synopsis_sims_by_id: dict[int, float] = {}
    seed_type_target: str | None = None
    if synopsis_tfidf_artifact is not None:
        try:
            synopsis_sims_by_id = compute_seed_similarity_map(synopsis_tfidf_artifact, seed_ids=seed_ids)
            seed_type_target = most_common_seed_type(work, seed_ids)
        except Exception:
            synopsis_sims_by_id = {}
            seed_type_target = None

    seed_genre_map: dict[str, set[str]] = {}
    all_seed_genres: set[str] = set()
    genre_weights: dict[str, int] = {}

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
    # Prefer TF-IDF neighbors first (when available) to keep the shortlist
    # seed-conditioned before allowing hybrid/MF priors in Stage 2.
    stage1_tfidf_pool: list[dict[str, Any]] = []
    stage1_fallback_pool: list[dict[str, Any]] = []

    stage1_off_type_allowed_sims: list[float] = []

    for _, row in work.iterrows():
        aid = int(row["anime_id"])
        if aid in exclude_ids:
            continue
        if aid in seed_ids:
            continue

        item_genres = _parse_genres(row.get("genres"))
        raw_overlap = sum(genre_weights.get(g, 0) for g in item_genres)
        max_possible_overlap = len(all_seed_genres) * num_seeds
        weighted_overlap = (raw_overlap / max_possible_overlap) if max_possible_overlap > 0 else 0.0

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
        cand_type = None if pd.isna(row.get("type")) else str(row.get("type")).strip()
        cand_eps = row.get("episodes")
        base_passes_gate = synopsis_gate_passes(
            seed_type=seed_type_target,
            candidate_type=cand_type,
            candidate_episodes=cand_eps,
        )

        high_sim_override = (not bool(base_passes_gate)) and (float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD))
        passes_gate_effective = bool(base_passes_gate) or bool(high_sim_override)

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
                "seed_coverage": float(seed_coverage),
                "metadata_affinity": float(meta_affinity),
                "synopsis_tfidf_sim": float(synopsis_tfidf_sim),
                "synopsis_tfidf_base_gate_passed": bool(base_passes_gate),
                "synopsis_tfidf_high_sim_override": bool(high_sim_override),
                "overlap_per_seed": overlap_per_seed,
            },
        }

        # Pool A: TF-IDF neighbors (gated) – use similarity as the primary Stage 1 rank.
        if bool(passes_gate_effective) and float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_MIN_SIM):
            item = dict(base)
            item["stage1_score"] = float(synopsis_tfidf_sim)
            stage1_tfidf_pool.append(item)
            if bool(high_sim_override):
                stage1_off_type_allowed_sims.append(float(synopsis_tfidf_sim))
            continue

        # Pool B: backfill candidates when TF-IDF is absent/insufficient.
        fallback_score = (
            (0.5 * float(weighted_overlap))
            + (0.2 * float(seed_coverage))
            + float(meta_bonus_s1)
        )
        if float(fallback_score) > 0.0:
            item = dict(base)
            item["stage1_score"] = float(fallback_score)
            stage1_fallback_pool.append(item)

    stage1_tfidf_pool.sort(
        key=lambda x: (
            -float((x.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0)),
            -float((x.get("_stage1") or {}).get("weighted_overlap", 0.0)),
            -float((x.get("_stage1") or {}).get("metadata_affinity", 0.0)),
            int(x.get("anime_id", 0)),
        )
    )
    stage1_fallback_pool.sort(key=lambda x: (-float(x.get("stage1_score", 0.0)), int(x.get("anime_id", 0))))

    shortlist_k = max(0, int(shortlist_size))
    stage1_total_candidates = int(len(stage1_tfidf_pool) + len(stage1_fallback_pool))
    if shortlist_k <= 0:
        shortlist = stage1_tfidf_pool + stage1_fallback_pool
    else:
        shortlist: list[dict[str, Any]] = []
        seen_ids: set[int] = set()
        for it in stage1_tfidf_pool:
            if len(shortlist) >= shortlist_k:
                break
            aid = int(it.get("anime_id", 0))
            if aid in seen_ids:
                continue
            shortlist.append(it)
            seen_ids.add(aid)
        for it in stage1_fallback_pool:
            if len(shortlist) >= shortlist_k:
                break
            aid = int(it.get("anime_id", 0))
            if aid in seen_ids:
                continue
            shortlist.append(it)
            seen_ids.add(aid)

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
        high_sim_override = (not bool(passes_gate)) and (float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD))
        passes_gate_effective = bool(passes_gate) or bool(high_sim_override)

        # If we admitted a candidate via the high-sim override, treat it as a
        # cold-start-ish semantic neighbor for TF-IDF coefficient selection and
        # do not let a negative hybrid value effectively veto it.
        hybrid_val_for_scoring = float(hybrid_val)
        hybrid_val_for_tfidf = float(hybrid_val)
        if bool(high_sim_override):
            hybrid_val_for_scoring = max(0.0, float(hybrid_val))
            hybrid_val_for_tfidf = 0.0

        synopsis_tfidf_bonus = 0.0
        if bool(passes_gate_effective):
            synopsis_tfidf_bonus = float(
                synopsis_tfidf_bonus_for_candidate(
                    sim=synopsis_tfidf_sim,
                    hybrid_val=hybrid_val_for_tfidf,
                )
            )

        # Prefer a small penalty (not exclusion) for very-high-sim off-type items.
        # Keep the existing conservative short-form penalty for all other off-gate cases.
        if bool(high_sim_override):
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
                    "weighted_overlap": float(weighted_overlap),
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
                    "synopsis_tfidf_high_sim_override": bool(high_sim_override),
                    "demographics_overlap_bonus": float(demo_bonus),
                    "score_without_synopsis_tfidf_bonus": float(score - synopsis_tfidf_adjustment),
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

    top20_mean_abs_delta, top20_moved = _rank_diagnostics(with20, without20)
    top50_mean_abs_delta, top50_moved = _rank_diagnostics(with50, without50)

    top20_mean_abs_delta_tfidf, top20_moved_tfidf = _rank_diagnostics(with20, without_tfidf20)
    top50_mean_abs_delta_tfidf, top50_moved_tfidf = _rank_diagnostics(with50, without_tfidf50)

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

    # Seed-conditioning diagnostics for Option A shortlist
    top20 = recs_top_n[:20]
    top20_tfidf_nonzero = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_tfidf_sim", 0.0)) > 0.0)
    top20_tfidf_ge_min = sum(1 for r in top20 if float((r.get("signals") or {}).get("synopsis_tfidf_sim", 0.0)) >= 0.02)

    # Off-type here means: fails the conservative base gate (same type OR episodes>=min).
    top20_off_type = sum(1 for r in top20 if not bool((r.get("signals") or {}).get("synopsis_tfidf_base_gate_passed", True)))

    shortlist_from_tfidf = sum(1 for it in shortlist if float((it.get("_stage1") or {}).get("synopsis_tfidf_sim", 0.0)) >= 0.02)

    stage1_off_type_allowed_count = int(len(stage1_off_type_allowed_sims))
    if stage1_off_type_allowed_sims:
        s_min = float(min(stage1_off_type_allowed_sims))
        s_mean = float(sum(stage1_off_type_allowed_sims) / len(stage1_off_type_allowed_sims))
        s_max = float(max(stage1_off_type_allowed_sims))
    else:
        s_min = 0.0
        s_mean = 0.0
        s_max = 0.0

    diagnostics = {
        "stage1_shortlist_target": int(shortlist_k) if shortlist_k > 0 else int(stage1_total_candidates),
        "stage1_shortlist_size": int(len(shortlist)),
        "stage1_shortlist_from_tfidf_count": int(shortlist_from_tfidf),
        "stage1_off_type_allowed_count": int(stage1_off_type_allowed_count),
        "stage1_off_type_allowed_sim_min": float(s_min),
        "stage1_off_type_allowed_sim_mean": float(s_mean),
        "stage1_off_type_allowed_sim_max": float(s_max),
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
    }

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
                f"shortlist={diag.get('stage1_shortlist_size')}/{diag.get('stage1_shortlist_target')}, "
                f"stage1_off_type_allowed={diag.get('stage1_off_type_allowed_count')}, "
                f"top20_off_type={diag.get('top20_off_type_count')}, "
                f"off_type_sim_min={float(diag.get('stage1_off_type_allowed_sim_min', 0.0)):.5f}, "
                f"off_type_sim_mean={float(diag.get('stage1_off_type_allowed_sim_mean', 0.0)):.5f}, "
                f"off_type_sim_max={float(diag.get('stage1_off_type_allowed_sim_max', 0.0)):.5f}, "
                f"top20_tfidf_nonzero={diag.get('top20_tfidf_nonzero_count')}, "
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
