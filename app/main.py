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

from src.app.artifacts_loader import build_artifacts, ArtifactContractError
from src.app.components.cards import render_card, render_card_grid
from src.app.components.diversity import render_diversity_panel
from src.app.components.help import render_help_panel
from src.app.components.skeletons import render_card_skeleton  # retained import (may repurpose later)
from src.app.components.instructions import render_onboarding
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids
from src.app.metadata_features import (
    METADATA_AFFINITY_COLD_START_COEF,
    METADATA_AFFINITY_TRAINED_COEF,
    METADATA_AFFINITY_PERSONALIZED_COEF,
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
    personalized_synopsis_tfidf_bonus_for_candidate,
    SYNOPSIS_TFIDF_MIN_SIM,
    SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD,
    SYNOPSIS_TFIDF_OFFTYPE_HIGH_SIM_PENALTY,
)
from src.app.theme import get_theme
from src.app.constants import (
    DEFAULT_TOP_N,
    PERSONAS_JSON,
)
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
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
        # Browse mode: filter metadata directly without recommendations
        with st.spinner("🔍 Loading anime..."):
            browse_results = []
            for idx, row in metadata.iterrows():
                anime_id = int(row["anime_id"])
                row_genres_val = row.get("genres")
                
                # Handle both string and array formats
                item_genres = set()
                if isinstance(row_genres_val, str):
                    item_genres = set([g.strip() for g in row_genres_val.split("|") if g.strip()])
                elif hasattr(row_genres_val, '__iter__') and not isinstance(row_genres_val, str):
                    item_genres = set([str(g).strip() for g in row_genres_val if g])
                
                # Check if any selected genre matches
                if any(gf in item_genres for gf in genre_filter):
                    # Exclude watched anime (profile filter)
                    if st.session_state["active_profile"]:
                        watched_ids = st.session_state["active_profile"].get("watched_ids", [])
                        if anime_id in watched_ids:
                            continue  # Skip already-watched anime
                    
                    # Apply type filter
                    include = True
                    if type_filter and "type" in metadata.columns:
                        item_type = row.get("type")
                        if pd.notna(item_type):
                            type_str = str(item_type).strip()
                            if type_str not in type_filter:
                                include = False
                        else:
                            include = False  # Exclude items with no type when filter is active
                    
                    # Apply year filter
                    if include and (year_range[0] > 1960 or year_range[1] < 2025):
                        aired_from = row.get("aired_from")
                        if aired_from and isinstance(aired_from, str):
                            try:
                                year = int(aired_from[:4])
                                if not (year_range[0] <= year <= year_range[1]):
                                    include = False
                            except Exception:
                                include = False
                        else:
                            include = False
                    
                    if include:
                        # Create a rec-like dict for compatibility with existing card rendering
                        browse_results.append({
                            "anime_id": anime_id,
                            # Browse mode has no recommender score; keep this absent to avoid mixed semantics.
                            "score": None,
                            "explanation": None,  # No explanation in browse mode
                            "_mal_score": float(row.get("mal_score", 0) if pd.notna(row.get("mal_score")) else 0),
                            "_year": 0,
                            "_popularity": _pop_pct_for_anime_id(anime_id)
                        })
                        # Extract year for sorting
                        aired_from = row.get("aired_from")
                        if aired_from and isinstance(aired_from, str):
                            try:
                                browse_results[-1]["_year"] = int(aired_from[:4])
                            except Exception:
                                pass
            
            # Sort browse results
            if sort_by == "MAL Score":
                browse_results.sort(key=lambda x: x["_mal_score"], reverse=True)
            elif sort_by == "Year (Newest)":
                browse_results.sort(key=lambda x: x["_year"], reverse=True)
            elif sort_by == "Year (Oldest)":
                browse_results.sort(key=lambda x: x["_year"], reverse=False)
            elif sort_by == "Popularity":
                browse_results.sort(key=lambda x: x["_popularity"], reverse=False)
            else:  # Default
                browse_results.sort(key=lambda x: x["_mal_score"], reverse=True)
            
            # Limit to top N for performance
            recs = browse_results[:min(top_n, len(browse_results))]
            
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
        # Compute recommendations with progress indicator
        with st.spinner("🔍 Finding recommendations..."):
            with latency_timer("recommendations"):
                if selected_seed_ids:
                    # Multi-seed weighted average aggregation
                    # Build seed genre map and aggregate all genres
                    seed_genre_map = {}  # seed_title -> set of genres
                    all_seed_genres = set()
                    genre_weights = {}  # genre -> count of seeds having it
                    
                    for seed_id, seed_title in zip(selected_seed_ids, selected_seed_titles):
                        seed_row = metadata.loc[metadata["anime_id"] == seed_id].head(1)
                        if not seed_row.empty:
                            # Parse genres - handle both string and array formats
                            row_genres = seed_row.iloc[0].get("genres")
                            if isinstance(row_genres, str):
                                seed_genres = set([g.strip() for g in row_genres.split("|") if g.strip()])
                            elif hasattr(row_genres, '__iter__') and not isinstance(row_genres, str):
                                seed_genres = set([str(g).strip() for g in row_genres if g])
                            else:
                                seed_genres = set()
                            
                            seed_genre_map[seed_title] = seed_genres
                            all_seed_genres.update(seed_genres)
                            # Weight genres by how many seeds have them
                            for genre in seed_genres:
                                genre_weights[genre] = genre_weights.get(genre, 0) + 1

                    # Phase 4 / Chunk A3: lightweight metadata affinity profile.
                    # This is used as a *small* bonus for cold-start candidates.
                    seed_meta_profile = build_seed_metadata_profile(metadata, seed_ids=selected_seed_ids)

                    # Phase 4 (A3 → early A4): synopsis TF-IDF semantic rerank (optional artifact).
                    synopsis_tfidf_artifact = bundle.get("models", {}).get("synopsis_tfidf")
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
                    
                    num_seeds = len(selected_seed_ids)

                    # Option A (Phase 4): Two-stage seed-conditioned ranking.
                    # Stage 1: shortlist using seed-conditioned signals ONLY (no MF/demo-user/hybrid).
                    # Stage 2: rerank that shortlist using existing final scoring logic.
                    seed_shortlist_size = 600

                    watched_ids_set: set[int] = set()
                    if st.session_state["active_profile"]:
                        watched_ids_set = {int(x) for x in (st.session_state["active_profile"].get("watched_ids", []) or [])}

                    stage1_tfidf_pool: list[dict] = []
                    stage1_fallback_pool: list[dict] = []

                    for _, mrow in metadata.iterrows():
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
                        elif hasattr(row_genres, '__iter__') and not isinstance(row_genres, str):
                            item_genres = {str(g).strip() for g in row_genres if g}
                        else:
                            item_genres = set()

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
                        cand_type = None if pd.isna(mrow.get("type")) else str(mrow.get("type")).strip()
                        cand_eps = mrow.get("episodes")
                        base_passes_gate = synopsis_gate_passes(
                            seed_type=seed_type_target,
                            candidate_type=cand_type,
                            candidate_episodes=cand_eps,
                        )

                        high_sim_override = (not bool(base_passes_gate)) and (
                            float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD)
                        )
                        passes_gate_effective = bool(base_passes_gate) or bool(high_sim_override)

                        base = {
                            "anime_id": aid,
                            "mrow": mrow,
                            "item_genres": item_genres,
                            "weighted_overlap": float(weighted_overlap),
                            "seed_coverage": float(seed_coverage),
                            "overlap_per_seed": overlap_per_seed,
                            "seeds_matched": int(num_seeds_matched),
                            "metadata_affinity": float(meta_affinity),
                            "synopsis_tfidf_sim": float(synopsis_tfidf_sim),
                            "passes_gate": bool(base_passes_gate),
                            "synopsis_tfidf_high_sim_override": bool(high_sim_override),
                            "cand_type": cand_type,
                            "cand_eps": cand_eps,
                        }

                        # TF-IDF-first pool (gated): keep shortlist seed-like.
                        if bool(passes_gate_effective) and float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_MIN_SIM):
                            item = dict(base)
                            item["stage1_score"] = float(synopsis_tfidf_sim)
                            stage1_tfidf_pool.append(item)
                            continue

                        # Backfill pool when TF-IDF is absent/insufficient.
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
                            -float(x.get("synopsis_tfidf_sim", 0.0)),
                            -float(x.get("weighted_overlap", 0.0)),
                            -float(x.get("metadata_affinity", 0.0)),
                            int(x.get("anime_id", 0)),
                        )
                    )
                    stage1_fallback_pool.sort(key=lambda x: (-float(x.get("stage1_score", 0.0)), int(x.get("anime_id", 0))))

                    shortlist: list[dict] = []
                    seen_ids: set[int] = set()
                    for it in stage1_tfidf_pool:
                        if len(shortlist) >= seed_shortlist_size:
                            break
                        aid = int(it.get("anime_id", 0))
                        if aid in seen_ids:
                            continue
                        shortlist.append(it)
                        seen_ids.add(aid)
                    for it in stage1_fallback_pool:
                        if len(shortlist) >= seed_shortlist_size:
                            break
                        aid = int(it.get("anime_id", 0))
                        if aid in seen_ids:
                            continue
                        shortlist.append(it)
                        seen_ids.add(aid)

                    # Stage 2: rerank shortlist using existing hybrid + pop + bonuses.
                    try:
                        blended_scores = recommender._blend(user_index, weights)  # pylint: disable=protected-access
                    except Exception:
                        blended_scores = None

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

                        pop_pct = _pop_pct_for_anime_id(aid)
                        popularity_boost = max(0.0, (0.5 - pop_pct) / 0.5)

                        if blended_scores is not None and aid in id_to_index:
                            hybrid_val = float(blended_scores[id_to_index[aid]])
                        else:
                            hybrid_val = 0.0

                        meta_affinity = float(c.get("metadata_affinity", 0.0))
                        meta_bonus = 0.0
                        if meta_affinity > 0.0:
                            coef = float(METADATA_AFFINITY_COLD_START_COEF) if hybrid_val == 0.0 else float(METADATA_AFFINITY_TRAINED_COEF)
                            meta_bonus = float(coef) * float(meta_affinity)

                        synopsis_tfidf_sim = float(c.get("synopsis_tfidf_sim", 0.0))
                        passes_gate = bool(c.get("passes_gate", False))
                        high_sim_override = (not bool(passes_gate)) and (
                            float(synopsis_tfidf_sim) >= float(SYNOPSIS_TFIDF_HIGH_SIM_THRESHOLD)
                        )
                        passes_gate_effective = bool(passes_gate) or bool(high_sim_override)
                        cand_eps = c.get("cand_eps")

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
                                    candidate_episodes=cand_eps,
                                )
                            )

                        synopsis_tfidf_adjustment = float(synopsis_tfidf_bonus + synopsis_tfidf_penalty)

                        # Optional tiny tie-breaker: demographics overlap (Stage 2 only; never gates).
                        if "demographics" in metadata.columns:
                            demo_bonus = demographics_overlap_tiebreak_bonus(
                                seed_meta_profile.demographics,
                                mrow.get("demographics"),
                            )
                        else:
                            demo_bonus = 0.0

                        s1 = float(c.get("stage1_score", 0.0))

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
                        if score <= 0:
                            continue

                        raw_mf = 0.0
                        raw_knn = (
                            (0.5 * weighted_overlap)
                            + (0.2 * seed_coverage)
                            + (0.10 * float(s1))
                            + meta_bonus
                            + synopsis_tfidf_adjustment
                            + float(demo_bonus)
                        )
                        raw_pop = (0.05 * popularity_boost)
                        used_components: list[str] = ["knn", "pop"]
                        if aid in id_to_index:
                            idx = id_to_index[aid]
                            try:
                                raw_hybrid = recommender.raw_components_for_item(user_index, idx, weights)
                            except Exception:
                                raw_hybrid = {"mf": 0.0, "knn": 0.0, "pop": 0.0}
                            raw_mf += 0.25 * float(raw_hybrid.get("mf", 0.0))
                            raw_knn += 0.25 * float(raw_hybrid.get("knn", 0.0))
                            raw_pop += 0.25 * float(raw_hybrid.get("pop", 0.0))

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
                            "synopsis_tfidf_sim": float(synopsis_tfidf_sim),
                            "synopsis_tfidf_bonus": float(synopsis_tfidf_bonus),
                            "synopsis_tfidf_penalty": float(synopsis_tfidf_penalty),
                            "synopsis_tfidf_adjustment": float(synopsis_tfidf_adjustment),
                            "synopsis_tfidf_base_gate_passed": bool(passes_gate),
                            "synopsis_tfidf_high_sim_override": bool(high_sim_override),
                            "demographics_overlap_bonus": float(demo_bonus),
                            "stage1_score": float(s1),
                            "shortlist_size": int(len(shortlist)),
                        }
                        explanation.update(shares)

                        scored.append({
                            "anime_id": aid,
                            "score": score,
                            "explanation": explanation,
                            "_raw_components": raw_components,
                            "_used_components": used_components,
                            "_explanation_meta": {
                                "seed_titles": selected_seed_titles,
                                "seeds_matched": num_seeds_matched,
                            },
                        })

                    scored.sort(key=lambda x: (-float(x.get("score", 0.0)), int(x.get("anime_id", 0))))
                    recs = scored[:n_requested]
                else:
                    # Default: seed-based recommendations
                    recs = recommender.get_top_n_for_user(
                        user_index,
                        n=n_requested,
                        weights=weights,
                        exclude_item_ids=sorted(ranked_hygiene_exclude_ids),
                    )
        
        # Check if personalization is enabled (after recs are generated)
        personalization_enabled = st.session_state.get("personalization_enabled", False)
        user_embedding = st.session_state.get("user_embedding")
        personalization_strength = st.session_state.get("personalization_strength", 100) / 100.0  # Convert to 0-1
        
        # Apply personalization if enabled and requirements are met.
        if recs and personalization_enabled:
            mf_model = bundle.get("models", {}).get("mf")
            mf_stem = bundle.get("models", {}).get("_mf_stem")
            cached = st.session_state.get("user_embedding_meta", {}) or {}
            if mf_model is None:
                st.session_state["personalization_blocked_reason"] = (
                    "MF model is not available (artifact load/selection failed)."
                )
            elif user_embedding is None:
                st.session_state["personalization_blocked_reason"] = (
                    "User embedding is not available."
                )
            elif cached.get("mf_stem") != mf_stem:
                # Defensive: embeddings must correspond to the active MF artifact.
                st.session_state["personalization_blocked_reason"] = (
                    "User embedding was generated from a different MF artifact; rerun to refresh."
                )
            elif st.session_state.get("personalization_blocked_reason"):
                # Blocked earlier in the sidebar generation step.
                pass
            else:
                st.session_state["personalization_blocked_reason"] = None
            
            # Get watched anime IDs for exclusion
            watched_ids = []
            if st.session_state["active_profile"]:
                watched_ids = st.session_state["active_profile"].get("watched_ids", [])

            # Candidate hygiene exclusions always apply in ranked modes.
            exclude_ranked_ids = sorted(set(watched_ids) | set(ranked_hygiene_exclude_ids))

            if st.session_state.get("personalization_blocked_reason") is None:
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
                            st.session_state["personalization_blocked_reason"] = (
                                "MF personalization returned no results (likely no overlap with MF items)."
                            )
                        else:
                            # Phase 4 / Chunk A3: when seeds are selected, apply a tiny deterministic
                            # metadata affinity nudge to reduce occasional "weird match" outputs.
                            if selected_seed_ids:
                                seed_meta_profile = build_seed_metadata_profile(metadata, seed_ids=selected_seed_ids)
                                synopsis_tfidf_artifact = bundle.get("models", {}).get("synopsis_tfidf")
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
                                for rec in personalized_recs:
                                    aid = int(rec.get("anime_id"))
                                    row_df = metadata.loc[metadata["anime_id"] == aid].head(1)
                                    if row_df.empty:
                                        continue
                                    affinity = compute_metadata_affinity(seed_meta_profile, row_df.iloc[0])
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

                                    # Phase 4 (A3 → early A4): synopsis TF-IDF nudge in personalized mode
                                    # when seeds are selected (optional artifact).
                                    if synopsis_sims_by_id:
                                        sim = float(synopsis_sims_by_id.get(aid, 0.0))
                                        if sim > 0.0:
                                            cand_type = None
                                            if "type" in row_df.columns:
                                                cand_type = None if pd.isna(row_df.iloc[0].get("type")) else str(row_df.iloc[0].get("type")).strip()
                                            cand_eps = row_df.iloc[0].get("episodes") if "episodes" in row_df.columns else None
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
                                # Deterministic ordering: score desc, then anime_id asc.
                                personalized_recs.sort(key=lambda x: (-float(x.get("score", 0.0)), int(x.get("anime_id", 0))))
                                personalized_recs = personalized_recs[:n_requested]
                            recs = personalized_recs
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
                            st.session_state["personalization_blocked_reason"] = (
                                "MF personalization returned no results (likely no overlap with MF items)."
                            )
                        else:
                            personalization_applied = True
                except Exception as e:  # noqa: BLE001
                    st.session_state["personalization_blocked_reason"] = (
                        f"Personalization failed at scoring time: {e}"
                    )

                if personalization_applied and personalization_strength > 0.01 and personalization_strength < 0.99:
                    # Create score dictionaries
                    personalized_scores = {rec["anime_id"]: rec["score"] for rec in personalized_recs}
                    seed_scores = {rec["anime_id"]: rec["score"] for rec in recs}

                    # Keep raw components so we can compute truthful shares after blending.
                    personalized_raw = {
                        rec["anime_id"]: rec.get("_raw_components", {"mf": 0.0, "knn": 0.0, "pop": 0.0})
                        for rec in personalized_recs
                    }
                    seed_raw = {
                        rec["anime_id"]: rec.get("_raw_components", {"mf": 0.0, "knn": 0.0, "pop": 0.0})
                        for rec in recs
                    }
                    personalized_used = {
                        rec["anime_id"]: rec.get("_used_components", []) for rec in personalized_recs
                    }
                    seed_used = {rec["anime_id"]: rec.get("_used_components", []) for rec in recs}

                    # Collect all unique anime IDs
                    all_anime_ids = set(personalized_scores.keys()) | set(seed_scores.keys())

                    # Blend scores
                    blended = []
                    for aid in all_anime_ids:
                        if aid in ranked_hygiene_exclude_ids:
                            continue
                        p_score = personalized_scores.get(aid, 0.0)
                        s_score = seed_scores.get(aid, 0.0)

                        # Weighted blend based on personalization strength
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

                    # Sort and take top N
                    blended.sort(key=lambda x: x["score"], reverse=True)
                    recs = blended[:n_requested]
            # else: personalization_strength <= 0.01, keep seed-based recs as-is
        
        # Generate explanations for personalized recommendations
        if recs and personalization_enabled and st.session_state.get("active_profile"):
            from src.app.components.explanations import generate_batch_explanations
            recs = generate_batch_explanations(
                recommendations=recs,
                user_profile=st.session_state["active_profile"],
                metadata_df=metadata
            )

        # Ensure all cards show truthful MF/kNN/Pop shares (and hide components not used).
        # This runs *after* optional personalized explanation text generation so we can append shares.
        for rec in recs:
            raw = rec.get("_raw_components")
            used = rec.get("_used_components")
            if not isinstance(raw, dict) or not isinstance(used, list) or not used:
                continue
            shares = compute_component_shares(raw, used_components=used)

            contributions = {"mf": shares.get("mf", 0.0), "knn": shares.get("knn", 0.0), "pop": shares.get("pop", 0.0), "_used": shares.get("_used", used)}
            meta = rec.get("_explanation_meta")
            if isinstance(meta, dict):
                contributions.update(meta)
            share_text = format_explanation(contributions)

            existing = rec.get("explanation")
            if isinstance(existing, str) and existing.strip():
                rec["explanation"] = f"{existing} • {share_text}"
            else:
                rec["explanation"] = share_text
        
        # Apply user filters and sorting
        if recs:
            import pandas as pd
            # Filter by genre
            if genre_filter:
                filtered_recs = []
                for rec in recs:
                    anime_id = rec["anime_id"]
                    row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
                    if not row_df.empty:
                        row_genres_val = row_df.iloc[0].get("genres", "")
                        # Handle both string and array formats
                        item_genres = set()
                        if isinstance(row_genres_val, str):
                            item_genres = set([g.strip() for g in row_genres_val.split("|") if g.strip()])
                        elif hasattr(row_genres_val, '__iter__') and not isinstance(row_genres_val, str):
                            item_genres = set([str(g).strip() for g in row_genres_val if g])
                        # Check if any selected genre is in item genres
                        if any(gf in item_genres for gf in genre_filter):
                            filtered_recs.append(rec)
                recs = filtered_recs
            
            # Filter by type
            if type_filter and "type" in metadata.columns:
                before_count = len(recs)
                print(f"[TYPE FILTER] Active filter: {type_filter}")
                print(f"[TYPE FILTER] Processing {before_count} recommendations...")
                filtered_recs = []
                types_found = {}
                for rec in recs:
                    anime_id = rec["anime_id"]
                    row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
                    if not row_df.empty:
                        item_type = row_df.iloc[0].get("type")
                        type_str = str(item_type).strip() if pd.notna(item_type) else "None"
                        types_found[type_str] = types_found.get(type_str, 0) + 1
                        # Handle NaN and convert to string for comparison
                        if pd.notna(item_type) and str(item_type).strip() in type_filter:
                            filtered_recs.append(rec)
                after_count = len(filtered_recs)
                print(f"[TYPE FILTER] Types in recommendations: {dict(sorted(types_found.items(), key=lambda x: -x[1]))}")
                print(f"[TYPE FILTER] Result: {before_count} → {after_count} (removed {before_count - after_count})")
                recs = filtered_recs
            
            # Filter by year range
            if year_range[0] > 1960 or year_range[1] < 2025:
                filtered_recs = []
                for rec in recs:
                    anime_id = rec["anime_id"]
                    row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
                    if not row_df.empty:
                        aired_from = row_df.iloc[0].get("aired_from")
                        if aired_from:
                            try:
                                if isinstance(aired_from, str):
                                    year = int(aired_from[:4])
                                    if year_range[0] <= year <= year_range[1]:
                                        filtered_recs.append(rec)
                            except Exception:
                                pass
                recs = filtered_recs
            
            # Sort recommendations
            if sort_by != default_sort_for_mode:
                # Enrich recs with metadata for sorting
                enriched_recs = []
                for rec in recs:
                    anime_id = rec["anime_id"]
                    row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
                    if not row_df.empty:
                        row = row_df.iloc[0]
                        rec_copy = rec.copy()
                        rec_copy["_mal_score"] = row.get("mal_score") if pd.notna(row.get("mal_score")) else 0
                        rec_copy["_year"] = 0
                        aired_from = row.get("aired_from")
                        if aired_from and isinstance(aired_from, str):
                            try:
                                rec_copy["_year"] = int(aired_from[:4])
                            except Exception:
                                pass
                        rec_copy["_popularity"] = _pop_pct_for_anime_id(int(anime_id))
                        enriched_recs.append(rec_copy)
                
                # Sort based on selected option
                if sort_by == "MAL Score":
                    enriched_recs.sort(key=lambda x: x["_mal_score"], reverse=True)
                elif sort_by == "Year (Newest)":
                    enriched_recs.sort(key=lambda x: x["_year"], reverse=True)
                elif sort_by == "Year (Oldest)":
                    enriched_recs.sort(key=lambda x: x["_year"], reverse=False)
                elif sort_by == "Popularity":
                    enriched_recs.sort(key=lambda x: x["_popularity"], reverse=False)  # Lower percentile = more popular
                
                recs = enriched_recs
            
            # After all filtering and sorting, trim to requested top_n
            recs = recs[:top_n]

