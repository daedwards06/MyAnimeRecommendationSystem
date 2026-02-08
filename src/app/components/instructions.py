"""Onboarding / usage instructions component for the Streamlit app.

Provides a compact, dismissible panel so first-time users understand the UX.
"""
from __future__ import annotations

import streamlit as st

_MODE_STEPS: dict[str, list[str]] = {
    "Browse": [
        "Select **Browse** mode, then pick one or more genres to explore.",
        "Refine with type, year, or sort controls in the sidebar.",
    ],
    "Personalized": [
        "Load a **rated profile** (sidebar) with at least one rating.",
        "Results are re-ranked using your taste profile automatically.",
    ],
    "Seed-based": [
        "You'll see results for **Fullmetal Alchemist: Brotherhood** by default.",
        "Swap seeds anytime — pick 1–5 titles in the sidebar or click a sample button.",
        "Tweak hybrid weights and filters to steer discovery.",
    ],
}


def render_onboarding(*, ui_mode: str = "Seed-based"):
    key = "__ONBOARD_DISMISSED__"
    if st.session_state.get(key, False):
        return

    steps = _MODE_STEPS.get(ui_mode, _MODE_STEPS["Seed-based"])

    with st.expander("Quick start — click to dismiss", expanded=True):
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}.** {step}")
        st.caption(
            "**Modes:** Seed-based (similar titles) · Personalized (rated history) · Browse (catalog filters)"
        )
        if st.button("Got it", key="dismiss_onboarding"):
            st.session_state[key] = True

__all__ = ["render_onboarding"]
