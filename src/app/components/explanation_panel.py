"""Explanation panel component for displaying recommendation source attribution.

Shows detailed breakdown of MF/kNN/popularity contributions for top recommendations.
"""

from __future__ import annotations

import streamlit as st


def render_explanation_panel(recs: list[dict], top_k: int = 5) -> None:
    """Render explanation panel showing source score breakdowns for top-K recommendations.
    
    Parameters
    ----------
    recs : list[dict]
        Recommendation list with 'anime_id', 'score', and 'explanation' dicts.
    top_k : int, default=5
        Number of top items to explain in detail.
    """
    if not recs:
        return
    
    with st.expander("🔍 **Why These Recommendations?** (Source Breakdown)", expanded=False):
        st.markdown(
            "This panel shows how each recommendation score is composed from "
            "**Matrix Factorization (MF)**, **k-Nearest Neighbors (kNN)**, and **Popularity (Pop)** signals."
        )
        
        display_recs = recs[:top_k]
        for i, rec in enumerate(display_recs, start=1):
            anime_id = rec.get("anime_id", "?")
            score = rec.get("score", 0.0)
            explanation = rec.get("explanation", {})
            
            # Extract source shares
            mf_share = explanation.get("mf", 0.0)
            knn_share = explanation.get("knn", 0.0)
            pop_share = explanation.get("pop", 0.0)
            
            # Additional seed-path metadata if present
            overlap_count = explanation.get("genre_overlap_count", None)
            overlap_genres = explanation.get("overlap_genres", [])
            
            st.markdown(f"**#{i} — Anime ID: {anime_id}** (Score: {score:.4f})")
            
            # Source contribution bars
            cols = st.columns([1, 1, 1])
            with cols[0]:
                st.metric("MF", f"{mf_share * 100:.1f}%")
            with cols[1]:
                st.metric("kNN", f"{knn_share * 100:.1f}%")
            with cols[2]:
                st.metric("Pop", f"{pop_share * 100:.1f}%")
            
            # Seed-path extra context
            if overlap_count is not None:
                st.caption(
                    f"Seed similarity: {overlap_count} overlapping genre(s) "
                    f"({', '.join(overlap_genres[:3]) if overlap_genres else 'N/A'})"
                )
            
            if i < len(display_recs):
                st.markdown("---")
        
        st.caption(
            "**Note**: Shares sum to 100% per item. Higher MF indicates strong collaborative signal; "
            "higher kNN suggests neighborhood similarity; higher Pop reflects dataset-wide engagement."
        )


__all__ = ["render_explanation_panel"]
