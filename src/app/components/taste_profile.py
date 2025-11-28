"""Taste profile visualization component.

Provides radar charts and visualizations for user taste profiles.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.models.user_embedding import get_user_taste_profile


def render_taste_profile_panel(profile: dict, metadata: pd.DataFrame) -> None:
    """Render a comprehensive taste profile panel.
    
    Parameters
    ----------
    profile : dict
        User profile containing ratings.
    metadata : pd.DataFrame
        Anime metadata for analysis.
    """
    ratings = profile.get("ratings", {})
    if not ratings or len(ratings) < 3:
        st.info("💡 Rate at least 3 anime to see your taste profile")
        return
    
    st.markdown("### 🎨 Your Taste Profile")
    
    # Get taste profile data
    taste = get_user_taste_profile(ratings, metadata, top_n_genres=10)
    
    # Tab layout for different visualizations
    tab1, tab2, tab3 = st.tabs(["Genre Preferences", "Rating Patterns", "Statistics"])
    
    with tab1:
        _render_genre_radar(taste["top_genres"])
    
    with tab2:
        _render_rating_distribution(taste["rating_distribution"])
    
    with tab3:
        _render_statistics(taste, len(ratings))


def _render_genre_radar(top_genres: list[tuple[str, float]]) -> None:
    """Render radar chart of genre preferences.
    
    Parameters
    ----------
    top_genres : list[tuple[str, float]]
        List of (genre, avg_rating) tuples.
    """
    if not top_genres:
        st.caption("No genre data available")
        return
    
    # Take top 8 genres for clean visualization
    top_8 = top_genres[:8]
    genres = [g[0] for g in top_8]
    ratings = [g[1] for g in top_8]
    
    # Create radar chart using plotly
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=ratings,
        theta=genres,
        fill='toself',
        name='Your Ratings',
        line=dict(color='#3498DB', width=2),
        fillcolor='rgba(52, 152, 219, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickvals=[2, 4, 6, 8, 10],
                ticktext=['2', '4', '6', '8', '10']
            )
        ),
        showlegend=False,
        title="Genre Preferences (Avg Rating)",
        height=400,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show full list below
    st.markdown("**All Genre Ratings:**")
    for genre, rating in top_genres[:15]:
        # Color-code by rating
        if rating >= 8.0:
            color = "#27AE60"
        elif rating >= 7.0:
            color = "#3498DB"
        elif rating >= 6.0:
            color = "#F39C12"
        else:
            color = "#95A5A6"
        
        st.markdown(
            f"<div style='display: flex; justify-content: space-between; padding: 4px 0;'>"
            f"<span>{genre}</span>"
            f"<span style='color: {color}; font-weight: 600;'>{rating:.1f}/10</span>"
            f"</div>",
            unsafe_allow_html=True
        )


def _render_rating_distribution(rating_distribution: dict[str, int]) -> None:
    """Render rating distribution bar chart.
    
    Parameters
    ----------
    rating_distribution : dict[str, int]
        Rating buckets and counts.
    """
    st.markdown("**How You Rate Anime:**")
    
    # Create bar chart
    buckets = ["9-10", "7-8", "5-6", "1-4"]
    counts = [rating_distribution.get(bucket, 0) for bucket in buckets]
    
    fig = go.Figure()
    
    colors = ['#27AE60', '#3498DB', '#F39C12', '#E74C3C']
    
    fig.add_trace(go.Bar(
        x=buckets,
        y=counts,
        marker=dict(color=colors),
        text=counts,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Rating Distribution",
        xaxis_title="Rating Range",
        yaxis_title="Number of Anime",
        height=350,
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show percentages
    total = sum(counts)
    if total > 0:
        st.markdown("**Breakdown:**")
        for bucket, count, color in zip(buckets, counts, colors):
            if count > 0:
                pct = (count / total) * 100
                st.markdown(
                    f"<div style='display: flex; justify-content: space-between; padding: 4px 0;'>"
                    f"<span>{bucket} stars</span>"
                    f"<span style='color: {color}; font-weight: 600;'>{count} ({pct:.1f}%)</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )


def _render_statistics(taste: dict, total_ratings: int) -> None:
    """Render overall statistics.
    
    Parameters
    ----------
    taste : dict
        Taste profile data.
    total_ratings : int
        Total number of ratings.
    """
    st.markdown("**Overall Stats:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Ratings", total_ratings)
        st.metric("Avg Rating", f"{taste['avg_rating']:.2f}/10")
    
    with col2:
        # Calculate generosity (% of ratings >= 7)
        dist = taste["rating_distribution"]
        generous_count = dist.get("9-10", 0) + dist.get("7-8", 0)
        generosity_pct = (generous_count / total_ratings * 100) if total_ratings > 0 else 0
        st.metric("Generosity", f"{generosity_pct:.0f}%", help="% of ratings 7+")
        
        # Calculate diversity (number of genres rated)
        genres_count = len(taste["top_genres"])
        st.metric("Genre Diversity", genres_count, help="Number of genres you've rated")
    
    # Rating tendencies
    st.markdown("---")
    st.markdown("**Your Rating Style:**")
    
    if taste["avg_rating"] >= 8.0:
        st.success("🌟 **Enthusiast** - You love most anime you watch!")
    elif taste["avg_rating"] >= 7.0:
        st.info("👍 **Balanced** - You appreciate quality but are selective")
    elif taste["avg_rating"] >= 6.0:
        st.warning("🤔 **Critical** - You have high standards")
    else:
        st.error("😐 **Tough Critic** - Very few anime meet your expectations")
    
    # Diversity insight
    if genres_count >= 15:
        st.success("🌈 **Genre Explorer** - You enjoy diverse anime styles")
    elif genres_count >= 8:
        st.info("🎯 **Genre Sampler** - You explore multiple genres")
    else:
        st.warning("🎬 **Genre Specialist** - You focus on specific genres")


def render_personalized_explanation(anime_title: str, similar_rated: list[str]) -> str:
    """Generate personalized explanation for recommendation.
    
    Parameters
    ----------
    anime_title : str
        The recommended anime title.
    similar_rated : list[str]
        Titles of similar anime the user rated highly.
    
    Returns
    -------
    str
        Explanation text.
    """
    if not similar_rated:
        return f"Based on your overall taste profile"
    
    if len(similar_rated) == 1:
        return f"Because you rated **{similar_rated[0]}** highly"
    elif len(similar_rated) == 2:
        return f"Because you rated **{similar_rated[0]}** and **{similar_rated[1]}** highly"
    else:
        return f"Because you rated **{similar_rated[0]}**, **{similar_rated[1]}**, and {len(similar_rated)-2} other similar anime highly"
