"""Help / FAQ panel component."""
from __future__ import annotations
import streamlit as st

FAQ_MD = """
**Match score (relative):** a unitless, uncalibrated ranking signal (higher = better match). Compare within the current run (not a probability or /10 rating).

**Modes:**
- **Recommendations:** uses seeds (and optionally your ratings) to rank titles.
- **Browse by Genre:** filters/sorts the catalog only (no match score and no “why this” explanation).

**Seeds (1–5):** selecting multiple seeds blends their signals to broaden discovery.

**Personalization:** requires rated history in your active profile. If you have no ratings (or no MF overlap), personalization is shown as unavailable and novelty is **NA**.

**Component shares:** when shown, MF / Pop (etc.) reflect the components actually used for that item.

**Cold-start badge:** means the title is not in the MF model’s training set; some scoring/explanations may be limited.

**Performance:** see the sidebar panel for the most recent inference timing.
"""

def render_help_panel():
    with st.expander("Help / FAQ"):
        st.markdown(FAQ_MD)
