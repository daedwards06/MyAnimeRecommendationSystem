from __future__ import annotations
from pathlib import Path
import streamlit as st
import pandas as pd
from src.app.badges import badge_payload
from src.app.components.tooltips import format_badge_tooltip
from src.app.components.rating import render_quick_rating_buttons
from src.app.score_semantics import SCORE_LABEL_SHORT, format_match_score, has_match_score


def _get_user_genre_hist_from_session() -> dict:
    try:
        hist = st.session_state.get("user_genre_hist")
        return hist if isinstance(hist, dict) else {}
    except Exception:  # pragma: no cover
        return {}

def coerce_genres(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(v) for v in value if v)
    try:  # numpy array handling
        import numpy as _np  # type: ignore
        if isinstance(value, _np.ndarray):
            return "|".join(str(v) for v in value.tolist() if v)
    except Exception:  # pragma: no cover
        pass
    return str(value)

def _render_placeholder_box(label: str):
    st.markdown(
        f'<div style="width:180px;height:260px;background:#2A2F36;display:flex;align-items:center;justify-content:center;border:1px solid #3A3F47;border-radius:4px;font-size:12px;color:#A5AFB9;">{label}</div>',
        unsafe_allow_html=True,
    )

def _render_image_streamlit(thumb_rel: str | None, title_display: str):
    """Render image using Streamlit's native image component."""
    if not thumb_rel:
        _render_placeholder_box("No Image")
        st.caption(f"{title_display} (no image available)")
        return

    # Resolve base path robustly relative to repo root, not CWD
    try:
        repo_root = Path(__file__).resolve().parents[3]
    except Exception:
        repo_root = Path(".").resolve()
    base_processed = repo_root / "data" / "processed"

    rel_path = Path(str(thumb_rel))
    img_path = rel_path if rel_path.is_absolute() else base_processed / rel_path
    debug = False
    try:
        debug = bool(st.session_state.get("__IMG_DEBUG__", False))
    except Exception:
        debug = False

    if debug:
        try:
            st.text(f"[img debug] rel={thumb_rel} | resolved={img_path} | exists={img_path.exists()}")
        except Exception:
            pass

    if img_path.exists():
        try:
            # Use Streamlit's native image component
            st.image(str(img_path), width=180, caption=title_display)
            if debug:
                st.caption(f"[img ok] {img_path}")
            return
        except Exception as e:
            _render_placeholder_box("Image Error")
            st.caption(f"{title_display} (failed to render)")
            if debug:
                st.caption(f"[img error] {img_path}: {e}")
            return

    _render_placeholder_box("Missing")
    st.caption(f"{title_display} (image missing)")
    if debug:
        st.caption(f"[img missing] {img_path}")

