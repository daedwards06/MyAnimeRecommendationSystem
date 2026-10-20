"""Loading, empty and error states (UI redesign Task 3.1)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.display as display
import app.state as state
from app.display import (
    ENGINE_UNAVAILABLE_DEV_HINT,
    ENGINE_UNAVAILABLE_TEXT,
    LOADING_EYECATCH,
    NO_FALLBACK_TEXT,
    active_filter_labels,
    empty_results_html,
    loading_html,
    personalized_gate_copy,
    personalized_gate_html,
)
from app.sidebar import SidebarResult
from app.state import filter_defaults, reset_filters

DEFAULT_YEARS = (1960, 2025)


@pytest.fixture
def session(monkeypatch):
    ss: dict = {}
    monkeypatch.setattr(state, "st", SimpleNamespace(session_state=ss))
    return ss


def test_loading_block_has_eyecatch_status_and_skeletons():
    block = loading_html("ranking the catalog", cards=3)
    assert LOADING_EYECATCH in block and "ranking the catalog" in block
    assert "role='status'" in block
    assert block.count("mars-skel-card") == 3
    assert "progress" not in block


def test_filter_labels_name_each_active_filter():
    labels = active_filter_labels(["Romance", "Drama"], ["Movie"], (2020, 2025))
    assert labels == ["Genre: Romance, Drama", "Type: Movie", "Years: 2020–2025"]


def test_filter_labels_skip_defaults_and_browse_genres():
    assert active_filter_labels([], [], DEFAULT_YEARS) == []
    assert active_filter_labels(["Action"], ["TV"], DEFAULT_YEARS, include_genres=False) == ["Type: TV"]


@pytest.mark.parametrize("kind", ["browse", "seed", "personalized"])
def test_empty_state_names_the_active_filters(kind):
    panel = empty_results_html(kind, ["Type: Music", "Years: 2024–2025"])
    assert "Type: Music" in panel and "Years: 2024–2025" in panel
    assert "removed everything" in panel


def test_empty_state_without_filters_suggests_something_else():
    panel = empty_results_html("seed", [])
    assert "removed everything" not in panel
    assert "different seed" in panel


def test_empty_state_escapes_filter_values():
    assert "<script>" not in empty_results_html("seed", ["Genre: <script>"])


def test_reset_restores_defaults(session):
    session.update(genre_filter=["Action"], type_filter=["Movie"], year_min=2020, year_max=2021, sort_by="Popularity")
    reset_filters("Match score")
    assert session == {**filter_defaults(), "sort_by": "Match score"}


def test_browse_reset_keeps_the_genres(session):
    session.update(genre_filter=["Action"], type_filter=["Movie"], year_min=2020, year_max=2021)
    reset_filters("MAL Score", keep_genres=True)
    assert session["genre_filter"] == ["Action"]
    assert session["type_filter"] == [] and (session["year_min"], session["year_max"]) == DEFAULT_YEARS


def test_reset_defaults_match_first_run_defaults(session, monkeypatch):
    monkeypatch.setattr(state, "qp_get", lambda _key, default: default)
    state.init_session_state()
    assert {k: session[k] for k in filter_defaults()} == filter_defaults()


def test_empty_state_button_clears_only_what_the_message_names(monkeypatch):
    calls: list = []
    fake_st = SimpleNamespace(
        markdown=lambda body, **_: calls.append(("markdown", body)),
        button=lambda label, **_: calls.append(("button", label)) or True,
        rerun=lambda: calls.append(("rerun",)),
    )
    monkeypatch.setattr(display, "st", fake_st)
    resets: list = []
    monkeypatch.setattr(display, "reset_filters", lambda sort, **kw: resets.append((sort, kw)))

    sidebar = SidebarResult(browse_mode=True, genre_filter=["Action"], type_filter=["Music"])
    sidebar.default_sort_for_mode = "MAL Score"
    display.render_empty_results(sidebar, "browse")

    panel = calls[0][1]
    assert "Type: Music" in panel and "Genre" not in panel
    assert ("button", "Clear filters") in calls and ("rerun",) in calls
    assert resets == [("MAL Score", {"keep_genres": True})]


def test_no_button_when_no_filter_is_active(monkeypatch):
    calls: list = []
    fake_st = SimpleNamespace(
        markdown=lambda body, **_: calls.append("markdown"),
        button=lambda *a, **k: calls.append("button"),
    )
    monkeypatch.setattr(display, "st", fake_st)
    display.render_empty_results(SidebarResult(selected_seed_ids=[1]), "seed")
    assert calls == ["markdown"]


@pytest.mark.parametrize(
    ("profile", "enabled", "expected"),
    [
        (None, False, "needs a profile"),
        ({"ratings": {}}, False, "no ratings"),
        ({"ratings": {"1": 8}}, False, "switched off"),
        ({"ratings": {"1": 8}}, True, "can't rank"),
    ],
)
def test_gate_copy_follows_the_gate_order(profile, enabled, expected):
    headline, fix = personalized_gate_copy(profile, enabled)
    assert expected in headline
    assert fix


def test_gate_message_keeps_the_no_fallback_line_and_hides_internals():
    panel = personalized_gate_html(None, False)
    assert NO_FALLBACK_TEXT in panel
    assert "role='alert'" in panel
    for jargon in ("Active Profile", "MF", "embedding", "Seed-based"):
        assert jargon not in panel


def test_engine_unavailable_text_is_for_visitors():
    assert "APP_IMPORT_LIGHT" not in ENGINE_UNAVAILABLE_TEXT
    assert "APP_IMPORT_LIGHT" in ENGINE_UNAVAILABLE_DEV_HINT
