"""Onboarding / usage instructions component for the Streamlit app.

Provides a dismissible panel so first‑time users (non‑technical) understand
how to interact: choose a persona OR search & select a title seed, then adjust
weights and read explanations/badges.
"""
from __future__ import annotations
import streamlit as st

_HELP_STEPS = [
    "Pick a persona (left) OR search a title.",
    "If searching: click a result to use it as a seed.",
    "Adjust 'Hybrid Weights' for accuracy vs diversity.",
    "Hover badges (coming soon) to learn popularity/novelty.",
    "Use the FAQ at bottom for metric explanations.",
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
        st.write("Seed vs Persona")
        st.caption(
            "Persona simulates a user profile. A seed title finds similar anime. You can switch freely; selecting a seed overrides persona for that run."
        )
        st.markdown("**Tip:** After clicking a search result the heading changes to 'Similar to: <Title>' so you know seed mode is active.")
        if st.button("Got it – hide instructions"):
            st.session_state[key] = True

__all__ = ["render_onboarding"]