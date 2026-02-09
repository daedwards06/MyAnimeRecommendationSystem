"""Pipeline runner: connects sidebar state to scoring pipeline and produces results.

Encapsulates recommender-engine initialisation, recommendation execution,
and scoring-path determination.  Called by ``app/main.py`` after sidebar
rendering returns a ``SidebarResult``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.app.artifacts_loader import ArtifactContractError
from src.app.constants import SEED_RANKING_MODE
from src.app.diversity import compute_popularity_percentiles
from src.app.profiling import latency_timer
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids
from src.app.recommender import HybridComponents, HybridRecommender
from src.app.scoring_pipeline import (
    ScoringContext,
    run_seed_based_pipeline,
    run_personalized_pipeline,
    run_browse_pipeline,
    blend_personalized_and_seed,
    apply_post_filters,
    finalize_explanation_shares,
)

logger = logging.getLogger(__name__)


# ── Data containers ──────────────────────────────────────────────────────────


@dataclass
class RecommenderEngine:
    """Holds the initialised recommender, hybrid components, and helper lookups."""

    recommender: HybridRecommender | None = None
    components: HybridComponents | None = None
    pop_percentile_by_anime_id: dict[int, float] | None = None
    mf_model: Any = None

    def pop_pct_for_anime_id(self, anime_id: int) -> float:
        """Return popularity percentile for display; 0.5 when unavailable."""
        if not self.pop_percentile_by_anime_id:
            return 0.5
        try:
            return float(self.pop_percentile_by_anime_id.get(int(anime_id), 0.5))
        except Exception:
            return 0.5

    def is_in_training(self, anime_id: int) -> bool:
        """Cold-start detection: True iff anime_id is in mf_model.item_to_index."""
        if self.mf_model is None:
            return False
        if not hasattr(self.mf_model, "item_to_index"):
            return False
        try:
            return int(anime_id) in self.mf_model.item_to_index
        except Exception:
            return False


@dataclass
class PipelineRunResult:
    """Output container from :func:`run_recommendations`."""

    recs: list[dict] = field(default_factory=list)
    active_scoring_path: str = "Seedless"
    personalization_applied: bool = False
    personalized_gate_reason: str | None = None


# ── Artifact-failure UI ──────────────────────────────────────────────────────


def render_artifact_load_failure(err: Exception) -> None:
    """Display artifact-load error and halt the app via ``st.stop()``."""
    st.error(
        "Required artifacts are missing or invalid. "
        "Ranked modes are disabled until this is fixed."
    )
    st.markdown("**Active scoring path:** Ranked modes disabled")
    details: list[str] = []
    if isinstance(err, ArtifactContractError):
        details = getattr(err, "details", [])
    elif isinstance(err, FileNotFoundError):
        details = [str(err)]
    else:
        details = [str(err)]

    st.markdown("**Checklist**")
    st.markdown(
        "\n".join(
            [
                "- data/processed/anime_metadata.parquet exists",
                "- models/ contains MF .joblib artifact(s)",
                "- MF artifact provides: Q, item_to_index, index_to_item",
                "- If multiple MF artifacts exist, set APP_MF_MODEL_STEM to choose one",
            ]
        )
    )
    if details:
        st.markdown("**Details**")
        st.markdown("\n".join([f"- {d}" for d in details]))
    st.stop()


# ── Engine construction ──────────────────────────────────────────────────────


def build_recommender_engine(bundle: dict) -> RecommenderEngine:
    """Build a :class:`RecommenderEngine` from an artifact bundle.

    Validates the MF model contract, computes demo-user MF scores, wires
    the kNN popularity prior, and returns the initialised engine.  Calls
    :func:`render_artifact_load_failure` (which invokes ``st.stop()``) on
    any fatal contract violation.
    """
    engine = RecommenderEngine()

    mf_model = bundle.get("models", {}).get("mf")
    if mf_model is None:
        render_artifact_load_failure(
            ArtifactContractError(
                "MF model alias 'mf' not found in loaded models.",
                details=[
                    "Loader should add models['mf'] after validating MF contract.",
                    "Check models/*.joblib and APP_MF_MODEL_STEM.",
                ],
            )
        )
    engine.mf_model = mf_model

    # Build item-ID vector in MF index order.
    if not hasattr(mf_model, "index_to_item"):
        render_artifact_load_failure(
            ArtifactContractError(
                "MF model missing index_to_item.",
                details=["Required attributes: Q, item_to_index, index_to_item"],
            )
        )
    index_to_item = mf_model.index_to_item
    try:
        n_items_mf = len(index_to_item)
        item_ids = np.asarray(
            [int(index_to_item[i]) for i in range(n_items_mf)], dtype=np.int64
        )
    except Exception as e:  # noqa: BLE001
        render_artifact_load_failure(
            ArtifactContractError(
                "MF model index_to_item is not a contiguous 0..N-1 mapping.",
                details=[f"Error: {e}"],
            )
        )

    # Compute demo-user MF scores.
    if not (
        hasattr(mf_model, "P")
        and hasattr(mf_model, "Q")
        and hasattr(mf_model, "global_mean")
    ):
        render_artifact_load_failure(
            ArtifactContractError(
                "MF model is missing required fields to compute demo user scores "
                "(P, Q, global_mean).",
                details=[
                    "This is required for seedless recommendations without a user profile.",
                    "Fix: export MF artifact with P, Q, global_mean "
                    "(or enable personalization with profile ratings).",
                ],
            )
        )
    try:
        p = mf_model.P
        q = mf_model.Q
        if p is None or q is None:
            raise ValueError("P or Q is None")
        if hasattr(q, "shape") and int(q.shape[0]) != int(item_ids.shape[0]):
            raise ValueError(
                f"Q has {int(q.shape[0])} rows but index_to_item has "
                f"{int(item_ids.shape[0])} items"
            )
        if p.shape[0] < 1:
            raise ValueError("MF model has no users in P")
        demo_user_index = 0
        demo_scores = float(mf_model.global_mean) + (p[demo_user_index] @ q.T)
        mf_scores = np.asarray(demo_scores, dtype=np.float32).reshape(1, -1)
    except Exception as e:  # noqa: BLE001
        render_artifact_load_failure(
            ArtifactContractError(
                "Failed computing demo MF scores from MF artifact.",
                details=[f"Error: {e}"],
            )
        )

    components = HybridComponents(mf=mf_scores, knn=None, pop=None, item_ids=item_ids)

    # Wire popularity prior from kNN artifact (optional).
    try:
        knn_model = bundle.get("models", {}).get("knn")
        if (
            knn_model is not None
            and hasattr(knn_model, "item_pop")
            and hasattr(knn_model, "item_to_index")
            and knn_model.item_pop is not None
            and knn_model.item_to_index is not None
        ):
            pop_vec = np.zeros(len(item_ids), dtype=np.float32)
            it2i = knn_model.item_to_index
            pop_arr = knn_model.item_pop

            try:
                pop_pct_arr = compute_popularity_percentiles(
                    np.asarray(pop_arr, dtype=np.float32)
                )
                engine.pop_percentile_by_anime_id = {
                    int(aid): float(pop_pct_arr[int(idx)])
                    for aid, idx in it2i.items()
                    if idx is not None and 0 <= int(idx) < len(pop_pct_arr)
                }
            except Exception:
                engine.pop_percentile_by_anime_id = None

            for j, aid in enumerate(item_ids):
                idx = it2i.get(int(aid))
                if idx is not None and 0 <= int(idx) < len(pop_arr):
                    pop_vec[j] = float(pop_arr[int(idx)])
            components.pop = pop_vec
    except Exception:
        # Popularity prior is optional; do not block app startup.
        pass

    engine.recommender = HybridRecommender(components)
    engine.components = components
    return engine


# ── Recommendation execution ─────────────────────────────────────────────────


def run_recommendations(
    engine: RecommenderEngine,
    sidebar: Any,
    bundle: dict,
    metadata: pd.DataFrame,
) -> PipelineRunResult:
    """Execute the full recommendation pipeline and return results.

    This is the glue between sidebar selections and
    ``src.app.scoring_pipeline``.
    """
    result = PipelineRunResult()

    if sidebar.browse_mode:
        result.active_scoring_path = "Browse"
        return _run_browse(engine, sidebar, bundle, metadata, result)

    return _run_ranked(engine, sidebar, bundle, metadata, result)


# ── Browse mode ──────────────────────────────────────────────────────────────


def _run_browse(
    engine: RecommenderEngine,
    sidebar: Any,
    bundle: dict,
    metadata: pd.DataFrame,
    result: PipelineRunResult,
) -> PipelineRunResult:
    """Filter metadata directly for Browse mode."""
    if not sidebar.genre_filter:
        return result

    browse_ctx = ScoringContext(
        metadata=metadata,
        bundle=bundle,
        browse_mode=True,
        genre_filter=sidebar.genre_filter,
        type_filter=sidebar.type_filter,
        year_range=sidebar.year_range,
        sort_by=sidebar.sort_by,
        default_sort_for_mode=sidebar.default_sort_for_mode,
        top_n=sidebar.top_n,
        pop_pct_fn=engine.pop_pct_for_anime_id,
        watched_ids=(
            {
                int(x)
                for x in (
                    st.session_state["active_profile"].get("watched_ids", []) or []
                )
            }
            if st.session_state.get("active_profile")
            else set()
        ),
    )
    browse_result = run_browse_pipeline(browse_ctx)
    result.recs = browse_result.ranked_items
    return result


# ── Ranked modes (Seed-based / Personalized) ─────────────────────────────────


def _run_ranked(
    engine: RecommenderEngine,
    sidebar: Any,
    bundle: dict,
    metadata: pd.DataFrame,
    result: PipelineRunResult,
) -> PipelineRunResult:
    """Handle Seed-based and Personalized ranking modes."""
    ui_mode = sidebar.ui_mode
    selected_seed_ids = sidebar.selected_seed_ids

    # Personalised-mode gating
    personalized_gate_reason: str | None = None
    if ui_mode == "Personalized":
        personalized_gate_reason = _check_personalization_gate()
    result.personalized_gate_reason = personalized_gate_reason

    if engine.recommender is None or engine.components is None:
        result.active_scoring_path = "Ranked modes disabled"
        return result

    # Request extra candidates to compensate for post-filtering.
    has_profile = st.session_state.get("active_profile") is not None
    has_filters = (
        sidebar.genre_filter
        or sidebar.type_filter
        or sidebar.year_range[0] > 1960
        or sidebar.year_range[1] < 2025
    )
    filter_multiplier = 10 if (has_profile or has_filters) else 1
    n_requested = min(
        sidebar.top_n * filter_multiplier,
        (
            engine.components.num_items
            if hasattr(engine.components, "num_items")
            else len(metadata)
        ),
    )

    if n_requested <= 0 or personalized_gate_reason:
        result.active_scoring_path = _determine_scoring_path(
            ui_mode, personalized_gate_reason, engine, False, selected_seed_ids,
        )
        return result

    # Hygiene exclusion set (once per run).
    ranked_hygiene_exclude_ids = build_ranked_candidate_hygiene_exclude_ids(metadata)

    with st.spinner("🔍 Finding recommendations..."):
        with latency_timer("recommendations"):
            recs, personalization_applied = _execute_pipeline(
                engine, sidebar, bundle, metadata,
                n_requested, ranked_hygiene_exclude_ids,
            )

    result.recs = recs
    result.personalization_applied = personalization_applied
    result.active_scoring_path = _determine_scoring_path(
        ui_mode, personalized_gate_reason, engine,
        personalization_applied, selected_seed_ids,
    )

    # Augment path label when personalization was requested but not applied.
    personalization_requested = st.session_state.get("personalization_enabled", False)
    blocked_reason = st.session_state.get("personalization_blocked_reason")
    if (
        personalization_requested
        and not personalization_applied
        and blocked_reason
        and ui_mode != "Personalized"
    ):
        result.active_scoring_path += " (Personalization unavailable)"

    return result


# ── Helpers ──────────────────────────────────────────────────────────────────


def _check_personalization_gate() -> str | None:
    """Return a blocking reason if personalised mode cannot run, else ``None``."""
    active_profile = st.session_state.get("active_profile")
    ratings = (
        (active_profile or {}).get("ratings", {})
        if isinstance(active_profile, dict)
        else {}
    )
    blocked_reason = st.session_state.get("personalization_blocked_reason")
    user_embedding = st.session_state.get("user_embedding")

    if not active_profile:
        return "Select an Active Profile to use Personalized mode."
    if not isinstance(ratings, dict) or len(ratings) == 0:
        return "Add at least one rating to your active profile to use Personalized mode."
    if not st.session_state.get("personalization_enabled", False):
        return "Enable personalization in the sidebar to run Personalized mode."
    if blocked_reason:
        return blocked_reason
    if user_embedding is None:
        return "Taste profile is not ready yet."
    return None


def _execute_pipeline(
    engine: RecommenderEngine,
    sidebar: Any,
    bundle: dict,
    metadata: pd.DataFrame,
    n_requested: int,
    ranked_hygiene_exclude_ids: set[int],
) -> tuple[list[dict], bool]:
    """Run the scoring pipeline and return ``(recs, personalization_applied)``."""
    _active_profile = st.session_state.get("active_profile")
    _watched_ids: set[int] = set()
    if _active_profile:
        _watched_ids = {int(x) for x in (_active_profile.get("watched_ids", []) or [])}

    _personalization_enabled = st.session_state.get("personalization_enabled", False)
    _personalization_strength = (
        st.session_state.get("personalization_strength", 100) / 100.0
    )
    _user_embedding = st.session_state.get("user_embedding")
    _user_embedding_meta = st.session_state.get("user_embedding_meta", {}) or {}
    _seed_ranking_mode = st.session_state.get("seed_ranking_mode", SEED_RANKING_MODE)
    _mf_model = bundle.get("models", {}).get("mf")
    _mf_stem = bundle.get("models", {}).get("_mf_stem")

    ctx = ScoringContext(
        metadata=metadata,
        bundle=bundle,
        recommender=engine.recommender,
        components=engine.components,
        seed_ids=list(sidebar.selected_seed_ids),
        seed_titles=list(sidebar.selected_seed_titles),
        user_index=0,
        user_embedding=_user_embedding,
        personalization_enabled=_personalization_enabled,
        personalization_strength=_personalization_strength,
        active_profile=_active_profile,
        watched_ids=_watched_ids,
        personalization_blocked_reason=st.session_state.get(
            "personalization_blocked_reason"
        ),
        weights=sidebar.weights,
        seed_ranking_mode=_seed_ranking_mode,
        genre_filter=sidebar.genre_filter,
        type_filter=sidebar.type_filter,
        year_range=sidebar.year_range,
        sort_by=sidebar.sort_by,
        default_sort_for_mode=sidebar.default_sort_for_mode,
        n_requested=n_requested,
        top_n=sidebar.top_n,
        pop_pct_fn=engine.pop_pct_for_anime_id,
        is_in_training_fn=engine.is_in_training,
        mf_model=_mf_model,
        mf_stem=_mf_stem,
        user_embedding_meta=_user_embedding_meta,
        ranked_hygiene_exclude_ids=ranked_hygiene_exclude_ids,
    )

    selected_seed_ids = sidebar.selected_seed_ids
    recs: list[dict] = []
    personalization_applied = False

    # ── Seed-based pipeline ──────────────────────────────────────────────
    if selected_seed_ids:
        seed_result = run_seed_based_pipeline(ctx)
        recs = seed_result.ranked_items
        st.session_state["stage0_diagnostics"] = seed_result.stage0_diagnostics
        st.session_state["stage0_enforcement"] = seed_result.stage0_enforcement
        st.session_state["franchise_cap_diagnostics"] = (
            seed_result.franchise_cap_diagnostics
        )
    else:
        # Seedless fallback: community-baseline when personalization is active
        _mf_mean_user_scores = bundle.get("models", {}).get("mf_mean_user_scores")
        if _personalization_enabled and _mf_mean_user_scores is not None:
            recs = engine.recommender.get_top_n_for_user(
                0,
                n=n_requested,
                weights=sidebar.weights,
                exclude_item_ids=sorted(ranked_hygiene_exclude_ids),
                override_mf_scores=_mf_mean_user_scores,
            )
        else:
            recs = engine.recommender.get_top_n_for_user(
                0,
                n=n_requested,
                weights=sidebar.weights,
                exclude_item_ids=sorted(ranked_hygiene_exclude_ids),
            )

    # ── Personalization overlay (seedless path only) ─────────────────────
    if recs and _personalization_enabled and not selected_seed_ids:
        pers_result = run_personalized_pipeline(ctx)

        if pers_result.personalization_blocked_reason is not None:
            st.session_state["personalization_blocked_reason"] = (
                pers_result.personalization_blocked_reason
            )

        if pers_result.personalization_applied:
            personalization_applied = True
            if _personalization_strength >= 0.99:
                recs = pers_result.ranked_items
            elif _personalization_strength > 0.01:
                recs = blend_personalized_and_seed(
                    personalized_recs=pers_result.ranked_items,
                    seed_recs=recs,
                    personalization_strength=_personalization_strength,
                    n_requested=n_requested,
                    ranked_hygiene_exclude_ids=ranked_hygiene_exclude_ids,
                )

    # Seed pipeline + personalization
    if selected_seed_ids and _personalization_enabled and _user_embedding is not None:
        personalization_applied = True

    # Personalized explanation text
    if recs and _personalization_enabled and _active_profile:
        from src.app.components.explanations import generate_batch_explanations

        recs = generate_batch_explanations(
            recommendations=recs,
            user_profile=_active_profile,
            metadata_df=metadata,
        )

    # Finalise shares, post-filters, trim
    recs = finalize_explanation_shares(recs)
    recs = apply_post_filters(recs, ctx)
    recs = recs[: sidebar.top_n]

    return recs, personalization_applied


def _determine_scoring_path(
    ui_mode: str,
    personalized_gate_reason: str | None,
    engine: RecommenderEngine,
    personalization_applied: bool,
    selected_seed_ids: list[int],
) -> str:
    """Derive a human-readable scoring-path label."""
    if ui_mode == "Personalized" and personalized_gate_reason:
        return "Personalized (Unavailable)"
    if engine.recommender is None or engine.components is None:
        return "Ranked modes disabled"
    if personalization_applied:
        return "Personalized"
    if selected_seed_ids:
        return "Seed-based" if len(selected_seed_ids) == 1 else "Multi-seed"
    return "Seedless"
