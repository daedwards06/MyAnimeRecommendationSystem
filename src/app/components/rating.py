"""Rating component for anime cards.

Provides UI for users to rate anime on a 1-10 scale and updates their profile.
"""

from __future__ import annotations
import streamlit as st
from src.data.user_profiles import load_profile, save_profile


def render_rating_widget(anime_id: int, title: str, current_rating: int | None = None) -> None:
    """Render a rating widget for an anime.
    
    Parameters
    ----------
    anime_id : int
        The anime ID to rate.
    title : str
        The anime title for display.
    current_rating : int | None
        Current rating if anime is already rated (1-10), or None.
    """
    # Check if profile is loaded
    profile = st.session_state.get("active_profile")
    if not profile:
        st.caption("💡 Load a profile to rate anime")
        return
    
    # Create unique key for this anime's rating
    rating_key = f"rating_input_{anime_id}"
    
    # Initialize rating in session state if not present
    if rating_key not in st.session_state:
        st.session_state[rating_key] = current_rating or 0
    
    # Rating display and input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Star rating selector (1-10 as 0.5 to 5.0 stars)
        rating_options = ["—"] + [f"{'⭐' * (i // 2)}{('½' if i % 2 else '')} {i}" for i in range(1, 11)]
        selected_index = st.session_state[rating_key] if st.session_state[rating_key] > 0 else 0
        
        new_rating_display = st.selectbox(
            "Your Rating",
            options=rating_options,
            index=selected_index,
            key=f"rating_select_{anime_id}",
            label_visibility="collapsed"
        )
        
        # Parse rating from display
        if new_rating_display == "—":
            new_rating = 0
        else:
            new_rating = int(new_rating_display.split()[-1])
    
    with col2:
        # Save button
        if st.button("💾", key=f"save_rating_{anime_id}", help="Save Rating", use_container_width=True):
            if new_rating > 0:
                _save_rating(anime_id, new_rating, title)
                st.session_state[rating_key] = new_rating
                st.success(f"✓ Rated {new_rating}/10")
                st.rerun()
            else:
                st.warning("Select a rating first")


def render_quick_rating_buttons(anime_id: int, title: str, current_rating: int | None = None) -> None:
    """Render quick rating buttons (👍 8, ❤️ 10, 👎 4).
    
    Parameters
    ----------
    anime_id : int
        The anime ID to rate.
    title : str
        The anime title for display.
    current_rating : int | None
        Current rating if already rated.
    """
    profile = st.session_state.get("active_profile")
    if not profile:
        return
    
    # Show current rating if exists
    if current_rating:
        st.caption(f"Your rating: {current_rating}/10")
    
    # Quick rating buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👍 8", key=f"quick_good_{anime_id}", help="Good (8/10)", use_container_width=True):
            _save_rating(anime_id, 8, title)
            st.rerun()
    
    with col2:
        if st.button("❤️ 10", key=f"quick_love_{anime_id}", help="Love it! (10/10)", use_container_width=True):
            _save_rating(anime_id, 10, title)
            st.rerun()
    
    with col3:
        if st.button("👎 4", key=f"quick_meh_{anime_id}", help="Meh (4/10)", use_container_width=True):
            _save_rating(anime_id, 4, title)
            st.rerun()


def _save_rating(anime_id: int, rating: int, title: str) -> None:
    """Save a rating to the user's profile.
    
    Parameters
    ----------
    anime_id : int
        The anime ID being rated.
    rating : int
        The rating value (1-10).
    title : str
        The anime title for logging.
    """
    profile = st.session_state.get("active_profile")
    if not profile:
        st.error("No active profile")
        return
    
    username = profile.get("username")
    if not username:
        st.error("Invalid profile")
        return
    
    # Reload profile to ensure we have latest data
    fresh_profile = load_profile(username)
    if not fresh_profile:
        st.error("Failed to load profile")
        return
    
    # Update ratings
    if "ratings" not in fresh_profile:
        fresh_profile["ratings"] = {}
    
    old_rating = fresh_profile["ratings"].get(str(anime_id))
    fresh_profile["ratings"][str(anime_id)] = rating
    
    # Add to watched list (you can't rate something you haven't watched)
    if "watched_ids" not in fresh_profile:
        fresh_profile["watched_ids"] = []
    if anime_id not in fresh_profile["watched_ids"]:
        fresh_profile["watched_ids"].append(anime_id)
    
    # Update stats
    if "stats" not in fresh_profile:
        fresh_profile["stats"] = {}
    
    fresh_profile["stats"]["total_watched"] = len(fresh_profile["watched_ids"])
    ratings_list = list(fresh_profile["ratings"].values())
    fresh_profile["stats"]["total_ratings"] = len(ratings_list)
    fresh_profile["stats"]["avg_rating"] = sum(ratings_list) / len(ratings_list) if ratings_list else 0.0
    
    # Save profile
    username = fresh_profile.get("username", "unknown")
    save_profile(username, fresh_profile)
    
    # Update session state
    st.session_state["active_profile"] = fresh_profile
    
    # Invalidate cached user embedding (force regeneration)
    if "user_embedding" in st.session_state:
        st.session_state["user_embedding"] = None
    
    # Log action
    action = "Updated" if old_rating else "Added"
    if old_rating:
        st.toast(f"{action} rating: {title} ({old_rating}/10 → {rating}/10)", icon="✏️")
    else:
        st.toast(f"{action} rating: {title} ({rating}/10)", icon="⭐")


def render_rating_history(max_recent: int = 10) -> None:
    """Render a list of recently rated anime.
    
    Parameters
    ----------
    max_recent : int
        Maximum number of recent ratings to display.
    """
    profile = st.session_state.get("active_profile")
    if not profile:
        st.info("💡 Load a profile to see your ratings")
        return
    
    ratings = profile.get("ratings", {})
    if not ratings:
        st.info("No ratings yet! Rate some anime to build your taste profile.")
        return
    
    st.markdown(f"**Your Ratings** ({len(ratings)} total)")
    
    # Sort by rating value (descending)
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Display recent ratings
    for anime_id, rating in sorted_ratings[:max_recent]:
        # Try to get title from metadata (would need to pass metadata)
        # For now, just show ID
        col1, col2 = st.columns([4, 1])
        with col1:
            st.caption(f"Anime {anime_id}")
        with col2:
            st.caption(f"{rating}/10")
    
    if len(ratings) > max_recent:
        st.caption(f"...and {len(ratings) - max_recent} more")
