"""Onboarding / usage instructions component for the Streamlit app.

Provides a dismissible panel so first‑time users understand the current UX.

Phase 3 / Chunk 2 adds a top-level mode selector, so this component
supports mode-aware copy.
"""
from __future__ import annotations
import streamlit as st

def _steps_for_mode(ui_mode: str) -> list[str]:
    if ui_mode == "Browse":
        return [
            "Choose **Browse** mode in the sidebar.",
            "Pick ≥1 genre in Filters to see titles.",
            "Refine with type/year and sort by MAL score / year / popularity.",
        ]
    if ui_mode == "Personalized":
        return [
            "Choose **Personalized** mode in the sidebar.",
            "Select an **Active Profile** with at least one rating (or rate an anime after loading a profile).",
            "Personalization runs only when rated history overlaps the MF model; if unavailable, the sidebar explains why.",
        ]
    # Seed-based (default)
    return [
        "On first visit, you'll see recommendations for **Fullmetal Alchemist: Brotherhood** — a great starting point!",
        "Change the seed anytime: Pick 1–5 seed titles in **Search & Seeds** (or use the sample buttons).",
        "Adjust Hybrid Weights + filters (genre/type/year) to steer discovery.",
    ]


def render_onboarding(*, ui_mode: str = "Seed-based"):
    # Persist dismissal
    key = "__ONBOARD_DISMISSED__"
    dismissed = st.session_state.get(key, False)
    if dismissed:
        return
    with st.expander("How to use this app (click to hide)", expanded=True):
        st.markdown("### Quick Start")
        if ui_mode == "Browse":
            st.write("Follow these steps to start browsing:")
        else:
            st.write("Follow these steps to get ranked results:")

        for i, step in enumerate(_steps_for_mode(ui_mode), start=1):
            st.markdown(f"**{i}.** {step}")
        st.markdown("---")
        st.write("What the modes mean")
        if ui_mode == "Browse":
            st.caption(
                "Browse filters/sorts catalog metadata only. "
                "Seed-based uses your selected title(s) as anchors. "
                "Personalized uses your rated history (when available)."
            )
        else:
            st.caption(
                "Seed-based uses your selected title(s) as anchors. "
                "Personalized uses your rated history (when available). "
                "Browse filters/sorts catalog metadata only."
            )
            st.caption("Ranked modes display scores as **Match score (relative)** (unitless; compare within a run).")
        if ui_mode in {"Seed-based", "Personalized"}:
            st.markdown("**Tip:** When seeds are active, the sidebar shows an **Active Seed(s)** indicator.")
        if st.button("Got it – hide instructions"):
            st.session_state[key] = True

__all__ = ["render_onboarding"]