# Active scoring path indicator (single source of truth: derived from executed flags)
active_scoring_path = None
if browse_mode:
    active_scoring_path = "Browse"
else:
    ui_mode_main = str(st.session_state.get("ui_mode", "Seed-based"))
    personalized_gate_reason = locals().get("personalized_gate_reason")
    if ui_mode_main == "Personalized" and personalized_gate_reason:
        active_scoring_path = "Personalized (Unavailable)"
    else:
        if recommender is None or components is None:
            active_scoring_path = "Ranked modes disabled"
        elif locals().get("personalization_applied", False):
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
    and not locals().get("personalization_applied", False)
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
        and not locals().get("personalization_applied", False)
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
    
    if view_mode_state == "grid":
        # Grid layout: 3 columns
        # Process in batches of 3 for grid layout
        for i in range(0, len(recs), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(recs):
                    rec = recs[i + j]
                    anime_id = rec["anime_id"]
                    row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
                    if not row_df.empty:
                        row = row_df.iloc[0]
                        pop_pct = _pop_pct_for_anime_id(int(anime_id))
                        with col:
                            render_card_grid(row, rec, pop_pct, is_in_training=_is_in_training(int(anime_id)))
    else:
        # List layout: standard cards
        for rec in recs:
            anime_id = rec["anime_id"]
            row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
            if row_df.empty:
                continue
            row = row_df.iloc[0]
            pop_pct = _pop_pct_for_anime_id(int(anime_id))
            render_card(row, rec, pop_pct, is_in_training=_is_in_training(int(anime_id)))
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
            # Cold-start / first-load clarity (mode-aware)
            st.markdown(
                "<div style='background: linear-gradient(135deg, #E8F4F8 0%, #F0F8FF 100%); border-radius: 12px; "
                "padding: 28px; margin: 28px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>"
                "<h3 style='color: #2C3E50; margin: 0 0 10px 0;'>What this is</h3>"
                "<p style='color: #7F8C8D; font-size: 1.0rem; margin: 0 0 10px 0;'>"
                "A hybrid anime recommender that ranks titles similar to your chosen seed title(s)."
                "</p>"
                "<p style='color: #2C3E50; font-weight: 600; margin: 0;'>What next: Pick a sample seed or choose 1 title in <b>Search &amp; Seeds</b>.</p>"
                "</div>",
                unsafe_allow_html=True,
            )


st.markdown("---")
# Note: Old explanation panel removed - explanations now shown inline on cards
render_diversity_panel(recs, metadata, is_browse=browse_mode)



# Help / FAQ ---------------------------------------------------------------
render_help_panel()
render_help_panel(ui_mode=str(st.session_state.get("ui_mode", "Seed-based")))

st.sidebar.caption("Prototype – performance instrumentation active.")
