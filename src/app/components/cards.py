from __future__ import annotations
from pathlib import Path
import streamlit as st
from src.app.badges import badge_payload
from src.app.explanations import format_explanation
from src.app.components.tooltips import format_badge_tooltip

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

def render_card(row, rec: dict, pop_pct: float):
    raw_genres = row.get("genres")
    genres = coerce_genres(raw_genres)
    item_genres = [g for g in genres.split("|") if g]
    badges = badge_payload(
        is_in_training=True,
        pop_percentile=pop_pct,
        user_genre_hist={g: 1 for g in item_genres},
        item_genres=item_genres,
    )
    rec["badges"] = badges
    exp_str = format_explanation(rec.get("explanation", {}))
    thumb = row.get("poster_thumb_url")
    
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
    
    synopsis = row.get("synopsis_snippet") or row.get("synopsis") or ""
    
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
    def _smart_truncate(text: str, max_words: int = 40, max_chars: int = 220) -> str:
        if not text:
            return ""
        words = text.split()
        if len(words) <= max_words and len(text) <= max_chars:
            return text
        out_words = []
        total_chars = 0
        for w in words:
            # +1 for space when joined later
            next_len = len(w) + (1 if out_words else 0)
            if len(out_words) < max_words and (total_chars + next_len) <= max_chars:
                out_words.append(w)
                total_chars += next_len
            else:
                break
        return " ".join(out_words) + "…"
    truncated_synopsis = _smart_truncate(synopsis)
    
    # Visual card container with colored left border
    card_color = "#4A90E2" if not badges['cold_start'] else "#F39C12"
    st.markdown(
        f'<div style="border-left: 4px solid {card_color}; padding-left: 12px; margin-bottom: 24px;">',
        unsafe_allow_html=True
    )
    
    # Render image using Streamlit's native image component to avoid HTML rendering issues
    _render_image_streamlit(thumb, title_display)
    # Confidence stars
    score = rec.get("score", 0.0)
    def _compute_confidence_stars(s: float) -> str:
        if s > 1.0:
            normalized = min(s / 2.0, 5.0)
        else:
            normalized = s * 5.0
        full_stars = int(normalized)
        half_star = (normalized - full_stars) >= 0.5
        stars = "⭐" * full_stars
        if half_star and full_stars < 5:
            stars += "⭐"
        empty = max(0, 5 - len(stars))
        stars += "☆" * empty
        return stars[:5]
    
    confidence = _compute_confidence_stars(score)
    st.markdown(f"**{title_display}** {confidence}")
    
    # Alternative title (Japanese/original)
    if alt_title:
        st.caption(f"*{alt_title}*")
    
    # Metadata row: Score, Episodes, Year, Status
    meta_parts = []
    if mal_score:
        score_color = "#2ECC71" if mal_score >= 8.0 else "#3498DB" if mal_score >= 7.0 else "#95A5A6"
        meta_parts.append(f'<span style="color:{score_color};font-weight:bold;">⭐ {mal_score:.2f}</span>')
    if episodes:
        meta_parts.append(f"📺 {episodes} eps")
    if year:
        meta_parts.append(f"📅 {year}")
    if status:
        status_icon = "✅" if status == "Finished Airing" else "🟢" if "Airing" in str(status) else "🔵"
        meta_parts.append(f"{status_icon} {status}")
    
    if meta_parts:
        st.markdown(" • ".join(meta_parts), unsafe_allow_html=True)
    
    # Studio and source
    if studios:
        studio_str = ", ".join(studios[:2])  # Show up to 2 studios
        if len(studios) > 2:
            studio_str += f" +{len(studios)-2} more"
        st.caption(f"🎬 {studio_str}" + (f" • Source: {source}" if source else ""))
    elif source:
        st.caption(f"Source: {source}")
    
    st.caption(f"Genres: {genres}")
    
    # Inline badge pills
    explanation = rec.get("explanation", {})
    mf_pct = explanation.get("mf", 0.0) * 100
    knn_pct = explanation.get("knn", 0.0) * 100
    pop_pct = explanation.get("pop", 0.0) * 100
    
    # Simplified inline explanation
    if mf_pct > 50:
        simple_exp = f"📊 Collaborative {mf_pct:.0f}%, Others {100-mf_pct:.0f}%"
    elif knn_pct > 30:
        simple_exp = f"🔗 Neighborhood {knn_pct:.0f}%, Collab {mf_pct:.0f}%, Pop {pop_pct:.0f}%"
    else:
        simple_exp = f"⭐ Collab {mf_pct:.0f}%, Neighbor {knn_pct:.0f}%, Popular {pop_pct:.0f}%"
    
    st.caption(simple_exp)
    
    # Badge pills inline
    cols = st.columns([1, 1, 1])
    with cols[0]:
        cs_icon = "🆕" if badges['cold_start'] else "✓"
        st.markdown(f"{cs_icon} {'Cold-start' if badges['cold_start'] else 'Trained'}")
    with cols[1]:
        pop_icon = "🔥" if "Top" in badges['popularity_band'] else "📊"
        st.markdown(f"{pop_icon} {badges['popularity_band']}")
    with cols[2]:
        nov_val = badges['novelty_ratio']
        nov_icon = "🌟" if nov_val > 0.6 else "🎯"
        st.markdown(f"{nov_icon} Novelty {nov_val:.2f}")
    
    # Synopsis preview and full text
    if synopsis:
        st.caption(f"📝 {truncated_synopsis}")
        if len(synopsis) > len(truncated_synopsis):
            with st.expander("📖 Read full synopsis", expanded=False):
                st.write(synopsis)
    
    # Streaming platforms (if available)
    streaming = row.get("streaming", [])
    if streaming and isinstance(streaming, list) and len(streaming) > 0:
        st.markdown("**🎬 Watch on:**")
        # Display as clickable badges
        stream_html = " ".join([
            f'<a href="{s["url"]}" target="_blank" style="display:inline-block;background:#3498DB;color:white;padding:4px 8px;margin:2px;border-radius:4px;text-decoration:none;font-size:11px;">{s["name"]}</a>'
            for s in streaming if isinstance(s, dict) and s.get("name") and s.get("url")
        ])
        if stream_html:
            st.markdown(stream_html, unsafe_allow_html=True)
    
    # Detailed tooltips in expander
    with st.expander("ℹ️ Details", expanded=False):
        cs_tooltip = format_badge_tooltip("cold_start", badges['cold_start'])
        pop_tooltip = format_badge_tooltip("popularity_band", badges['popularity_band'])
        nov_tooltip = format_badge_tooltip("novelty_ratio", badges['novelty_ratio'])
        
        st.caption(cs_tooltip)
        st.caption(pop_tooltip)
        st.caption(nov_tooltip)
        st.caption(f"**Full breakdown**: {exp_str}")
    
    st.markdown('</div>', unsafe_allow_html=True)
