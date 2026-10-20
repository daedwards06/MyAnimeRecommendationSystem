"""One stylesheet entry point, and HTML helpers that emit classes, not inline styles (Task 2.1)."""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.styles as styles
from app.display import (
    empty_results_html,
    header_html,
    loading_html,
    mix_bar_html,
    personalized_gate_html,
    result_scope_html,
    start_panel_html,
    title_card,
)
from app.sidebar import SAMPLE_SEEDS_LABEL_HTML, group_label_html, section_label_html
from src.app.components.cards import (
    CARD_MARKER_HTML,
    GRID_MARKER_HTML,
    explanation_html,
    flag_html,
    meta_span,
    poster_html,
    score_badge_html,
)
from src.app.components.instructions import intro_line_html
from src.app.components.taste_profile import stat_row_html
from src.app.theme_tokens import TOKENS, contrast_ratio

ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "app" / "styles"
CLASS_ATTR = re.compile(r"""class=['"]([^'"]+)['"]""")


@pytest.fixture
def emitted(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(styles.st, "markdown", lambda body, **_: calls.append(body))
    return calls


def _use_ctx(monkeypatch, ctx) -> None:
    monkeypatch.setattr(styles, "get_script_run_ctx", lambda **_: ctx)


def test_inject_styles_is_idempotent_within_a_run(monkeypatch, emitted):
    ctx = SimpleNamespace(cursors={})
    _use_ctx(monkeypatch, ctx)
    assert styles.inject_styles() is True
    assert styles.inject_styles() is False
    assert len(emitted) == 1


def test_inject_styles_emits_again_on_the_next_run(monkeypatch, emitted):
    ctx = SimpleNamespace(cursors={})
    _use_ctx(monkeypatch, ctx)
    styles.inject_styles()
    ctx.cursors = {}  # what ScriptRunContext.reset does at the start of a rerun
    assert styles.inject_styles() is True
    assert len(emitted) == 2


def test_inject_styles_without_a_run_context_always_emits(monkeypatch, emitted):
    _use_ctx(monkeypatch, None)
    styles.inject_styles()
    styles.inject_styles()
    assert len(emitted) == 2


def test_stylesheet_is_tokens_then_base_then_components(monkeypatch, emitted):
    _use_ctx(monkeypatch, None)
    styles.inject_styles()
    body = emitted[0]
    assert body.startswith("<style>") and body.rstrip().endswith("</style>")
    first_lines = [(STYLES / name).read_text(encoding="utf-8").splitlines()[0] for name in styles.STYLESHEETS]
    positions = [body.index(line) for line in first_lines]
    assert positions == sorted(positions)


def test_css_uses_tokens_and_stable_selectors():
    for name in ("base.css", "components.css"):
        css = (STYLES / name).read_text(encoding="utf-8")
        assert "st-emotion-cache" not in css, name
        assert not re.search(r"#[0-9A-Fa-f]{3,8}\b", css), f"{name} has a hex literal; use a token"


def test_no_inline_styles_outside_the_loader():
    sources = [*ROOT.glob("app/*.py"), *ROOT.glob("src/app/**/*.py")]
    offenders = [
        f"{path.relative_to(ROOT)}:{n}"
        for path in sources
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"<style|style=", line)
    ]
    assert offenders == []
    assert "<style" in (STYLES / "__init__.py").read_text(encoding="utf-8")


SCORES = [0.9, 0.7, 0.5, 0.3]

HELPER_HTML = {
    "header": header_html("Seed-based"),
    "title_card": title_card("Similar to Steins;Gate", "10 recommendations"),
    "result_scope": result_scope_html(13062, "  ·  filtered by 1 genre"),
    "intro_line": intro_line_html("Seed-based", ["Steins;Gate"], default_seed_title="Steins;Gate"),
    "mix_bar": mix_bar_html("Recommendation mix", 3, 5, 2),
    "mix_bar_empty": mix_bar_html("Catalog mix", 0, 0, 0),
    "badge_tiered": score_badge_html(0.9, SCORES),
    "badge_compact": score_badge_html(0.3, SCORES, compact=True),
    "badge_untiered": score_badge_html(0.42, None),
    "card_marker": CARD_MARKER_HTML,
    "grid_marker": GRID_MARKER_HTML,
    "poster": poster_html("https://example.com/p.jpg", "Steins;Gate"),
    "explanation": explanation_html("You rate Drama highly"),
    "explanation_compact": explanation_html("You rate Drama highly", compact=True),
    "meta": meta_span("★ 8.50", "success", "score"),
    "flag": flag_html("Trained", "success"),
    "section_label": section_label_html("Profile"),
    "group_label": group_label_html("Find"),
    "try_label": SAMPLE_SEEDS_LABEL_HTML,
    "stat_row": stat_row_html("Action", "8.2/10", "high"),
    "loading": loading_html("ranking the catalog"),
    "empty_filtered": empty_results_html("seed", ["Type: Movie"]),
    "empty_unfiltered": empty_results_html("personalized", []),
    "gate": personalized_gate_html(None, False),
    "start_panel": start_panel_html("Pick a genre to start", "Choose a genre."),
}


@pytest.mark.parametrize("name", HELPER_HTML)
def test_helpers_emit_defined_classes_not_inline_styles(name):
    html = HELPER_HTML[name]
    assert "style=" not in html
    classes = {c for attr in CLASS_ATTR.findall(html) for c in attr.split()}
    assert classes, f"{name} emits no classes"
    css = (STYLES / "components.css").read_text(encoding="utf-8")
    undefined = {c for c in classes if not re.search(rf"\.{re.escape(c)}\b", css)}
    assert not undefined, f"{name}: classes missing from components.css: {undefined}"


