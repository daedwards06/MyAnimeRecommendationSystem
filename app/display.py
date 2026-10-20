"""Display rendering for the MARS Streamlit app.

Handles header rendering, result card orchestration,
diversity mix bar, empty states, and the footer (diversity panel, help,
scoring details).
"""

from __future__ import annotations

import html
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from app.state import filter_defaults, reset_filters
from src.app.artifacts_loader import FAMILY_LABELS, missing_expected_families
from src.app.badges import badge_payload
from src.app.components.cards import GRID_MARKER_HTML, render_card, render_card_grid
from src.app.components.diversity import render_diversity_panel
from src.app.components.help import render_help_panel
from src.app.components.instructions import render_intro_line
from src.app.components.skeletons import card_skeleton_html
from src.app.score_semantics import has_match_score

if TYPE_CHECKING:
    from app.pipeline_runner import PipelineRunResult
    from app.sidebar import SidebarResult


# ── Header ───────────────────────────────────────────────────────────────────


HEADER_TITLE = "MARS"

_MODE_SUBTITLES: dict[str, str] = {
    "Seed-based": "Find anime like the ones you love",
    "Personalized": "Ranked from your ratings",
    "Browse": "Browse the catalog",
}


def header_text(ui_mode: str) -> tuple[str, str]:
    """(title, subtitle) for the page header; the title is the same in every mode."""
    return HEADER_TITLE, _MODE_SUBTITLES.get(ui_mode, _MODE_SUBTITLES["Seed-based"])


def header_html(ui_mode: str) -> str:
    title, subtitle = header_text(ui_mode)
    return (
        f"<h1 class='mars-wordmark'>{title}</h1>"
        f"<p class='mars-header-subtitle'>{subtitle}</p>"
    )


def render_header(ui_mode: str) -> None:
    """Render the page header: MARS plus a one-line subtitle for the current mode."""
    st.markdown(header_html(ui_mode), unsafe_allow_html=True)


def render_import_light_warning() -> None:
    """Show warning banner when running in lightweight import mode."""
    if os.environ.get("APP_IMPORT_LIGHT"):
        st.warning(
            "Lightweight import mode active. Restart without APP_IMPORT_LIGHT for full functionality."
        )


def artifact_notice(load_report: dict | None) -> str | None:
    """One-line notice naming expected model families that did not load, or None."""
    if load_report is None:
        return None
    missing = missing_expected_families(load_report)
    if not missing:
        return None
    names = ", ".join(FAMILY_LABELS.get(f, f) for f in missing)
    return (
        f"Some model artifacts did not load ({names}); recommendations run without them. "
        "Details under Scoring details at the bottom of the page."
    )


def franchise_hidden_text(diagnostics: dict | None) -> str | None:
    """Footer line for franchise entries the discovery cap kept out of the shown results."""
    hidden = int((diagnostics or {}).get("franchise_items_dropped_count_topn", 0) or 0)
    if hidden <= 0:
        return None
    noun = "entry" if hidden == 1 else "entries"
    return (
        f"{hidden} franchise {noun} hidden — check the box to show them "
        "(Advanced → Include sequels & spin-offs)."
    )


def render_artifact_notice(load_report: dict | None) -> None:
    """Show the missing-artifact notice under the header when an expected family failed."""
    notice = artifact_notice(load_report)
    if notice:
        st.warning(notice)


def render_intro_section(
    ui_mode: str,
    seed_titles: list[str],
    *,
    default_seed_title: str | None = None,
) -> None:
    """Render the dismissible one-line intro under the header."""
    render_intro_line(ui_mode, seed_titles, default_seed_title=default_seed_title)


# ── Results rendering ────────────────────────────────────────────────────────


def title_card(label: str, text: str = "") -> str:
    """Section header: the label in the display face, an optional plain-text line under it."""
    parts = [f"<h2 class='mars-title-card-label'>{html.escape(label)}</h2>"]
    if text:
        parts.append(f"<p class='mars-title-card-text'>{html.escape(text)}</p>")
    return f"<div class='mars-title-card'>{''.join(parts)}</div>"


def render_title_card(label: str, text: str = "") -> None:
    st.markdown(title_card(label, text), unsafe_allow_html=True)


