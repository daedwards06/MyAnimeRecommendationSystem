"""Streamlit application entry point for Phase 5.

Features:
  - Persona selection (sample personas JSON)
  - Title fuzzy search
  - Hybrid weight toggle (balanced vs diversity-emphasized)
  - Top-N recommendations with explanation shares & badges
  - Diversity summary placeholder (coverage / novelty to be integrated)
  - Help / FAQ section
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Ensure project root is on sys.path when running `streamlit run app/main.py`
ROOT_DIR = Path(__file__).resolve().parents[1]
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

from src.app.artifacts_loader import build_artifacts
from src.app.components.cards import render_card, render_card_grid
from src.app.components.diversity import render_diversity_panel
from src.app.components.help import render_help_panel
from src.app.components.skeletons import render_card_skeleton  # retained import (may repurpose later)
from src.app.components.instructions import render_onboarding
from src.app.quality_filters import apply_quality_filters
from src.app.components.explanation_panel import render_explanation_panel
from src.app.theme import get_theme
from src.app.constants import (
    DEFAULT_TOP_N,
    PERSONAS_JSON,
)
from src.app.recommender import (
    HybridComponents,
    HybridRecommender,
    choose_weights,
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


if os.environ.get("APP_IMPORT_LIGHT"):
    # Lightweight import mode for tests: avoid loading heavy artifacts.
    bundle = {"metadata": pd.DataFrame({"anime_id": [1], "title_display": ["Dummy"], "genres": [""], "synopsis_snippet": [""]}), "models": {}, "explanations": {}, "diversity": {}}
else:
    bundle = init_bundle()

metadata: pd.DataFrame = bundle["metadata"]
personas = load_personas(PERSONAS_JSON)

st.set_page_config(page_title="Anime Recommender", layout="wide", page_icon="🎬")
theme = get_theme()

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

st.title("🎬 Anime Recommendation System")
st.markdown("<p style='color: #7F8C8D; font-size: 1.1rem; margin-top: -10px;'>Discover your next favorite anime with AI-powered recommendations</p>", unsafe_allow_html=True)

if os.environ.get("APP_IMPORT_LIGHT"):
    st.warning("Lightweight import mode is active (APP_IMPORT_LIGHT=1). Images and full metadata may be unavailable. Restart without this flag to see thumbnails.")
render_onboarding()

# Sidebar Controls ---------------------------------------------------------
st.sidebar.header("Controls")
if st.sidebar.button("Reload artifacts"):
    try:
        init_bundle.clear()  # type: ignore[attr-defined]
    except Exception:
        st.sidebar.warning("Could not clear cache; please restart the app.")
    st.rerun()
persona_labels = [p["label"] for p in personas] if personas else []
params = st.query_params
# Persisting image debug toggle across reruns
img_debug = st.sidebar.checkbox("Debug images", value=bool(st.session_state.get("__IMG_DEBUG__", False)))
st.session_state["__IMG_DEBUG__"] = img_debug

def _qp_get(key: str, default):
    val = params.get(key, default)
    # Streamlit's new query_params may return str or list; normalize
    if isinstance(val, list):
        return val[0] if val else default
    return val

# Initialize session state defaults
for key, default in {
    "persona_choice": _qp_get("persona", None) or (persona_labels[0] if persona_labels else "(none)"),
    "query": _qp_get("q", ""),
    "weight_mode": _qp_get("wm", "Balanced"),
    "top_n": int(_qp_get("n", DEFAULT_TOP_N)),
    "sort_by": _qp_get("sort", "Confidence"),
    "genre_filter": [],
    "year_min": 1960,
    "year_max": 2025,
    "view_mode": "list",
    "selected_seed_ids": [],
    "selected_seed_titles": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

persona_choice = st.sidebar.selectbox("Persona", options=persona_labels or ["(none)"], index=(persona_labels.index(st.session_state["persona_choice"]) if persona_labels and st.session_state.get("persona_choice") in persona_labels else 0))

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
    help="Select 1-5 anime to blend their recommendations. More seeds = broader discovery!"
)

# Update query for backward compatibility
query = selected_titles[0] if selected_titles else ""

weight_mode = st.sidebar.radio("Hybrid Weights", ["Balanced", "Diversity"], index=(0 if st.session_state.get("weight_mode") != "Diversity" else 1), horizontal=True)
top_n = st.sidebar.slider("Top N", 5, 30, int(st.session_state.get("top_n", DEFAULT_TOP_N)))

# Sort and Filter Controls
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Sort & Filter")

# Browse mode toggle
browse_mode = st.sidebar.checkbox(
    "🗂️ Browse by Genre",
    value=st.session_state.get("browse_mode", False),
    help="Explore anime by genre without needing a seed recommendation"
)
st.session_state["browse_mode"] = browse_mode

if browse_mode:
    st.sidebar.info("💡 Select at least one genre to browse")

sort_by = st.sidebar.selectbox(
    "Sort by",
    ["Confidence", "MAL Score", "Year (Newest)", "Year (Oldest)", "Popularity"],
    index=["Confidence", "MAL Score", "Year (Newest)", "Year (Oldest)", "Popularity"].index(st.session_state.get("sort_by", "Confidence"))
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
    help="Show only anime with these genres"
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
    help="Show only TV series, Movies, OVAs, etc."
)

year_range = st.sidebar.slider(
    "Release Year Range",
    min_value=1960,
    max_value=2025,
    value=(st.session_state.get("year_min", 1960), st.session_state.get("year_max", 2025)),
    help="Filter anime by release year"
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
if genre_filter or year_range[0] > 1960 or year_range[1] < 2025 or sort_by != "Confidence":
    if st.sidebar.button("🔄 Reset Filters", help="Clear all filters and reset to defaults"):
        st.session_state["sort_by"] = "Confidence"
        st.session_state["genre_filter"] = []
        st.session_state["year_min"] = 1960
        st.session_state["year_max"] = 2025
        st.rerun()

# Performance Metrics Display
st.sidebar.markdown("---")
with st.sidebar.expander("⚡ Performance", expanded=False):
    # Get latest timing from profiling context if available
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
            st.caption("No timing data yet - generate recommendations first")
    except Exception:
        st.caption("Run recommendations to see metrics")
    
    # Memory estimate
    import sys
    if hasattr(bundle, '__sizeof__'):
        mem_mb = sys.getsizeof(bundle) / (1024 * 1024)
        st.markdown(f"""
        <div style='background: #F8F9FA; border-radius: 6px; padding: 12px;'>
            <p style='margin: 0; font-size: 0.85rem; color: #7F8C8D;'>Bundle Size</p>
            <p style='margin: 0; font-size: 1.3rem; font-weight: 600; color: #3498DB;'>{mem_mb:.1f}MB</p>
        </div>
        """, unsafe_allow_html=True)

# User Profile (Watchlist Import) ----------------------------------------
st.sidebar.markdown("---")
with st.sidebar.expander("👤 User Profile", expanded=False):
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
    
    selected_profile = st.selectbox(
        "Active Profile",
        options=profile_options,
        index=profile_options.index(current_selection) if current_selection in profile_options else 0,
        help="Select a profile to hide already-watched anime from recommendations"
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
        
        st.success(f"✓ **{profile['username']}** – {watched_count} watched")
        if avg_rating > 0:
            st.caption(f"Avg Rating: {avg_rating:.1f}/10")
    else:
        st.info("💡 Import your MAL watchlist to hide anime you've already watched")
    
    st.markdown("---")
    st.markdown("**Import from MyAnimeList**")
    
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
                    # Save uploaded file temporarily
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Get summary
                    summary = get_mal_export_summary(tmp_path)
                    st.session_state["mal_summary"] = summary
                    st.session_state["mal_tmp_path"] = tmp_path
                    
                except Exception as e:
                    st.error(f"Error parsing XML: {e}")
        
        with col2:
            if st.button("🔄 Parse", use_container_width=True):
                try:
                    # Use temp path from preview or create new one
                    if "mal_tmp_path" not in st.session_state:
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                    else:
                        tmp_path = st.session_state["mal_tmp_path"]
                    
                    # Parse with options
                    with st.spinner("Parsing MAL export..."):
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
                    st.error(f"Error parsing: {e}")
    
    # Show preview summary
    if "mal_summary" in st.session_state:
        summary = st.session_state["mal_summary"]
        st.markdown("**Preview:**")
        st.caption(f"Username: {summary['username']}")
        st.caption(f"Total: {summary['total_anime']} anime ({summary['rated_count']} rated)")
    
    # Show parsed data and save option
    if st.session_state["parsed_mal_data"]:
        parsed = st.session_state["parsed_mal_data"]
        
        st.markdown("**Import Summary:**")
        st.caption(f"✓ {parsed['stats']['total_watched']} anime matched")
        st.caption(f"✓ {parsed['stats']['rated_count']} with ratings")
        
        if parsed['unmatched']:
            # Use warning instead of nested expander (Streamlit doesn't allow nested expanders)
            unmatched_titles = ", ".join([entry['title'] for entry in parsed['unmatched'][:3]])
            if len(parsed['unmatched']) > 3:
                unmatched_titles += f" +{len(parsed['unmatched']) - 3} more"
            st.warning(f"⚠️ {len(parsed['unmatched'])} unmatched: {unmatched_titles}")
        
        # Username input and save
        username_input = st.text_input(
            "Profile Name",
            value=parsed.get('username', 'my_profile'),
            help="Choose a name for this profile"
        )
        
        if st.button("💾 Save Profile", type="primary", use_container_width=True):
            try:
                save_profile(username_input, parsed)
                st.session_state["active_profile"] = load_profile(username_input)
                st.session_state["parsed_mal_data"] = None  # Clear parsed data
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
                st.error(f"Failed to save: {e}")

# Quick Usage Hints ------------------------------------------------------
with st.sidebar.expander("💡 Quick Guide", expanded=False):
    st.markdown("""
    <div style='font-size: 0.9rem; line-height: 1.8;'>
    1️⃣ Search a title OR pick a persona<br>
    2️⃣ Select from dropdown to set seed<br>
    3️⃣ Adjust hybrid weights as desired<br>
    4️⃣ Use sort/filter to refine results<br>
    5️⃣ Explore badges & explanations
    </div>
    """, unsafe_allow_html=True)

# Persist updates
st.session_state["persona_choice"] = persona_choice
st.session_state["query"] = query
st.session_state["weight_mode"] = weight_mode
st.session_state["top_n"] = top_n
st.query_params.update({"persona": persona_choice, "q": query, "wm": weight_mode, "n": str(top_n)})

weights = choose_weights(weight_mode)

# Persona summary ----------------------------------------------------------
if persona_choice != "(none)":
    persona_obj = next((p for p in personas if p["label"] == persona_choice), None)
    if persona_obj:
        st.sidebar.markdown(f"**Genres:** {', '.join(persona_obj['favorite_genres'])}")
        st.sidebar.caption(persona_obj["preference_summary"])


# Seed selection indicator & handler --------------------------------------
# Convert selected titles to IDs
selected_seed_ids = []
selected_seed_titles = []
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


# Hybrid recommender initialization (placeholder scores) ------------------
# NOTE: Replace placeholders with actual loaded matrices from models bundle.
num_items = len(metadata)
dummy_item_ids = metadata["anime_id"].to_numpy()

# Minimal dummy arrays to allow UI demonstration.
mf_scores = None
knn_scores = None
pop_scores = None
if "mf_sgd_v1.0" in bundle["models"]:
    # Placeholder: expecting precomputed score matrix attribute or a method.
    # Fallback zeros if not present.
    model = bundle["models"]["mf_sgd_v1.0"]
    if hasattr(model, "scores"):
        mf_scores = model.scores  # type: ignore[attr-defined]
if mf_scores is None:
    mf_scores = (0.01 * (1 + (dummy_item_ids % 5))).reshape(1, -1)
if knn_scores is None:
    knn_scores = (0.005 * (1 + (dummy_item_ids % 7))).reshape(1, -1)
if pop_scores is None:
    pop_scores = (0.002 * (1 + (dummy_item_ids % 11)))

# Precompute popularity percentiles for display (lower = more popular)
pop_percentiles = compute_popularity_percentiles(pop_scores.astype(float))

components = HybridComponents(
    mf=mf_scores,
    knn=knn_scores,
    pop=pop_scores,
    item_ids=dummy_item_ids,
)
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
        st.info("👈 Select at least one genre from the sidebar to start browsing")
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
                            "score": float(row.get("mal_score", 0) if pd.notna(row.get("mal_score")) else 0),
                            "explanation": {"browse": "catalog"},
                            "_mal_score": float(row.get("mal_score", 0) if pd.notna(row.get("mal_score")) else 0),
                            "_year": 0,
                            "_popularity": float(pop_percentiles[idx]) if idx < len(pop_percentiles) else 50.0
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
            else:  # Confidence / MAL Score as default
                browse_results.sort(key=lambda x: x["_mal_score"], reverse=True)
            
            # Limit to top N for performance
            recs = browse_results[:min(top_n, len(browse_results))]
            
            if not recs:
                st.warning("No anime found matching your filters. Try adjusting your genre or year selections.")
else:
    # Recommendation mode (existing logic)
    if selected_seed_ids and selected_seed_titles:
        if len(selected_seed_titles) == 1:
            st.subheader(f"Similar to: {selected_seed_titles[0]}")
        else:
            seed_display = ", ".join(selected_seed_titles[:3])
            if len(selected_seed_titles) > 3:
                seed_display += f" +{len(selected_seed_titles)-3} more"
            st.subheader(f"Blended from: {seed_display}")
    else:
        st.subheader("Recommendations")
    user_index = 0  # demo user index (persona mapping to be added)
    
    # Request extra recommendations to account for filtering
    # If filters are active (including profile exclusion), request more to ensure we have enough after filtering
    has_profile = st.session_state["active_profile"] is not None
    filter_multiplier = 10 if (has_profile or genre_filter or type_filter or year_range[0] > 1960 or year_range[1] < 2025) else 1
    n_requested = min(top_n * filter_multiplier, components.num_items if hasattr(components, "num_items") else len(metadata))
    
    recs: list[dict] = []
    if n_requested > 0:
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
                    
                    num_seeds = len(selected_seed_ids)
                    
                    # Get blended hybrid scores for user to incorporate global preference signal.
                    try:
                        blended_scores = recommender._blend(user_index, weights)  # pylint: disable=protected-access
                    except Exception:
                        blended_scores = None
                    
                    # Map anime_id -> index for quick lookup.
                    id_to_index = {int(aid): idx for idx, aid in enumerate(components.item_ids)}
                    scored: list[dict] = []
                    
                    for _, mrow in metadata.iterrows():
                        aid = int(mrow["anime_id"])
                        if aid in selected_seed_ids:
                            continue
                        
                        # Exclude watched anime (profile filter)
                        if st.session_state["active_profile"]:
                            watched_ids = st.session_state["active_profile"].get("watched_ids", [])
                            if aid in watched_ids:
                                continue
                        
                        # Parse genres - handle both string and array formats
                        row_genres = mrow.get("genres")
                        if isinstance(row_genres, str):
                            item_genres = set([g.strip() for g in row_genres.split("|") if g.strip()])
                        elif hasattr(row_genres, '__iter__') and not isinstance(row_genres, str):
                            item_genres = set([str(g).strip() for g in row_genres if g])
                        else:
                            item_genres = set()
                        
                        # Weighted overlap: sum of genre weights for matching genres, normalized to 0-1
                        # Maximum possible overlap would be if item has all seed genres
                        raw_overlap = sum(genre_weights.get(g, 0) for g in item_genres)
                        max_possible_overlap = len(all_seed_genres) * num_seeds  # Each genre could appear in all seeds
                        weighted_overlap = raw_overlap / max_possible_overlap if max_possible_overlap > 0 else 0.0
                        
                        # Track which seeds this item matches
                        overlap_per_seed = {
                            seed_title: len(seed_genres & item_genres)
                            for seed_title, seed_genres in seed_genre_map.items()
                        }
                        num_seeds_matched = sum(1 for count in overlap_per_seed.values() if count > 0)
                        
                        if blended_scores is not None and aid in id_to_index:
                            hybrid_val = float(blended_scores[id_to_index[aid]])
                            # Popularity percentile (invert so lower percentile => higher boost)
                            pop_pct = float(pop_percentiles[id_to_index[aid]]) if id_to_index[aid] < len(pop_percentiles) else 50.0
                            popularity_boost = max(0.0, (50.0 - pop_pct) / 50.0)  # scale 0..1 favoring more popular mildly
                        else:
                            hybrid_val = 0.0
                            popularity_boost = 0.0
                        
                        # Weighted average scoring: emphasize matches across multiple seeds
                        # (matches/num_seeds) gives proportion of seeds matched
                        seed_coverage = num_seeds_matched / num_seeds
                        
                        # Final score: weighted overlap + seed coverage bonus + hybrid signal + popularity
                        score = (0.5 * weighted_overlap) + (0.2 * seed_coverage) + (0.25 * hybrid_val) + (0.05 * popularity_boost)
                        
                        if score <= 0:
                            continue
                        
                        explanation = {
                            "seed_titles": selected_seed_titles,
                            "overlap_per_seed": overlap_per_seed,
                            "weighted_overlap": weighted_overlap,
                            "seeds_matched": num_seeds_matched,
                            "seed_coverage": seed_coverage,
                            "common_genres": list(all_seed_genres & item_genres),
                        }
                        # Append hybrid contribution shares if available
                        if aid in id_to_index:
                            explanation.update(recommender.explain_item(user_index, id_to_index[aid], weights))
                        
                        scored.append({
                            "anime_id": aid,
                            "score": score,
                            "explanation": explanation,
                        })
                    
                    scored.sort(key=lambda x: x["score"], reverse=True)
                    recs = scored[:n_requested]
                else:
                    recs = recommender.get_top_n_for_user(user_index, n=n_requested, weights=weights)
        
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
            if sort_by != "Confidence":
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
                        rec_copy["_popularity"] = float(pop_percentiles[metadata.index[metadata["anime_id"] == anime_id][0]]) if len(metadata.index[metadata["anime_id"] == anime_id]) > 0 else 50.0
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

def _compute_confidence_stars(score: float) -> str:
    """Convert recommendation score to visual star rating (1-5 stars)."""
    # Normalize score to 0-5 range (assuming scores typically 0-1 or 0-10)
    if score > 1.0:
        normalized = min(score / 2.0, 5.0)  # If score is 0-10 range
    else:
        normalized = score * 5.0  # If score is 0-1 range
    
    full_stars = int(normalized)
    half_star = (normalized - full_stars) >= 0.5
    
    stars = "⭐" * full_stars
    if half_star and full_stars < 5:
        stars += "⭐"
    empty = max(0, 5 - len(stars))
    stars += "☆" * empty
    
    return stars[:5]  # Ensure exactly 5 characters

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
    item_type = "anime" if browse_mode else "Recommendations"
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
    
    if sort_by != "Confidence":
        st.markdown(f"<p style='color: #7F8C8D; font-size: 0.9rem; margin-top: -8px; margin-bottom: 20px;'>Sorted by: {sort_by}</p>", unsafe_allow_html=True)
    
    # Calculate diversity mix
    pop_count = sum(1 for r in recs if "Top 25%" in str(badge_payload(
        is_in_training=True,
        pop_percentile=float(pop_percentiles[metadata.index[metadata["anime_id"] == r["anime_id"]][0]]) if len(metadata.index[metadata["anime_id"] == r["anime_id"]]) > 0 else 50.0,
        user_genre_hist={},
        item_genres=[]
    ).get("popularity_band", "")))
    long_tail_count = sum(1 for r in recs if "Long-tail" in str(badge_payload(
        is_in_training=True,
        pop_percentile=float(pop_percentiles[metadata.index[metadata["anime_id"] == r["anime_id"]][0]]) if len(metadata.index[metadata["anime_id"] == r["anime_id"]]) > 0 else 50.0,
        user_genre_hist={},
        item_genres=[]
    ).get("popularity_band", "")))
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
    
    st.markdown(f"""
    <div style="background: #F8F9FA; border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
        <p style="color: #7F8C8D; font-size: 0.9rem; margin-bottom: 12px; font-weight: 500;">Recommendation Mix</p>
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
                        idx = metadata.index[metadata["anime_id"] == anime_id][0]
                        pop_pct = float(pop_percentiles[idx])
                        with col:
                            render_card_grid(row, rec, pop_pct)
    else:
        # List layout: standard cards
        for rec in recs:
            anime_id = rec["anime_id"]
            row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
            if row_df.empty:
                continue
            row = row_df.iloc[0]
            idx = metadata.index[metadata["anime_id"] == anime_id][0]
            pop_pct = float(pop_percentiles[idx])
            render_card(row, rec, pop_pct)
