"""One-line intro under the header: what is showing and where to change it.

Dismissible; its "How it works" button opens the Help panel in the footer.
"""
from __future__ import annotations

import html
import re

import streamlit as st

_MODE_HINTS: dict[str, str] = {
    "Browse": "Pick one or more genres in the sidebar to browse the catalog",
    "Personalized": "Load a rated profile, or try a demo profile, in the sidebar to rank titles from ratings",
    "Seed-based": "Pick 1–5 titles you love in the sidebar to find similar anime",
}


def intro_line(
    ui_mode: str,
    seed_titles: list[str],
    *,
    default_seed_title: str | None = None,
    profile_name: str | None = None,
) -> str:
    """Markdown for the intro line; names the default seed while it is the only seed."""
    if ui_mode == "Personalized" and profile_name:
        return f"Ranked for **{profile_name}** from their ratings — change the profile in the sidebar"
    if (
        ui_mode == "Seed-based"
        and default_seed_title is not None
        and seed_titles == [default_seed_title]
    ):
        return (
            f"Showing picks for **{default_seed_title}** — pick your own titles in the sidebar"
        )
    return _MODE_HINTS.get(ui_mode, _MODE_HINTS["Seed-based"])


def intro_line_html(
    ui_mode: str,
    seed_titles: list[str],
    *,
    default_seed_title: str | None = None,
    profile_name: str | None = None,
) -> str:
    """The intro line as HTML; the markdown bold becomes the highlighted name."""
    text = html.escape(
        intro_line(
            ui_mode, seed_titles, default_seed_title=default_seed_title, profile_name=profile_name
        )
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong class='mars-intro-highlight'>\1</strong>", text)
    return f"<p class='mars-intro'>{text}</p>"


def render_intro_line(
    ui_mode: str,
    seed_titles: list[str],
    *,
    default_seed_title: str | None = None,
    profile_name: str | None = None,
) -> None:
    if st.session_state.get("intro_dismissed", False):
        return

    text_col, help_col, close_col = st.columns([8, 1.6, 0.6], vertical_alignment="center")
    with text_col:
        st.markdown(
            intro_line_html(
                ui_mode,
                seed_titles,
                default_seed_title=default_seed_title,
                profile_name=profile_name,
            ),
            unsafe_allow_html=True,
        )
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


__all__ = ["intro_line", "intro_line_html", "render_intro_line"]
