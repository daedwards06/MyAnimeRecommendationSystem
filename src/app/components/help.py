"""Help / FAQ panel component."""
from __future__ import annotations
import streamlit as st

FAQ_MD = """
**Hybrid Logic** blends MF, kNN, and popularity components.
**Weights Toggle** illustrates accuracy vs. diversity emphasis.
**Cold-Start** items rely on content similarity (no interactions).
**Latency Targets:** <250ms inference typical; profiling printed to logs.
"""

def render_help_panel():
    with st.expander("Help / FAQ"):
        st.markdown(FAQ_MD)
