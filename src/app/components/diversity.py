"""Diversity & novelty panel component."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from src.app.diversity import coverage, genre_exposure_ratio, average_novelty
from src.utils import coerce_genres


def render_diversity_panel(recs: list[dict], metadata: pd.DataFrame, *, is_browse: bool = False) -> None:
    st.subheader("Diversity & Novelty Summary")
    if not recs:
        st.info("No titles to summarize yet." if is_browse else "No recommendations to summarize yet.")
        return
    cov = coverage(recs)
    safe_metadata = metadata
    if "genres" in safe_metadata.columns:
        try:
            safe_metadata = safe_metadata.copy()
            safe_metadata["genres"] = safe_metadata["genres"].map(lambda v: coerce_genres(v))
        except Exception:  # pragma: no cover
            pass
    genre_ratio = genre_exposure_ratio(recs, safe_metadata)
    avg_nov = average_novelty(recs)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Coverage (unique/total)", f"{cov:.2f}")
    with col2:
        st.metric("Genre Exposure Ratio", f"{genre_ratio:.3f}")
    with col3:
        if avg_nov is None:
            st.metric("Avg Novelty (profile)", "NA")
        else:
            st.metric("Avg Novelty (profile)", f"{avg_nov:.3f}")

    st.caption(
        "Novelty is only computed when a rated profile is active. "
        "Popularity bands shown per item (Top 10%, Top 25%, Mid, Long Tail)."
    )
