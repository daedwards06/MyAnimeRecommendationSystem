"""Skeleton loading components for perceived performance."""
from __future__ import annotations
import streamlit as st

# Simple CSS shimmer style (can be expanded later)
_SKELETON_STYLE = """
<style>
.skel-box {background: #2A2F36; border-radius: 4px; height: 260px; width: 100%; position: relative; overflow: hidden;}
.skel-box:before {content:''; position:absolute; top:0; left:-40%; height:100%; width:40%; background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.08), rgba(255,255,255,0)); animation: shimmer 1.2s infinite;}
@keyframes shimmer {0% {left:-40%;} 100% {left:100%;}}
</style>
"""


def inject_skeleton_css():
    st.markdown(_SKELETON_STYLE, unsafe_allow_html=True)


def render_card_skeleton(count: int = 5):
    if count <= 0:
        return
    inject_skeleton_css()
    cols = st.columns(min(count, 5))
    for i in range(count):
        with cols[i % len(cols)]:
            st.markdown('<div class="skel-box"></div>', unsafe_allow_html=True)
