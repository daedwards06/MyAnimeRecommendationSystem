"""Sidebar rendering for the MARS Streamlit app.

Extracts all sidebar sections from the former monolithic ``app/main.py``:
profile management, personalisation controls, search & seeds, filters &
display options, and help/FAQ.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import streamlit as st

from src.app.constants import DEFAULT_TOP_N, SEED_RANKING_MODE
from src.app.diversity import build_user_genre_hist
from src.app.recommender import choose_weights

from app.state import ratings_signature


# ── Return type ──────────────────────────────────────────────────────────────


@dataclass
class SidebarResult:
    """Container for all state produced by the sidebar."""

    ui_mode: str = "Seed-based"
    browse_mode: bool = False
    selected_seed_ids: list[int] = field(default_factory=list)
    selected_seed_titles: list[str] = field(default_factory=list)
    query: str = ""
    weight_mode: str = "Balanced"
    weights: dict = field(default_factory=dict)
    genre_filter: list[str] = field(default_factory=list)
    type_filter: list[str] = field(default_factory=list)
    year_range: tuple[int, int] = (1960, 2025)
    sort_by: str = "Match score"
    default_sort_for_mode: str = "Match score"
    top_n: int = DEFAULT_TOP_N
    view_mode: str = "list"
    show_seeds_controls: bool = True
    title_to_id: dict[str, int] = field(default_factory=dict)
    available_titles: list[str] = field(default_factory=list)


# ── Public entry point ───────────────────────────────────────────────────────


def render_sidebar(
    bundle: dict,
    metadata,
    personas: list[dict],
    *,
    clear_cache_fn: Callable[[], None] | None = None,
) -> SidebarResult:
    """Render the full sidebar and return derived state.

    Parameters
    ----------
    bundle : dict
        Artifact bundle from ``build_artifacts()``.
    metadata : DataFrame
        Anime metadata (``bundle["metadata"]``).
    personas : list[dict]
        Loaded persona definitions (may be empty).
    clear_cache_fn : callable, optional
        Callback to clear the artifact cache (``init_bundle.clear``).
    """
    result = SidebarResult()

    _render_mode_selector(result)
    _render_reload_button(clear_cache_fn)
    _render_profile_section(metadata)
    _render_personalization_section(bundle, metadata)
    _render_search_seeds_section(metadata, result)
    _render_filters_display_section(metadata, result)
    _render_help_section()

    # Persist to query params
    st.session_state["query"] = result.query
    st.session_state["weight_mode"] = result.weight_mode
    st.session_state["top_n"] = result.top_n
    st.query_params.update(
        {"q": result.query, "wm": result.weight_mode, "n": str(result.top_n)}
    )

    result.weights = choose_weights(result.weight_mode)

    _render_seed_indicator(result)
    _render_performance_section()

    st.sidebar.caption("MARS · My Anime Recommendation System")

    return result


# ── Section 0: Mode selector ────────────────────────────────────────────────


def _render_mode_selector(result: SidebarResult) -> None:
    st.sidebar.markdown(
        "<p style='font-weight:700; font-size:0.8rem; color:#4A5568; "
        "letter-spacing:0.06em; text-transform:uppercase; margin-bottom:4px;'>"
        "Mode</p>",
        unsafe_allow_html=True,
    )

    prev_mode = st.session_state.get("_ui_mode_prev")
    _ui_mode_options = ["Personalized", "Seed-based", "Browse"]
    _ui_mode_current = st.session_state.get("ui_mode")
    _legacy_browse = bool(st.session_state.get("browse_mode", False))
    if _ui_mode_current in _ui_mode_options:
        _ui_mode_index = _ui_mode_options.index(str(_ui_mode_current))
    else:
        _ui_mode_index = 2 if _legacy_browse else 1

    ui_mode = st.sidebar.radio(
        "Choose your mode",
        _ui_mode_options,
        index=_ui_mode_index,
        key="ui_mode",
        help=(
            "Personalized: ranked results using your rated profile history. "
            "Seed-based: ranked results anchored to 1–5 seed titles. "
            "Browse: filters/sorts catalog metadata only (no ranking)."
        ),
    )

    mode_changed = prev_mode is not None and ui_mode != prev_mode
    st.session_state["_ui_mode_prev"] = ui_mode

    browse_mode = ui_mode == "Browse"
    st.session_state["browse_mode"] = browse_mode

    if ui_mode != "Personalized":
        st.session_state["personalization_enabled"] = False
        st.session_state["_personalization_autoset"] = False
    elif prev_mode != "Personalized":
        st.session_state["_personalization_autoset"] = False

    if mode_changed:
        st.rerun()

    result.ui_mode = str(ui_mode)
    result.browse_mode = browse_mode


def _render_reload_button(clear_cache_fn: Callable[[], None] | None) -> None:
    if st.sidebar.button("Reload artifacts"):
        if clear_cache_fn:
            try:
                clear_cache_fn()
            except Exception:
                st.sidebar.warning("Could not clear cache; please restart the app.")
        st.rerun()


# ── Section 1: User Profile ─────────────────────────────────────────────────


def _render_profile_section(metadata) -> None:
    st.sidebar.markdown(
        "<p style='font-weight:700; font-size:0.8rem; color:#4A5568; "
        "letter-spacing:0.06em; text-transform:uppercase; margin-bottom:4px;'>"
        "Profile</p>",
        unsafe_allow_html=True,
    )

    from src.data.user_profiles import list_profiles, load_profile, save_profile
    from src.data.mal_parser import parse_mal_export, get_mal_export_summary

    # Initialise session state for profile
    if "active_profile" not in st.session_state:
        st.session_state["active_profile"] = None
    if "parsed_mal_data" not in st.session_state:
        st.session_state["parsed_mal_data"] = None

    # Profile selector
    available_profiles = list_profiles()
    profile_options = ["(none)"] + available_profiles

    current_selection = "(none)"
    if st.session_state["active_profile"]:
        current_selection = st.session_state["active_profile"].get("username", "(none)")
        if current_selection not in profile_options:
            current_selection = "(none)"

    selected_profile = st.sidebar.selectbox(
        "Active Profile",
        options=profile_options,
        index=(
            profile_options.index(current_selection)
            if current_selection in profile_options
            else 0
        ),
        help="Select a profile to hide already-watched titles from results",
        label_visibility="collapsed",
    )

    # Load profile when selection changes
    if selected_profile != "(none)" and (
        not st.session_state["active_profile"]
        or st.session_state["active_profile"].get("username") != selected_profile
    ):
        profile_data = load_profile(selected_profile)
        if profile_data:
            st.session_state["active_profile"] = profile_data
            st.rerun()
    elif selected_profile == "(none)" and st.session_state["active_profile"]:
        st.session_state["active_profile"] = None
        st.rerun()

    # Show profile stats or import CTA
    if st.session_state["active_profile"]:
        _render_profile_stats(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary)
    else:
        _render_profile_import_cta(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary)


def _render_profile_stats(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary) -> None:
    profile = st.session_state["active_profile"]
    watched_count = len(profile.get("watched_ids", []))
    avg_rating = profile.get("stats", {}).get("avg_rating", 0)

    st.sidebar.success(f"**{profile['username']}** · {watched_count} watched")

    ratings_count = len(profile.get("ratings", {}))
    if ratings_count > 0:
        st.sidebar.caption(f"{ratings_count} ratings · Avg {avg_rating:.1f}/10")

        if st.sidebar.checkbox("Rating distribution", key="show_rating_dist", value=False):
            ratings = profile.get("ratings", {})
            distribution = {str(i): 0 for i in range(10, 0, -1)}
            for rating in ratings.values():
                distribution[str(rating)] = distribution.get(str(rating), 0) + 1
            for rating in ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]:
                count = distribution[rating]
                if count > 0:
                    bar = "█" * min(count, 20)
                    st.sidebar.caption(f"{rating}/10: {bar} ({count})")
    elif avg_rating > 0:
        st.sidebar.caption(f"Avg Rating: {avg_rating:.1f}/10")

    # Import MAL (collapsed by default)
    _render_mal_import(
        metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary,
        expanded=False, key_suffix="",
    )


def _render_profile_import_cta(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary) -> None:
    st.sidebar.info("Import your MAL watchlist to hide watched anime")
    _render_mal_import(
        metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary,
        expanded=True, key_suffix="_no_profile",
    )


def _render_mal_import(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary, *, expanded, key_suffix) -> None:
    with st.sidebar.expander("📥 Import from MAL", expanded=expanded):
        st.caption("Update your watchlist & ratings" if not key_suffix else "Get started by importing your watchlist")

        uploaded_file = st.file_uploader(
            "Upload MAL XML Export",
            type=["xml"],
            help="Export your list from MyAnimeList.net" if not key_suffix else "Export from MyAnimeList.net",
            label_visibility="collapsed",
            key=f"mal_uploader{key_suffix}",
        )

        if uploaded_file is not None:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Preview", use_container_width=True, key=f"preview{key_suffix}"):
                    try:
                        import tempfile

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        summary = get_mal_export_summary(tmp_path)
                        st.session_state["mal_summary"] = summary
                        st.session_state["mal_tmp_path"] = tmp_path
                    except Exception as e:
                        st.error(f"Error: {e}")

            with col2:
                if st.button("🔄 Parse", use_container_width=True, key=f"parse{key_suffix}"):
                    try:
                        if "mal_tmp_path" not in st.session_state:
                            import tempfile

                            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name
                        else:
                            tmp_path = st.session_state["mal_tmp_path"]

                        with st.spinner("Parsing..."):
                            parsed_data = parse_mal_export(
                                xml_path=tmp_path,
                                metadata_df=metadata,
                                include_statuses={"Completed", "Watching", "On-Hold"},
                                use_default_for_unrated=True,
                                default_rating=7.0,
                            )
                            st.session_state["parsed_mal_data"] = parsed_data
                        st.success(f"✓ Parsed {len(parsed_data['watched_ids'])} anime")
                    except Exception as e:
                        st.error(f"Error: {e}")

        if st.session_state.get("parsed_mal_data"):
            parsed = st.session_state["parsed_mal_data"]
            st.caption(
                f"✓ {parsed['stats']['total_watched']} matched • "
                f"{parsed['stats']['rated_count']} rated"
            )

            if parsed.get("unmatched") and not key_suffix:
                st.warning(f"⚠️ {len(parsed['unmatched'])} unmatched")

            username_input = st.text_input(
                "Profile Name",
                value=parsed.get("username", "my_profile"),
                help="Choose a name for this profile" if not key_suffix else None,
                key=f"username{key_suffix}",
            )

            if st.button(
                "💾 Save Profile",
                type="primary",
                use_container_width=True,
                key=f"save{key_suffix}",
            ):
                try:
                    save_profile(username_input, parsed)
                    st.session_state["active_profile"] = load_profile(username_input)
                    st.session_state["parsed_mal_data"] = None
                    if "mal_summary" in st.session_state:
                        del st.session_state["mal_summary"]
                    if "mal_tmp_path" in st.session_state:
                        import os

                        try:
                            os.unlink(st.session_state["mal_tmp_path"])
                        except Exception:
                            pass
                        del st.session_state["mal_tmp_path"]
                    st.success(f"✓ Saved as '{username_input}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")


# ── Section 2: Personalisation ───────────────────────────────────────────────


def _render_personalization_section(bundle: dict, metadata) -> None:
    st.sidebar.markdown("---")
    ui_mode = str(st.session_state.get("ui_mode", "Seed-based"))
    st.sidebar.markdown(
        "<p style='font-weight:700; font-size:0.8rem; color:#4A5568; "
        "letter-spacing:0.06em; text-transform:uppercase; margin-bottom:4px;'>"
        "Personalization</p>",
        unsafe_allow_html=True,
    )

    # User genre history (for novelty) ----------------------------------------
    if "user_genre_hist" not in st.session_state:
        st.session_state["user_genre_hist"] = {}
    if "user_genre_hist_meta" not in st.session_state:
        st.session_state["user_genre_hist_meta"] = {}

    if st.session_state.get("active_profile"):
        _ratings = st.session_state["active_profile"].get("ratings", {})
        _ratings_sig = ratings_signature(_ratings)
        _profile_username = (st.session_state.get("active_profile") or {}).get("username")
        _cached = st.session_state.get("user_genre_hist_meta") or {}
        _needs_refresh = (
            not isinstance(st.session_state.get("user_genre_hist"), dict)
            or _cached.get("ratings_sig") != _ratings_sig
            or _cached.get("profile_username") != _profile_username
        )
        if _needs_refresh:
            st.session_state["user_genre_hist"] = build_user_genre_hist(_ratings, metadata)
            st.session_state["user_genre_hist_meta"] = {
                "ratings_sig": _ratings_sig,
                "profile_username": _profile_username,
            }
    else:
        st.session_state["user_genre_hist"] = {}
        st.session_state["user_genre_hist_meta"] = {}

    # Initialise personalisation state
    for key, default in {
        "personalization_enabled": False,
        "personalization_strength": 100,
        "user_embedding": None,
        "user_embedding_meta": {},
        "personalization_blocked_reason": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Check if profile has ratings
    profile_has_ratings = False
    ratings: dict = {}
    if st.session_state.get("active_profile"):
        ratings = st.session_state["active_profile"].get("ratings", {})
        profile_has_ratings = len(ratings) > 0

    if ui_mode != "Personalized":
        with st.sidebar.expander("🎯 Personalization (Personalized mode only)", expanded=False):
            st.caption("Switch to **Personalized** mode to use rated history.")
            st.caption("Novelty remains **NA** without rated profile history.")
        st.session_state["personalization_enabled"] = False
        st.session_state["personalization_blocked_reason"] = None
    else:
        if not st.session_state.get("active_profile"):
            st.sidebar.warning("Personalized mode unavailable: select a profile")
            st.sidebar.caption(
                "Fix: Choose an **Active Profile** (top of sidebar) and add at least one rating."
            )
            st.session_state["personalization_enabled"] = False
            st.session_state["personalization_blocked_reason"] = "No active profile selected."
        elif not profile_has_ratings:
            st.sidebar.warning("Personalized mode unavailable: no ratings")
            st.sidebar.caption(
                "Fix: Add at least one rating (use the in-card rating buttons after selecting a profile)."
            )
            st.session_state["personalization_enabled"] = False
            st.session_state["personalization_blocked_reason"] = "No ratings in active profile."
        else:
            # Auto-enable when entering Personalized mode
            if not st.session_state.get("personalization_enabled", False) and not st.session_state.get(
                "_personalization_autoset", False
            ):
                st.session_state["personalization_enabled"] = True
                st.session_state["_personalization_autoset"] = True

            personalization_enabled = st.sidebar.checkbox(
                "Enable personalization",
                value=bool(st.session_state.get("personalization_enabled", False)),
                help=(
                    f"Applies only in Personalized mode. Uses your {len(ratings)} ratings to "
                    "rerank results. If personalization is unavailable (no ratings / no MF overlap / "
                    "missing model), the UI says why and shows no fallback results."
                ),
            )
            st.session_state["personalization_enabled"] = personalization_enabled

            if not personalization_enabled:
                st.sidebar.info("Enable personalization to run Personalized mode")
            else:
                personalization_strength = st.sidebar.slider(
                    "Strength",
                    min_value=0,
                    max_value=100,
                    value=int(st.session_state.get("personalization_strength", 100)),
                    help=(
                        "Controls how strongly your rated-history signal influences ranking. "
                        "0% = seed-based only, 100% = fully personalized. "
                        "Applied only when personalization is enabled and available."
                    ),
                    format="%d%%",
                )
                st.session_state["personalization_strength"] = personalization_strength

            # Generate / refresh user embedding
            _refresh_user_embedding(bundle, ratings)

    # Taste profile visualisation
    if (
        st.session_state.get("active_profile")
        and st.session_state.get("user_embedding") is not None
        and ui_mode == "Personalized"
    ):
        if st.sidebar.checkbox("🎨 View Taste Profile", key="show_taste_profile", value=False):
            from src.app.components.taste_profile import render_taste_profile_panel

            render_taste_profile_panel(st.session_state["active_profile"], metadata)


def _refresh_user_embedding(bundle: dict, ratings: dict) -> None:
    """Generate or refresh user embedding when inputs change."""
    mf_model = bundle.get("models", {}).get("mf")
    mf_stem = bundle.get("models", {}).get("_mf_stem")
    profile_username = (st.session_state.get("active_profile", {}) or {}).get("username")
    ratings_sig = ratings_signature(ratings)
    cached = st.session_state.get("user_embedding_meta", {}) or {}

    needs_refresh = (
        st.session_state["user_embedding"] is None
        or cached.get("ratings_sig") != ratings_sig
        or cached.get("mf_stem") != mf_stem
        or cached.get("profile_username") != profile_username
    )

    if mf_model is None:
        st.session_state["user_embedding"] = None
        st.session_state["user_embedding_meta"] = {
            "ratings_sig": ratings_sig,
            "mf_stem": mf_stem,
            "profile_username": profile_username,
        }
        st.session_state["personalization_blocked_reason"] = (
            "MF model is not available (artifact load/selection failed)."
        )
        st.sidebar.error("Personalization unavailable: MF model missing")
    elif needs_refresh:
        with st.spinner("Generating taste profile..."):
            from src.models.user_embedding import generate_user_embedding

            try:
                user_embedding = generate_user_embedding(
                    ratings_dict=ratings,
                    mf_model=mf_model,
                    method="weighted_average",
                    normalize=True,
                )
            except Exception as e:  # noqa: BLE001
                st.session_state["user_embedding"] = None
                st.session_state["personalization_blocked_reason"] = (
                    f"Failed generating user embedding: {e}"
                )
                st.sidebar.error("Personalization unavailable: embedding failed")
            else:
                try:
                    emb_norm = float(np.linalg.norm(user_embedding))
                except Exception:
                    emb_norm = 0.0
                if emb_norm <= 1e-8:
                    st.session_state["user_embedding"] = None
                    st.session_state["personalization_blocked_reason"] = (
                        "Your rated items do not overlap the MF model training set."
                    )
                    st.sidebar.warning("Personalization unavailable: no MF overlap")
                else:
                    st.session_state["user_embedding"] = user_embedding
                    st.session_state["personalization_blocked_reason"] = None
                    st.sidebar.success(f"✓ Profile ready ({len(ratings)} ratings)")

            st.session_state["user_embedding_meta"] = {
                "ratings_sig": ratings_sig,
                "mf_stem": mf_stem,
                "profile_username": profile_username,
            }
    else:
        st.sidebar.caption(f"✓ Using {len(ratings)} ratings")


# ── Section 3: Search & Seeds ────────────────────────────────────────────────


def _render_search_seeds_section(metadata, result: SidebarResult) -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='font-weight:700; font-size:0.8rem; color:#4A5568; "
        "letter-spacing:0.06em; text-transform:uppercase; margin-bottom:4px;'>"
        "Search &amp; Seeds</p>",
        unsafe_allow_html=True,
    )

    ui_mode = str(st.session_state.get("ui_mode", "Seed-based"))
    show_seeds_controls = ui_mode in {"Seed-based", "Personalized"}
    result.show_seeds_controls = show_seeds_controls

    if not show_seeds_controls:
        with st.sidebar.expander("🔍 Search & Seeds (not used in Browse)", expanded=False):
            st.caption("Browse mode uses genre/type/year filters only.")
        result.query = ""
        result.weight_mode = str(st.session_state.get("weight_mode", "Balanced"))
        return

    # Build title→id mapping
    def get_display_title(row):
        title_eng = row.get("title_english")
        if title_eng and isinstance(title_eng, str) and title_eng.strip():
            return title_eng
        title_disp = row.get("title_display")
        if title_disp and isinstance(title_disp, str) and title_disp.strip():
            return title_disp
        return None

    title_to_id: dict[str, int] = {}
    for _, row in metadata.iterrows():
        title = get_display_title(row)
        if title:
            title_to_id[title] = int(row["anime_id"])

    available_titles = sorted(title_to_id.keys())
    result.title_to_id = title_to_id
    result.available_titles = available_titles

    current_seed_titles = st.session_state.get("selected_seed_titles", [])
    selected_titles = st.sidebar.multiselect(
        "Search Titles (1-5 seeds)",
        options=available_titles,
        default=current_seed_titles,
        max_selections=5,
        help=(
            "Select 1–5 seed titles. Ranked results are anchored to these "
            "seeds and show Match score (relative) for the current run."
        ),
    )

    result.query = selected_titles[0] if selected_titles else ""

    weight_mode = st.sidebar.radio(
        "Hybrid Weights",
        ["Balanced", "Diversity"],
        index=(0 if st.session_state.get("weight_mode") != "Diversity" else 1),
        horizontal=True,
        help=(
            "Changes how the ranking blends signals (e.g., similarity vs popularity "
            "emphasis). Useful when you want broader discovery; most noticeable in "
            "Seed-based and Personalized modes."
        ),
    )
    result.weight_mode = str(weight_mode)

    # Seed ranking goal
    if ui_mode in {"Seed-based", "Personalized"}:
        _goal_opts = [
            "Goal: Completion (more from franchise)",
            "Goal: Discovery (similar vibes)",
        ]
        _mode_default = str(
            st.session_state.get("seed_ranking_mode", SEED_RANKING_MODE) or SEED_RANKING_MODE
        ).strip().lower()
        _goal_index = 0 if _mode_default != "discovery" else 1
        _goal_label = st.sidebar.radio(
            "Seed goal",
            _goal_opts,
            index=_goal_index,
            horizontal=False,
            key="seed_goal_ui",
            help=(
                "Completion lets sequels/spin-offs surface freely. "
                "Discovery limits franchise dominance in top results "
                "using a deterministic title-overlap cap."
            ),
        )
        st.session_state["seed_ranking_mode"] = (
            "discovery" if "Discovery" in str(_goal_label) else "completion"
        )

    # Convert selected titles to IDs
    selected_seed_ids: list[int] = []
    selected_seed_titles: list[str] = []
    for title in selected_titles:
        aid = title_to_id.get(title)
        if aid:
            selected_seed_ids.append(aid)
            selected_seed_titles.append(title)

    result.selected_seed_ids = selected_seed_ids
    result.selected_seed_titles = selected_seed_titles
    st.session_state["selected_seed_ids"] = selected_seed_ids
    st.session_state["selected_seed_titles"] = selected_seed_titles


# ── Section 4: Filters & Display ─────────────────────────────────────────────


def _render_filters_display_section(metadata, result: SidebarResult) -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='font-weight:700; font-size:0.8rem; color:#4A5568; "
        "letter-spacing:0.06em; text-transform:uppercase; margin-bottom:4px;'>"
        "Filters &amp; Display</p>",
        unsafe_allow_html=True,
    )

    top_n = st.sidebar.slider(
        "Top N", 5, 30, int(st.session_state.get("top_n", DEFAULT_TOP_N))
    )
    st.session_state["top_n"] = top_n
    result.top_n = top_n

    browse_mode = bool(st.session_state.get("browse_mode", False))
    if browse_mode:
        st.sidebar.caption("Browse mode: select at least one genre to see results.")

    default_sort_for_mode = "MAL Score" if browse_mode else "Match score"
    result.default_sort_for_mode = default_sort_for_mode

    sort_options = (
        ["MAL Score", "Year (Newest)", "Year (Oldest)", "Popularity"]
        if browse_mode
        else ["Match score", "MAL Score", "Year (Newest)", "Year (Oldest)", "Popularity"]
    )
    current_sort = st.session_state.get("sort_by", default_sort_for_mode)
    if current_sort not in sort_options:
        current_sort = default_sort_for_mode
    sort_by = st.sidebar.selectbox(
        "Sort by",
        sort_options,
        index=sort_options.index(current_sort),
    )
    result.sort_by = str(sort_by)

    # Genre filter
    all_genres: set[str] = set()
    for genres_val in metadata["genres"].dropna():
        if isinstance(genres_val, str):
            all_genres.update([g.strip() for g in genres_val.split("|") if g.strip()])
        elif hasattr(genres_val, "__iter__") and not isinstance(genres_val, str):
            all_genres.update([str(g).strip() for g in genres_val if g])
    genre_options = sorted(list(all_genres))

    genre_filter = st.sidebar.multiselect(
        "Filter by Genre",
        options=genre_options,
        default=st.session_state.get("genre_filter", []),
        help="Applies in all modes. In Browse, select at least one genre to see titles.",
    )
    result.genre_filter = list(genre_filter)

    # Type filter
    all_types: set[str] = set()
    for type_val in metadata["type"].dropna() if "type" in metadata.columns else []:
        if type_val and isinstance(type_val, str):
            all_types.add(type_val.strip())
    type_options = (
        sorted(list(all_types))
        if all_types
        else ["TV", "Movie", "OVA", "Special", "ONA", "Music"]
    )

    type_filter = st.sidebar.multiselect(
        "Filter by Type",
        options=type_options,
        default=st.session_state.get("type_filter", []),
        help="Applies in all modes to the displayed list (TV, Movie, OVA, etc.)",
    )
    result.type_filter = list(type_filter)

    year_range = st.sidebar.slider(
        "Release Year Range",
        min_value=1960,
        max_value=2025,
        value=(
            st.session_state.get("year_min", 1960),
            st.session_state.get("year_max", 2025),
        ),
        help="Applies in all modes to the displayed list",
    )
    result.year_range = (year_range[0], year_range[1])

    st.session_state["sort_by"] = sort_by
    st.session_state["genre_filter"] = genre_filter
    st.session_state["type_filter"] = type_filter
    st.session_state["year_min"] = year_range[0]
    st.session_state["year_max"] = year_range[1]

    # View mode toggle
    view_mode = st.sidebar.radio(
        "📊 View Mode",
        ["List", "Grid"],
        index=0 if st.session_state.get("view_mode", "list") == "list" else 1,
        horizontal=True,
        help="Switch between list and grid layout",
    )
    st.session_state["view_mode"] = "list" if view_mode == "List" else "grid"
    result.view_mode = st.session_state["view_mode"]

    # Clear filters button
    if (
        genre_filter
        or type_filter
        or year_range[0] > 1960
        or year_range[1] < 2025
        or sort_by != default_sort_for_mode
    ):
        if st.sidebar.button("🔄 Reset Filters", help="Clear all filters and reset to defaults"):
            st.session_state["sort_by"] = default_sort_for_mode
            st.session_state["genre_filter"] = []
            st.session_state["type_filter"] = []
            st.session_state["year_min"] = 1960
            st.session_state["year_max"] = 2025
            st.rerun()


# ── Section 5: Help & FAQ ────────────────────────────────────────────────────


def _render_help_section() -> None:
    st.sidebar.markdown("---")
    with st.sidebar.expander("Quick Guide", expanded=False):
        st.markdown(
            """
    <div style='font-size: 0.88rem; line-height: 1.9; color: #4A5568;'>
    <b>1.</b> Choose a mode &mdash; Personalized / Seed-based / Browse<br>
    <b>2.</b> Seed-based &mdash; pick 1&ndash;5 seeds or try the sample buttons<br>
    <b>3.</b> Browse &mdash; select genres to explore the catalog<br>
    <b>4.</b> Personalized &mdash; load a rated profile to unlock<br>
    <b>5.</b> Refine with filters, weights, and sort options
    </div>
    """,
            unsafe_allow_html=True,
        )


# ── Seed indicator ───────────────────────────────────────────────────────────


def _render_seed_indicator(result: SidebarResult) -> None:
    selected_seed_ids = result.selected_seed_ids
    selected_seed_titles = result.selected_seed_titles
    show_seeds_controls = result.show_seeds_controls

    if selected_seed_ids and selected_seed_titles:
        if len(selected_seed_titles) == 1:
            st.sidebar.success(f"**Active Seed:** {selected_seed_titles[0]}")
        else:
            st.sidebar.success(f"**Active Seeds** ({len(selected_seed_titles)})")
            for title in selected_seed_titles:
                st.sidebar.caption(f"· {title}")
        if st.sidebar.button("Clear Seeds", key="clear_seed"):
            st.session_state["selected_seed_ids"] = []
            st.session_state["selected_seed_titles"] = []
            st.session_state["_default_seed_active"] = False
            st.rerun()
    elif show_seeds_controls:
        st.sidebar.caption("**Try a popular title:**")
        sample_titles = [
            "Steins;Gate",
            "Cowboy Bebop",
            "Death Note",
            "Fullmetal Alchemist: Brotherhood",
        ]
        available_samples = [t for t in sample_titles if t in result.available_titles]
        if available_samples:
            cols = st.sidebar.columns(2)
            for i, sample in enumerate(available_samples[:4]):
                with cols[i % 2]:
                    if st.button(sample, key=f"sample_{i}", use_container_width=True):
                        current_ids = st.session_state.get("selected_seed_ids", [])
                        current_titles = st.session_state.get("selected_seed_titles", [])
                        aid = result.title_to_id.get(sample)
                        if aid and sample not in current_titles and len(current_ids) < 5:
                            current_ids.append(aid)
                            current_titles.append(sample)
                            st.session_state["selected_seed_ids"] = current_ids
                            st.session_state["selected_seed_titles"] = current_titles
                            st.session_state["_default_seed_active"] = False
                            st.rerun()


# ── Performance metrics ──────────────────────────────────────────────────────


def _render_performance_section() -> None:
    with st.sidebar.expander("Performance", expanded=False):
        from src.app.profiling import get_last_timing

        try:
            last_timing = get_last_timing()
            if last_timing:
                latency_ms = last_timing.get("recommendations", 0) * 1000
                status_color = (
                    "#48BB78" if latency_ms < 250 else "#ECC94B" if latency_ms < 500 else "#FC8181"
                )
                st.markdown(
                    f"""
            <div style='background:#F7FAFC; border-radius:8px; padding:12px; margin-bottom:8px; border:1px solid #E2E8F0;'>
                <p style='margin:0; font-size:0.78rem; color:#A0AEC0; text-transform:uppercase; letter-spacing:0.05em;'>Inference</p>
                <p style='margin:0; font-size:1.2rem; font-weight:700; color:{status_color};'>{latency_ms:.0f}ms</p>
            </div>
            """,
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Run a ranked mode to see timing data.")
        except Exception:
            st.caption("Run a ranked mode to see metrics.")
