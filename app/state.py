"""Session-state initialisation and query-param helpers for MARS.

Provides pure state management with no Streamlit widget rendering.
Used by app/main.py and app/sidebar.py.
"""

from __future__ import annotations

import hashlib
import json

import streamlit as st

from src.app.constants import DEFAULT_TOP_N


# ── Query-param helpers ──────────────────────────────────────────────────────


def qp_get(key: str, default):
    """Read a Streamlit query parameter, normalizing list vs scalar."""
    val = st.query_params.get(key, default)
    if isinstance(val, list):
        return val[0] if val else default
    return val


# ── Stable cache key ─────────────────────────────────────────────────────────


def ratings_signature(ratings_dict: dict) -> str:
    """Stable SHA-256 signature for a ratings dict (cache invalidation)."""
    items = sorted((int(k), float(v)) for k, v in (ratings_dict or {}).items())
    payload = json.dumps(items, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ── Session-state initialisation ─────────────────────────────────────────────


def init_mode_state() -> None:
    """Initialise mode-tracking session-state keys.

    Must be called before any widget that reads ``ui_mode``.
    """
    if "_ui_mode_prev" not in st.session_state:
        st.session_state["_ui_mode_prev"] = st.session_state.get("ui_mode")
    if "_personalization_autoset" not in st.session_state:
        st.session_state["_personalization_autoset"] = False


def init_session_state() -> None:
    """Set session-state defaults for the MARS app.

    Reads query parameters for initial values where applicable.
    """
    for key, default in {
        "query": qp_get("q", ""),
        "weight_mode": qp_get("wm", "Balanced"),
        "top_n": int(qp_get("n", DEFAULT_TOP_N)),
        "sort_by": qp_get("sort", "Match score"),
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


def setup_first_run(metadata, *, import_light: bool = False) -> None:
    """Auto-populate default seed on first visit (Seed-based mode only).

    Ensures portfolio reviewers see recommendations immediately.
    """
    if (
        not st.session_state.get("_first_load_done", False)
        and not st.session_state.get("selected_seed_ids")
        and str(st.session_state.get("ui_mode", "Seed-based")) == "Seed-based"
        and not import_light
    ):
        _default_title = "Fullmetal Alchemist: Brotherhood"
        _fmab_rows = metadata[metadata["title_display"] == _default_title]
        if not _fmab_rows.empty:
            _fmab_id = int(_fmab_rows.iloc[0]["anime_id"])
            st.session_state["selected_seed_ids"] = [_fmab_id]
            st.session_state["selected_seed_titles"] = [_default_title]
            st.session_state["_default_seed_active"] = True
        st.session_state["_first_load_done"] = True
