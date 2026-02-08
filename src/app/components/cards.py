from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.app.badges import badge_payload
from src.app.components.rating import render_quick_rating_buttons
from src.app.components.tooltips import format_badge_tooltip
from src.app.score_semantics import (
    SCORE_LABEL_SHORT,
    format_match_score,
    format_user_friendly_score,
    has_match_score,
)
from src.utils import coerce_genres


def _get_user_genre_hist_from_session() -> dict:
    try:
        hist = st.session_state.get("user_genre_hist")
        return hist if isinstance(hist, dict) else {}
    except Exception:  # pragma: no cover
        return {}

# Removed coerce_genres - now using canonical version from src.utils.parsing

def _render_placeholder_box(label: str):
    st.markdown(
        f'<div style="width:180px;height:260px;background:#F0F2F6;display:flex;align-items:center;justify-content:center;border:1px solid #E2E8F0;border-radius:8px;font-size:12px;color:#A0AEC0;">{label}</div>',
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

def render_card_grid(
    row, rec: dict, pop_pct: float, *, is_in_training: bool, all_raw_scores: list[float] | None = None
):
    """Render a compact grid card version.

    Args:
        row: Metadata row for the anime
        rec: Recommendation dict with score
        pop_pct: Popularity percentile
        is_in_training: Whether anime was in training set
        all_raw_scores: All scores in result set for percentile calculation (optional)
    """
    # Extract anime_id early (needed for button keys)
    anime_id = int(row.get("anime_id"))

    raw_genres = row.get("genres")
    genres = coerce_genres(raw_genres)

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

    container = st.container(border=True)
    with container:
        # Image
        _render_image_streamlit(thumb, title_display)

        # Title + score
        truncated_title = title_display if len(title_display) <= 30 else title_display[:27] + "..."

        score = rec.get("score")
        score_badge = ""
        if has_match_score(score):
            if all_raw_scores:
                user_friendly, tooltip, color = format_user_friendly_score(float(score), all_raw_scores)
                score_badge = (
                    f"<span style='background:{color}15; color:{color}; padding:2px 8px; "
                    f"border-radius:16px; font-weight:700; font-size:0.78rem;' title='{tooltip}'>{user_friendly}</span>"
                )
            else:
                score_str = format_match_score(float(score))
                score_badge = (
                    f"<span style='background:#6C63FF15; color:#6C63FF; padding:2px 8px; "
                    f"border-radius:16px; font-weight:700; font-size:0.78rem;'>{SCORE_LABEL_SHORT}: {score_str}</span>"
                )

        st.markdown(
            f"<p style='font-weight:700; font-size:0.95rem; color:#1A1A2E; margin:8px 0 4px 0;'>{truncated_title}</p>",
            unsafe_allow_html=True,
        )
        if score_badge:
            st.markdown(f"<p style='margin:2px 0;'>{score_badge}</p>", unsafe_allow_html=True)

        # Personalized explanation
        explanation = rec.get("explanation")
        if explanation:
            st.markdown(f"<p style='font-size:0.72rem; color:#4A5568; margin:4px 0; font-style:italic;'>{explanation}</p>", unsafe_allow_html=True)

        # Metadata chips
        meta_parts = []
        if mal_score:
            sc = "#48BB78" if mal_score >= 8.0 else "#6C63FF" if mal_score >= 7.0 else "#A0AEC0"
            meta_parts.append(f'<span style="color:{sc}; font-weight:700;">★ {mal_score:.1f}</span>')

        anime_type = row.get("type")
        if anime_type and pd.notna(anime_type):
            meta_parts.append(f'<span style="color:#B794F4; font-weight:600;">{anime_type}</span>')

        if year:
            meta_parts.append(f'<span style="color:#A0AEC0;">{year}</span>')

        if meta_parts:
            st.markdown(f"<p style='font-size:0.82rem; margin:4px 0;'>{' · '.join(meta_parts)}</p>", unsafe_allow_html=True)

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
                            st.session_state["ui_mode"] = "Browse"
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
            if st.button(
                "🔄",
                key=f"grid_more_{anime_id}",
                help="Add as a seed (used in Seed-based / Personalized modes)",
                use_container_width=True,
            ):
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

def render_card(
    row, rec: dict, pop_pct: float, *, is_in_training: bool, all_raw_scores: list[float] | None = None
):
    """Render a detailed list card with image left / content right layout.

    Args:
        row: Metadata row for the anime
        rec: Recommendation dict with score
        pop_pct: Popularity percentile
        is_in_training: Whether anime was in training set
        all_raw_scores: All scores in result set for percentile calculation (optional)
    """
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

    anime_id = int(row.get("anime_id"))

    # Title selection
    title_candidates = [
        row.get("title_english"),
        row.get("title_display"),
        row.get("title_primary"),
        row.get("title"),
        row.get("title_japanese"),
    ]
    title_display = next((t for t in title_candidates if isinstance(t, str) and t.strip()), "Anime")

    alt_title = None
    if row.get("title_japanese") and row.get("title_japanese") != title_display:
        alt_title = row.get("title_japanese")
    elif row.get("title_primary") and row.get("title_primary") != title_display:
        alt_title = row.get("title_primary")

    # Synopsis
    synopsis_val = row.get("synopsis") if "synopsis" in row else row.get("synopsis_snippet")
    display_synopsis = ""
    if synopsis_val is not None and pd.notna(synopsis_val) and str(synopsis_val).strip():
        display_synopsis = str(synopsis_val).strip()

    # Metadata fields
    mal_score = row.get("mal_score")
    episodes = row.get("episodes")
    status = row.get("status")
    studios_raw = row.get("studios", [])
    studios = studios_raw if isinstance(studios_raw, list) else []
    source = row.get("source_material")
    anime_type = row.get("type")

    # Year
    year = None
    aired_from = row.get("aired_from")
    if aired_from:
        try:
            if isinstance(aired_from, str):
                year = aired_from[:4]
        except Exception:
            pass

    container = st.container(border=True)
    with container:
        # Two-column layout: image | content
        col_img, col_content = st.columns([1, 3])

        with col_img:
            _render_image_streamlit(thumb, title_display)

        with col_content:
            # Title + match score on same line
            score = rec.get("score")
            score_html = ""
            badge_color = "#6C63FF"
            if has_match_score(score):
                if all_raw_scores:
                    user_friendly, tooltip, color = format_user_friendly_score(float(score), all_raw_scores)
                    badge_color = color
                    score_html = (
                        f"<span style='background:{badge_color}15; color:{badge_color}; padding:2px 10px; "
                        f"border-radius:20px; font-size:0.82rem; font-weight:700; margin-left:8px;' "
                        f"title='{tooltip}'>{user_friendly}</span>"
                    )
                else:
                    score_str = format_match_score(float(score))
                    score_html = (
                        f"<span style='background:{badge_color}15; color:{badge_color}; padding:2px 10px; "
                        f"border-radius:20px; font-size:0.82rem; font-weight:700; margin-left:8px;'>"
                        f"{SCORE_LABEL_SHORT}: {score_str}</span>"
                    )

            st.markdown(
                f"<h3 style='margin:0; font-size:1.15rem; color:#1A1A2E; font-weight:700;'>"
                f"{title_display}{score_html}</h3>",
                unsafe_allow_html=True,
            )
            if alt_title:
                st.markdown(
                    f"<p style='color:#A0AEC0; font-style:italic; font-size:0.85rem; margin:2px 0 0 0;'>{alt_title}</p>",
                    unsafe_allow_html=True,
                )

            # Personalized explanation
            explanation = rec.get("explanation")
            if explanation:
                st.markdown(
                    f"<div style='background:#F0EFFF; padding:6px 12px; border-radius:6px; margin:6px 0; "
                    f"border-left:3px solid #6C63FF;'>"
                    f"<span style='font-size:0.82rem; color:#4A5568;'>{explanation}</span></div>",
                    unsafe_allow_html=True,
                )

            # Metadata chips
            meta_parts = []
            if mal_score:
                sc = "#48BB78" if mal_score >= 8.0 else "#6C63FF" if mal_score >= 7.0 else "#A0AEC0"
                meta_parts.append(f'<span style="color:{sc}; font-weight:700;">★ {mal_score:.2f}</span>')
            if anime_type and pd.notna(anime_type):
                meta_parts.append(f'<span style="color:#B794F4; font-weight:600;">{anime_type}</span>')
            if episodes:
                meta_parts.append(f'<span style="color:#A0AEC0;">{episodes} eps</span>')
            if year:
                meta_parts.append(f'<span style="color:#A0AEC0;">{year}</span>')
            if status:
                sc = "#48BB78" if status == "Finished Airing" else "#ECC94B" if "Airing" in str(status) else "#63B3ED"
                meta_parts.append(f'<span style="color:{sc}; font-weight:500;">{status}</span>')
            if meta_parts:
                st.markdown(
                    f"<div style='margin:6px 0; font-size:0.88rem;'>{' &nbsp;·&nbsp; '.join(meta_parts)}</div>",
                    unsafe_allow_html=True,
                )

            # Studio / source
            if studios:
                studio_str = ", ".join(studios[:2])
                if len(studios) > 2:
                    studio_str += f" +{len(studios)-2}"
                extra = f" · {source}" if source else ""
                st.markdown(
                    f"<p style='color:#A0AEC0; font-size:0.82rem; margin:4px 0;'>{studio_str}{extra}</p>",
                    unsafe_allow_html=True,
                )
            elif source:
                st.markdown(
                    f"<p style='color:#A0AEC0; font-size:0.82rem; margin:4px 0;'>{source}</p>",
                    unsafe_allow_html=True,
                )

            # Genres as pills
            if genres:
                genre_list = [g.strip() for g in genres.split('|') if g.strip()]
                cols = st.columns([1] * min(len(genre_list[:5]), 5) + [max(0, 5 - len(genre_list[:5]))] if len(genre_list[:5]) < 5 else [1] * 5)
                for idx, genre in enumerate(genre_list[:5]):
                    with cols[idx]:
                        if st.button(
                            genre, key=f"genre_{anime_id}_{genre}",
                            help=f"Browse {genre} anime", type="secondary",
                            use_container_width=True,
                        ):
                            st.session_state["ui_mode"] = "Browse"
                            st.session_state["browse_mode"] = True
                            st.session_state["genre_filter"] = [genre]
                            st.session_state["selected_seed_ids"] = []
                            st.session_state["selected_seed_titles"] = []
                            st.rerun()

        # Synopsis in full width below columns
        if display_synopsis:
            truncated = display_synopsis[:280] + "..." if len(display_synopsis) > 280 else display_synopsis
            st.markdown(
                f"<p style='color:#4A5568; font-size:0.88rem; line-height:1.6; margin:4px 0 8px 0;'>{truncated}</p>",
                unsafe_allow_html=True,
            )

        # Badges row - compact
        badge_cols = st.columns([1, 1, 1, 2])
        with badge_cols[0]:
            lbl = "Cold-start" if badges['cold_start'] else "Trained"
            color = "#ECC94B" if badges['cold_start'] else "#48BB78"
            st.markdown(f"<span style='font-size:0.75rem; color:{color}; font-weight:600;'>{lbl}</span>", unsafe_allow_html=True)
        with badge_cols[1]:
            st.markdown(f"<span style='font-size:0.75rem; color:#63B3ED; font-weight:600;'>{badges['popularity_band']}</span>", unsafe_allow_html=True)
        with badge_cols[2]:
            nov_val = badges.get('novelty_ratio')
            if nov_val is None:
                st.markdown("<span style='font-size:0.75rem; color:#A0AEC0;'>Novelty NA</span>", unsafe_allow_html=True)
            else:
                nc = "#B794F4" if float(nov_val) > 0.6 else "#6C63FF"
                st.markdown(f"<span style='font-size:0.75rem; color:{nc}; font-weight:600;'>Novelty {float(nov_val):.2f}</span>", unsafe_allow_html=True)
        with badge_cols[3]:
            # "Add to Seeds" or "Already in seeds"
            current_ids = st.session_state.get("selected_seed_ids", [])
            current_titles = st.session_state.get("selected_seed_titles", [])
            if anime_id in current_ids:
                st.markdown("<span style='font-size:0.75rem; color:#48BB78;'>In seeds</span>", unsafe_allow_html=True)
            elif len(current_ids) >= 5:
                st.markdown("<span style='font-size:0.75rem; color:#A0AEC0;'>Max 5 seeds</span>", unsafe_allow_html=True)
            else:
                if st.button("+ Add to Seeds", key=f"more_like_{anime_id}", use_container_width=True):
                    current_ids.append(anime_id)
                    current_titles.append(title_display)
                    st.session_state["selected_seed_ids"] = current_ids
                    st.session_state["selected_seed_titles"] = current_titles
                    st.rerun()

        # Expandable details
        with st.expander("More details", expanded=False):
            # Streaming
            streaming = row.get("streaming")
            streaming_list = []
            try:
                if streaming is None or (isinstance(streaming, float) and pd.isna(streaming)):
                    streaming_list = []
                elif isinstance(streaming, list):
                    streaming_list = streaming
                elif hasattr(streaming, 'tolist'):
                    streaming_list = streaming.tolist()
            except Exception:
                streaming_list = []

            if streaming_list:
                stream_html = " ".join([
                    f'<a href="{s["url"]}" target="_blank" style="display:inline-block;background:#6C63FF;color:white;padding:3px 10px;margin:2px;border-radius:16px;text-decoration:none;font-size:0.75rem;font-weight:600;">{s["name"]}</a>'
                    for s in streaming_list if isinstance(s, dict) and s.get("name") and s.get("url")
                ])
                if stream_html:
                    st.markdown(f"**Watch on:** {stream_html}", unsafe_allow_html=True)

            # Badge tooltips
            cs_tooltip = format_badge_tooltip("cold_start", badges['cold_start'])
            pop_tooltip = format_badge_tooltip("popularity_band", badges['popularity_band'])
            nov_tooltip = format_badge_tooltip("novelty_ratio", badges.get('novelty_ratio'))
            st.caption(cs_tooltip)
            st.caption(pop_tooltip)
            st.caption(nov_tooltip)

            # Full synopsis if truncated
            if display_synopsis and len(display_synopsis) > 280:
                st.markdown(f"**Full synopsis:** {display_synopsis}")

            # Rating
            profile = st.session_state.get("active_profile")
            if profile:
                current_rating = profile.get("ratings", {}).get(str(anime_id))
                st.markdown("**Rate this anime**")
                render_quick_rating_buttons(anime_id, title_display, current_rating)
            else:
                st.caption("Load a profile to rate anime")
