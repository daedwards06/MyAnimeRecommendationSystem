"""Header title/subtitle, result title cards, and the one-line intro under the header."""

from __future__ import annotations

import re

import pytest

from app.display import header_html, header_text, title_card
from src.app.components.instructions import intro_line, intro_line_html

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


def test_header_html_is_a_plain_wordmark():
    html = header_html("Seed-based")
    assert ">MARS</h1>" in html
    assert "Find anime like the ones you love" in html
    assert "style=" not in html


def test_title_card_keeps_count_as_plain_text():
    html = title_card("Similar to Steins;Gate", "10 recommendations")
    assert ">Similar to Steins;Gate</h2>" in html
    # The live check matches a leaf element whose whole text is "N recommendations".
    assert re.search(r">10 recommendations</p>", html)
    assert "style=" not in html


def test_title_card_escapes_and_omits_empty_text():
    html = title_card("Tom & Jerry <3")
    assert "Tom &amp; Jerry &lt;3" in html
    assert "<p" not in html


def test_intro_line_html_matches_markdown_wording():
    html = intro_line_html("Seed-based", [FMAB], default_seed_title=FMAB)
    assert f"<strong class='mars-intro-highlight'>{FMAB}</strong>" in html
    assert re.sub(r"<[^>]+>", "", html) == intro_line(
        "Seed-based", [FMAB], default_seed_title=FMAB
    ).replace("**", "")
    assert "style=" not in html
