"""Sidebar mode labels map onto the stable internal mode values."""

from __future__ import annotations

import pandas as pd

from app.sidebar import MODE_LABELS, MODE_OPTIONS, SAMPLE_SEEDS, SidebarResult, mode_label
from src.app.constants import METADATA_PARQUET


def test_internal_mode_values_unchanged():
    assert set(MODE_OPTIONS) == {"Seed-based", "Personalized", "Browse"}


def test_mode_options_order_matches_find_labels():
    assert [mode_label(m) for m in MODE_OPTIONS] == ["Similar to a title", "For me", "Browse"]


def test_label_mapping_is_one_to_one():
    assert set(MODE_LABELS) == set(MODE_OPTIONS)
    assert len(set(MODE_LABELS.values())) == len(MODE_LABELS)


def test_unknown_mode_label_passes_through():
    assert mode_label("Legacy") == "Legacy"


def test_sidebar_result_defaults_use_internal_mode():
    assert SidebarResult().ui_mode == "Seed-based"


def test_sample_seed_titles_exist_in_catalog():
    meta = pd.read_parquet(f"data/processed/{METADATA_PARQUET}", columns=["title_english", "title_display"])
    titles = set(meta["title_english"].dropna()) | set(meta["title_display"].dropna())
    assert list(SAMPLE_SEEDS) == ["Steins;Gate", "Your Name", "Cowboy Bebop"]
    for title in SAMPLE_SEEDS.values():
        assert title in titles


class _FakeSt:
    def __init__(self, view_mode: str) -> None:
        self.session_state = {"view_mode": view_mode}
        self.reruns: list[str] = []

    def rerun(self, *, scope: str = "app") -> None:
        self.reruns.append(scope)


def test_view_mode_change_reruns_the_whole_app(monkeypatch):
    # Audit F18: the radio is inside a fragment, so a fragment rerun never reached the cards.
    import app.sidebar as sidebar

    fake = _FakeSt("list")
    monkeypatch.setattr(sidebar, "st", fake)
    assert sidebar._apply_view_mode("Grid") == "grid"
    assert fake.session_state["view_mode"] == "grid"
    assert fake.reruns == ["app"]


def test_unchanged_view_mode_does_not_rerun(monkeypatch):
    import app.sidebar as sidebar

    fake = _FakeSt("grid")
    monkeypatch.setattr(sidebar, "st", fake)
    assert sidebar._apply_view_mode("Grid") == "grid"
    assert fake.reruns == []
