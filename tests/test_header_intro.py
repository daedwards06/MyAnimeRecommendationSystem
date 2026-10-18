"""Header title/subtitle and the one-line intro under it (Task 1.1)."""

from __future__ import annotations

import pytest

from app.display import header_text
from src.app.components.instructions import intro_line

FMAB = "Fullmetal Alchemist: Brotherhood"


@pytest.mark.parametrize(
    ("ui_mode", "subtitle"),
    [
        ("Seed-based", "Find anime like the ones you love"),
        ("Personalized", "Ranked from your ratings"),
        ("Browse", "Browse the catalog"),
    ],
)
def test_header_text_per_mode(ui_mode, subtitle):
    assert header_text(ui_mode) == ("MARS", subtitle)


def test_header_text_unknown_mode_falls_back_to_seed_based():
    assert header_text("Nonsense") == header_text("Seed-based")


def test_intro_line_names_default_seed():
    line = intro_line("Seed-based", [FMAB], default_seed_title=FMAB)
    assert line == f"Showing picks for **{FMAB}** — pick your own titles in the sidebar"


def test_intro_line_drops_default_seed_once_seeds_change():
    for seeds in ([FMAB, "Steins;Gate"], ["Steins;Gate"], []):
        assert FMAB not in intro_line("Seed-based", seeds, default_seed_title=FMAB)
    assert FMAB not in intro_line("Seed-based", [FMAB], default_seed_title=None)


@pytest.mark.parametrize("ui_mode", ["Browse", "Personalized"])
def test_intro_line_ignores_default_seed_outside_seed_mode(ui_mode):
    line = intro_line(ui_mode, [FMAB], default_seed_title=FMAB)
    assert FMAB not in line
    assert "sidebar" in line
