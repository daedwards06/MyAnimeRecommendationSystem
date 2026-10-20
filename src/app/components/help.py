"""Help / FAQ panel component."""
from __future__ import annotations

import streamlit as st

FAQ_MD_USER = """
**What am I looking at?** Anime picked to match the titles you chose (Seed-based), your ratings (Personalized), or your genre filters (Browse). Higher on the list means a closer match.

**How do I get better picks?** Add 1–5 titles you love in the sidebar; more titles broaden the mix. For picks from your whole watch history, load a rated profile or import your MyAnimeList list and switch to Personalized.

**What do "Top match" and "Worth a look" mean?** They are relative to the current run: the first quarter of this list is "Top match", then "Strong match", "Good match", and "Worth a look". The "#N" next to the label is the title's rank in this run. Change your titles or filters and the tiers are recomputed. They are not ratings out of 10 or probabilities.
"""

FAQ_MD_RANKED = """
**Match score (relative):** a unitless, uncalibrated ranking signal (higher = better match). Compare within the current run (not a probability or /10 rating). Card labels are within-run rank quartiles; hover a label for the rank and raw score.

**Modes:**
- **Seed-based:** uses 1–5 seed titles to rank results.
- **Personalized:** uses your rated profile history to rank results. If you have no ratings (or no MF overlap), personalization is unavailable and the UI explains why.
- **Browse:** filters/sorts the catalog only (metadata-only).

**Seeds (1–5):** selecting multiple seeds blends their signals to broaden discovery.

**Personalization:** requires rated history in your active profile. If you have no ratings (or no MF overlap), personalization is unavailable and the genre-novelty flag is hidden. The app does not silently switch modes.

**Component shares:** when shown, MF / Pop (etc.) reflect the components actually used for that item.

**Few ratings badge:** the title is not in the MF model’s training set (cold-start), so it is matched on content and popularity; some explanations may be limited.

**Performance:** see the sidebar panel or Scoring details for the most recent ranking timing.
"""

FAQ_MD_BROWSE = """
**Browse mode:** filters/sorts the catalog using metadata only.

**Filters:** genre/type/year filters apply in all modes. In Browse, you need at least one selected genre to see titles.

**Seeds & personalization:** not used in Browse. Switch to **Seed-based** (1–5 seeds) or **Personalized** (rated profile) to get ranked results.

**Performance:** timing is shown for ranked modes.
"""


def render_help_panel(*, ui_mode: str | None = None, expanded: bool = False):
    with st.expander("Help / FAQ", expanded=expanded):
        st.markdown(FAQ_MD_USER)
        st.markdown("#### For reviewers")
        if str(ui_mode or "").strip() == "Browse":
            st.markdown(FAQ_MD_BROWSE)
        else:
            st.markdown(FAQ_MD_RANKED)
