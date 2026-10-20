from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.app.badges import badge_payload, band_label
from src.app.components.rating import render_quick_rating_buttons
from src.app.components.tooltips import format_badge_tooltip, novelty_flag
from src.app.score_semantics import (
    MATCH_TIERS,
    SCORE_LABEL_SHORT,
    format_match_score,
    format_user_friendly_score,
    has_match_score,
    match_rank,
)
from src.app.theme_tokens import TIER_TOKENS
from src.utils import coerce_genres

_TIER_CLASSES: dict[str, str] = {
    label: "mars-" + token.replace("_", "-") for (label, _), token in zip(MATCH_TIERS, TIER_TOKENS)
}


def _get_user_genre_hist_from_session() -> dict:
    try:
        hist = st.session_state.get("user_genre_hist")
        return hist if isinstance(hist, dict) else {}
    except Exception:  # pragma: no cover
        return {}

# Removed coerce_genres - now using canonical version from src.utils.parsing

def _render_placeholder_box(label: str):
    st.markdown(f'<div class="mars-poster-placeholder">{label}</div>', unsafe_allow_html=True)


# Hidden first element of every card container; CSS finds the card through it with :has().
CARD_MARKER_HTML = "<span class='mars-card-marker' aria-hidden='true'></span>"
# Same trick for the grid view's container, which CSS turns into a responsive grid.
GRID_MARKER_HTML = "<span class='mars-grid-marker' aria-hidden='true'></span>"
# Placed right before a row of genre buttons; only that row gets the pill style.
GENRE_ROW_MARKER_HTML = "<span class='mars-genre-row' aria-hidden='true'></span>"


def poster_html(src: str, title: str) -> str:
    """Poster as a real <img> whose alt is the title (st.image in 1.38 sets alt to "0")."""
    t = escape(title, quote=True)
    return (
        f"<figure class='mars-poster-figure'><img class='mars-poster' src='{escape(src, quote=True)}' "
        f"alt='{t}'><figcaption class='mars-poster-caption'>{t}</figcaption></figure>"
    )


def explanation_html(explanation: str, *, compact: bool = False) -> str:
    size = " mars-explanation-compact" if compact else ""
    return f"<p class='mars-explanation{size}'>{explanation}</p>"


def score_badge_html(score, all_raw_scores: list[float] | None, *, compact: bool = False) -> str:
    """Match badge (tier label, or the raw score when there is no run to rank in) plus rank."""
    if not has_match_score(score):
        return ""
    size = " mars-badge-compact" if compact else ""
    if all_raw_scores:
        label, tooltip, _ = format_user_friendly_score(float(score), all_raw_scores)
        rank = match_rank(float(score), all_raw_scores)
        tier = _TIER_CLASSES.get(label, "mars-tier-look")
        return (
            f"<span class='mars-badge{size} {tier}' title='{tooltip}'>"
            f"<span class='mars-rank'>#{rank}</span> {label}</span>"
        )
    return (
        f"<span class='mars-badge{size} mars-tier-none'>"
        f"{SCORE_LABEL_SHORT}: {format_match_score(float(score))}</span>"
    )


def mal_score_tone(mal_score: float) -> str:
    return "success" if mal_score >= 8.0 else "primary" if mal_score >= 7.0 else "muted"


def status_tone(status) -> str:
    return "success" if status == "Finished Airing" else "warn" if "Airing" in str(status) else "info"


def meta_span(text, tone: str, role: str | None = None) -> str:
    role_class = f" mars-meta-{role}" if role else ""
    return f'<span class="mars-tone-{tone}{role_class}">{text}</span>'


def flag_html(text: str, tone: str, *, strong: bool = True) -> str:
    weight = " mars-flag-strong" if strong else ""
    return f"<span class='mars-flag{weight} mars-tone-{tone}'>{text}</span>"

