"""Design tokens: contrast floor, generated-file sync, tier colors (UI redesign Task 1.2)."""

from __future__ import annotations

import importlib.util
import re
import tomllib
from pathlib import Path

import pytest

from src.app.score_semantics import MATCH_TIERS
from src.app.theme_tokens import (
    LIVE,
    TEXT_PAIRS,
    TIER_TOKENS,
    TOKENS,
    contrast_ratio,
    render_tokens_css,
    streamlit_theme,
)

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
WCAG_AA = 4.5


def _load_build_theme():
    spec = importlib.util.spec_from_file_location("build_theme", ROOT / "scripts" / "build_theme.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contrast_ratio_reference_values() -> None:
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0)


@pytest.mark.parametrize(("fg", "bg"), TEXT_PAIRS)
def test_text_pairs_meet_wcag_aa(fg: str, bg: str) -> None:
    assert contrast_ratio(fg, bg) >= WCAG_AA, f"{fg} on {bg} is {contrast_ratio(fg, bg):.2f}:1"


def test_color_tokens_are_hex() -> None:
    colors = {**TOKENS["color"], **LIVE["color"], **LIVE["chart"]}
    colors.update({k: v for k, v in streamlit_theme().items() if k.endswith("Color")})
    bad = {k: v for k, v in colors.items() if not HEX.match(v)}
    assert not bad


def test_font_stacks_end_in_generic_family() -> None:
    for name, stack in TOKENS["font"].items():
        assert stack.rsplit(",", 1)[-1].strip() in {"sans-serif", "serif", "monospace"}, name


def test_every_tier_token_is_a_tested_text_pair() -> None:
    panel = TOKENS["color"]["panel"]
    for tier in TIER_TOKENS:
        assert (TOKENS["color"][tier], panel) in TEXT_PAIRS


def test_tokens_css_matches_tokens() -> None:
    generated = (ROOT / "app" / "styles" / "tokens.css").read_text(encoding="utf-8")
    assert generated == render_tokens_css(), "tokens.css edited by hand; run scripts/build_theme.py"


def test_config_toml_theme_matches_tokens() -> None:
    with (ROOT / ".streamlit" / "config.toml").open("rb") as f:
        config = tomllib.load(f)
    assert config["theme"] == streamlit_theme(), "config.toml [theme] edited by hand; run scripts/build_theme.py"
    assert {"server", "client", "browser"} <= config.keys()


def test_replace_section_keeps_other_sections() -> None:
    build_theme = _load_build_theme()
    text = '[server]\nheadless = true\n\n[theme]\nprimaryColor = "#000000"\n\n[client]\nx = 1\n'
    out = build_theme.replace_section(text, "theme", {"primaryColor": "#111111", "font": "serif"})
    assert tomllib.loads(out) == {
        "server": {"headless": True},
        "theme": {"primaryColor": "#111111", "font": "serif"},
        "client": {"x": 1},
    }
    assert build_theme.replace_section(out, "theme", {"primaryColor": "#111111", "font": "serif"}) == out


def test_badge_tier_colors_come_from_tokens() -> None:
    assert [color for _, color in MATCH_TIERS] == [TOKENS["color"][t] for t in TIER_TOKENS]
    assert "tier_colors" not in LIVE


def test_streamlit_theme_is_dark_and_from_tokens() -> None:
    c = TOKENS["color"]
    assert streamlit_theme() == {
        "base": "dark",
        "primaryColor": c["signal"],
        "backgroundColor": c["bg"],
        "secondaryBackgroundColor": c["panel"],
        "textColor": c["text"],
        "font": "sans serif",
    }
