"""Skeleton loading components for perceived performance; `.skel-box` lives in app/styles/components.css."""
from __future__ import annotations

import streamlit as st


def render_card_skeleton(count: int = 5):
    if count <= 0:
        return
    cols = st.columns(min(count, 5))
    for i in range(count):
        with cols[i % len(cols)]:
            st.markdown('<div class="skel-box"></div>', unsafe_allow_html=True)
