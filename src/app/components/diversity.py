"""Diversity & novelty panel component."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.diversity import average_novelty, coverage, genre_exposure_ratio
from src.utils import coerce_genres


def render_diversity_panel(recs: list[dict], metadata: pd.DataFrame, *, is_browse: bool = False) -> None:
    with st.expander("Diversity & Novelty", expanded=False):
        if not recs:
            st.caption("No results to analyze yet.")
            return

        cov = coverage(recs)
        safe_metadata = metadata
        if "genres" in safe_metadata.columns:
            try:
                safe_metadata = safe_metadata.copy()
                safe_metadata["genres"] = safe_metadata["genres"].map(lambda v: coerce_genres(v))
            except Exception:
                pass
        genre_ratio = genre_exposure_ratio(recs, safe_metadata)
        avg_nov = average_novelty(recs)

        # Check if MMR was applied
        mmr_enabled = st.session_state.get("mmr_enabled", False)
        mmr_lambda = st.session_state.get("mmr_lambda", 0.3)

        # Show MMR status badge if enabled
        if mmr_enabled:
            st.markdown(
                f"<div style='background-color: #1A1A2E; padding: 8px 12px; "
                f"border-radius: 4px; margin-bottom: 12px; border-left: 3px solid #4ECDC4;'>"
                f"<span style='font-weight: 600; color: #4ECDC4;'>🎯 MMR Diversification Active</span> "
                f"<span style='color: #B0B0B0;'>• λ = {mmr_lambda:.1f}</span> "
                f"<span style='color: #888; font-size: 0.85em;'>"
                f"({'High diversity' if mmr_lambda < 0.4 else 'Balanced' if mmr_lambda < 0.7 else 'Relevance-focused'})"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Coverage", f"{cov:.2f}")
        with col2:
            st.metric("Genre Exposure", f"{genre_ratio:.3f}")
        with col3:
            st.metric("Avg Novelty", "NA" if avg_nov is None else f"{avg_nov:.3f}")

        st.caption(
            "Coverage = unique/total titles. Genre Exposure = ratio of genres represented. "
            "Novelty requires a rated profile."
        )
