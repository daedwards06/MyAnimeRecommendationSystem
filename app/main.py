"""Streamlit application entry point for MARS.

Thin orchestrator that wires together the focused modules:
- ``app.state``           — session-state initialisation & query-param helpers
- ``app.sidebar``         — sidebar rendering (profile, personalization, search, filters)
- ``app.pipeline_runner`` — recommender engine construction & pipeline execution
- ``app.display``         — CSS injection, header, card rendering, empty states, footer
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# ── Project imports ──────────────────────────────────────────────────────────
from app.display import (
    inject_css,
    render_empty_state,
    render_footer,
    render_header,
    render_import_light_warning,
    render_onboarding_section,
    render_results,
)
from app.pipeline_runner import (
    RecommenderEngine,
    build_recommender_engine,
    render_artifact_load_failure,
    run_recommendations,
)
from app.sidebar import render_sidebar
from app.state import init_mode_state, init_session_state, setup_first_run
from src.app.artifacts_loader import build_artifacts
from src.app.constants import PERSONAS_JSON
from src.app.theme import get_theme

# ── Logging ──────────────────────────────────────────────────────────────────
log_level = logging.DEBUG if os.getenv("DEBUG_LOGGING") else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Cached loaders ───────────────────────────────────────────────────────────


@st.cache_resource(show_spinner=False)
def init_bundle():
    """Load and cache the full artifact bundle."""
    return build_artifacts()


@st.cache_data(show_spinner=False)
def load_personas(path: str) -> list[dict]:
    """Load persona definitions from JSON."""
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


# ── Lightweight-import mode (for test_app_import) ────────────────────────────
IMPORT_LIGHT = bool(os.environ.get("APP_IMPORT_LIGHT"))

if IMPORT_LIGHT:
    bundle: dict = {
        "metadata": pd.DataFrame(
            {
                "anime_id": [1],
                "title_display": ["Dummy"],
                "genres": [""],
                "synopsis_snippet": [""],
            }
        ),
        "models": {},
        "explanations": {},
        "diversity": {},
        "_import_light": True,
    }
else:
    try:
        bundle = init_bundle()
    except Exception as e:
        render_artifact_load_failure(e)

metadata: pd.DataFrame = bundle["metadata"]
personas = load_personas(PERSONAS_JSON)

# ── Page configuration ───────────────────────────────────────────────────────
st.set_page_config(page_title="Anime Explorer", layout="wide", page_icon="🎬")
theme = get_theme()

# ── State initialisation ─────────────────────────────────────────────────────
init_mode_state()
init_session_state()

# ── CSS & header ─────────────────────────────────────────────────────────────
inject_css(theme)
_ui_mode_for_header = str(st.session_state.get("ui_mode", "Seed-based"))
render_header(_ui_mode_for_header, theme)
render_import_light_warning()
render_onboarding_section(_ui_mode_for_header)

# ── First-run experience: auto-populate default seed ─────────────────────────
setup_first_run(metadata, import_light=IMPORT_LIGHT)

# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_state = render_sidebar(
    bundle,
    metadata,
    personas,
    clear_cache_fn=getattr(init_bundle, "clear", None),
)

# ── Build recommender engine ─────────────────────────────────────────────────
engine: RecommenderEngine
if IMPORT_LIGHT:
    engine = RecommenderEngine()
else:
    engine = build_recommender_engine(bundle)

# ── Execute pipeline ─────────────────────────────────────────────────────────
pipeline_result = run_recommendations(engine, sidebar_state, bundle, metadata)

# ── Main-area content header ─────────────────────────────────────────────────
st.markdown("---")

if sidebar_state.browse_mode:
    if sidebar_state.genre_filter:
        genre_list_display = ", ".join(sidebar_state.genre_filter[:3])
        if len(sidebar_state.genre_filter) > 3:
            genre_list_display += f" +{len(sidebar_state.genre_filter) - 3} more"
        st.subheader(f"Browsing: {genre_list_display}")
    else:
        st.subheader("Browse by Genre")
        st.info("Select at least one genre in the sidebar to start browsing.")

elif (
    sidebar_state.ui_mode == "Personalized"
    and pipeline_result.personalized_gate_reason
):
    st.subheader("Your Recommendations")
    st.warning(
        f"Personalized mode selected, but it can't run: "
        f"{pipeline_result.personalized_gate_reason}"
    )
    st.info(
        "Fix it by adding ratings (or choosing a rated profile), then enable "
        "personalization in the sidebar. "
        "This app does not silently fall back to Seed-based results."
    )

else:
    # Show banner if default seed is active
    if (
        st.session_state.get("_default_seed_active", False)
        and sidebar_state.selected_seed_ids
        and sidebar_state.selected_seed_titles
    ):
        st.info(
            f"Showing recommendations based on **{sidebar_state.selected_seed_titles[0]}** "
            "— change the seed in the sidebar to explore."
        )

    if sidebar_state.selected_seed_ids and sidebar_state.selected_seed_titles:
        if len(sidebar_state.selected_seed_titles) == 1:
            st.subheader(f"Similar to {sidebar_state.selected_seed_titles[0]}")
        else:
            seed_display = ", ".join(sidebar_state.selected_seed_titles[:3])
            if len(sidebar_state.selected_seed_titles) > 3:
                seed_display += (
                    f" +{len(sidebar_state.selected_seed_titles) - 3} more"
                )
            st.subheader(f"Blended from {seed_display}")
    else:
        label = (
            "Your Recommendations"
            if sidebar_state.ui_mode == "Personalized"
            else "Recommendations"
        )
        st.subheader(label)

# ── Results / empty state ────────────────────────────────────────────────────
if pipeline_result.recs:
    render_results(
        pipeline_result.recs,
        metadata,
        sidebar_state,
        pipeline_result,
        pop_pct_fn=engine.pop_pct_for_anime_id,
        is_in_training_fn=engine.is_in_training,
        theme=theme,
    )
elif sidebar_state.browse_mode and sidebar_state.genre_filter:
    # Browse returned zero results
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
elif not sidebar_state.browse_mode and engine.recommender is None:
    st.error(
        "Recommendation engine is unavailable because required artifacts did not "
        "load. Disable APP_IMPORT_LIGHT and ensure MF artifacts are present/valid."
    )
elif not sidebar_state.browse_mode:
    render_empty_state(sidebar_state, pipeline_result, metadata)

# ── Footer (diversity panel + help) ──────────────────────────────────────────
st.markdown("---")
render_footer(
    pipeline_result.recs,
    metadata,
    sidebar_state.browse_mode,
    str(st.session_state.get("ui_mode", "Seed-based")),
)
