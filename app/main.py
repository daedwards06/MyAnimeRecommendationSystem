"""Streamlit application entry point.

Features:
    - Seed-based recommendations (1–5 titles)
    - Optional personalization from profile ratings
    - Browse-by-genre mode (metadata-only)
    - Hybrid weight toggle (balanced vs diversity-emphasized)
    - Top-N recommendations with explanation shares & badges
    - Diversity summary panel
    - Help / FAQ section
"""

from __future__ import annotations

import json
import hashlib
import logging
import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

# Ensure project root is on sys.path when running `streamlit run app/main.py`
ROOT_DIR = Path(__file__).resolve().parents[1]
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

from src.utils import parse_pipe_set

from src.app.artifacts_loader import build_artifacts, ArtifactContractError
from src.app.components.cards import render_card, render_card_grid
from src.app.components.diversity import render_diversity_panel
from src.app.components.help import render_help_panel
from src.app.components.skeletons import render_card_skeleton  # retained import (may repurpose later)
from src.app.components.instructions import render_onboarding
from src.app.score_semantics import has_match_score
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids
from src.app.franchise_cap import apply_franchise_cap
from src.app.constants import (
    STAGE0_META_MIN_GENRE_OVERLAP,
    STAGE0_META_MIN_THEME_OVERLAP,
    SEED_RANKING_MODE,
    FRANCHISE_TITLE_OVERLAP_THRESHOLD,
    FRANCHISE_CAP_TOP20,
    FRANCHISE_CAP_TOP50,
    STAGE0_NEURAL_TOPK,
    STAGE0_POPULARITY_BACKFILL,
    STAGE0_POOL_CAP,
    STAGE0_ENFORCEMENT_BUFFER,
)
from src.app.stage0_candidates import build_stage0_seed_candidate_pool
from src.app.scoring_pipeline import (
    ScoringContext,
    PipelineResult,
    run_seed_based_pipeline,
    run_personalized_pipeline,
    run_browse_pipeline,
    blend_personalized_and_seed,
    apply_post_filters,
    finalize_explanation_shares,
)

# Configure logging: INFO level by default, DEBUG if env var is set
log_level = logging.DEBUG if os.getenv("DEBUG_LOGGING") else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
from src.app.metadata_features import (
    METADATA_AFFINITY_COLD_START_COEF,
    METADATA_AFFINITY_TRAINED_COEF,
    METADATA_AFFINITY_PERSONALIZED_COEF,
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
    personalized_synopsis_tfidf_bonus_for_candidate,
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
    personalized_synopsis_embeddings_bonus_for_candidate,
)
from src.app.synopsis_neural_embeddings import (
    compute_seed_similarity_map as compute_seed_neural_similarity_map,
    SYNOPSIS_NEURAL_MIN_SIM,
    SYNOPSIS_NEURAL_HIGH_SIM_THRESHOLD,
    SYNOPSIS_NEURAL_OFFTYPE_HIGH_SIM_PENALTY,
    synopsis_neural_bonus_for_candidate,
    synopsis_neural_penalty_for_candidate,
)
from src.app.stage2_overrides import content_first_final_score, relax_off_type_penalty, should_use_content_first
from src.app.theme import get_theme
from src.app.constants import (
    DEFAULT_TOP_N,
    PERSONAS_JSON,
    FORCE_NEURAL_TOPK,
    FORCE_NEURAL_MIN_SIM,
    CONTENT_FIRST_ALPHA,
)

from src.app.stage1_shortlist import build_stage1_shortlist, force_neural_enabled, select_forced_neural_pairs
from src.app.recommender import (
    HybridComponents,
    HybridRecommender,
    choose_weights,
    compute_component_shares,
    compute_dense_similarity,
)
from src.app.search import fuzzy_search, normalize_title
from src.app.badges import badge_payload
from src.app.explanations import format_explanation
from src.app.profiling import latency_timer
from src.app.semantic_admission import (
    STAGE1_DEMO_SHOUNEN_MIN_SIM_NEURAL,
    stage1_semantic_admission,
    theme_overlap_ratio,
)
from src.app.diversity import (
    compute_popularity_percentiles,
    coverage,
    genre_exposure_ratio,
    average_novelty,
    build_user_genre_hist,
)


@st.cache_resource(show_spinner=False)
def init_bundle():
    return build_artifacts()