def render_results(
    recs: list[dict],
    metadata: pd.DataFrame,
    sidebar: SidebarResult,
    pipeline: PipelineRunResult,
    *,
    title: str = "Recommendations",
    pop_pct_fn: Callable[[int], float],
    is_in_training_fn: Callable[[int], bool],
) -> None:
    """Render recommendation results: title card with the count, mix bar, cards."""
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

    item_type = "titles" if sidebar.browse_mode else "recommendations"
    st.markdown(
        title_card(title, f"{len(recs)} {item_type}")
        + result_scope_html(total_anime, filters_text),
        unsafe_allow_html=True,
    )

    if st.session_state.get("active_profile"):
        watched_count = len(st.session_state["active_profile"].get("watched_ids", []))
        st.caption(f"Excluded {watched_count} already-watched titles")

    if sidebar.sort_by != sidebar.default_sort_for_mode:
        st.caption(f"Sorted by {sidebar.sort_by}")

    # Diversity mix bar
    _render_mix_bar(
        recs, sidebar.browse_mode, pop_pct_fn=pop_pct_fn, is_in_training_fn=is_in_training_fn
    )

    # Cards
    _render_cards(recs, metadata, pop_pct_fn=pop_pct_fn, is_in_training_fn=is_in_training_fn)


def result_scope_html(total: int, filters_text: str = "") -> str:
    return f"<p class='mars-result-scope'>of {total:,}{html.escape(filters_text)}</p>"


