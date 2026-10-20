"""Streamlit application entry point for MARS.

Thin orchestrator that wires together the focused modules:
- ``app.state``           — session-state initialisation & query-param helpers
- ``app.sidebar``         — sidebar rendering (profile, personalization, search, filters)
- ``app.pipeline_runner`` — recommender engine construction & pipeline execution
- ``app.display``         — header, card rendering, empty states, footer
- ``app.styles``          — the stylesheet, injected once per run
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
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
    ENGINE_UNAVAILABLE_TEXT,
    render_artifact_notice,
    render_empty_results,
    render_empty_state,
    render_footer,
    render_header,
    render_import_light_warning,
    render_intro_section,
    render_personalized_gate,
    render_results,
    render_title_card,
    start_panel_html,
)
from app.pipeline_runner import (
    RecommenderEngine,
    build_recommender_engine,
    render_artifact_load_failure,
    run_recommendations,
)
from app.sidebar import render_sidebar
from app.state import (
    DEFAULT_SEED_TITLE,
    init_mode_state,
    init_session_state,
    setup_first_run,
)
from app.styles import inject_styles
from src.app.artifacts_loader import build_artifacts
from src.app.constants import PERSONAS_JSON

# ── Logging ──────────────────────────────────────────────────────────────────
log_level = logging.DEBUG if os.getenv("DEBUG_LOGGING") else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Cached loaders ───────────────────────────────────────────────────────────


@st.cache_resource(show_spinner="Now loading… model files (first visit only)")
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


# ── Page configuration ───────────────────────────────────────────────────────
# Before the bundle loads, so the cold-load status line is not the first Streamlit command.
st.set_page_config(page_title="MARS", layout="wide", page_icon="🎬")

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

# ── State initialisation ─────────────────────────────────────────────────────
init_mode_state()
init_session_state()

# ── CSS & header ─────────────────────────────────────────────────────────────
inject_styles()
_ui_mode_for_header = str(st.session_state.get("ui_mode", "Seed-based"))
render_header(_ui_mode_for_header)
# Filled after the sidebar runs, so it reflects this run's seeds.
intro_slot = st.empty()
render_import_light_warning()
render_artifact_notice(bundle.get("load_report"))

# ── First-run experience: auto-populate default seed ─────────────────────────
setup_first_run(metadata, import_light=IMPORT_LIGHT)

# ── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_state = render_sidebar(
    bundle,
    metadata,
    personas,
    clear_cache_fn=getattr(init_bundle, "clear", None),
)

with intro_slot.container():
    render_intro_section(
        sidebar_state.ui_mode,
        list(sidebar_state.selected_seed_titles or []),
        default_seed_title=(
            DEFAULT_SEED_TITLE if st.session_state.get("_default_seed_active", False) else None
        ),
    )

# ── Build recommender engine ─────────────────────────────────────────────────
engine: RecommenderEngine
if IMPORT_LIGHT:
    engine = RecommenderEngine()
else:
    engine = build_recommender_engine(bundle)

# ── Execute pipeline ─────────────────────────────────────────────────────────
pipeline_start = time.perf_counter()
pipeline_result = run_recommendations(engine, sidebar_state, bundle, metadata)
pipeline_elapsed = (time.perf_counter() - pipeline_start) * 1000
st.session_state["_pipeline_ms"] = pipeline_elapsed

# ── Main-area content header ─────────────────────────────────────────────────
st.markdown("---")

# Shown in the results title card with the count, or alone when there are no results.
section_title: str | None = None
if sidebar_state.browse_mode:
    if sidebar_state.genre_filter:
        genre_list_display = ", ".join(sidebar_state.genre_filter[:3])
        if len(sidebar_state.genre_filter) > 3:
            genre_list_display += f" +{len(sidebar_state.genre_filter) - 3} more"
        section_title = f"Browsing: {genre_list_display}"
    else:
        render_title_card("Browse by Genre")
        st.markdown(
            start_panel_html(
                "Pick a genre to start", "Choose one or more genres under Refine in the sidebar."
            ),
            unsafe_allow_html=True,
        )

elif (
    sidebar_state.ui_mode == "Personalized"
    and pipeline_result.personalized_gate_reason
):
    render_title_card("Your Recommendations")
    render_personalized_gate(pipeline_result.personalized_gate_reason)

else:
    if sidebar_state.selected_seed_ids and sidebar_state.selected_seed_titles:
        if len(sidebar_state.selected_seed_titles) == 1:
            section_title = f"Similar to {sidebar_state.selected_seed_titles[0]}"
        else:
            seed_display = ", ".join(sidebar_state.selected_seed_titles[:3])
            if len(sidebar_state.selected_seed_titles) > 3:
                seed_display += (
                    f" +{len(sidebar_state.selected_seed_titles) - 3} more"
                )
            section_title = f"Blended from {seed_display}"
    else:
        section_title = (
            "Your Recommendations"
            if sidebar_state.ui_mode == "Personalized"
            else "Recommendations"
        )

# ── Results / empty state ────────────────────────────────────────────────────
if section_title and not pipeline_result.recs:
    render_title_card(section_title)

if pipeline_result.recs:
    render_results(
        pipeline_result.recs,
        metadata,
        sidebar_state,
        pipeline_result,
        title=section_title or "Recommendations",
        pop_pct_fn=engine.pop_pct_for_anime_id,
        is_in_training_fn=engine.is_in_training,
    )
elif sidebar_state.browse_mode:
    if sidebar_state.genre_filter:
        render_empty_results(sidebar_state, "browse")
elif pipeline_result.personalized_gate_reason:
    pass  # explained once, under the section title above
elif engine.recommender is None:
    st.error(ENGINE_UNAVAILABLE_TEXT)
else:
    render_empty_state(sidebar_state, metadata)

# ── Footer (diversity panel, help, scoring details) ──────────────────────────
st.markdown("---")
render_footer(
    pipeline_result.recs,
    metadata,
    sidebar_state.browse_mode,
    str(st.session_state.get("ui_mode", "Seed-based")),
    pipeline=pipeline_result,
    load_report=bundle.get("load_report"),
    pipeline_ms=pipeline_elapsed,
)