def render_card_grid(row, rec: dict, pop_pct: float, *, is_in_training: bool):
    """Render a compact grid card version."""
    # Extract anime_id early (needed for button keys)
    anime_id = int(row.get("anime_id"))
    
    raw_genres = row.get("genres")
    genres = coerce_genres(raw_genres)
    item_genres = [g for g in genres.split("|") if g]
    user_genre_hist = _get_user_genre_hist_from_session()
    badges = badge_payload(
        is_in_training=is_in_training,
        pop_percentile=pop_pct,
        user_genre_hist=user_genre_hist,
        item_genres=item_genres,
    )
    
    thumb = row.get("poster_thumb_url")
    
    # Title selection
    title_candidates = [
        row.get("title_english"),
        row.get("title_display"),
        row.get("title_primary"),
        row.get("title"),
    ]
    title_display = next((t for t in title_candidates if isinstance(t, str) and t.strip()), "Anime")
    
    # Metadata
    mal_score = row.get("mal_score")
    year = None
    aired_from = row.get("aired_from")
    if aired_from:
        try:
            if isinstance(aired_from, str):
                year = aired_from[:4]
        except Exception:
            pass
    
    card_color = "#3498DB" if not badges['cold_start'] else "#E67E22"
    
    # Use Streamlit container instead of manual HTML div
    # Manual divs don't work with st.image() - it renders outside the div
    container = st.container(border=True)
    with container:
        # Image
        _render_image_streamlit(thumb, title_display)
        
        # Title (truncated for grid) with match score badge (relative)
        truncated_title = title_display if len(title_display) <= 30 else title_display[:27] + "..."

        score = rec.get("score")
        score_badge = ""
        if has_match_score(score):
            score_str = format_match_score(float(score))
            score_badge = (
                f"<span style='background: #3498DB20; color: #3498DB; padding: 2px 6px; "
                f"border-radius: 8px; font-weight: 600;'>{SCORE_LABEL_SHORT}: {score_str}</span>"
            )

        st.markdown(
            f"<p style='font-weight: 600; font-size: 0.95rem; color: #2C3E50; margin: 8px 0 4px 0;'>{truncated_title}</p>",
            unsafe_allow_html=True,
        )
        if score_badge:
            st.markdown(f"<p style='font-size: 0.75rem; margin: 2px 0;'>{score_badge}</p>", unsafe_allow_html=True)
        
        # Personalized explanation (if available)
        explanation = rec.get("explanation")
        if explanation:
            st.markdown(f"<p style='font-size: 0.7rem; color: #7F8C8D; margin: 4px 0; font-style: italic;'>{explanation}</p>", unsafe_allow_html=True)
        
        # Score, type, and year
        meta_parts = []
        if mal_score:
            score_color = "#27AE60" if mal_score >= 8.0 else "#3498DB" if mal_score >= 7.0 else "#95A5A6"
            meta_parts.append(f'<span style="color: {score_color}; font-weight: 600;">⭐ {mal_score:.1f}</span>')
        
        # Type (TV, Movie, OVA, etc.)
        anime_type = row.get("type")
        if anime_type and pd.notna(anime_type):
            meta_parts.append(f'<span style="color: #9B59B6; font-weight: 600;">🎬 {anime_type}</span>')
        
        if year:
            meta_parts.append(f'<span style="color: #7F8C8D;">📅 {year}</span>')
        
        if meta_parts:
            st.markdown(f"<p style='font-size: 0.8rem; margin: 4px 0;'>{' • '.join(meta_parts)}</p>", unsafe_allow_html=True)
        
        # Genres (first 3) - clickable
        if genres:
            genre_list = [g.strip() for g in genres.split('|') if g.strip()][:3]
            if genre_list:
                cols = st.columns(len(genre_list))
                for idx, genre in enumerate(genre_list):
                    with cols[idx]:
                        if st.button(
                            genre,
                            key=f"grid_genre_{anime_id}_{genre}",
                            help=f"Browse {genre}",
                            type="secondary",
                            use_container_width=True
                        ):
                            # Enable browse mode and set genre filter
                            st.session_state["browse_mode"] = True
                            st.session_state["genre_filter"] = [genre]
                            st.session_state["selected_seed_ids"] = []
                            st.session_state["selected_seed_titles"] = []
                            st.rerun()
    
        # More Like This button - adds to seed list
        # anime_id already extracted at top of function
        current_ids = st.session_state.get("selected_seed_ids", [])
        current_titles = st.session_state.get("selected_seed_titles", [])
        
        if anime_id in current_ids:
            st.caption("✓ In seeds")
        elif len(current_ids) >= 5:
            st.caption("⚠️ Max 5")
        else:
            if st.button("🔄", key=f"grid_more_{anime_id}", help="Add to Seeds", use_container_width=True):
                current_ids.append(anime_id)
                current_titles.append(title_display)
                st.session_state["selected_seed_ids"] = current_ids
                st.session_state["selected_seed_titles"] = current_titles
                st.rerun()
        
        # Rating buttons (if profile loaded)
        profile = st.session_state.get("active_profile")
        if profile:
            current_rating = profile.get("ratings", {}).get(str(anime_id))
            st.markdown("---")
            render_quick_rating_buttons(anime_id, title_display, current_rating)