def test_score_badge_tier_classes():
    assert "mars-tier-top" in score_badge_html(0.9, SCORES)
    assert "mars-tier-look" in score_badge_html(0.3, SCORES)
    assert "mars-tier-none" in score_badge_html(0.42, None)
    assert score_badge_html(None, SCORES) == ""


def test_mix_bar_segments_fill_the_track():
    widths = re.findall(r'width="([\d.]+)%"', mix_bar_html("Recommendation mix", 3, 5, 2))
    assert sum(float(w) for w in widths[1:]) == pytest.approx(100.0)  # [0] is the <svg>
    assert "Popular 3" in mix_bar_html("Recommendation mix", 3, 5, 2)
    assert "mars-mix-empty" in mix_bar_html("Catalog mix", 0, 0, 0)


def test_font_import_is_hoisted_to_the_top_of_the_stylesheet() -> None:
    sheet = styles.stylesheet()
    first_rule = next(line for line in sheet.splitlines() if line.strip())
    assert first_rule.startswith("@import url('https://fonts.googleapis.com/css2?")
    assert "display=swap" in first_rule
    assert "Shippori+Mincho+B1:wght@800" in first_rule
    assert "M+PLUS+Rounded+1c:wght@400;700" in first_rule
    assert sheet.count("@import") == 1


def test_headings_body_and_code_use_the_font_tokens() -> None:
    base = (STYLES / "base.css").read_text(encoding="utf-8")
    for token in ("--mars-font-body", "--mars-font-display", "--mars-font-mono"):
        assert f"font-family: var({token});" in base
    assert re.search(r"\.stApp code,[^{]*\{\s*font-family: var\(--mars-font-mono\);", base)


def test_sidebar_groups_render_in_order_through_one_helper() -> None:
    source = (ROOT / "app" / "sidebar.py").read_text(encoding="utf-8")
    assert sorted(re.findall(r'_group_label\("([^"]+)"', source)) == ["Advanced", "Find", "Personalize", "Refine"]
    # Refine's label is drawn inside the filters fragment, so render order is checked by call site.
    body = source[source.index("def render_sidebar(") : source.index("def _section_label(")]
    calls = ['_group_label("Find")', "_render_filters_display_section(", '_group_label("Personalize")', '_group_label("Advanced")']
    positions = [body.index(call) for call in calls]
    assert positions == sorted(positions)


def test_sample_seed_tags_are_scoped_to_the_try_row() -> None:
    css = (STYLES / "components.css").read_text(encoding="utf-8")
    assert '[data-testid="stHorizontalBlock"]:has(.mars-try-label) button[kind="secondary"]' in css


def test_focus_ring_uses_the_focus_token_across_the_app() -> None:
    base = (STYLES / "base.css").read_text(encoding="utf-8")
    assert re.search(
        r'\.stApp button:focus-visible,[^{]*\{\s*outline: 2px solid var\(--mars-color-focus\)',
        base,
    )
    colors = TOKENS["color"]
    assert contrast_ratio(colors["focus"], colors["panel"]) >= 3.0
    assert contrast_ratio(colors["focus"], colors["bg"]) >= 3.0


def test_reduced_motion_disables_all_animation_and_transitions() -> None:
    sheet = styles.stylesheet()
    block = re.search(r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", sheet, re.S)
    assert block, "no prefers-reduced-motion: reduce block"
    assert ".stApp *::before" in block.group(1)
    assert "animation: none !important;" in block.group(1)
    assert "transition: none !important;" in block.group(1)


GRID_BLOCK = '[data-testid="stVerticalBlock"]:has(> [data-testid="element-container"] .mars-grid-marker)'


def test_grid_view_steps_down_4_3_2_1_columns_by_viewport_width() -> None:
    css = (STYLES / "components.css").read_text(encoding="utf-8")
    steps = re.findall(
        r"(?:@media \(max-width: (\d+)px\) \{\s*)?\.stApp " + re.escape(GRID_BLOCK)
        + r" \{\s*(?:display: grid;\s*)?grid-template-columns: (repeat\((\d)|minmax)",
        css,
    )
    columns = [(int(w) if w else None, int(n) if n else 1) for w, _, n in steps]
    assert columns == [(None, 4), (1279, 3), (999, 2), (639, 1)]


def test_phone_and_touch_buttons_are_at_least_44px() -> None:
    css = (STYLES / "components.css").read_text(encoding="utf-8")
    block = re.search(r"@media \(max-width: 640px\), \(pointer: coarse\) \{(.*?)\n\}", css, re.S)
    assert block, "no phone/touch block"
    assert ".stApp .stButton button," in block.group(1)
    assert ".mars-try-label) button" in block.group(1)
    assert ".mars-genre-row) + [data-testid=\"stHorizontalBlock\"] button" in block.group(1)
    assert "min-height: 44px !important;" in block.group(1)


def test_genre_pill_style_is_scoped_to_genre_rows() -> None:
    # Audit F6: the pill rule used to hit every secondary button in the app.
    base = (STYLES / "base.css").read_text(encoding="utf-8")
    assert not re.search(r"^button\[kind=\"secondary\"\]", base, re.MULTILINE)
    pill = '[data-testid="element-container"]:has(.mars-genre-row) + [data-testid="stHorizontalBlock"] button[kind="secondary"] {'
    assert pill in base
    assert "height: 30px" in base[base.index(pill) :].split("}")[0]
