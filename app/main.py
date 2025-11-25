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
from src.app.components.cards import render_card
from src.app.components.diversity import render_diversity_panel
from src.app.components.help import render_help_panel
from src.app.components.skeletons import render_card_skeleton  # retained import (may repurpose later)
from src.app.components.instructions import render_onboarding
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

st.set_page_config(page_title="Anime Recommender", layout="wide")
theme = get_theme()
st.title("Anime Recommendation System")
st.caption("Phase 5 prototype – modular refactor in progress.")
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

available_titles = ["(none)"] + sorted(title_to_id.keys())
current_query = st.session_state.get("query", "")
if current_query and current_query in available_titles:
    default_idx = available_titles.index(current_query)
else:
    default_idx = 0

selected_title = st.sidebar.selectbox(
    "Search Title",
    options=available_titles,
    index=default_idx,
    help="Browse and select an anime title to use as a seed for recommendations"
)
query = selected_title if selected_title != "(none)" else ""

weight_mode = st.sidebar.radio("Hybrid Weights", ["Balanced", "Diversity"], index=(0 if st.session_state.get("weight_mode") != "Diversity" else 1), horizontal=True)
top_n = st.sidebar.slider("Top N", 5, 30, int(st.session_state.get("top_n", DEFAULT_TOP_N)))

# Quick Usage Hints ------------------------------------------------------
with st.sidebar.expander("Quick Steps", expanded=True):
    st.markdown(
        "1. Search a title OR pick a persona.\n"
        "2. Click a search match to set it as a seed.\n"
        "3. Adjust hybrid weights (Balanced vs Diversity).\n"
        "4. Explore badges (popularity band, novelty) & explanations."
    )

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
selected_seed_id = st.session_state.get("selected_seed_id")
selected_seed_title = st.session_state.get("selected_seed_title")

# Auto-select seed when title chosen from dropdown
if query and query != st.session_state.get("last_query"):
    # Use title_to_id mapping for direct lookup
    aid = title_to_id.get(query)
    if aid:
        st.session_state["selected_seed_id"] = aid
        st.session_state["selected_seed_title"] = query
        st.session_state["last_query"] = query
        selected_seed_id = aid
        selected_seed_title = query

# Prominent seed indicator
if selected_seed_id and selected_seed_title:
    st.sidebar.success(f"🎯 **Active Seed**: {selected_seed_title}")
    if st.sidebar.button("✖ Clear Seed", key="clear_seed"):
        st.session_state.pop("selected_seed_id", None)
        st.session_state.pop("selected_seed_title", None)
        st.session_state["last_query"] = ""
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
                    # Use title_to_id mapping
                    aid = title_to_id.get(sample)
                    if aid:
                        st.session_state["selected_seed_id"] = aid
                        st.session_state["selected_seed_title"] = sample
                        st.session_state["query"] = sample
                        st.session_state["last_query"] = sample
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
if selected_seed_id and selected_seed_title:
    st.subheader(f"Similar to: {selected_seed_title}")
else:
    st.subheader("Recommendations")
user_index = 0  # demo user index (persona mapping to be added)

# Ensure we do not request more items than available (important for APP_IMPORT_LIGHT mode).
n_eff = min(top_n, components.num_items if hasattr(components, "num_items") else len(metadata))

recs: list[dict] = []
if n_eff > 0:
    # Compute recommendations with progress indicator
    with st.spinner("🔍 Finding recommendations..."):
        with latency_timer("recommendations"):
            if selected_seed_id:
                # Refined seed similarity path: genre overlap blended with hybrid scores & popularity.
                seed_row = metadata.loc[metadata["anime_id"] == selected_seed_id].head(1)
                if not seed_row.empty:
                    seed_genres = set(str(seed_row.iloc[0].get("genres", "")).split("|"))
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
                        if aid == selected_seed_id:
                            continue
                        gset = set(str(mrow.get("genres", "")).split("|"))
                        overlap = len(seed_genres & gset)
                        if blended_scores is not None and aid in id_to_index:
                            hybrid_val = float(blended_scores[id_to_index[aid]])
                            # Popularity percentile (invert so lower percentile => higher boost)
                            pop_pct = float(pop_percentiles[id_to_index[aid]]) if id_to_index[aid] < len(pop_percentiles) else 50.0
                            popularity_boost = max(0.0, (50.0 - pop_pct) / 50.0)  # scale 0..1 favoring more popular mildly
                        else:
                            hybrid_val = 0.0
                            popularity_boost = 0.0
                        # Final score components: emphasize overlap, then hybrid, then mild popularity
                        score = (0.7 * overlap) + (0.25 * hybrid_val) + (0.05 * popularity_boost)
                        if score <= 0:
                            continue
                        explanation = {
                            "overlap_genres": list(seed_genres & gset),
                            "genre_overlap_count": overlap,
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
                    recs = scored[:n_eff]
            else:
                recs = recommender.get_top_n_for_user(user_index, n=n_eff, weights=weights)

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
    # Result count and diversity summary
    st.markdown(f"### Showing {len(recs)} recommendations")
    
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
    
    # Visual diversity bar
    total = len(recs)
    pop_pct = (pop_count / total * 100) if total > 0 else 0
    mid_pct = (mid_count / total * 100) if total > 0 else 0
    long_pct = (long_tail_count / total * 100) if total > 0 else 0
    
    cols = st.columns([pop_pct/100 if pop_pct > 0 else 0.01, mid_pct/100 if mid_pct > 0 else 0.01, long_pct/100 if long_pct > 0 else 0.01])
    with cols[0]:
        st.markdown(f'<div style="background:#E74C3C;padding:8px;text-align:center;color:white;border-radius:4px;">🔥 Popular {pop_count}</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div style="background:#3498DB;padding:8px;text-align:center;color:white;border-radius:4px;">📊 Balanced {mid_count}</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div style="background:#9B59B6;padding:8px;text-align:center;color:white;border-radius:4px;">🌟 Exploratory {long_tail_count}</div>', unsafe_allow_html=True)
    
    st.markdown("---")

if recs:
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
    if selected_seed_id and not recs:
        st.warning("No similar titles found via genre overlap – try another seed or broaden search.")
    else:
        # Enhanced empty state with guidance
        st.info("👋 **Welcome!** To get started:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Option 1: Browse Titles**")
            st.caption("Use the 'Search Title' dropdown in the sidebar to browse all available anime.")
        with col2:
            st.markdown("**Option 2: Try a Sample**")
            st.caption("Click one of the popular titles in the sidebar for instant recommendations.")


st.markdown("---")
if recs:
    render_explanation_panel(recs, top_k=min(5, len(recs)))
    st.markdown("---")
render_diversity_panel(recs, metadata)


# Help / FAQ ---------------------------------------------------------------
render_help_panel()

st.sidebar.caption("Phase 5 prototype – performance instrumentation active.")