def _clean_url(value) -> str | None:
    """Return a usable http(s) URL string, or None for NaN/empty/non-string values."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value.startswith(("http://", "https://")):
        return None
    return value


def card_flags(badges: dict) -> list[tuple[str, str]]:
    """(label, tone) per card flag, in plain words; "rated by viewers" and "no profile" show nothing."""
    flags: list[tuple[str, str]] = []
    if badges.get("cold_start"):
        flags.append(("Few ratings", "warn"))
    flags.append((band_label(badges["popularity_band"]), "info"))
    novelty = badges.get("novelty_ratio")
    if novelty is not None:
        flags.append(novelty_flag(float(novelty)))
    return flags


_REPO_ROOT = Path(__file__).resolve().parents[3]
_IMAGE_MIME = {".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


@lru_cache(maxsize=512)
def _local_poster_url(thumb_rel: str) -> str | None:
    """Local thumbnail (``data/processed/images/posters/*_thumb.webp``, ~15 kB) as a data URI;
    None when the file is missing. Streamlit's media-URL helper is private and moved between
    releases (1.38 → Cloud's newer build broke on import), so it is not used."""
    rel_path = Path(str(thumb_rel))
    img_path = rel_path if rel_path.is_absolute() else _REPO_ROOT / "data" / "processed" / rel_path
    mime = _IMAGE_MIME.get(img_path.suffix.lower())
    if mime is None or not img_path.is_file():
        return None
    try:
        data = base64.b64encode(img_path.read_bytes()).decode("ascii")
    except OSError:
        return None
    return f"data:{mime};base64,{data}"


def _render_poster(thumb_rel: str | None, title_display: str, remote_url: str | None, anime_id: int):
    """Render a poster: the local thumbnail when shipped, else the MyAnimeList CDN URL (slim
    deployments do not ship the image cache), else a placeholder box."""
    src = _local_poster_url(str(thumb_rel)) if isinstance(thumb_rel, str) and thumb_rel else None
    src = src or _clean_url(remote_url)
    if src:
        st.markdown(poster_html(src, title_display), unsafe_allow_html=True)
        return
    _render_placeholder_box("No Image")
    st.caption(f"{title_display} (no image available)")

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
        st.markdown(CARD_MARKER_HTML, unsafe_allow_html=True)
        _render_poster(thumb, title_display, row.get("poster_url"), anime_id)

        score_badge = score_badge_html(rec.get("score"), all_raw_scores, compact=True)

        st.markdown(
            f"<p class='mars-card-title-compact'>{title_display}</p>",
            unsafe_allow_html=True,
        )
        if score_badge:
            st.markdown(f"<p class='mars-badge-row'>{score_badge}</p>", unsafe_allow_html=True)

        # Personalized explanation
        explanation = rec.get("explanation")
        if explanation:
            st.markdown(explanation_html(explanation, compact=True), unsafe_allow_html=True)

        # Metadata chips
        meta_parts = []
        if mal_score:
            meta_parts.append(meta_span(f"★ {mal_score:.1f}", mal_score_tone(mal_score), "score"))

        anime_type = row.get("type")
        if anime_type and pd.notna(anime_type):
            meta_parts.append(meta_span(anime_type, "purple", "type"))

        if year:
            meta_parts.append(meta_span(year, "muted"))

        if meta_parts:
            st.markdown(f"<p class='mars-meta-compact'>{' · '.join(meta_parts)}</p>", unsafe_allow_html=True)

        # Genres (first 3) - clickable
        if genres:
            genre_list = [g.strip() for g in genres.split('|') if g.strip()][:3]
            if genre_list:
                st.markdown(GENRE_ROW_MARKER_HTML, unsafe_allow_html=True)
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
        st.markdown(CARD_MARKER_HTML, unsafe_allow_html=True)
        # Two-column layout: image | content
        col_img, col_content = st.columns([1, 3])

        with col_img:
            _render_poster(thumb, title_display, row.get("poster_url"), anime_id)

        with col_content:
            # Title + match score on same line
            score_html = score_badge_html(rec.get("score"), all_raw_scores)

            st.markdown(
                f"<h3 class='mars-card-title'>{title_display}{score_html}</h3>",
                unsafe_allow_html=True,
            )
            explanation = rec.get("explanation")
            if explanation:
                st.markdown(explanation_html(explanation), unsafe_allow_html=True)

            if alt_title:
                st.markdown(
                    f"<p class='mars-alt-title'>{alt_title}</p>",
                    unsafe_allow_html=True,
                )

            # Metadata chips
            meta_parts = []
            if mal_score:
                meta_parts.append(meta_span(f"★ {mal_score:.2f}", mal_score_tone(mal_score), "score"))
            if anime_type and pd.notna(anime_type):
                meta_parts.append(meta_span(anime_type, "purple", "type"))
            if episodes:
                meta_parts.append(meta_span(f"{episodes} eps", "muted"))
            if year:
                meta_parts.append(meta_span(year, "muted"))
            if status:
                meta_parts.append(meta_span(status, status_tone(status), "status"))
            if meta_parts:
                st.markdown(
                    f"<div class='mars-meta'>{' &nbsp;·&nbsp; '.join(meta_parts)}</div>",
                    unsafe_allow_html=True,
                )

            # Studio / source
            if studios:
                studio_str = ", ".join(studios[:2])
                if len(studios) > 2:
                    studio_str += f" +{len(studios)-2}"
                extra = f" · {source}" if source else ""
                st.markdown(
                    f"<p class='mars-studio'>{studio_str}{extra}</p>",
                    unsafe_allow_html=True,
                )
            elif source:
                st.markdown(
                    f"<p class='mars-studio'>{source}</p>",
                    unsafe_allow_html=True,
                )

            # Genres as pills
            if genres:
                genre_list = [g.strip() for g in genres.split('|') if g.strip()]
                st.markdown(GENRE_ROW_MARKER_HTML, unsafe_allow_html=True)
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
                f"<p class='mars-synopsis'>{truncated}</p>",
                unsafe_allow_html=True,
            )

        # Badges row - compact. Routine flags (rated, no profile) are left off (audit F7).
        flags = card_flags(badges)
        badge_cols = st.columns([1, 1, 1, 2])
        for col, (label, tone) in zip(badge_cols[:3], flags, strict=False):
            with col:
                st.markdown(flag_html(label, tone), unsafe_allow_html=True)
        with badge_cols[3]:
            # "Add to Seeds" or "Already in seeds"
            current_ids = st.session_state.get("selected_seed_ids", [])
            current_titles = st.session_state.get("selected_seed_titles", [])
            if anime_id in current_ids:
                st.markdown(flag_html("In seeds", "success", strong=False), unsafe_allow_html=True)
            elif len(current_ids) >= 5:
                st.markdown(flag_html("Max 5 seeds", "muted", strong=False), unsafe_allow_html=True)
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
                    f'<a href="{s["url"]}" target="_blank" class="mars-stream-link">{s["name"]}</a>'
                    for s in streaming_list if isinstance(s, dict) and s.get("name") and s.get("url")
                ])
                if stream_html:
                    st.markdown(f"**Watch on:** {stream_html}", unsafe_allow_html=True)

            # Badge tooltips
            if badges['cold_start']:
                st.caption(format_badge_tooltip("cold_start", True))
            st.caption(format_badge_tooltip("popularity_band", badges['popularity_band']))
            if badges.get('novelty_ratio') is not None:
                st.caption(format_badge_tooltip("novelty_ratio", badges['novelty_ratio']))

            signal_breakdown = rec.get("signal_breakdown")
            if signal_breakdown:
                st.markdown("**Signal breakdown**")
                st.caption(signal_breakdown)

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