@st.cache_data(show_spinner=False)
def load_personas(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


IMPORT_LIGHT = bool(os.environ.get("APP_IMPORT_LIGHT"))


# Removed _parse_str_set - now using canonical version from src.utils.parsing


def _render_artifact_load_failure(err: Exception) -> None:
    st.error("Required artifacts are missing or invalid. Ranked modes are disabled until this is fixed.")
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


if IMPORT_LIGHT:
    # Lightweight import mode for tests: avoid heavy artifact loading.
    # IMPORTANT: recommendations must not run in this mode (no placeholders).
    bundle = {
        "metadata": pd.DataFrame(
            {"anime_id": [1], "title_display": ["Dummy"], "genres": [""], "synopsis_snippet": [""]}
        ),
        "models": {},
        "explanations": {},
        "diversity": {},
        "_import_light": True,
    }
else:
    try:
        bundle = init_bundle()
    except Exception as e:  # noqa: BLE001
        _render_artifact_load_failure(e)

metadata: pd.DataFrame = bundle["metadata"]
personas = load_personas(PERSONAS_JSON)

st.set_page_config(page_title="Anime Explorer", layout="wide", page_icon="🎬")
theme = get_theme()

# ---------------------------------------------------------------------------
# Phase 3 / Chunk 2: Choose-a-mode gating (progressive disclosure)
# Single top-level mode: Personalized / Seed-based / Browse.
# This is UI-only routing; scoring behavior and score semantics remain unchanged.
#
# NOTE: Do not pre-set st.session_state["ui_mode"] here.
# Streamlit widgets manage their own key; pre-setting can trigger:
# "The widget with key 'ui_mode' was created with a default value but also had its value set via the Session State API."
# ---------------------------------------------------------------------------
if "_ui_mode_prev" not in st.session_state:
    st.session_state["_ui_mode_prev"] = st.session_state.get("ui_mode")
if "_personalization_autoset" not in st.session_state:
    st.session_state["_personalization_autoset"] = False

# Custom CSS for modern, polished aesthetic
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    h1 {
        color: #1E1E1E;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #2C3E50;
        font-weight: 600;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Card improvements */
    .stMarkdown {
        line-height: 1.6;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Genre pill button styling - make them look like badges */
    button[kind="secondary"] {
        background-color: #ECF0F1 !important;
        color: #34495E !important;
        border: none !important;
        padding: 4px 12px !important;
        font-size: 0.8rem !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        min-height: 28px !important;
        height: 28px !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #3498DB !important;
        color: white !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3) !important;
    }
    
    /* Remove extra spacing */
    .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #34495E;
    }
    
    /* Caption text */
    .css-1629p8f, [data-testid="stCaptionContainer"] {
        color: #7F8C8D;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

_ui_mode_for_header = str(st.session_state.get("ui_mode", "Seed-based"))
if _ui_mode_for_header == "Browse":
    st.title("🎬 Anime Explorer")
    st.markdown(
        "<p style='color: #7F8C8D; font-size: 1.1rem; margin-top: -10px;'>Explore the catalog by genre, type, and year (metadata-only)</p>",
        unsafe_allow_html=True,
    )
elif _ui_mode_for_header == "Personalized":
    st.title("🎬 Personalized Anime Recommendations")
    st.markdown(
        "<p style='color: #7F8C8D; font-size: 1.1rem; margin-top: -10px;'>Ranked using your rated history (shows ‘unavailable’ when it can’t run)</p>",
        unsafe_allow_html=True,
    )
else:
    st.title("🎬 Seed-based Anime Recommendations")
    st.markdown(
        "<p style='color: #7F8C8D; font-size: 1.1rem; margin-top: -10px;'>Ranked from 1–5 seed titles using Match score (relative)</p>",
        unsafe_allow_html=True,
    )

if os.environ.get("APP_IMPORT_LIGHT"):
    st.warning("Lightweight import mode is active (APP_IMPORT_LIGHT=1). Images and full metadata may be unavailable. Restart without this flag to see thumbnails.")
render_onboarding(ui_mode=_ui_mode_for_header)

# Sidebar Controls ---------------------------------------------------------
st.sidebar.header("Controls")

# Top-level mode selector (single control)
prev_mode = st.session_state.get("_ui_mode_prev")
_ui_mode_options = ["Personalized", "Seed-based", "Browse"]
_ui_mode_current = st.session_state.get("ui_mode")
_legacy_browse = bool(st.session_state.get("browse_mode", False))
if _ui_mode_current in _ui_mode_options:
    _ui_mode_index = _ui_mode_options.index(str(_ui_mode_current))
else:
    _ui_mode_index = 2 if _legacy_browse else 1

ui_mode = st.sidebar.radio(
    "Choose your mode",
    _ui_mode_options,
    index=_ui_mode_index,
    key="ui_mode",
    help=(
        "Personalized: ranked results using your rated profile history. "
        "Seed-based: ranked results anchored to 1–5 seed titles. "
        "Browse: filters/sorts catalog metadata only (no ranking)."
    ),
)

# When the mode changes, force a rerun so the main-area branch and prompts
# reflect the new mode immediately.
mode_changed = prev_mode is not None and ui_mode != prev_mode
st.session_state["_ui_mode_prev"] = ui_mode

# Derive legacy flags used throughout the app.
browse_mode = ui_mode == "Browse"
st.session_state["browse_mode"] = browse_mode

# Prevent misleading personalization in non-personalized modes.
if ui_mode != "Personalized":
    st.session_state["personalization_enabled"] = False
    st.session_state["_personalization_autoset"] = False
elif prev_mode != "Personalized":
    # Allow auto-enable when entering Personalized mode.
    st.session_state["_personalization_autoset"] = False

if mode_changed:
    st.rerun()

if st.sidebar.button("Reload artifacts"):
    try:
        init_bundle.clear()  # type: ignore[attr-defined]
    except Exception:
        st.sidebar.warning("Could not clear cache; please restart the app.")
    st.rerun()
persona_labels = [p["label"] for p in personas] if personas else []
params = st.query_params

def _qp_get(key: str, default):
    val = params.get(key, default)
    # Streamlit's new query_params may return str or list; normalize
    if isinstance(val, list):
        return val[0] if val else default
    return val

# Initialize session state defaults
for key, default in {
    "query": _qp_get("q", ""),
    "weight_mode": _qp_get("wm", "Balanced"),
    "top_n": int(_qp_get("n", DEFAULT_TOP_N)),
    "sort_by": _qp_get("sort", "Match score"),
    "browse_mode": bool(st.session_state.get("browse_mode", False)),
    "genre_filter": [],
    "type_filter": [],
    "year_min": 1960,
    "year_max": 2025,
    "view_mode": "list",
    "selected_seed_ids": [],
    "selected_seed_titles": [],
    "_first_load_done": False,
    "_default_seed_active": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================================
# FIRST-RUN EXPERIENCE: Auto-populate default seed
# ============================================================================
# On first load, auto-set Fullmetal Alchemist: Brotherhood as the default seed
# This ensures portfolio reviewers see recommendations immediately.
if (
    not st.session_state.get("_first_load_done", False)
    and not st.session_state.get("selected_seed_ids")
    and str(st.session_state.get("ui_mode", "Seed-based")) == "Seed-based"
    and not IMPORT_LIGHT
):
    # Find Fullmetal Alchemist: Brotherhood in metadata
    _default_title = "Fullmetal Alchemist: Brotherhood"
    _fmab_rows = metadata[metadata["title_display"] == _default_title]
    if not _fmab_rows.empty:
        _fmab_id = int(_fmab_rows.iloc[0]["anime_id"])
        st.session_state["selected_seed_ids"] = [_fmab_id]
        st.session_state["selected_seed_titles"] = [_default_title]
        st.session_state["_default_seed_active"] = True
    st.session_state["_first_load_done"] = True

# ============================================================================
# SIDEBAR: USER PROFILE (Section 1 - Top Priority)
# ============================================================================
st.sidebar.markdown("### 👤 User Profile")

from src.data.user_profiles import list_profiles, load_profile, save_profile, get_profile_summary
from src.data.mal_parser import parse_mal_export, get_mal_export_summary

# Initialize session state for profile
if "active_profile" not in st.session_state:
    st.session_state["active_profile"] = None
if "parsed_mal_data" not in st.session_state:
    st.session_state["parsed_mal_data"] = None

# Profile Selector
available_profiles = list_profiles()
profile_options = ["(none)"] + available_profiles

current_selection = "(none)"
if st.session_state["active_profile"]:
    current_selection = st.session_state["active_profile"].get("username", "(none)")
    if current_selection not in profile_options:
        current_selection = "(none)"

selected_profile = st.sidebar.selectbox(
    "Active Profile",
    options=profile_options,
    index=profile_options.index(current_selection) if current_selection in profile_options else 0,
    help="Select a profile to hide already-watched titles from results",
    label_visibility="collapsed"
)

# Load profile when selection changes
if selected_profile != "(none)" and (not st.session_state["active_profile"] or st.session_state["active_profile"].get("username") != selected_profile):
    profile_data = load_profile(selected_profile)
    if profile_data:
        st.session_state["active_profile"] = profile_data
        st.rerun()
elif selected_profile == "(none)" and st.session_state["active_profile"]:
    st.session_state["active_profile"] = None
    st.rerun()

# Show profile stats or info message
if st.session_state["active_profile"]:
    profile = st.session_state["active_profile"]
    watched_count = len(profile.get("watched_ids", []))
    avg_rating = profile.get("stats", {}).get("avg_rating", 0)
    
    st.sidebar.success(f"✓ **{profile['username']}** – {watched_count} watched")
    
    # Show rating stats
    ratings_count = len(profile.get("ratings", {}))
    if ratings_count > 0:
        st.sidebar.caption(f"⭐ {ratings_count} ratings • Avg: {avg_rating:.1f}/10")
        
        # Show rating distribution (simple display)
        if st.sidebar.checkbox("📊 Rating distribution", key="show_rating_dist", value=False):
            ratings = profile.get("ratings", {})
            
            # Count by rating bucket
            distribution = {"10": 0, "9": 0, "8": 0, "7": 0, "6": 0, "5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
            for rating in ratings.values():
                distribution[str(rating)] = distribution.get(str(rating), 0) + 1
            
            # Display as simple bars
            for rating in ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]:
                count = distribution[rating]
                if count > 0:
                    bar = "█" * min(count, 20)
                    st.sidebar.caption(f"{rating}/10: {bar} ({count})")
    elif avg_rating > 0:
        st.sidebar.caption(f"Avg Rating: {avg_rating:.1f}/10")
    
    # Import MAL (collapsed by default)
    with st.sidebar.expander("📥 Import from MAL", expanded=False):
        st.caption("Update your watchlist & ratings")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload MAL XML Export",
            type=["xml"],
            help="Export your list from MyAnimeList.net",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # Show preview button
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Preview", use_container_width=True):
                    try:
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        summary = get_mal_export_summary(tmp_path)
                        st.session_state["mal_summary"] = summary
                        st.session_state["mal_tmp_path"] = tmp_path
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col2:
                if st.button("🔄 Parse", use_container_width=True):
                    try:
                        if "mal_tmp_path" not in st.session_state:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name
                        else:
                            tmp_path = st.session_state["mal_tmp_path"]
                        
                        with st.spinner("Parsing..."):
                            parsed_data = parse_mal_export(
                                xml_path=tmp_path,
                                metadata_df=metadata,
                                include_statuses={'Completed', 'Watching', 'On-Hold'},
                                use_default_for_unrated=True,
                                default_rating=7.0
                            )
                            st.session_state["parsed_mal_data"] = parsed_data
                        
                        st.success(f"✓ Parsed {len(parsed_data['watched_ids'])} anime")
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Show parsed data and save option
        if st.session_state["parsed_mal_data"]:
            parsed = st.session_state["parsed_mal_data"]
            
            st.caption(f"✓ {parsed['stats']['total_watched']} matched • {parsed['stats']['rated_count']} rated")
            
            if parsed['unmatched']:
                st.warning(f"⚠️ {len(parsed['unmatched'])} unmatched")
            
            username_input = st.text_input(
                "Profile Name",
                value=parsed.get('username', 'my_profile'),
                help="Choose a name for this profile"
            )
            
            if st.button("💾 Save Profile", type="primary", use_container_width=True):
                try:
                    save_profile(username_input, parsed)
                    st.session_state["active_profile"] = load_profile(username_input)
                    st.session_state["parsed_mal_data"] = None
                    if "mal_summary" in st.session_state:
                        del st.session_state["mal_summary"]
                    if "mal_tmp_path" in st.session_state:
                        import os
                        try:
                            os.unlink(st.session_state["mal_tmp_path"])
                        except:
                            pass
                        del st.session_state["mal_tmp_path"]
                    st.success(f"✓ Saved as '{username_input}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
else:
    st.sidebar.info("💡 Import your MAL watchlist to hide watched anime")
    
    # Import MAL (expanded when no profile)
    with st.sidebar.expander("📥 Import from MAL", expanded=True):
        st.caption("Get started by importing your watchlist")
        
        uploaded_file = st.file_uploader(
            "Upload MAL XML Export",
            type=["xml"],
            help="Export from MyAnimeList.net",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Preview", use_container_width=True, key="preview_no_profile"):
                    try:
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        summary = get_mal_export_summary(tmp_path)
                        st.session_state["mal_summary"] = summary
                        st.session_state["mal_tmp_path"] = tmp_path
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col2:
                if st.button("🔄 Parse", use_container_width=True, key="parse_no_profile"):
                    try:
                        if "mal_tmp_path" not in st.session_state:
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name
                        else:
                            tmp_path = st.session_state["mal_tmp_path"]
                        
                        with st.spinner("Parsing..."):
                            parsed_data = parse_mal_export(
                                xml_path=tmp_path,
                                metadata_df=metadata,
                                include_statuses={'Completed', 'Watching', 'On-Hold'},
                                use_default_for_unrated=True,
                                default_rating=7.0
                            )
                            st.session_state["parsed_mal_data"] = parsed_data
                        
                        st.success(f"✓ Parsed {len(parsed_data['watched_ids'])} anime")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        if st.session_state["parsed_mal_data"]:
            parsed = st.session_state["parsed_mal_data"]
            st.caption(f"✓ {parsed['stats']['total_watched']} matched • {parsed['stats']['rated_count']} rated")
            
            username_input = st.text_input(
                "Profile Name",
                value=parsed.get('username', 'my_profile'),
                key="username_no_profile"
            )
            
            if st.button("💾 Save Profile", type="primary", use_container_width=True, key="save_no_profile"):
                try:
                    save_profile(username_input, parsed)
                    st.session_state["active_profile"] = load_profile(username_input)
                    st.session_state["parsed_mal_data"] = None
                    st.success(f"✓ Saved as '{username_input}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

# ============================================================================
# SIDEBAR: PERSONALIZATION (Section 2 - Separate from Profile)
# ============================================================================
st.sidebar.markdown("---")
ui_mode = str(st.session_state.get("ui_mode", "Seed-based"))
st.sidebar.markdown("### 🎯 Personalization")


def _ratings_signature(ratings_dict: dict) -> str:
    """Stable signature for rating dict (for cache invalidation)."""
    items = sorted((int(k), float(v)) for k, v in (ratings_dict or {}).items())
    payload = json.dumps(items, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# User genre history (for novelty) -----------------------------------------
if "user_genre_hist" not in st.session_state:
    st.session_state["user_genre_hist"] = {}
if "user_genre_hist_meta" not in st.session_state:
    st.session_state["user_genre_hist_meta"] = {}

if st.session_state.get("active_profile"):
    _ratings = st.session_state["active_profile"].get("ratings", {})
    _ratings_sig = _ratings_signature(_ratings)
    _profile_username = (st.session_state.get("active_profile") or {}).get("username")
    _cached = st.session_state.get("user_genre_hist_meta") or {}
    _needs_refresh = (
        not isinstance(st.session_state.get("user_genre_hist"), dict)
        or _cached.get("ratings_sig") != _ratings_sig
        or _cached.get("profile_username") != _profile_username
    )
    if _needs_refresh:
        st.session_state["user_genre_hist"] = build_user_genre_hist(_ratings, metadata)
        st.session_state["user_genre_hist_meta"] = {
            "ratings_sig": _ratings_sig,
            "profile_username": _profile_username,
        }
else:
    st.session_state["user_genre_hist"] = {}
    st.session_state["user_genre_hist_meta"] = {}

# Initialize personalization state
if "personalization_enabled" not in st.session_state:
    st.session_state["personalization_enabled"] = False
if "personalization_strength" not in st.session_state:
    st.session_state["personalization_strength"] = 100
if "user_embedding" not in st.session_state:
    st.session_state["user_embedding"] = None
if "user_embedding_meta" not in st.session_state:
    st.session_state["user_embedding_meta"] = {}
if "personalization_blocked_reason" not in st.session_state:
    st.session_state["personalization_blocked_reason"] = None

# Check if profile has ratings
profile_has_ratings = False
if st.session_state["active_profile"]:
    ratings = st.session_state["active_profile"].get("ratings", {})
    profile_has_ratings = len(ratings) > 0

# Track personalized-mode gating reason so we can avoid silent fallback.
personalized_mode_blocked_reason: str | None = None

if ui_mode != "Personalized":
    # Progressive disclosure: personalization is not relevant outside Personalized mode.
    with st.sidebar.expander("🎯 Personalization (Personalized mode only)", expanded=False):
        st.caption("Switch to **Personalized** mode to use rated history.")
        st.caption("Novelty remains **NA** without rated profile history.")
    st.session_state["personalization_enabled"] = False
    st.session_state["personalization_blocked_reason"] = None
else:
    # Personalized mode: require rated history and avoid misleading fallbacks.
    if not st.session_state.get("active_profile"):
        personalized_mode_blocked_reason = "No active profile selected."
        st.sidebar.warning("Personalized mode unavailable: select a profile")
        st.sidebar.caption("Fix: Choose an **Active Profile** (top of sidebar) and add at least one rating.")
        st.session_state["personalization_enabled"] = False
        st.session_state["personalization_blocked_reason"] = "No active profile selected."
    elif not profile_has_ratings:
        personalized_mode_blocked_reason = "Active profile has no ratings."
        st.sidebar.warning("Personalized mode unavailable: no ratings")
        st.sidebar.caption("Fix: Add at least one rating (use the in-card rating buttons after selecting a profile).")
        st.session_state["personalization_enabled"] = False
        st.session_state["personalization_blocked_reason"] = "No ratings in active profile."
    else:
        # Auto-enable personalization when entering Personalized mode (keeps ≤2 actions from cold start).
        if not st.session_state.get("personalization_enabled", False) and not st.session_state.get("_personalization_autoset", False):
            st.session_state["personalization_enabled"] = True
            st.session_state["_personalization_autoset"] = True

        personalization_enabled = st.sidebar.checkbox(
            "Enable personalization",
            value=bool(st.session_state.get("personalization_enabled", False)),
            help=(
                f"Applies only in Personalized mode. Uses your {len(ratings)} ratings to rerank results. "
                "If personalization is unavailable (no ratings / no MF overlap / missing model), the UI says why and shows no fallback results."
            ),
        )
        st.session_state["personalization_enabled"] = personalization_enabled

        if not personalization_enabled:
            personalized_mode_blocked_reason = "Personalization is disabled."
            st.sidebar.info("Enable personalization to run Personalized mode")
        else:
            # Personalization strength slider
            personalization_strength = st.sidebar.slider(
                "Strength",
                min_value=0,
                max_value=100,
                value=int(st.session_state.get("personalization_strength", 100)),
                help=(
                    "Controls how strongly your rated-history signal influences ranking. "
                    "0% = seed-based only, 100% = fully personalized. Applied only when personalization is enabled and available."
                ),
                format="%d%%",
            )
            st.session_state["personalization_strength"] = personalization_strength

            # Generate / refresh user embedding when inputs change.
        # Single source of truth for MF model: bundle['models']['mf'] selected by artifacts_loader.
        mf_model = bundle.get("models", {}).get("mf")
        mf_stem = bundle.get("models", {}).get("_mf_stem")
        profile_username = (
            st.session_state.get("active_profile", {}) or {}
        ).get("username")
        ratings_sig = _ratings_signature(ratings)
        cached = st.session_state.get("user_embedding_meta", {}) or {}

        needs_refresh = (
            st.session_state["user_embedding"] is None
            or cached.get("ratings_sig") != ratings_sig
            or cached.get("mf_stem") != mf_stem
            or cached.get("profile_username") != profile_username
        )

        if mf_model is None:
            st.session_state["user_embedding"] = None
            st.session_state["user_embedding_meta"] = {
                "ratings_sig": ratings_sig,
                "mf_stem": mf_stem,
                "profile_username": profile_username,
            }
            st.session_state["personalization_blocked_reason"] = (
                "MF model is not available (artifact load/selection failed)."
            )
            st.sidebar.error("Personalization unavailable: MF model missing")
        elif needs_refresh:
            with st.spinner("Generating taste profile..."):
                from src.models.user_embedding import generate_user_embedding
                try:
                    user_embedding = generate_user_embedding(
                        ratings_dict=ratings,
                        mf_model=mf_model,
                        method="weighted_average",
                        normalize=True,
                    )
                except Exception as e:  # noqa: BLE001
                    st.session_state["user_embedding"] = None
                    st.session_state["personalization_blocked_reason"] = (
                        f"Failed generating user embedding: {e}"
                    )
                    st.sidebar.error("Personalization unavailable: embedding failed")
                else:
                    # Guard against zero/near-zero embeddings (typically means no overlap with training set).
                    try:
                        emb_norm = float(np.linalg.norm(user_embedding))
                    except Exception:
                        emb_norm = 0.0
                    if emb_norm <= 1e-8:
                        st.session_state["user_embedding"] = None
                        st.session_state["personalization_blocked_reason"] = (
                            "Your rated items do not overlap the MF model training set."
                        )
                        st.sidebar.warning("Personalization unavailable: no MF overlap")
                    else:
                        st.session_state["user_embedding"] = user_embedding
                        st.session_state["personalization_blocked_reason"] = None
                        st.sidebar.success(f"✓ Profile ready ({len(ratings)} ratings)")

                st.session_state["user_embedding_meta"] = {
                    "ratings_sig": ratings_sig,
                    "mf_stem": mf_stem,
                    "profile_username": profile_username,
                }
        else:
            st.sidebar.caption(f"✓ Using {len(ratings)} ratings")
        
            # Taste profile visualization
            if st.sidebar.checkbox("🎨 View Taste Profile", key="show_taste_profile", value=False):
                from src.app.components.taste_profile import render_taste_profile_panel
                render_taste_profile_panel(st.session_state["active_profile"], metadata)

# ============================================================================
# SIDEBAR: SEARCH & SEEDS (Section 3 - Discovery Tools)
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Search & Seeds")

show_seeds_controls = ui_mode in {"Seed-based", "Personalized"}

if not show_seeds_controls:
    with st.sidebar.expander("🔍 Search & Seeds (not used in Browse)", expanded=False):
        st.caption("Browse mode uses genre/type/year filters only.")
    selected_titles = []
    query = ""
    weight_mode = str(st.session_state.get("weight_mode", "Balanced"))
else:
    # Searchable title dropdown - prefer English titles
    def get_display_title(row):
        """Get best display title preferring English"""
        title_eng = row.get("title_english")
        if title_eng and isinstance(title_eng, str) and title_eng.strip():
            return title_eng
        title_disp = row.get("title_display")
        if title_disp and isinstance(title_disp, str) and title_disp.strip():
            return title_disp
        return None

    # Create title mapping: display_title -> anime_id for lookup
    title_to_id = {}
    for _, row in metadata.iterrows():
        title = get_display_title(row)
        if title:
            title_to_id[title] = int(row["anime_id"])

    available_titles = sorted(title_to_id.keys())

    # Multi-select for seeds (max 5)
    current_seed_titles = st.session_state.get("selected_seed_titles", [])
    selected_titles = st.sidebar.multiselect(
        "Search Titles (1-5 seeds)",
        options=available_titles,
        default=current_seed_titles,
        max_selections=5,
        help=(
            "Select 1–5 seed titles. Ranked results are anchored to these seeds and show Match score (relative) for the current run."
        ),
    )

    # Update query for backward compatibility
    query = selected_titles[0] if selected_titles else ""

    weight_mode = st.sidebar.radio(
        "Hybrid Weights",
        ["Balanced", "Diversity"],
        index=(0 if st.session_state.get("weight_mode") != "Diversity" else 1),
        horizontal=True,
        help=(
            "Changes how the ranking blends signals (e.g., similarity vs popularity emphasis). "
            "Useful when you want broader discovery; most noticeable in Seed-based and Personalized modes."
        ),
    )

    # Phase 5 follow-up: Seed-based ranking goal (Completion vs Discovery).
    # Keep Browse unchanged; only show when Seed-based is the active top-level mode.
    if str(st.session_state.get("ui_mode", "Seed-based")) == "Seed-based":
        _goal_opts = [
            "Goal: Completion (more from franchise)",
            "Goal: Discovery (similar vibes)",
        ]
        _mode_default = str(st.session_state.get("seed_ranking_mode", SEED_RANKING_MODE) or SEED_RANKING_MODE)
        _mode_default = _mode_default.strip().lower()
        _goal_index = 0 if _mode_default != "discovery" else 1
        _goal_label = st.sidebar.radio(
            "Seed goal",
            _goal_opts,
            index=_goal_index,
            horizontal=False,
            key="seed_goal_ui",
            help=(
                "Completion lets sequels/spin-offs surface freely. "
                "Discovery limits franchise dominance in top results using a deterministic title-overlap cap."
            ),
        )
        st.session_state["seed_ranking_mode"] = "discovery" if "Discovery" in str(_goal_label) else "completion"

# ============================================================================
# SIDEBAR: FILTERS & DISPLAY (Section 4)
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Filters & Display")

# Top-N applies to both ranked results and Browse.
top_n = st.sidebar.slider("Top N", 5, 30, int(st.session_state.get("top_n", DEFAULT_TOP_N)))
st.session_state["top_n"] = top_n

# Mode-derived browse flag (single source of truth: Choose your mode)
browse_mode = bool(st.session_state.get("browse_mode", False))

if browse_mode:
    st.sidebar.info("💡 Browse: select at least one genre")

default_sort_for_mode = "MAL Score" if browse_mode else "Match score"
sort_options = ["MAL Score", "Year (Newest)", "Year (Oldest)", "Popularity"] if browse_mode else [
    "Match score",
    "MAL Score",
    "Year (Newest)",
    "Year (Oldest)",
    "Popularity",
]
current_sort = st.session_state.get("sort_by", default_sort_for_mode)
if current_sort not in sort_options:
    current_sort = default_sort_for_mode
sort_by = st.sidebar.selectbox(
    "Sort by",
    sort_options,
    index=sort_options.index(current_sort),
)

# Get unique genres from metadata for filter
all_genres = set()
for genres_val in metadata["genres"].dropna():
    # Handle both string (pipe-delimited) and array formats
    if isinstance(genres_val, str):
        all_genres.update([g.strip() for g in genres_val.split("|") if g.strip()])
    elif hasattr(genres_val, '__iter__') and not isinstance(genres_val, str):
        # Handle numpy arrays, lists, etc.
        all_genres.update([str(g).strip() for g in genres_val if g])
genre_options = sorted(list(all_genres))

genre_filter = st.sidebar.multiselect(
    "Filter by Genre",
    options=genre_options,
    default=st.session_state.get("genre_filter", []),
    help=(
        "Applies in all modes. In Browse, select at least one genre to see titles."
    ),
)

# Get unique types from metadata for filter
all_types = set()
for type_val in metadata["type"].dropna() if "type" in metadata.columns else []:
    if type_val and isinstance(type_val, str):
        all_types.add(type_val.strip())
type_options = sorted(list(all_types)) if all_types else ["TV", "Movie", "OVA", "Special", "ONA", "Music"]

type_filter = st.sidebar.multiselect(
    "Filter by Type",
    options=type_options,
    default=st.session_state.get("type_filter", []),
    help="Applies in all modes to the displayed list (TV, Movie, OVA, etc.)",
)

year_range = st.sidebar.slider(
    "Release Year Range",
    min_value=1960,
    max_value=2025,
    value=(st.session_state.get("year_min", 1960), st.session_state.get("year_max", 2025)),
    help="Applies in all modes to the displayed list",
)

st.session_state["sort_by"] = sort_by
st.session_state["genre_filter"] = genre_filter
st.session_state["type_filter"] = type_filter
st.session_state["year_min"] = year_range[0]
st.session_state["year_max"] = year_range[1]

# View mode toggle
view_mode = st.sidebar.radio(
    "📊 View Mode",
    ["List", "Grid"],
    index=0 if st.session_state.get("view_mode", "list") == "list" else 1,
    horizontal=True,
    help="Switch between list and grid layout"
)
st.session_state["view_mode"] = "list" if view_mode == "List" else "grid"

# Clear filters button
if genre_filter or type_filter or year_range[0] > 1960 or year_range[1] < 2025 or sort_by != default_sort_for_mode:
    if st.sidebar.button("🔄 Reset Filters", help="Clear all filters and reset to defaults"):
        st.session_state["sort_by"] = default_sort_for_mode
        st.session_state["genre_filter"] = []
        st.session_state["type_filter"] = []
        st.session_state["year_min"] = 1960
        st.session_state["year_max"] = 2025
        st.rerun()

# Performance Metrics
with st.sidebar.expander("⚡ Performance", expanded=False):
    from src.app.profiling import get_last_timing
    try:
        last_timing = get_last_timing()
        if last_timing:
            latency_ms = last_timing.get("recommendations", 0) * 1000
            status_color = "#27AE60" if latency_ms < 250 else "#E67E22" if latency_ms < 500 else "#E74C3C"
            st.markdown(f"""
            <div style='background: #F8F9FA; border-radius: 6px; padding: 12px; margin-bottom: 8px;'>
                <p style='margin: 0; font-size: 0.85rem; color: #7F8C8D;'>Inference Time</p>
                <p style='margin: 0; font-size: 1.3rem; font-weight: 600; color: {status_color};'>{latency_ms:.0f}ms</p>
            </div>
            """, unsafe_allow_html=True)
        else:
                st.caption(
                    "No timing data yet — run a ranked mode first" if not browse_mode
                    else "No timing data yet — timing is shown for ranked modes (Seed-based / Personalized)"
                )
    except Exception:
        st.caption(
            "Run a ranked mode to see metrics" if not browse_mode
            else "Timing is shown for ranked modes (Seed-based / Personalized)"
        )
    
    import sys
    if hasattr(bundle, '__sizeof__'):
        mem_mb = sys.getsizeof(bundle) / (1024 * 1024)
        st.markdown(f"""
        <div style='background: #F8F9FA; border-radius: 6px; padding: 12px;'>
            <p style='margin: 0; font-size: 0.85rem; color: #7F8C8D;'>Bundle Size</p>
            <p style='margin: 0; font-size: 1.3rem; font-weight: 600; color: #3498DB;'>{mem_mb:.1f}MB</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# SIDEBAR: HELP & FAQ (Section 5 - Bottom)
# ============================================================================
st.sidebar.markdown("---")
with st.sidebar.expander("💡 Quick Guide", expanded=False):
    st.markdown("""
    <div style='font-size: 0.9rem; line-height: 1.8;'>
    1️⃣ <b>Choose your mode</b> – Personalized / Seed-based / Browse<br>
    2️⃣ <b>Seed-based</b> – Pick 1–5 seeds (or use the sample buttons)<br>
    3️⃣ <b>Browse</b> – Pick ≥1 genre (filters apply; metadata-only)<br>
    4️⃣ <b>Personalized</b> – Select a rated profile (no ratings → unavailable)<br>
    5️⃣ <b>Refine</b> – Filters (and hybrid weights in ranked modes)
    </div>
    """, unsafe_allow_html=True)

# Persist updates
st.session_state["query"] = query
st.session_state["weight_mode"] = weight_mode
st.session_state["top_n"] = top_n
st.query_params.update({"q": query, "wm": weight_mode, "n": str(top_n)})

weights = choose_weights(weight_mode)

# Seed selection indicator & handler --------------------------------------
selected_seed_ids: list[int] = []
selected_seed_titles: list[str] = []
if show_seeds_controls:
    # Convert selected titles to IDs
    for title in selected_titles:
        aid = title_to_id.get(title)
        if aid:
            selected_seed_ids.append(aid)
            selected_seed_titles.append(title)

# Update session state
st.session_state["selected_seed_ids"] = selected_seed_ids
st.session_state["selected_seed_titles"] = selected_seed_titles

# Prominent seed indicator
if selected_seed_ids and selected_seed_titles:
    if len(selected_seed_titles) == 1:
        st.sidebar.success(f"🎯 **Active Seed**: {selected_seed_titles[0]}")
    else:
        st.sidebar.success(f"🎯 **Active Seeds** ({len(selected_seed_titles)}):")
        for title in selected_seed_titles:
            st.sidebar.caption(f"• {title}")
    if st.sidebar.button("✖ Clear All Seeds", key="clear_seed"):
        st.session_state["selected_seed_ids"] = []
        st.session_state["selected_seed_titles"] = []
        st.session_state["_default_seed_active"] = False
        st.rerun()
else:
    if show_seeds_controls:
        # Sample search suggestions
        st.sidebar.info("💡 **Try these popular titles:**")
        sample_titles = ["Steins;Gate", "Cowboy Bebop", "Death Note", "Fullmetal Alchemist: Brotherhood"]
        available_samples = [t for t in sample_titles if t in available_titles]
        if available_samples:
            cols = st.sidebar.columns(2)
            for i, sample in enumerate(available_samples[:4]):
                with cols[i % 2]:
                    if st.button(sample, key=f"sample_{i}", use_container_width=True):
                        # Add to existing seeds (up to max 5)
                        current_ids = st.session_state.get("selected_seed_ids", [])
                        current_titles = st.session_state.get("selected_seed_titles", [])
                        aid = title_to_id.get(sample)
                        if aid and sample not in current_titles and len(current_ids) < 5:
                            current_ids.append(aid)
                            current_titles.append(sample)
                            st.session_state["selected_seed_ids"] = current_ids
                            st.session_state["selected_seed_titles"] = current_titles
                            st.session_state["_default_seed_active"] = False
                            st.rerun()


# Hybrid recommender initialization (artifact-backed; no placeholders) -----
recommender: HybridRecommender | None = None
components: HybridComponents | None = None
pop_percentile_by_anime_id: dict[int, float] | None = None


def _pop_pct_for_anime_id(anime_id: int) -> float:
    """Return popularity percentile for display; defaults to neutral when unavailable."""
    if not pop_percentile_by_anime_id:
        return 0.5
    try:
        return float(pop_percentile_by_anime_id.get(int(anime_id), 0.5))
    except Exception:
        return 0.5


def _is_in_training(anime_id: int) -> bool:
    """Cold-start detection based on MF factor availability.

    Rule: an item is in training iff anime_id is present in mf_model.item_to_index.
    """
    if IMPORT_LIGHT:
        return False

    local_mf_model = globals().get("mf_model")
    if local_mf_model is None:
        _render_artifact_load_failure(
            ArtifactContractError(
                "MF model is not loaded; cannot determine cold-start status.",
                details=["Expected bundle['models']['mf'] to be present."],
            )
        )
    if not hasattr(local_mf_model, "item_to_index"):
        _render_artifact_load_failure(
            ArtifactContractError(
                "MF model missing item_to_index; cannot determine cold-start status.",
                details=["Required attributes: Q, item_to_index, index_to_item"],
            )
        )

    try:
        return int(anime_id) in local_mf_model.item_to_index
    except Exception as e:  # noqa: BLE001
        _render_artifact_load_failure(
            ArtifactContractError(
                "Failed checking MF training membership for anime_id.",
                details=[f"anime_id={anime_id}", f"Error: {e}"],
            )
        )
    return False

if not IMPORT_LIGHT:
    mf_model = bundle.get("models", {}).get("mf")
    if mf_model is None:
        _render_artifact_load_failure(
            ArtifactContractError(
                "MF model alias 'mf' not found in loaded models.",
                details=[
                    "Loader should add models['mf'] after validating MF contract.",
                    "Check models/*.joblib and APP_MF_MODEL_STEM.",
                ],
            )
        )

    # Build item id vector in MF index order.
    if not hasattr(mf_model, "index_to_item"):
        _render_artifact_load_failure(
            ArtifactContractError(
                "MF model missing index_to_item.",
                details=["Required attributes: Q, item_to_index, index_to_item"],
            )
        )
    index_to_item = mf_model.index_to_item
    try:
        n_items_mf = len(index_to_item)
        item_ids = np.asarray([int(index_to_item[i]) for i in range(n_items_mf)], dtype=np.int64)
    except Exception as e:  # noqa: BLE001
        _render_artifact_load_failure(
            ArtifactContractError(
                "MF model index_to_item is not a contiguous 0..N-1 mapping.",
                details=[f"Error: {e}"],
            )
        )

    # Compute a real MF score vector for the demo user index (0).
    # This avoids any placeholder arrays while keeping behavior deterministic.
    if not (hasattr(mf_model, "P") and hasattr(mf_model, "Q") and hasattr(mf_model, "global_mean")):
        _render_artifact_load_failure(
            ArtifactContractError(
                "MF model is missing required fields to compute demo user scores (P, Q, global_mean).",
                details=[
                    "This is required for seedless recommendations without a user profile.",
                    "Fix: export MF artifact with P, Q, global_mean (or enable personalization with profile ratings).",
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
                f"Q has {int(q.shape[0])} rows but index_to_item has {int(item_ids.shape[0])} items"
            )
        if p.shape[0] < 1:
            raise ValueError("MF model has no users in P")
        demo_user_index = 0
        demo_scores = float(mf_model.global_mean) + (p[demo_user_index] @ q.T)
        mf_scores = np.asarray(demo_scores, dtype=np.float32).reshape(1, -1)
    except Exception as e:  # noqa: BLE001
        _render_artifact_load_failure(
            ArtifactContractError(
                "Failed computing demo MF scores from MF artifact.",
                details=[f"Error: {e}"],
            )
        )

    components = HybridComponents(
        mf=mf_scores,
        knn=None,
        pop=None,
        item_ids=item_ids,
    )

    # Wire a popularity prior if an item-kNN artifact is available.
    # We use its learned per-item popularity vector (normalized 0..1) and align it to MF item_ids.
    # This enables truthful MF/Pop shares and makes the weight presets visibly affect shares.
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

            # Percentiles keyed by anime_id for UI badges and browse/sorting (covers cold-start too).
            try:
                pop_pct_arr = compute_popularity_percentiles(np.asarray(pop_arr, dtype=np.float32))
                pop_percentile_by_anime_id = {
                    int(aid): float(pop_pct_arr[int(idx)])
                    for aid, idx in it2i.items()
                    if idx is not None and 0 <= int(idx) < len(pop_pct_arr)
                }
            except Exception:
                pop_percentile_by_anime_id = None

            for j, aid in enumerate(item_ids):
                idx = it2i.get(int(aid))
                if idx is not None and int(idx) >= 0 and int(idx) < len(pop_arr):
                    pop_vec[j] = float(pop_arr[int(idx)])
            components.pop = pop_vec
    except Exception:
        # Popularity prior is optional; do not block app startup.
        pass
    recommender = HybridRecommender(components)


st.markdown("---")

# Browse mode handling
if browse_mode:
    if genre_filter:
        # Show which genres are being browsed
        genre_list_display = ", ".join(genre_filter[:3])
        if len(genre_filter) > 3:
            genre_list_display += f" +{len(genre_filter)-3} more"
        st.subheader(f"📚 Browsing {genre_list_display}")
        st.markdown(f"<p style='color: #7F8C8D; margin-top: -8px;'>Click any genre badge on cards to explore similar titles</p>", unsafe_allow_html=True)
    else:
        st.subheader("📚 Browse Anime by Genre")
    
    if not genre_filter:
        st.info(
            "Pick ≥1 genre in Filters to start browsing. "
            "Browse mode filters/sorts catalog metadata only (no ranking)."
        )
        recs = []
    else:
        # Browse mode: filter metadata directly via pipeline module
        with st.spinner("🔍 Loading anime..."):
            browse_ctx = ScoringContext(
                metadata=metadata,
                bundle=bundle,
                browse_mode=True,
                genre_filter=genre_filter,
                type_filter=type_filter,
                year_range=year_range,
                sort_by=sort_by,
                default_sort_for_mode=default_sort_for_mode,
                top_n=top_n,
                pop_pct_fn=_pop_pct_for_anime_id,
                watched_ids={int(x) for x in (st.session_state["active_profile"].get("watched_ids", []) or [])} if st.session_state["active_profile"] else set(),
            )
            browse_result = run_browse_pipeline(browse_ctx)
            recs = browse_result.ranked_items
            
            if not recs:
                st.warning("No titles found matching your filters.")
                st.markdown("**Try:**")
                st.markdown(
                    "\n".join(
                        [
                            "- Widen the year range (Filters)",
                            "- Remove the type filter (Filters)",
                            "- Reduce the number of selected genres (Filters)",
                            "- Use **Reset Filters** in the sidebar",
                        ]
                    )
                )
else:
    # Recommendation mode (existing logic)
    ui_mode_main = str(st.session_state.get("ui_mode", "Seed-based"))
    
    # Show banner if default seed is active
    if st.session_state.get("_default_seed_active", False) and selected_seed_ids and selected_seed_titles:
        st.info(
            f"🎬 Showing recommendations based on **{selected_seed_titles[0]}** — "
            "change the seed in the sidebar to explore!",
            icon="💡"
        )
    
    if selected_seed_ids and selected_seed_titles:
        if len(selected_seed_titles) == 1:
            st.subheader(f"Similar to: {selected_seed_titles[0]}")
        else:
            seed_display = ", ".join(selected_seed_titles[:3])
            if len(selected_seed_titles) > 3:
                seed_display += f" +{len(selected_seed_titles)-3} more"
            st.subheader(f"Blended from: {seed_display}")
    else:
        st.subheader("Personalized recommendations" if ui_mode_main == "Personalized" else "Recommendations")
    user_index = 0  # demo user index (persona mapping to be added)

    # Phase 4 / Chunk A2: Candidate hygiene guardrails (ranked modes only).
    # Build an exclusion set once and thread it through ranked pipelines.
    ranked_hygiene_exclude_ids: set[int] = set()
    if not bool(st.session_state.get("browse_mode", False)):
        ranked_hygiene_exclude_ids = build_ranked_candidate_hygiene_exclude_ids(metadata)
    
    # Request extra recommendations to account for filtering
    # If filters are active (including profile exclusion), request more to ensure we have enough after filtering
    has_profile = st.session_state["active_profile"] is not None
    filter_multiplier = 10 if (has_profile or genre_filter or type_filter or year_range[0] > 1960 or year_range[1] < 2025) else 1
    n_requested = min(top_n * filter_multiplier, components.num_items if hasattr(components, "num_items") else len(metadata))
    
    recs: list[dict] = []
    personalization_applied = False
    personalized_gate_reason: str | None = None

    if ui_mode_main == "Personalized":
        active_profile = st.session_state.get("active_profile")
        ratings = (active_profile or {}).get("ratings", {}) if isinstance(active_profile, dict) else {}
        blocked_reason = st.session_state.get("personalization_blocked_reason")
        user_embedding = st.session_state.get("user_embedding")
        if not active_profile:
            personalized_gate_reason = "Select an Active Profile to use Personalized mode."
        elif not isinstance(ratings, dict) or len(ratings) == 0:
            personalized_gate_reason = "Add at least one rating to your active profile to use Personalized mode."
        elif not st.session_state.get("personalization_enabled", False):
            personalized_gate_reason = "Enable personalization in the sidebar to run Personalized mode."
        elif blocked_reason:
            personalized_gate_reason = blocked_reason
        elif user_embedding is None:
            personalized_gate_reason = "Taste profile is not ready yet."

        if personalized_gate_reason:
            st.warning(f"Personalized mode selected, but it can't run: {personalized_gate_reason}")
            st.info(
                "Fix it by adding ratings (or choosing a rated profile), then enable personalization in the sidebar. "
                "This app does not silently fall back to Seed-based results."
            )

    if recommender is None or components is None:
        st.error(
            "Recommendation engine is unavailable because required artifacts did not load. "
            "Disable APP_IMPORT_LIGHT and ensure MF artifacts are present/valid."
        )
        recs = []
    elif n_requested > 0 and not personalized_gate_reason:
        # ── Scoring pipeline (delegated to src.app.scoring_pipeline) ─────
        with st.spinner("🔍 Finding recommendations..."):
            with latency_timer("recommendations"):
                # ── Build ScoringContext from session state + local vars ──
                _active_profile = st.session_state.get("active_profile")
                _watched_ids: set[int] = set()
                if _active_profile:
                    _watched_ids = {int(x) for x in (_active_profile.get("watched_ids", []) or [])}
    
                _personalization_enabled = st.session_state.get("personalization_enabled", False)
                _personalization_strength = st.session_state.get("personalization_strength", 100) / 100.0
                _user_embedding = st.session_state.get("user_embedding")
                _user_embedding_meta = st.session_state.get("user_embedding_meta", {}) or {}
                _seed_ranking_mode = st.session_state.get("seed_ranking_mode", SEED_RANKING_MODE)
                _mf_model = bundle.get("models", {}).get("mf")
                _mf_stem = bundle.get("models", {}).get("_mf_stem")
    
                ctx = ScoringContext(
                    metadata=metadata,
                    bundle=bundle,
                    recommender=recommender,
                    components=components,
                    seed_ids=list(selected_seed_ids),
                    seed_titles=list(selected_seed_titles),
                    user_index=user_index,
                    user_embedding=_user_embedding,
                    personalization_enabled=_personalization_enabled,
                    personalization_strength=_personalization_strength,
                    active_profile=_active_profile,
                    watched_ids=_watched_ids,
                    personalization_blocked_reason=st.session_state.get("personalization_blocked_reason"),
                    weights=weights,
                    seed_ranking_mode=_seed_ranking_mode,
                    genre_filter=genre_filter,
                    type_filter=type_filter,
                    year_range=year_range,
                    sort_by=sort_by,
                    default_sort_for_mode=default_sort_for_mode,
                    n_requested=n_requested,
                    top_n=top_n,
                    pop_pct_fn=_pop_pct_for_anime_id,
                    is_in_training_fn=_is_in_training,
                    mf_model=_mf_model,
                    mf_stem=_mf_stem,
                    user_embedding_meta=_user_embedding_meta,
                    ranked_hygiene_exclude_ids=ranked_hygiene_exclude_ids,
                )
    
                # ── Run seed-based pipeline ──────────────────────────────
                if selected_seed_ids:
                    seed_result = run_seed_based_pipeline(ctx)
                    recs = seed_result.ranked_items
                    st.session_state["stage0_diagnostics"] = seed_result.stage0_diagnostics
                    st.session_state["stage0_enforcement"] = seed_result.stage0_enforcement
                    st.session_state["franchise_cap_diagnostics"] = seed_result.franchise_cap_diagnostics
                else:
                    # Seedless fallback: plain hybrid recommender
                    recs = recommender.get_top_n_for_user(
                        user_index,
                        n=n_requested,
                        weights=weights,
                        exclude_item_ids=sorted(ranked_hygiene_exclude_ids),
                    )
    
                # ── Personalization overlay ──────────────────────────────
                if recs and _personalization_enabled:
                    pers_result = run_personalized_pipeline(ctx)
    
                    # Propagate any blocked reason back to session state
                    if pers_result.personalization_blocked_reason is not None:
                        st.session_state["personalization_blocked_reason"] = (
                            pers_result.personalization_blocked_reason
                        )
    
                    if pers_result.personalization_applied:
                        personalization_applied = True
    
                        if _personalization_strength >= 0.99:
                            # Pure personalized — replace seed-based recs
                            recs = pers_result.ranked_items
                        elif _personalization_strength > 0.01:
                            # Blend personalized with seed-based
                            recs = blend_personalized_and_seed(
                                personalized_recs=pers_result.ranked_items,
                                seed_recs=recs,
                                personalization_strength=_personalization_strength,
                                n_requested=n_requested,
                                ranked_hygiene_exclude_ids=ranked_hygiene_exclude_ids,
                            )
                        # else: strength ≤ 0.01 → keep seed-based as-is
    
                # ── Personalized explanation text (Streamlit-dependent) ──
                if recs and _personalization_enabled and _active_profile:
                    from src.app.components.explanations import generate_batch_explanations
                    recs = generate_batch_explanations(
                        recommendations=recs,
                        user_profile=_active_profile,
                        metadata_df=metadata,
                    )
    
                # ── Truthful MF/kNN/Pop share labels ─────────────────────
                recs = finalize_explanation_shares(recs)
    
                # ── Post-filters (genre / type / year / sort) ────────────
                recs = apply_post_filters(recs, ctx)
    
                # ── Trim to requested top_n ──────────────────────────────
                recs = recs[:top_n]


# Active scoring path indicator (single source of truth: derived from executed flags)
active_scoring_path = None
if browse_mode:
    active_scoring_path = "Browse"
else:
    ui_mode_main = str(st.session_state.get("ui_mode", "Seed-based"))
    if ui_mode_main == "Personalized" and personalized_gate_reason:
        active_scoring_path = "Personalized (Unavailable)"
    else:
        if recommender is None or components is None:
            active_scoring_path = "Ranked modes disabled"
        elif personalization_applied:
            active_scoring_path = "Personalized"
        elif selected_seed_ids:
            active_scoring_path = "Seed-based" if len(selected_seed_ids) == 1 else "Multi-seed"
        else:
            active_scoring_path = "Seedless"

# If personalization was requested but couldn't run, reflect that explicitly.
personalization_requested = st.session_state.get("personalization_enabled", False)
blocked_reason = st.session_state.get("personalization_blocked_reason")
if (
    personalization_requested
    and not personalization_applied
    and blocked_reason
    and str(st.session_state.get("ui_mode", "Seed-based")) != "Personalized"
):
    active_scoring_path = f"{active_scoring_path} (Personalization unavailable)"

def _coerce_genres(value) -> str:
    """Normalize genre field into pipe-delimited string."""
    if value is None:
        return ""
    # If already a string
    if isinstance(value, str):
        return value
    # Iterable of genres
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(v) for v in value if v)
    # Numpy array
    try:  # handle numpy arrays without importing numpy explicitly here
        import numpy as _np  # type: ignore
        if isinstance(value, _np.ndarray):
            return "|".join(str(v) for v in value.tolist() if v)
    except Exception:
        pass
    return str(value)

if recs:
    st.markdown(f"**Active scoring path:** {active_scoring_path}")
    # Be explicit when personalization is enabled but blocked.
    blocked_reason = st.session_state.get("personalization_blocked_reason")
    if (
        st.session_state.get("personalization_enabled", False)
        and not personalization_applied
        and blocked_reason
    ):
        st.warning(f"Personalization enabled but not applied: {blocked_reason}")
    # Result count with total anime count badge
    total_anime = len(metadata)
    result_count = len(recs)
    filter_info = []
    if type_filter:
        filter_info.append(f"Type: {', '.join(type_filter)}")
    if genre_filter:
        filter_info.append(f"Genre: {', '.join(genre_filter[:3])}{'...' if len(genre_filter) > 3 else ''}")
    if genre_filter:
        filter_info.append(f"{len(genre_filter)} genre{'s' if len(genre_filter) > 1 else ''}")
    if year_range[0] > 1960 or year_range[1] < 2025:
        filter_info.append(f"{year_range[0]}-{year_range[1]}")
    
    filters_text = f" (filtered by {', '.join(filter_info)})" if filter_info else ""
    
    # Header with count badge
    mode_icon = "📚" if browse_mode else "✨"
    mode_label = "Browsing" if browse_mode else "Showing"
    item_type = "titles" if browse_mode else "recommendations"
    st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 12px;'>
        <h3 style='color: #2C3E50; margin: 0;'>{mode_icon} {mode_label} {len(recs)} {item_type}{filters_text}</h3>
        <span style='background: #3498DB; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; font-weight: 600;'>{total_anime:,} total anime</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Show exclusion count if profile active
    if st.session_state["active_profile"]:
        watched_count = len(st.session_state["active_profile"].get("watched_ids", []))
        st.markdown(f"""
        <p style='color: #27AE60; font-size: 0.9rem; margin-top: -8px; margin-bottom: 8px;'>
            ✓ Excluded {watched_count} already-watched anime
        </p>
        """, unsafe_allow_html=True)
    
    if sort_by != default_sort_for_mode:
        st.markdown(f"<p style='color: #7F8C8D; font-size: 0.9rem; margin-top: -8px; margin-bottom: 20px;'>Sorted by: {sort_by}</p>", unsafe_allow_html=True)
    
    # Calculate diversity mix
    pop_count = sum(
        1
        for r in recs
        if "Top 25%"
        in str(
            badge_payload(
                is_in_training=_is_in_training(int(r["anime_id"])),
                pop_percentile=_pop_pct_for_anime_id(int(r["anime_id"])),
                user_genre_hist={},
                item_genres=[],
            ).get("popularity_band", "")
        )
    )
    long_tail_count = sum(
        1
        for r in recs
        if "Long-tail"
        in str(
            badge_payload(
                is_in_training=_is_in_training(int(r["anime_id"])),
                pop_percentile=_pop_pct_for_anime_id(int(r["anime_id"])),
                user_genre_hist={},
                item_genres=[],
            ).get("popularity_band", "")
        )
    )
    mid_count = len(recs) - pop_count - long_tail_count
    
    # Modern diversity visualization with gradient bar
    total = len(recs)
    pop_pct = (pop_count / total * 100) if total > 0 else 0
    mid_pct = (mid_count / total * 100) if total > 0 else 0
    long_pct = (long_tail_count / total * 100) if total > 0 else 0
    
    # Build bar segments - only include non-zero categories
    bar_segments = []
    if pop_count > 0:
        bar_segments.append(f'<div style="background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); flex: {pop_count}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.85rem; min-height: 40px;">🔥 {pop_count}</div>')
    if mid_count > 0:
        bar_segments.append(f'<div style="background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); flex: {mid_count}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.85rem; min-height: 40px;">📊 {mid_count}</div>')
    if long_tail_count > 0:
        bar_segments.append(f'<div style="background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); flex: {long_tail_count}; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.85rem; min-height: 40px;">🌟 {long_tail_count}</div>')
    
    # Fallback if no segments (shouldn't happen but just in case)
    if not bar_segments:
        bar_segments.append(f'<div style="background: linear-gradient(135deg, #95A5A6 0%, #7F8C8D 100%); flex: 1; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.85rem; min-height: 40px;">📊 {len(recs)} Mixed</div>')
    
    bar_html = ''.join(bar_segments)
    
    mix_label = "Catalog Mix" if browse_mode else "Recommendation Mix"
    st.markdown(f"""
    <div style="background: #F8F9FA; border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
        <p style="color: #7F8C8D; font-size: 0.9rem; margin-bottom: 12px; font-weight: 500;">{mix_label}</p>
        <div style="display: flex; height: 40px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {bar_html}
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 0.8rem; color: #95A5A6;">
            <span>Popular Titles</span>
            <span>Balanced Mix</span>
            <span>Hidden Gems</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

if recs:
    view_mode_state = st.session_state.get("view_mode", "list")
    
    # Extract all raw scores for percentile-based display
    all_raw_scores = [rec.get("score") for rec in recs if has_match_score(rec.get("score"))]
    
    # Create indexed lookup for O(1) access (performance optimization)
    metadata_by_id = metadata.set_index("anime_id", drop=False)
    
    if view_mode_state == "grid":
        # Grid layout: 3 columns
        # Process in batches of 3 for grid layout
        for i in range(0, len(recs), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(recs):
                    rec = recs[i + j]
                    anime_id = rec["anime_id"]
                    try:
                        row = metadata_by_id.loc[anime_id]
                        if isinstance(row, pd.DataFrame):
                            row = row.iloc[0]
                        pop_pct = _pop_pct_for_anime_id(int(anime_id))
                        with col:
                            render_card_grid(
                                row, rec, pop_pct,
                                is_in_training=_is_in_training(int(anime_id)),
                                all_raw_scores=all_raw_scores
                            )
                    except KeyError:
                        pass
    else:
        # List layout: standard cards
        for rec in recs:
            anime_id = rec["anime_id"]
            try:
                row = metadata_by_id.loc[anime_id]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
            except KeyError:
                continue
            pop_pct = _pop_pct_for_anime_id(int(anime_id))
            render_card(
                row, rec, pop_pct,
                is_in_training=_is_in_training(int(anime_id)),
                all_raw_scores=all_raw_scores
            )
else:
    if (browse_mode or active_scoring_path == "Ranked modes disabled"):
        st.markdown(f"**Active scoring path:** {active_scoring_path}")

    if browse_mode:
        # Browse mode renders its empty state guidance above.
        pass
    else:
        ui_mode_now = str(st.session_state.get("ui_mode", "Seed-based"))

        if ui_mode_now == "Personalized":
            active_profile = st.session_state.get("active_profile")
            ratings = (active_profile or {}).get("ratings", {}) if isinstance(active_profile, dict) else {}
            blocked_reason = st.session_state.get("personalization_blocked_reason")
            user_embedding = st.session_state.get("user_embedding")
            personalization_enabled = bool(st.session_state.get("personalization_enabled", False))

            personalized_unavailable_reason: str | None = None
            if not active_profile:
                personalized_unavailable_reason = "Select a rated profile"
            elif not isinstance(ratings, dict) or len(ratings) == 0:
                personalized_unavailable_reason = "Add at least one rating"
            elif not personalization_enabled:
                personalized_unavailable_reason = "Enable personalization"
            elif blocked_reason or user_embedding is None:
                personalized_unavailable_reason = "Personalization is not ready"

            if personalized_unavailable_reason:
                st.markdown(
                    "<div style='background: linear-gradient(135deg, #FFF3CD 0%, #FCF8E3 100%); "
                    "border-left: 4px solid #F0AD4E; border-radius: 8px; padding: 20px; margin: 20px 0;'>"
                    "<p style='color: #8A6D3B; font-weight: 600; margin: 0;'>Personalized mode is selected, but it isn’t running yet.</p>"
                    "<p style='color: #8A6D3B; margin: 8px 0 0 0;'>What next: <b>Select a rated profile</b>, <b>add at least one rating</b>, and <b>enable personalization</b> in the sidebar.</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.warning("No personalized results found with the current filters.")
                st.markdown("**Try:**")
                st.markdown(
                    "\n".join(
                        [
                            "- Use **Reset Filters** in the sidebar",
                            "- Widen the year range (Filters)",
                            "- Remove the type filter (Filters)",
                            "- Switch to **Seed-based** mode to explore via a seed",
                        ]
                    )
                )

        elif selected_seed_ids:
            st.warning("No similar titles found with the current filters.")
            st.markdown("**Try:**")
            st.markdown(
                "\n".join(
                    [
                        "- Use **Reset Filters** in the sidebar",
                        "- Try fewer seeds (1–2) or a different seed",
                        "- Widen the year range (Filters)",
                        "- Remove the type filter (Filters)",
                    ]
                )
            )
        else:
            # Cold-start / seedless state — show prominent sample buttons
            st.markdown(
                "<div style='background: linear-gradient(135deg, #E8F4F8 0%, #F0F8FF 100%); border-radius: 12px; "
                "padding: 28px; margin: 28px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>"
                "<h3 style='color: #2C3E50; margin: 0 0 10px 0;'>🎬 Get Started</h3>"
                "<p style='color: #7F8C8D; font-size: 1.0rem; margin: 0 0 20px 0;'>"
                "A hybrid anime recommender that ranks titles similar to your chosen seed title(s)."
                "</p>"
                "<p style='color: #2C3E50; font-weight: 600; margin: 0 0 16px 0;'>Try these popular titles:</p>"
                "</div>",
                unsafe_allow_html=True,
            )
            
            # Show prominent sample buttons in main area
            sample_titles = ["Steins;Gate", "Cowboy Bebop", "Death Note", "Fullmetal Alchemist: Brotherhood"]
            # Get title_to_id mapping from the earlier code
            _title_to_id = {}
            for _, row in metadata.iterrows():
                # Use same logic as sidebar
                title_eng = row.get("title_english")
                if title_eng and isinstance(title_eng, str) and title_eng.strip():
                    _title_to_id[title_eng] = int(row["anime_id"])
                else:
                    title_disp = row.get("title_display")
                    if title_disp and isinstance(title_disp, str) and title_disp.strip():
                        _title_to_id[title_disp] = int(row["anime_id"])
            
            _available_samples = [t for t in sample_titles if t in _title_to_id]
            if _available_samples:
                cols = st.columns(4)
                for i, sample in enumerate(_available_samples[:4]):
                    with cols[i]:
                        if st.button(
                            f"🎯 {sample}",
                            key=f"main_sample_{i}",
                            use_container_width=True,
                            type="primary" if i == 3 else "secondary",  # Highlight FMAB
                        ):
                            _aid = _title_to_id.get(sample)
                            if _aid:
                                st.session_state["selected_seed_ids"] = [_aid]
                                st.session_state["selected_seed_titles"] = [sample]
                                st.session_state["_default_seed_active"] = False
                                st.rerun()
            
            st.markdown(
                "<p style='color: #7F8C8D; text-align: center; margin-top: 20px;'>Or search for any title in the sidebar →</p>",
                unsafe_allow_html=True,
            )


st.markdown("---")
# Note: Old explanation panel removed - explanations now shown inline on cards
render_diversity_panel(recs, metadata, is_browse=browse_mode)



# Help / FAQ ---------------------------------------------------------------
render_help_panel()
render_help_panel(ui_mode=str(st.session_state.get("ui_mode", "Seed-based")))

st.sidebar.caption("Prototype – performance instrumentation active.")
