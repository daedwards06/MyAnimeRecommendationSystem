"""Sidebar rendering for the MARS Streamlit app.

Extracts all sidebar sections from the former monolithic ``app/main.py``:
profile management, personalisation controls, search & seeds, filters &
display options, and help/FAQ.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import streamlit as st

from app.state import ratings_signature, reset_filters
from src.app.constants import DEFAULT_TOP_N, SEED_RANKING_MODE
from src.app.diversity import build_user_genre_hist
from src.app.recommender import choose_weights

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
    mmr_lambda: float | None = None
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

    _group_label("Find")
    _render_mode_selector(result)
    _render_search_seeds_section(metadata, result)
    _render_seed_indicator(result)

    _render_filters_display_section(metadata, result)

    _group_label("Personalize")
    with st.sidebar.expander("Profile and ratings", expanded=result.ui_mode == "Personalized"):
        _render_profile_section(metadata)
        show_taste_profile = _render_personalization_section(bundle, metadata)

    _group_label("Advanced")
    with st.sidebar.expander("Ranking and diagnostics", expanded=False):
        _render_advanced_section(result, clear_cache_fn)

    # Persist to query params
    st.session_state["query"] = result.query
    st.session_state["weight_mode"] = result.weight_mode
    st.session_state["top_n"] = result.top_n
    st.query_params.update({"q": result.query, "wm": result.weight_mode, "n": str(result.top_n)})

    result.weights = choose_weights(result.weight_mode)

    _render_help_section()

    st.sidebar.caption("MARS · My Anime Recommendation System")

    # Rendered outside the sidebar context so the panel lands in the main area.
    if show_taste_profile:
        from src.app.components.taste_profile import render_taste_profile_panel

        render_taste_profile_panel(st.session_state["active_profile"], metadata)

    return result


def _section_label(text: str, *, container=None) -> None:
    (container or st.sidebar).markdown(section_label_html(text), unsafe_allow_html=True)


def section_label_html(text: str) -> str:
    return f"<p class='mars-section-label'>{text}</p>"


def _group_label(text: str, *, container=None) -> None:
    (container or st.sidebar).markdown(group_label_html(text), unsafe_allow_html=True)


def group_label_html(text: str) -> str:
    return f"<p class='mars-group-label'>{text}</p>"


# ── Find: mode selector ─────────────────────────────────────────────────────

# Internal values stay stable (pipeline_runner, state and tests key on them);
# only the user-facing labels change.
MODE_OPTIONS = ["Seed-based", "Personalized", "Browse"]
MODE_LABELS = {
    "Seed-based": "Similar to a title",
    "Personalized": "For me",
    "Browse": "Browse",
}


def mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode, mode)


def _render_mode_selector(result: SidebarResult) -> None:
    prev_mode = st.session_state.get("_ui_mode_prev")
    _ui_mode_current = st.session_state.get("ui_mode")
    _legacy_browse = bool(st.session_state.get("browse_mode", False))
    if _ui_mode_current in MODE_OPTIONS:
        _ui_mode_index = MODE_OPTIONS.index(str(_ui_mode_current))
    else:
        _ui_mode_index = MODE_OPTIONS.index("Browse" if _legacy_browse else "Seed-based")

    ui_mode = st.sidebar.radio(
        "What do you want?",
        MODE_OPTIONS,
        index=_ui_mode_index,
        key="ui_mode",
        format_func=mode_label,
        help=(
            "Similar to a title: ranked results anchored to 1–5 titles you pick. "
            "For me: ranked results using your rated profile history. "
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
    if st.button("Reload artifacts"):
        if clear_cache_fn:
            try:
                clear_cache_fn()
            except Exception:
                st.warning("Could not clear cache; please restart the app.")
        st.rerun()


# ── Section 1: User Profile ─────────────────────────────────────────────────


def _render_profile_section(metadata) -> None:
    _section_label("Profile", container=st)

    from src.data.mal_parser import get_mal_export_summary, parse_mal_export
    from src.data.user_profiles import list_profiles, load_profile, save_profile

    # Initialise session state for profile
    if "active_profile" not in st.session_state:
        st.session_state["active_profile"] = None
    if "parsed_mal_data" not in st.session_state:
        st.session_state["parsed_mal_data"] = None

    # Profile selector
    available_profiles = list_profiles()
    profile_options = ["(none)", *available_profiles]

    current_selection = "(none)"
    if st.session_state["active_profile"]:
        current_selection = st.session_state["active_profile"].get("username", "(none)")
        if current_selection not in profile_options:
            current_selection = "(none)"

    selected_profile = st.selectbox(
        "Active Profile",
        options=profile_options,
        index=(profile_options.index(current_selection) if current_selection in profile_options else 0),
        help="Select a profile to hide already-watched titles from results",
        label_visibility="collapsed",
    )

    # Load profile when selection changes
    if selected_profile != "(none)" and (
        not st.session_state["active_profile"] or st.session_state["active_profile"].get("username") != selected_profile
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
        if st.session_state.get("ui_mode") == "Personalized":
            _render_demo_profile_buttons(available_profiles, load_profile)
        _render_profile_import_cta(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary)


def _render_demo_profile_buttons(available_profiles: list[str], load_profile) -> None:
    demos = [p for p in (load_profile(u) for u in available_profiles if u.startswith("demo_")) if p and p.get("demo")]
    if not demos:
        return
    st.markdown("**Try a demo profile**")
    st.caption("Fictional rating histories, so you can see For me without a MAL export.")
    for demo in demos:
        if st.button(
            demo.get("label", demo["username"]),
            key=f"demo_profile_{demo['username']}",
            help=demo.get("preference_summary") or None,
            use_container_width=True,
        ):
            st.session_state["active_profile"] = demo
            st.session_state["personalization_enabled"] = True
            st.session_state["_personalization_autoset"] = True
            st.rerun()


def _render_profile_stats(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary) -> None:
    profile = st.session_state["active_profile"]
    watched_count = len(profile.get("watched_ids", []))
    avg_rating = profile.get("stats", {}).get("avg_rating", 0)

    if profile.get("demo"):
        st.success(f"**{profile.get('label', profile['username'])}** · {watched_count} watched")
        st.caption(f"Demo profile (read-only). {profile.get('preference_summary', '')}".strip())
    else:
        st.success(f"**{profile['username']}** · {watched_count} watched")

    ratings_count = len(profile.get("ratings", {}))
    if ratings_count > 0:
        st.caption(f"{ratings_count} ratings · Avg {avg_rating:.1f}/10")

        if st.checkbox("Rating distribution", key="show_rating_dist", value=False):
            ratings = profile.get("ratings", {})
            distribution = {str(i): 0 for i in range(10, 0, -1)}
            for rating in ratings.values():
                distribution[str(rating)] = distribution.get(str(rating), 0) + 1
            for rating in ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"]:
                count = distribution[rating]
                if count > 0:
                    bar = "█" * min(count, 20)
                    st.caption(f"{rating}/10: {bar} ({count})")
    elif avg_rating > 0:
        st.caption(f"Avg Rating: {avg_rating:.1f}/10")

    # Import MAL (collapsed by default)
    _render_mal_import(
        metadata,
        save_profile,
        load_profile,
        parse_mal_export,
        get_mal_export_summary,
        expanded=False,
        key_suffix="",
    )


def _render_profile_import_cta(metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary) -> None:
    st.info("Import your MAL watchlist to hide watched anime")
    _render_mal_import(
        metadata,
        save_profile,
        load_profile,
        parse_mal_export,
        get_mal_export_summary,
        expanded=True,
        key_suffix="_no_profile",
    )


def _render_mal_import(
    metadata, save_profile, load_profile, parse_mal_export, get_mal_export_summary, *, expanded, key_suffix
) -> None:
    # A toggle, not an expander: this already sits inside the Personalize expander,
    # and Streamlit forbids nesting expanders.
    if not st.toggle("📥 Import from MAL", value=expanded, key=f"show_mal_import{key_suffix}"):
        return
    with st.container(border=True):
        st.caption("Update your watchlist & ratings" if not key_suffix else "Get started by importing your watchlist")

        # Inline instructions so first-time visitors know how to get their XML
        st.markdown(
            "**How to get your XML export:**\n"
            "1. Log in at [myanimelist.net](https://myanimelist.net)\n"
            "2. Go to [Export](https://myanimelist.net/panel.php?go=export)\n"
            "3. Click **Export My List** and save the `.xml` file\n"
            "4. Upload it below",
            help="The export includes all anime on your list (Completed, Watching, etc.).",
        )

        uploaded_file = st.file_uploader(
            "Upload MAL XML Export",
            type=["xml"],
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
            st.caption(f"✓ {parsed['stats']['total_watched']} matched • {parsed['stats']['rated_count']} rated")

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


def _render_personalization_section(bundle: dict, metadata) -> bool:
    """Render personalization controls; return whether to show the taste-profile panel."""
    st.markdown("---")
    ui_mode = str(st.session_state.get("ui_mode", "Seed-based"))
    _section_label("Personalization", container=st)

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
        st.caption("Switch to **For me** to rank by your rated history.")
        st.caption("Genre novelty is shown only with a rated profile.")
        st.session_state["personalization_enabled"] = False
        st.session_state["personalization_blocked_reason"] = None
    else:
        if not st.session_state.get("active_profile"):
            st.caption("For me needs a profile: pick a demo profile above.")
            st.session_state["personalization_enabled"] = False
            st.session_state["personalization_blocked_reason"] = "No active profile selected."
        elif not profile_has_ratings:
            st.caption("This profile has no ratings yet.")
            st.session_state["personalization_enabled"] = False
            st.session_state["personalization_blocked_reason"] = "No ratings in active profile."
        else:
            # Auto-enable when entering Personalized mode
            if not st.session_state.get("personalization_enabled", False) and not st.session_state.get(
                "_personalization_autoset", False
            ):
                st.session_state["personalization_enabled"] = True
                st.session_state["_personalization_autoset"] = True

            personalization_enabled = st.checkbox(
                "Enable personalization",
                value=bool(st.session_state.get("personalization_enabled", False)),
                help=(
                    f"Applies only in For me mode. Uses your {len(ratings)} ratings to "
                    "rerank results. If personalization is unavailable (no ratings / no MF overlap / "
                    "missing model), the UI says why and shows no fallback results."
                ),
            )
            st.session_state["personalization_enabled"] = personalization_enabled

            if not personalization_enabled:
                st.caption("Personalization is off.")
            else:
                personalization_strength = st.slider(
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
        return bool(st.checkbox("🎨 View Taste Profile", key="show_taste_profile", value=False))
    return False


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
        st.error("Personalization unavailable: MF model missing")
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
            except Exception as e:
                st.session_state["user_embedding"] = None
                st.session_state["personalization_blocked_reason"] = f"Failed generating user embedding: {e}"
                st.caption("This profile couldn't be read for For me.")
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
                    st.caption("None of this profile's titles are in the model yet.")
                else:
                    st.session_state["user_embedding"] = user_embedding
                    st.session_state["personalization_blocked_reason"] = None
                    st.success(f"✓ Profile ready ({len(ratings)} ratings)")

            st.session_state["user_embedding_meta"] = {
                "ratings_sig": ratings_sig,
                "mf_stem": mf_stem,
                "profile_username": profile_username,
            }
    else:
        st.caption(f"✓ Using {len(ratings)} ratings")


# ── Find: title search & sample seeds ───────────────────────────────────────

# Button label -> catalog display title.
SAMPLE_SEEDS = {
    "Steins;Gate": "Steins;Gate",
    "Your Name": "Your Name.",
    "Cowboy Bebop": "Cowboy Bebop",
}
SAMPLE_SEEDS_LABEL_HTML = "<p class='mars-try-label'>Try:</p>"


def _render_search_seeds_section(metadata, result: SidebarResult) -> None:
    ui_mode = str(st.session_state.get("ui_mode", "Seed-based"))
    show_seeds_controls = ui_mode in {"Seed-based", "Personalized"}
    result.show_seeds_controls = show_seeds_controls

    if not show_seeds_controls:
        st.sidebar.caption("Browse uses the genre/type/year filters below; no titles needed.")
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
        "Pick 1–5 titles you like",
        options=available_titles,
        default=current_seed_titles,
        max_selections=5,
        help=(
            "Select 1–5 seed titles. Ranked results are anchored to these "
            "seeds and show Match score (relative) for the current run."
        ),
    )

    result.query = selected_titles[0] if selected_titles else ""

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

    _render_sample_seeds(result)


def _render_sample_seeds(result: SidebarResult) -> None:
    current_titles = list(result.selected_seed_titles)
    if len(current_titles) >= 5:
        return
    samples = [
        (label, title)
        for label, title in SAMPLE_SEEDS.items()
        if title in result.title_to_id and title not in current_titles
    ]
    if not samples:
        return
    # The marker sits inside the row so the CSS can find it; Streamlit 1.38 has no per-key class.
    try_col, *cols = st.sidebar.columns(len(samples) + 1)
    try_col.markdown(SAMPLE_SEEDS_LABEL_HTML, unsafe_allow_html=True)
    for col, (label, title) in zip(cols, samples):
        with col:
            if st.button(label, key=f"sample_{label}"):
                st.session_state["selected_seed_ids"] = [*result.selected_seed_ids, result.title_to_id[title]]
                st.session_state["selected_seed_titles"] = [*current_titles, title]
                st.session_state["_default_seed_active"] = False
                st.rerun()


# ── Section 4: Filters & Display ─────────────────────────────────────────────


def _render_filters_display_section(metadata, result: SidebarResult) -> None:
    """Render filters section in sidebar.

    Note: Fragment optimization for this section requires restructuring to avoid
    st.sidebar calls inside fragments. This is a known Streamlit limitation.
    """
    with st.sidebar:
        _render_filters_display_fragment(metadata, result)


@st.fragment
def _render_filters_display_fragment(metadata, result: SidebarResult) -> None:
    """Filter panel fragment - reruns independently without triggering pipeline."""
    _group_label("Refine", container=st)

    browse_mode = bool(st.session_state.get("browse_mode", False))
    if browse_mode:
        st.caption("Browse mode: select at least one genre to see results.")

    # Genre filter
    all_genres: set[str] = set()
    for genres_val in metadata["genres"].dropna():
        if isinstance(genres_val, str):
            all_genres.update([g.strip() for g in genres_val.split("|") if g.strip()])
        elif hasattr(genres_val, "__iter__") and not isinstance(genres_val, str):
            all_genres.update([str(g).strip() for g in genres_val if g])
    # Public demo safety: exclude explicit genres from UI
    banned_genres_lower = {"hentai", "ecchi", "erotica"}
    genre_options = sorted([g for g in all_genres if str(g).strip().lower() not in banned_genres_lower])

    default_genres = st.session_state.get("genre_filter", [])
    if isinstance(default_genres, (list, tuple)):
        default_genres = [g for g in default_genres if str(g).strip().lower() not in banned_genres_lower]
    else:
        default_genres = []

    genre_filter = st.multiselect(
        "Filter by Genre",
        options=genre_options,
        default=default_genres,
        help="Applies in all modes. In Browse, select at least one genre to see titles.",
    )

    # Sanitize selection defensively (e.g., old session state or query params)
    genre_filter = [g for g in list(genre_filter) if str(g).strip().lower() not in banned_genres_lower]

    # In Browse mode, trigger full rerun when genre selection changes
    prev_genre_filter = st.session_state.get("genre_filter", [])
    if browse_mode and list(genre_filter) != prev_genre_filter:
        st.session_state["genre_filter"] = genre_filter
        st.rerun()

    result.genre_filter = list(genre_filter)

    # Type filter
    all_types: set[str] = set()
    for type_val in metadata["type"].dropna() if "type" in metadata.columns else []:
        if type_val and isinstance(type_val, str):
            all_types.add(type_val.strip())
    type_options = sorted(list(all_types)) if all_types else ["TV", "Movie", "OVA", "Special", "ONA", "Music"]

    type_filter = st.multiselect(
        "Filter by Type",
        options=type_options,
        default=st.session_state.get("type_filter", []),
        help="Applies in all modes to the displayed list (TV, Movie, OVA, etc.)",
    )

    # In Browse mode, trigger full rerun when type selection changes
    prev_type_filter = st.session_state.get("type_filter", [])
    if browse_mode and list(type_filter) != prev_type_filter:
        st.session_state["type_filter"] = type_filter
        st.rerun()

    result.type_filter = list(type_filter)

    year_range = st.slider(
        "Release Year Range",
        min_value=1960,
        max_value=2025,
        value=(
            st.session_state.get("year_min", 1960),
            st.session_state.get("year_max", 2025),
        ),
        help="Applies in all modes to the displayed list",
    )

    # In Browse mode, trigger full rerun when year range changes
    prev_year_min = st.session_state.get("year_min", 1960)
    prev_year_max = st.session_state.get("year_max", 2025)
    if browse_mode and (year_range[0] != prev_year_min or year_range[1] != prev_year_max):
        st.session_state["year_min"] = year_range[0]
        st.session_state["year_max"] = year_range[1]
        st.rerun()

    result.year_range = (year_range[0], year_range[1])

    top_n = st.slider("Top N", 5, 30, int(st.session_state.get("top_n", DEFAULT_TOP_N)))
    st.session_state["top_n"] = top_n
    result.top_n = top_n

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
    sort_by = st.selectbox(
        "Sort by",
        sort_options,
        index=sort_options.index(current_sort),
    )
    result.sort_by = str(sort_by)


    st.session_state["sort_by"] = sort_by
    st.session_state["genre_filter"] = genre_filter
    st.session_state["type_filter"] = type_filter
    st.session_state["year_min"] = year_range[0]
    st.session_state["year_max"] = year_range[1]

    # View mode toggle
    view_mode = st.radio(
        "📊 View Mode",
        ["List", "Grid"],
        index=0 if st.session_state.get("view_mode", "list") == "list" else 1,
        horizontal=True,
        help="Switch between list and grid layout",
    )
    result.view_mode = _apply_view_mode(view_mode)

    # Clear filters button
    if genre_filter or type_filter or year_range[0] > 1960 or year_range[1] < 2025 or sort_by != default_sort_for_mode:
        if st.button("🔄 Reset Filters", help="Clear all filters and reset to defaults"):
            reset_filters(default_sort_for_mode)
            st.rerun()


def _apply_view_mode(choice: str) -> str:
    """Store the List/Grid choice. A change reruns the whole app: this radio sits in a fragment,
    and a fragment-only rerun never reaches the cards (audit F18)."""
    view_mode = "list" if choice == "List" else "grid"
    changed = st.session_state.get("view_mode", "list") != view_mode
    st.session_state["view_mode"] = view_mode
    if changed:
        st.rerun(scope="app")
    return view_mode


# ── Advanced ────────────────────────────────────────────────────────────────


def _render_advanced_section(result: SidebarResult, clear_cache_fn: Callable[[], None] | None) -> None:
    """Ranking knobs and diagnostics; rendered inside the sidebar's Advanced expander."""
    if result.show_seeds_controls:
        weight_mode = st.radio(
            "Hybrid Weights",
            ["Balanced", "Diversity"],
            index=(0 if st.session_state.get("weight_mode") != "Diversity" else 1),
            horizontal=True,
            help=(
                "Changes how the ranking blends signals (e.g., similarity vs popularity "
                "emphasis). Useful when you want broader discovery; most noticeable in "
                "Similar to a title and For me."
            ),
        )
        result.weight_mode = str(weight_mode)
    else:
        result.weight_mode = str(st.session_state.get("weight_mode", "Balanced"))

    # Diversity control (MMR lambda parameter)
    mmr_enabled = st.checkbox(
        "Enable diversity reranking",
        value=st.session_state.get("mmr_enabled", False),
        help="Use MMR (Maximal Marginal Relevance) to balance relevance with genre diversity",
    )
    st.session_state["mmr_enabled"] = mmr_enabled

    if mmr_enabled:
        mmr_lambda = st.slider(
            "Diversity strength",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get("mmr_lambda", 0.3),
            step=0.1,
            help="Lower = more diverse genres, Higher = focus on relevance (0.3 is balanced)",
        )
        st.session_state["mmr_lambda"] = mmr_lambda
        result.mmr_lambda = float(mmr_lambda)
    else:
        result.mmr_lambda = None


    if result.show_seeds_controls:
        _mode_current = (
            str(st.session_state.get("seed_ranking_mode", SEED_RANKING_MODE) or SEED_RANKING_MODE).strip().lower()
        )
        _include_franchise = st.checkbox(
            "Include sequels & spin-offs",
            value=_mode_current == "completion",
            help=(
                "Off: entries from the seed's own franchise are kept out of your results, "
                "so you see similar shows rather than more of the same one. "
                "On: sequels, movies and specials can rank freely."
            ),
        )
        st.session_state["seed_ranking_mode"] = "completion" if _include_franchise else "discovery"

    st.markdown("---")
    _render_reload_button(clear_cache_fn)
    _render_performance_fragment()


