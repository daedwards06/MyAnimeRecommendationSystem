"""Onboarding / usage instructions component for the Streamlit app.

Provides a dismissible panel so first‑time users understand the current UX:
- Seed-based recommendations (pick 1–5 titles)
- Optional personalization (requires ratings)
- Browse-by-genre mode (no recommender scoring)
"""
from __future__ import annotations
import streamlit as st

_HELP_STEPS = [
    "Pick 1–5 seed titles in the sidebar (Search & Seeds) to get recommendations.",
    "(Optional) Load a profile to exclude watched titles; add ratings to enable personalization.",
    "(Optional) Turn on Personalization (only works when you have ratings in your active profile).",
    "Adjust Hybrid Weights + filters (genre/type/year) to steer discovery.",
    "Use Browse by Genre to explore the catalog without match scores or explanations.",
]

def render_onboarding():
    # Persist dismissal
    key = "__ONBOARD_DISMISSED__"
    dismissed = st.session_state.get(key, False)
    if dismissed:
        return
    with st.expander("How to use this app (click to hide)", expanded=True):
        st.markdown("### Quick Start")
        st.write("Follow these steps to generate meaningful recommendations:")
        for i, step in enumerate(_HELP_STEPS, start=1):
            st.markdown(f"**{i}.** {step}")
        st.markdown("---")
        st.write("What the modes mean")
        st.caption(
            "Seed-based recommendations use your selected title(s) as anchors. "
            "Personalization uses your rated history (if available). "
            "Browse by Genre filters/sorts metadata only (no recommender match score)."
        )
        st.markdown("**Tip:** When seeds are active, the sidebar shows an **Active Seed(s)** indicator.")
        if st.button("Got it – hide instructions"):
            st.session_state[key] = True

__all__ = ["render_onboarding"]