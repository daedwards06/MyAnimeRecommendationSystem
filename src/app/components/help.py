"""Help / FAQ panel component."""
from __future__ import annotations

import streamlit as st

FAQ_MD_RANKED = """
**Match score (relative):** a unitless, uncalibrated ranking signal (higher = better match). Compare within the current run (not a probability or /10 rating).

**Modes:**
- **Seed-based:** uses 1–5 seed titles to rank results.
- **Personalized:** uses your rated profile history to rank results. If you have no ratings (or no MF overlap), personalization is unavailable and the UI explains why.
- **Browse:** filters/sorts the catalog only (metadata-only).

**Seeds (1–5):** selecting multiple seeds blends their signals to broaden discovery.

**Personalization:** requires rated history in your active profile. If you have no ratings (or no MF overlap), personalization is unavailable and novelty is **NA**. The app does not silently switch modes.

**Component shares:** when shown, MF / Pop (etc.) reflect the components actually used for that item.

**Cold-start badge:** means the title is not in the MF model’s training set; some scoring/explanations may be limited.

**Performance:** see the sidebar panel for the most recent ranking timing.
"""

FAQ_MD_BROWSE = """
**Browse mode:** filters/sorts the catalog using metadata only.

**Filters:** genre/type/year filters apply in all modes. In Browse, you need at least one selected genre to see titles.

**Seeds & personalization:** not used in Browse. Switch to **Seed-based** (1–5 seeds) or **Personalized** (rated profile) to get ranked results.

**Performance:** timing is shown for ranked modes.
"""

def render_help_panel(*, ui_mode: str | None = None):
    with st.expander("Help / FAQ"):
        if str(ui_mode or "").strip() == "Browse":
            st.markdown(FAQ_MD_BROWSE)
        else:
            st.markdown(FAQ_MD_RANKED)