# ── Section 5: Help & FAQ ────────────────────────────────────────────────────


def _render_help_section() -> None:
    st.sidebar.markdown("---")
    with st.sidebar.expander("Quick Guide", expanded=False):
        st.markdown(
            """
    <div class='mars-quick-guide'>
    <b>1.</b> Choose what you want &mdash; Similar to a title / For me / Browse<br>
    <b>2.</b> Similar to a title &mdash; pick 1&ndash;5 titles or try the sample buttons<br>
    <b>3.</b> Browse &mdash; select genres to explore the catalog<br>
    <b>4.</b> For me &mdash; load a rated profile under Personalize<br>
    <b>5.</b> Refine with filters and sort; tune the ranking under Advanced
    </div>
    """,
            unsafe_allow_html=True,
        )


# ── Seed indicator ───────────────────────────────────────────────────────────


def _render_seed_indicator(result: SidebarResult) -> None:
    selected_seed_ids = result.selected_seed_ids
    selected_seed_titles = result.selected_seed_titles

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


# ── Performance metrics ──────────────────────────────────────────────────────


@st.fragment
def _render_performance_fragment() -> None:
    """Performance metrics fragment - reruns independently."""
    _section_label("Performance", container=st)
    from src.app.profiling import get_last_timing

    try:
        last_timing = get_last_timing()
        if last_timing:
            latency_ms = last_timing.get("recommendations", 0) * 1000
            tone = "success" if latency_ms < 250 else "warn" if latency_ms < 500 else "error"
            st.markdown(
                f"""
        <div class='mars-stat-tile'>
            <p class='mars-stat-tile-label'>Inference</p>
            <p class='mars-stat-tile-value mars-tone-{tone}'>{latency_ms:.0f}ms</p>
        </div>
        """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("Run a ranked mode to see timing data.")
    except Exception:
        st.caption("Run a ranked mode to see metrics.")

    # Show pipeline timing from main flow
    pipeline_ms = st.session_state.get("_pipeline_ms")
    if pipeline_ms is not None:
        st.caption(f"Last pipeline: {pipeline_ms:.0f}ms")