def render_card(row, rec: dict, pop_pct: float, *, is_in_training: bool):
    raw_genres = row.get("genres")
    genres = coerce_genres(raw_genres)
    item_genres = [g for g in genres.split("|") if g]
    user_genre_hist = _get_user_genre_hist_from_session()
    badges = badge_payload(
        is_in_training=is_in_training,
        pop_percentile=pop_pct,
        user_genre_hist=user_genre_hist,
        item_genres=item_genres,
    )
    rec["badges"] = badges
    thumb = row.get("poster_thumb_url")
    
    # Extract anime_id early (needed for button keys)
    anime_id = int(row.get("anime_id"))
    
    # Primary title: prefer English, fallback to display/primary/Japanese
    title_candidates = [
        row.get("title_english"),
        row.get("title_display"),
        row.get("title_primary"),
        row.get("title"),
        row.get("title_japanese"),
    ]
    title_display = next((t for t in title_candidates if isinstance(t, str) and t.strip()), "Anime")
    
    # Secondary title for reference (show Japanese or primary if different from main title)
    alt_title = None
    if row.get("title_japanese") and row.get("title_japanese") != title_display:
        alt_title = row.get("title_japanese")
    elif row.get("title_primary") and row.get("title_primary") != title_display:
        alt_title = row.get("title_primary")
    
    # Get synopsis - try full synopsis first, then snippet
    synopsis_val = row.get("synopsis") if "synopsis" in row else row.get("synopsis_snippet")
    # Handle pandas NaN/None values
    if synopsis_val is not None and pd.notna(synopsis_val) and str(synopsis_val).strip():
        display_synopsis = str(synopsis_val).strip()
    else:
        display_synopsis = ""
    
    # Extract metadata fields
    mal_score = row.get("mal_score")
    episodes = row.get("episodes")
    status = row.get("status")
    studios_raw = row.get("studios", [])
    studios = studios_raw if isinstance(studios_raw, list) else []
    source = row.get("source_material")
    
    # Extract year from aired_from
    year = None
    aired_from = row.get("aired_from")
    if aired_from:
        try:
            if isinstance(aired_from, str):
                year = aired_from[:4]
        except Exception:
            pass
    
    # Visual card container with modern design
    card_color = "#3498DB" if not badges['cold_start'] else "#E67E22"
    
    # Use Streamlit container instead of manual HTML div
    # Manual divs don't work with st.image() - it renders outside the div
    container = st.container(border=True)
    with container:
        # Render image using Streamlit's native image component to avoid HTML rendering issues
        _render_image_streamlit(thumb, title_display)
        
        # Recommendation score display (single semantic: Match score (relative))
        score = rec.get("score")
        score_badge = ""
        badge_color = "#3498DB"
        if has_match_score(score):
            score_str = format_match_score(float(score))
            score_badge = (
                f"<span style=\"background: {badge_color}20; color: {badge_color}; padding: 2px 8px; "
                f"border-radius: 12px; font-size: 0.85rem; font-weight: 600;\">{SCORE_LABEL_SHORT}: {score_str}</span>"
            )

        if score_badge:
            st.markdown(
                f"<h3 style='margin: 0; padding: 0; font-size: 1.25rem; color: #2C3E50;'>{title_display} {score_badge}</h3>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<h3 style='margin: 0; padding: 0; font-size: 1.25rem; color: #2C3E50;'>{title_display}</h3>",
                unsafe_allow_html=True,
            )
        
        # Alternative title (Japanese/original)
        if alt_title:
            st.markdown(f"<p style='color: #95A5A6; font-style: italic; font-size: 0.9rem; margin-top: 2px;'>{alt_title}</p>", unsafe_allow_html=True)
        
        # Personalized explanation (if available)
        explanation = rec.get("explanation")
        if explanation:
            st.markdown(f"<div style='background: #ECF0F1; padding: 8px 12px; border-radius: 6px; margin: 8px 0; border-left: 3px solid {badge_color};'><p style='font-size: 0.85rem; color: #34495E; margin: 0;'>{explanation}</p></div>", unsafe_allow_html=True)
        
        # Metadata row: Score, Type, Episodes, Year, Status
        meta_parts = []
        if mal_score:
            score_color = "#27AE60" if mal_score >= 8.0 else "#3498DB" if mal_score >= 7.0 else "#95A5A6"
            meta_parts.append(f'<span style="background: {score_color}20; color: {score_color}; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.85rem;">⭐ {mal_score:.2f}</span>')
        
        # Type (TV, Movie, OVA, etc.)
        anime_type = row.get("type")
        if anime_type and pd.notna(anime_type):
            meta_parts.append(f'<span style="color: #9B59B6; font-size: 0.9rem; font-weight: 600;">🎬 {anime_type}</span>')
        
        if episodes:
            meta_parts.append(f'<span style="color: #7F8C8D; font-size: 0.9rem;">📺 {episodes} eps</span>')
        if year:
            meta_parts.append(f'<span style="color: #7F8C8D; font-size: 0.9rem;">📅 {year}</span>')
        if status:
            status_icon = "✅" if status == "Finished Airing" else "🟢" if "Airing" in str(status) else "🔵"
            status_color = "#27AE60" if status == "Finished Airing" else "#E67E22" if "Airing" in str(status) else "#3498DB"
            meta_parts.append(f'<span style="color: {status_color}; font-size: 0.9rem; font-weight: 500;">{status_icon} {status}</span>')
        
        if meta_parts:
            st.markdown(f"<div style='margin: 12px 0;'>{' &nbsp;•&nbsp; '.join(meta_parts)}</div>", unsafe_allow_html=True)        # Studio and source
        if studios:
            studio_str = ", ".join(studios[:2])  # Show up to 2 studios
            if len(studios) > 2:
                studio_str += f" +{len(studios)-2} more"
            st.markdown(f"<p style='color: #7F8C8D; font-size: 0.85rem; margin: 8px 0;'>🎬 <strong>{studio_str}</strong>" + (f" • {source}" if source else "") + "</p>", unsafe_allow_html=True)
        elif source:
            st.markdown(f"<p style='color: #7F8C8D; font-size: 0.85rem; margin: 8px 0;'>{source}</p>", unsafe_allow_html=True)
        
        # Genre tags with clickable pill styling
        if genres:
            genre_list = [g.strip() for g in genres.split('|') if g.strip()]
            st.markdown("<div style='margin: 8px 0;'>", unsafe_allow_html=True)
            cols = st.columns([1] * min(len(genre_list[:5]), 5))
            for idx, genre in enumerate(genre_list[:5]):
                with cols[idx]:
                    if st.button(
                        genre,
                        key=f"genre_{anime_id}_{genre}",
                        help=f"Browse more {genre} anime",
                        type="secondary",
                        use_container_width=True
                    ):
                        # Enable browse mode and set genre filter
                        st.session_state["browse_mode"] = True
                        st.session_state["genre_filter"] = [genre]
                        st.session_state["selected_seed_ids"] = []
                        st.session_state["selected_seed_titles"] = []
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Badge pills inline
        cols = st.columns([1, 1, 1])
        with cols[0]:
            cs_icon = "🆕" if badges['cold_start'] else "✓"
            st.markdown(f"{cs_icon} {'Cold-start' if badges['cold_start'] else 'Trained'}")
        with cols[1]:
            pop_icon = "🔥" if "Top" in badges['popularity_band'] else "📊"
            st.markdown(f"{pop_icon} {badges['popularity_band']}")
        with cols[2]:
            nov_val = badges.get('novelty_ratio')
            if nov_val is None:
                st.markdown("— Novelty NA")
            else:
                nov_icon = "🌟" if float(nov_val) > 0.6 else "🎯"
                st.markdown(f"{nov_icon} Novelty {float(nov_val):.2f}")
        
        # Synopsis - show full text directly
        if display_synopsis:
            st.caption(f"📝 {display_synopsis}")
        
        # Streaming platforms (if available)
        streaming = row.get("streaming")
        # Handle both list and pandas Series/numpy array
        streaming_list = []
        try:
            # Check for None or NaN first (avoid ambiguous truth value)
            if streaming is None:
                streaming_list = []
            elif isinstance(streaming, float) and pd.isna(streaming):
                streaming_list = []
            elif isinstance(streaming, list):
                streaming_list = streaming
            elif isinstance(streaming, str):
                streaming_list = []  # Skip string values
            elif hasattr(streaming, 'tolist'):  # pandas Series or numpy array
                streaming_list = streaming.tolist()
            else:
                streaming_list = []
        except Exception:
            streaming_list = []
        
        if len(streaming_list) > 0:
            st.markdown("**🎬 Watch on:**")
            # Display as clickable badges
            stream_html = " ".join([
                f'<a href="{s["url"]}" target="_blank" style="display:inline-block;background:#3498DB;color:white;padding:4px 8px;margin:2px;border-radius:4px;text-decoration:none;font-size:11px;">{s["name"]}</a>'
                for s in streaming_list if isinstance(s, dict) and s.get("name") and s.get("url")
            ])
            if stream_html:
                st.markdown(stream_html, unsafe_allow_html=True)        # Detailed tooltips in expander
        with st.expander("ℹ️ Details", expanded=False):
            cs_tooltip = format_badge_tooltip("cold_start", badges['cold_start'])
            pop_tooltip = format_badge_tooltip("popularity_band", badges['popularity_band'])
            nov_tooltip = format_badge_tooltip("novelty_ratio", badges.get('novelty_ratio'))
            
            st.caption(cs_tooltip)
            st.caption(pop_tooltip)
            st.caption(nov_tooltip)
        
        # "More Like This" button - adds to seed list (up to 5)
        # anime_id already extracted at top of function
        current_ids = st.session_state.get("selected_seed_ids", [])
        current_titles = st.session_state.get("selected_seed_titles", [])
        
        if anime_id in current_ids:
            st.caption("✓ Already in seeds")
        elif len(current_ids) >= 5:
            st.caption("⚠️ Max 5 seeds (clear some first)")
        else:
            if st.button(f"🔄 Add to Seeds", key=f"more_like_{anime_id}", use_container_width=True):
                current_ids.append(anime_id)
                current_titles.append(title_display)
                st.session_state["selected_seed_ids"] = current_ids
                st.session_state["selected_seed_titles"] = current_titles
                st.rerun()
        
        st.markdown("---")
        
        # Rating section (if profile loaded)
        profile = st.session_state.get("active_profile")
        if profile:
            current_rating = profile.get("ratings", {}).get(str(anime_id))
            st.markdown("**Rate This Anime**")
            render_quick_rating_buttons(anime_id, title_display, current_rating)
        else:
            st.caption("💡 Load a profile to rate anime")