def mix_bar_html(mix_label: str, pop_count: int, mid_count: int, long_tail_count: int) -> str:
    """Mix bar markup. Segments are SVG rects sized by attribute, so no inline style is needed."""
    segments = [
        ("popular", pop_count, "Popular"),
        ("midrange", mid_count, "Mid-range"),
        ("longtail", long_tail_count, "Hidden gems"),
    ]
    total = pop_count + mid_count + long_tail_count
    rects: list[str] = []
    x = 0.0
    for key, count, label in segments:
        if count <= 0:
            continue
        width = 100.0 * count / total
        rects.append(
            f'<rect class="mars-mix-{key}" x="{x:.4f}%" y="0" width="{width:.4f}%" height="100%">'
            f"<title>{label}: {count}</title></rect>"
        )
        x += width
    if not rects:
        rects.append('<rect class="mars-mix-empty" x="0" y="0" width="100%" height="100%"></rect>')
    return (
        '<div class="mars-mix">'
        '<div class="mars-mix-head">'
        f'<span class="mars-mix-label">{mix_label}</span>'
        '<span class="mars-mix-legend">'
        f'<span class="mars-mix-dot-popular">●</span> Popular {pop_count}'
        f' &nbsp;<span class="mars-mix-dot-midrange">●</span> Mid {mid_count}'
        f' &nbsp;<span class="mars-mix-dot-longtail">●</span> Hidden gems {long_tail_count}'
        "</span>"
        "</div>"
        f'<svg class="mars-mix-track" width="100%" height="6" aria-hidden="true">{"".join(rects)}</svg>'
        "</div>"
    )


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

    mix_label = "Catalog mix" if browse_mode else "Recommendation mix"
    st.markdown(
        mix_bar_html(mix_label, pop_count, mid_count, long_tail_count), unsafe_allow_html=True
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
        # One block of cards in rank order; CSS lays it out at 4/3/2/1 columns by width.
        with st.container():
            st.markdown(GRID_MARKER_HTML, unsafe_allow_html=True)
            for rec in recs:
                anime_id = rec["anime_id"]
                try:
                    row = metadata_by_id.loc[anime_id]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                except KeyError:
                    continue
                render_card_grid(
                    row,
                    rec,
                    pop_pct_fn(int(anime_id)),
                    is_in_training=is_in_training_fn(int(anime_id)),
                    all_raw_scores=all_raw_scores,
                )
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


# ── Loading, empty and error states ──────────────────────────────────────────

LOADING_EYECATCH = "Now loading…"

ENGINE_UNAVAILABLE_TEXT = (
    "Recommendations can't run right now because the model files didn't load. "
    "Browse still works."
)
ENGINE_UNAVAILABLE_DEV_HINT = (
    "Developer: the recommender engine was not built. Ranked modes need the MF artifacts in "
    "models/ and a run without APP_IMPORT_LIGHT."
)
NO_FALLBACK_TEXT = "MARS does not silently fall back to Similar to a title results."

_EMPTY_SUBJECT = {
    "browse": "No titles",
    "seed": "No similar titles",
    "personalized": "No For me picks",
}
_EMPTY_HINT_WITHOUT_FILTERS = {
    "browse": "Try another genre.",
    "seed": "Try a different seed, or fewer seeds.",
    "personalized": "Try another profile, or switch to Similar to a title.",
}


def loading_html(detail: str, *, cards: int = 3) -> str:
    """The loading block: an eyecatch line with a spinner, over card-shaped skeletons."""
    return (
        "<div class='mars-loading' role='status' aria-live='polite'>"
        "<p class='mars-loading-eyecatch'>"
        "<span class='mars-loading-spinner' aria-hidden='true'></span>"
        f"{LOADING_EYECATCH} <span class='mars-loading-detail'>{html.escape(detail)}</span>"
        "</p>"
        f"{card_skeleton_html(cards)}"
        "</div>"
    )


@contextmanager
def loading_state(detail: str) -> Iterator[None]:
    """Show the loading block while the body runs, then clear it."""
    slot = st.empty()
    slot.markdown(loading_html(detail), unsafe_allow_html=True)
    try:
        yield
    finally:
        slot.empty()


def notice_panel_html(title: str, body_html: str, *, role: str = "status") -> str:
    """Notice panel; ``body_html`` is trusted markup, so callers escape what goes into it."""
    return (
        f"<div class='mars-panel-notice' role='{role}'>"
        f"<p class='mars-panel-notice-title'>{html.escape(title)}</p>"
        f"<p class='mars-panel-notice-body'>{body_html}</p>"
        "</div>"
    )


def start_panel_html(title: str, body: str) -> str:
    return (
        "<div class='mars-panel-start'>"
        f"<h3 class='mars-panel-start-title'>{html.escape(title)}</h3>"
        f"<p class='mars-panel-start-body'>{html.escape(body)}</p>"
        "</div>"
    )


def active_filter_labels(
    genre_filter: list[str],
    type_filter: list[str],
    year_range: tuple[int, int],
    *,
    include_genres: bool = True,
) -> list[str]:
    """One label per Refine filter that is narrowing the results, e.g. ``"Type: Movie"``."""
    defaults = filter_defaults()
    labels: list[str] = []
    if include_genres and genre_filter:
        labels.append(f"Genre: {', '.join(genre_filter)}")
    if type_filter:
        labels.append(f"Type: {', '.join(type_filter)}")
    if year_range[0] > defaults["year_min"] or year_range[1] < defaults["year_max"]:
        labels.append(f"Years: {year_range[0]}–{year_range[1]}")
    return labels


def empty_results_html(kind: str, filter_labels: list[str]) -> str:
    """Zero-results panel naming the filters that removed everything (``kind``: browse/seed/personalized)."""
    subject = _EMPTY_SUBJECT[kind]
    if filter_labels:
        named = " · ".join(f"<b>{html.escape(label)}</b>" for label in filter_labels)
        return notice_panel_html(
            f"{subject} match these filters.",
            f"These filters removed everything: {named}. Clear them to see results again.",
        )
    return notice_panel_html(
        f"{subject} came back.", html.escape(_EMPTY_HINT_WITHOUT_FILTERS[kind])
    )


def render_empty_results(sidebar: SidebarResult, kind: str) -> None:
    """Zero-results panel plus one button that clears the filters it names."""
    # Browse needs its genres, so only type and years count as filters to clear there.
    labels = active_filter_labels(
        sidebar.genre_filter,
        sidebar.type_filter,
        sidebar.year_range,
        include_genres=not sidebar.browse_mode,
    )
    st.markdown(empty_results_html(kind, labels), unsafe_allow_html=True)
    if labels and st.button("Clear filters", key="empty_clear_filters", type="primary"):
        reset_filters(sidebar.default_sort_for_mode, keep_genres=sidebar.browse_mode)
        st.rerun()


def personalized_gate_copy(
    active_profile: dict | None, personalization_enabled: bool
) -> tuple[str, str]:
    """(what is wrong, how to fix it) in visitor words, in the order the gate checks."""
    ratings = active_profile.get("ratings") if isinstance(active_profile, dict) else None
    if not active_profile:
        return (
            "For me needs a profile with ratings.",
            "Pick a demo profile under Personalize in the sidebar, or import your MyAnimeList list.",
        )
    if not ratings:
        return (
            "This profile has no ratings yet.",
            "Rate a few titles from their cards in Similar to a title, or pick a demo profile.",
        )
    if not personalization_enabled:
        return (
            "Personalization is switched off.",
            "Tick Enable personalization under Personalize in the sidebar.",
        )
    return (
        "For me can't rank with this profile yet.",
        "Try a demo profile, or switch to Similar to a title.",
    )


def personalized_gate_html(active_profile: dict | None, personalization_enabled: bool) -> str:
    headline, fix = personalized_gate_copy(active_profile, personalization_enabled)
    return notice_panel_html(
        headline, f"{html.escape(fix)} {html.escape(NO_FALLBACK_TEXT)}", role="alert"
    )


def render_personalized_gate(reason: str) -> None:
    """The one main-area message for a For me run that can't start; the raw reason is folded away."""
    st.markdown(
        personalized_gate_html(
            st.session_state.get("active_profile"),
            bool(st.session_state.get("personalization_enabled", False)),
        ),
        unsafe_allow_html=True,
    )
    with st.expander("Technical reason", expanded=False):
        st.caption(reason)


def render_empty_state(sidebar: SidebarResult, metadata: pd.DataFrame) -> None:
    """Render the guidance when a ranked mode returns no results."""
    if str(st.session_state.get("ui_mode", "Seed-based")) == "Personalized":
        render_empty_results(sidebar, "personalized")
    elif sidebar.selected_seed_ids:
        render_empty_results(sidebar, "seed")
    else:
        _render_cold_start_state(metadata, sidebar.title_to_id)


def _render_cold_start_state(metadata: pd.DataFrame, title_to_id: dict[str, int]) -> None:
    st.markdown(
        start_panel_html("Get Started", "Pick a seed title to discover similar anime"),
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


# ── Footer (diversity panel, help, scoring details) ──────────────────────────


def render_footer(
    recs: list[dict],
    metadata: pd.DataFrame,
    browse_mode: bool,
    ui_mode: str,
    *,
    pipeline: PipelineRunResult | None = None,
    load_report: dict | None = None,
    pipeline_ms: float | None = None,
) -> None:
    """Render the diversity panel, then Help/FAQ and Scoring details side by side."""
    _render_diversity_panel_fragment(recs, metadata, is_browse=browse_mode)
    help_col, details_col = st.columns(2)
    with help_col:
        render_help_panel(
            ui_mode=ui_mode, expanded=bool(st.session_state.get("help_expanded", False))
        )
    with details_col:
        _render_scoring_details(pipeline, load_report, pipeline_ms)


def _render_scoring_details(
    pipeline: PipelineRunResult | None,
    load_report: dict | None,
    pipeline_ms: float | None,
) -> None:
    """Reviewer panel: active scoring path, artifact stems, last pipeline time."""
    with st.expander("Scoring details", expanded=False):
        if pipeline is not None:
            st.caption(f"Active scoring path: {pipeline.active_scoring_path}")
            if pipeline.active_scoring_path == "Ranked modes disabled":
                st.caption(ENGINE_UNAVAILABLE_DEV_HINT)
            blocked_reason = st.session_state.get("personalization_blocked_reason")
            if (
                st.session_state.get("personalization_enabled", False)
                and not pipeline.personalization_applied
                and blocked_reason
            ):
                st.caption(f"Personalization note: {blocked_reason}")
        hidden_text = franchise_hidden_text(st.session_state.get("franchise_cap_diagnostics"))
        if hidden_text:
            st.caption(hidden_text)
        if pipeline_ms is not None:
            st.caption(f"Last pipeline: {pipeline_ms:.0f} ms")
        if load_report is not None:
            for family, entry in load_report.items():
                entry = entry or {}
                label = FAMILY_LABELS.get(family, family)
                if entry.get("loaded"):
                    st.caption(f"{label}: `{entry.get('stem')}`")
            for family in missing_expected_families(load_report):
                reason = (load_report.get(family) or {}).get("reason") or "not in the load report"
                st.caption(f"Not loaded: {FAMILY_LABELS.get(family, family)} — {reason}")


@st.fragment
def _render_diversity_panel_fragment(
    recs: list[dict],
    metadata: pd.DataFrame,
    is_browse: bool = False,
) -> None:
    """Diversity panel fragment - reruns independently when expanded/collapsed."""
    render_diversity_panel(recs, metadata, is_browse=is_browse)
