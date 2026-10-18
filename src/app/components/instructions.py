"""One-line intro under the header: what is showing and where to change it.

Dismissible; its "How it works" button opens the Help panel in the footer.
"""
from __future__ import annotations

import streamlit as st

_MODE_HINTS: dict[str, str] = {
    "Browse": "Pick one or more genres in the sidebar to browse the catalog",
    "Personalized": "Load a rated profile in the sidebar to rank titles from your ratings",
    "Seed-based": "Pick 1–5 titles you love in the sidebar to find similar anime",
}


def intro_line(
    ui_mode: str,
    seed_titles: list[str],
    *,
    default_seed_title: str | None = None,
) -> str:
    """Markdown for the intro line; names the default seed while it is the only seed."""
    if (
        ui_mode == "Seed-based"
        and default_seed_title is not None
        and seed_titles == [default_seed_title]
    ):
        return (
            f"Showing picks for **{default_seed_title}** — pick your own titles in the sidebar"
        )
    return _MODE_HINTS.get(ui_mode, _MODE_HINTS["Seed-based"])


def render_intro_line(
    ui_mode: str,
    seed_titles: list[str],
    *,
    default_seed_title: str | None = None,
) -> None:
    if st.session_state.get("intro_dismissed", False):
        return

    text_col, help_col, close_col = st.columns([8, 1.6, 0.6], vertical_alignment="center")
    with text_col:
        st.markdown(intro_line(ui_mode, seed_titles, default_seed_title=default_seed_title))
    with help_col:
        st.button(
            "How it works",
            key="intro_how_it_works",
            on_click=_set_state,
            args=("help_expanded",),
        )
    with close_col:
        st.button(
            "✕", key="intro_dismiss", help="Dismiss", on_click=_set_state, args=("intro_dismissed",)
        )


def _set_state(key: str) -> None:
    st.session_state[key] = True


__all__ = ["intro_line", "render_intro_line"]