else:
    if selected_seed_ids and not recs:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #FFF3CD 0%, #FCF8E3 100%); border-left: 4px solid #F0AD4E; border-radius: 8px; padding: 20px; margin: 20px 0;'>
            <p style='color: #8A6D3B; font-weight: 500; margin: 0;'>⚠️ No similar titles found – try another seed or adjust filters</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Enhanced empty state with modern design
        st.markdown("""
        <div style='background: linear-gradient(135deg, #E8F4F8 0%, #F0F8FF 100%); border-radius: 12px; padding: 40px; margin: 40px 0; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
            <h2 style='color: #2C3E50; margin-bottom: 16px;'>👋 Welcome to Anime Recommender!</h2>
            <p style='color: #7F8C8D; font-size: 1.1rem; margin-bottom: 32px;'>Get personalized anime recommendations powered by AI</p>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 700px; margin: 0 auto;'>
                <div style='background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);'>
                    <div style='font-size: 2rem; margin-bottom: 12px;'>🔍</div>
                    <h4 style='color: #2C3E50; margin-bottom: 8px;'>Browse Titles</h4>
                    <p style='color: #7F8C8D; font-size: 0.9rem;'>Use the 'Search Title' dropdown in the sidebar to explore 13,000+ anime</p>
                </div>
                <div style='background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);'>
                    <div style='font-size: 2rem; margin-bottom: 12px;'>⚡</div>
                    <h4 style='color: #2C3E50; margin-bottom: 8px;'>Quick Start</h4>
                    <p style='color: #7F8C8D; font-size: 0.9rem;'>Click one of the popular titles in the sidebar for instant recommendations</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("---")
if recs:
    render_explanation_panel(recs, top_k=min(5, len(recs)))
    st.markdown("---")
render_diversity_panel(recs, metadata)


# Help / FAQ ---------------------------------------------------------------
render_help_panel()

st.sidebar.caption("Phase 5 prototype – performance instrumentation active.")
