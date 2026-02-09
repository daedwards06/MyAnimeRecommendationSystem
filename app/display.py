"""Display rendering for the MARS Streamlit app.

Handles CSS injection, header rendering, result card orchestration,
diversity mix bar, empty states, and the footer (diversity panel + help).
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.app.badges import badge_payload
from src.app.components.cards import render_card, render_card_grid
from src.app.components.diversity import render_diversity_panel
from src.app.components.help import render_help_panel
from src.app.components.instructions import render_onboarding
from src.app.score_semantics import has_match_score

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from app.sidebar import SidebarResult
    from app.pipeline_runner import PipelineRunResult


# ── CSS injection ────────────────────────────────────────────────────────────


def inject_css() -> None:
    """Inject custom CSS for a modern, polished aesthetic."""
    st.markdown(
        """
<style>
    /* ===== Global Layout ===== */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* ===== Typography ===== */
    h1 {
        color: #1A1A2E;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    h2 {
        color: #1A1A2E;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    h3 {
        color: #2D3748;
        font-weight: 600;
    }
    .stMarkdown { line-height: 1.65; }

    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {
        background: #FAFBFC;
        border-right: 1px solid #E2E8F0;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #4A5568;
    }

    /* ===== Buttons ===== */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 1px solid #E2E8F0;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(108, 99, 255, 0.18);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C63FF 0%, #5A52D5 100%);
        border: none;
    }

    /* ===== Genre pill buttons ===== */
    button[kind="secondary"] {
        background-color: #F0EFFF !important;
        color: #6C63FF !important;
        border: 1px solid #D6D3FF !important;
        padding: 4px 14px !important;
        font-size: 0.78rem !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        min-height: 30px !important;
        height: 30px !important;
        letter-spacing: 0.02em !important;
    }
    button[kind="secondary"]:hover {
        background-color: #6C63FF !important;
        color: #FFFFFF !important;
        border-color: #6C63FF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 10px rgba(108, 99, 255, 0.25) !important;
    }

    /* ===== Containers / Cards ===== */
    [data-testid="stVerticalBlock"] > div[data-testid="stContainer"] {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    [data-testid="stVerticalBlock"] > div[data-testid="stContainer"]:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }

    /* ===== Expander ===== */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #2D3748;
        font-size: 0.9rem;
    }

    /* ===== Metrics ===== */
    [data-testid="stMetric"] {
        background: #F7FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #4A5568;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ===== Dividers ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E2E8F0, transparent);
        margin: 1.5rem 0;
    }

    /* ===== Captions ===== */
    [data-testid="stCaptionContainer"] {
        color: #A0AEC0;
        font-size: 0.82rem;
    }

    /* ===== Radio group horizontal ===== */
    .stRadio > div[role="radiogroup"] {
        gap: 0.5rem;
    }

    /* ===== Selectbox / Multiselect ===== */
    .stSelectbox, .stMultiSelect {
        border-radius: 8px;
    }

    /* ===== Hide default Streamlit branding ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
        unsafe_allow_html=True,
    )


# ── Header ───────────────────────────────────────────────────────────────────


def render_header(ui_mode: str) -> None:
    """Render the mode-dependent page header."""
    if ui_mode == "Browse":
        st.markdown(
            "<h1 style='margin-bottom:0; font-weight:800;'>Anime Explorer</h1>"
            "<p style='color:#A0AEC0; font-size:1.05rem; margin-top:0; margin-bottom:1rem;'>"
            "Browse the catalog by genre, type, and year</p>",
            unsafe_allow_html=True,
        )
    elif ui_mode == "Personalized":
        st.markdown(
            "<h1 style='margin-bottom:0; font-weight:800;'>Your Recommendations</h1>"
            "<p style='color:#A0AEC0; font-size:1.05rem; margin-top:0; margin-bottom:1rem;'>"
            "Ranked from your rated history</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<h1 style='margin-bottom:0; font-weight:800;'>Anime Recommender</h1>"
            "<p style='color:#A0AEC0; font-size:1.05rem; margin-top:0; margin-bottom:1rem;'>"
            "Discover anime similar to titles you love</p>",
            unsafe_allow_html=True,
        )


def render_import_light_warning() -> None:
    """Show warning banner when running in lightweight import mode."""
    if os.environ.get("APP_IMPORT_LIGHT"):
        st.warning(
            "Lightweight import mode active. Restart without APP_IMPORT_LIGHT for full functionality."
        )


def render_onboarding_section(ui_mode: str) -> None:
    """Render onboarding instructions for the current mode."""
    render_onboarding(ui_mode=ui_mode)


# ── Results rendering ────────────────────────────────────────────────────────


def render_results(
    recs: list[dict],
    metadata: pd.DataFrame,
    sidebar: "SidebarResult",
    pipeline: "PipelineRunResult",
    *,
    pop_pct_fn: Callable[[int], float],
    is_in_training_fn: Callable[[int], bool],
) -> None:
    """Render recommendation results: scoring details, count, mix bar, cards."""
    # Scoring path expander
    with st.expander("Scoring details", expanded=False):
        st.caption(f"Active scoring path: {pipeline.active_scoring_path}")
        blocked_reason = st.session_state.get("personalization_blocked_reason")
        if (
            st.session_state.get("personalization_enabled", False)
            and not pipeline.personalization_applied
            and blocked_reason
        ):
            st.caption(f"Personalization note: {blocked_reason}")

    # Result count
    total_anime = len(metadata)
    filter_parts: list[str] = []
    if sidebar.genre_filter:
        n = len(sidebar.genre_filter)
        filter_parts.append(f"{n} genre{'s' if n > 1 else ''}")
    if sidebar.type_filter:
        filter_parts.append(", ".join(sidebar.type_filter))
    if sidebar.year_range[0] > 1960 or sidebar.year_range[1] < 2025:
        filter_parts.append(f"{sidebar.year_range[0]}–{sidebar.year_range[1]}")
    filters_text = f"  ·  filtered by {', '.join(filter_parts)}" if filter_parts else ""

    mode_label = "Browsing" if sidebar.browse_mode else "Showing"
    item_type = "titles" if sidebar.browse_mode else "recommendations"
    st.markdown(
        f"<div style='display:flex; align-items:baseline; gap:10px; margin-bottom:6px;'>"
        f"<span style='font-size:1.15rem; font-weight:700; color:#1A1A2E;'>"
        f"{len(recs)} {item_type}</span>"
        f"<span style='font-size:0.82rem; color:#A0AEC0;'>"
        f"of {total_anime:,}{filters_text}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.get("active_profile"):
        watched_count = len(st.session_state["active_profile"].get("watched_ids", []))
        st.caption(f"Excluded {watched_count} already-watched titles")

    if sidebar.sort_by != sidebar.default_sort_for_mode:
        st.caption(f"Sorted by {sidebar.sort_by}")

    # Diversity mix bar
    _render_mix_bar(recs, sidebar.browse_mode, pop_pct_fn=pop_pct_fn, is_in_training_fn=is_in_training_fn)

    # Cards
    _render_cards(recs, metadata, pop_pct_fn=pop_pct_fn, is_in_training_fn=is_in_training_fn)


def _render_mix_bar(
    recs: list[dict],
    browse_mode: bool,
    *,
    pop_pct_fn: Callable[[int], float],
    is_in_training_fn: Callable[[int], bool],
) -> None:
    """Render the compact horizontal diversity mix bar."""
    pop_count = sum(
        1
        for r in recs
        if "Top 25%" in str(
            badge_payload(
                is_in_training=is_in_training_fn(int(r["anime_id"])),
                pop_percentile=pop_pct_fn(int(r["anime_id"])),
                user_genre_hist={},
                item_genres=[],
            ).get("popularity_band", "")
        )
    )
    long_tail_count = sum(
        1
        for r in recs
        if "Long-tail" in str(
            badge_payload(
                is_in_training=is_in_training_fn(int(r["anime_id"])),
                pop_percentile=pop_pct_fn(int(r["anime_id"])),
                user_genre_hist={},
                item_genres=[],
            ).get("popularity_band", "")
        )
    )
    mid_count = len(recs) - pop_count - long_tail_count

    bar_segments: list[str] = []
    if pop_count > 0:
        bar_segments.append(
            f'<div style="background:#FC8181; flex:{pop_count}; height:6px;" '
            f'title="Popular: {pop_count}"></div>'
        )
    if mid_count > 0:
        bar_segments.append(
            f'<div style="background:#63B3ED; flex:{mid_count}; height:6px;" '
            f'title="Mid-range: {mid_count}"></div>'
        )
    if long_tail_count > 0:
        bar_segments.append(
            f'<div style="background:#B794F4; flex:{long_tail_count}; height:6px;" '
            f'title="Hidden gems: {long_tail_count}"></div>'
        )
    if not bar_segments:
        bar_segments.append('<div style="background:#A0AEC0; flex:1; height:6px;"></div>')
    bar_html = "".join(bar_segments)

    mix_label = "Catalog mix" if browse_mode else "Recommendation mix"
    st.markdown(
        f"""
    <div style="margin: 8px 0 20px 0;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-size:0.75rem; color:#A0AEC0; text-transform:uppercase; letter-spacing:0.05em; font-weight:600;">{mix_label}</span>
            <span style="font-size:0.72rem; color:#A0AEC0;">
                <span style="color:#FC8181;">●</span> Popular {pop_count}
                &nbsp;<span style="color:#63B3ED;">●</span> Mid {mid_count}
                &nbsp;<span style="color:#B794F4;">●</span> Hidden gems {long_tail_count}
            </span>
        </div>
        <div style="display:flex; height:6px; border-radius:3px; overflow:hidden; background:#EDF2F7;">
            {bar_html}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_cards(
    recs: list[dict],
    metadata: pd.DataFrame,
    *,
    pop_pct_fn: Callable[[int], float],
    is_in_training_fn: Callable[[int], bool],
) -> None:
    """Render recommendation cards in list or grid mode."""
    view_mode_state = st.session_state.get("view_mode", "list")
    all_raw_scores = [rec.get("score") for rec in recs if has_match_score(rec.get("score"))]
    metadata_by_id = metadata.set_index("anime_id", drop=False)

    if view_mode_state == "grid":
        for i in range(0, len(recs), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(recs):
                    rec = recs[i + j]
                    anime_id = rec["anime_id"]
                    try:
                        row = metadata_by_id.loc[anime_id]
                        if isinstance(row, pd.DataFrame):
                            row = row.iloc[0]
                        pop_pct = pop_pct_fn(int(anime_id))
                        with col:
                            render_card_grid(
                                row,
                                rec,
                                pop_pct,
                                is_in_training=is_in_training_fn(int(anime_id)),
                                all_raw_scores=all_raw_scores,
                            )
                    except KeyError:
                        pass
    else:
        for rec in recs:
            anime_id = rec["anime_id"]
            try:
                row = metadata_by_id.loc[anime_id]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
            except KeyError:
                continue
            pop_pct = pop_pct_fn(int(anime_id))
            render_card(
                row,
                rec,
                pop_pct,
                is_in_training=is_in_training_fn(int(anime_id)),
                all_raw_scores=all_raw_scores,
            )


# ── Empty state ──────────────────────────────────────────────────────────────


def render_empty_state(
    sidebar: "SidebarResult",
    pipeline: "PipelineRunResult",
    metadata: pd.DataFrame,
) -> None:
    """Render the empty-state guidance when no results are available."""
    browse_mode = sidebar.browse_mode
    active_scoring_path = pipeline.active_scoring_path

    if browse_mode or active_scoring_path == "Ranked modes disabled":
        st.markdown(f"**Active scoring path:** {active_scoring_path}")

    if browse_mode:
        return  # Browse empty state is rendered by the pipeline runner

    ui_mode_now = str(st.session_state.get("ui_mode", "Seed-based"))

    if ui_mode_now == "Personalized":
        _render_personalized_empty_state()
    elif sidebar.selected_seed_ids:
        _render_seed_empty_state()
    else:
        _render_cold_start_state(metadata, sidebar.title_to_id)


def _render_personalized_empty_state() -> None:
    active_profile = st.session_state.get("active_profile")
    ratings = (
        (active_profile or {}).get("ratings", {}) if isinstance(active_profile, dict) else {}
    )
    blocked_reason = st.session_state.get("personalization_blocked_reason")
    user_embedding = st.session_state.get("user_embedding")
    personalization_enabled = bool(st.session_state.get("personalization_enabled", False))

    personalized_unavailable_reason: str | None = None
    if not active_profile:
        personalized_unavailable_reason = "Select a rated profile"
    elif not isinstance(ratings, dict) or len(ratings) == 0:
        personalized_unavailable_reason = "Add at least one rating"
    elif not personalization_enabled:
        personalized_unavailable_reason = "Enable personalization"
    elif blocked_reason or user_embedding is None:
        personalized_unavailable_reason = "Personalization is not ready"

    if personalized_unavailable_reason:
        st.markdown(
            "<div style='background: linear-gradient(135deg, #FFF3CD 0%, #FCF8E3 100%); "
            "border-left: 4px solid #F0AD4E; border-radius: 8px; padding: 20px; margin: 20px 0;'>"
            "<p style='color: #8A6D3B; font-weight: 600; margin: 0;'>"
            "Personalized mode is selected, but it isn't running yet.</p>"
            "<p style='color: #8A6D3B; margin: 8px 0 0 0;'>What next: "
            "<b>Select a rated profile</b>, <b>add at least one rating</b>, and "
            "<b>enable personalization</b> in the sidebar.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.warning("No personalized results found with the current filters.")
        st.markdown("**Try:**")
        st.markdown(
            "\n".join(
                [
                    "- Use **Reset Filters** in the sidebar",
                    "- Widen the year range (Filters)",
                    "- Remove the type filter (Filters)",
                    "- Switch to **Seed-based** mode to explore via a seed",
                ]
            )
        )


def _render_seed_empty_state() -> None:
    st.warning("No similar titles found with the current filters.")
    st.markdown("**Try:**")
    st.markdown(
        "\n".join(
            [
                "- Use **Reset Filters** in the sidebar",
                "- Try fewer seeds (1–2) or a different seed",
                "- Widen the year range (Filters)",
                "- Remove the type filter (Filters)",
            ]
        )
    )


def _render_cold_start_state(metadata: pd.DataFrame, title_to_id: dict[str, int]) -> None:
    st.markdown(
        "<div style='background:#F0EFFF; border-radius:12px; padding:32px; "
        "margin:24px 0; text-align:center;'>"
        "<h3 style='color:#1A1A2E; margin:0 0 8px 0; font-weight:800;'>Get Started</h3>"
        "<p style='color:#4A5568; font-size:1.0rem; margin:0 0 24px 0;'>"
        "Pick a seed title to discover similar anime</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    sample_titles = [
        "Steins;Gate",
        "Cowboy Bebop",
        "Death Note",
        "Fullmetal Alchemist: Brotherhood",
    ]

    # Use the title_to_id mapping from the sidebar if available;
    # otherwise build one from metadata (backward compatibility).
    if not title_to_id:
        title_to_id = {}
        for _, row in metadata.iterrows():
            title_eng = row.get("title_english")
            if title_eng and isinstance(title_eng, str) and title_eng.strip():
                title_to_id[title_eng] = int(row["anime_id"])
            else:
                title_disp = row.get("title_display")
                if title_disp and isinstance(title_disp, str) and title_disp.strip():
                    title_to_id[title_disp] = int(row["anime_id"])

    _available_samples = [t for t in sample_titles if t in title_to_id]
    if _available_samples:
        cols = st.columns(len(_available_samples[:4]))
        for i, sample in enumerate(_available_samples[:4]):
            with cols[i]:
                if st.button(
                    sample,
                    key=f"main_sample_{i}",
                    use_container_width=True,
                    type="primary" if i == 3 else "secondary",
                ):
                    _aid = title_to_id.get(sample)
                    if _aid:
                        st.session_state["selected_seed_ids"] = [_aid]
                        st.session_state["selected_seed_titles"] = [sample]
                        st.session_state["_default_seed_active"] = False
                        st.rerun()

    st.caption("Or search for any title in the sidebar.")


# ── Footer (diversity panel + help) ──────────────────────────────────────────


def render_footer(
    recs: list[dict],
    metadata: pd.DataFrame,
    browse_mode: bool,
    ui_mode: str,
) -> None:
    """Render the diversity panel and help/FAQ section."""
    render_diversity_panel(recs, metadata, is_browse=browse_mode)
    render_help_panel(ui_mode=ui_mode)
