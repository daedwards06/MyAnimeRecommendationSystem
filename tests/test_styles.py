"""One stylesheet entry point, and HTML helpers that emit classes, not inline styles (Task 2.1)."""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.styles as styles
from app.display import header_html, mix_bar_html, result_scope_html, title_card
from app.sidebar import section_label_html
from src.app.components.cards import flag_html, meta_span, score_badge_html
from src.app.components.instructions import intro_line_html
from src.app.components.taste_profile import stat_row_html

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
    "meta": meta_span("★ 8.50", "success", "score"),
    "flag": flag_html("Trained", "success"),
    "section_label": section_label_html("Find"),
    "stat_row": stat_row_html("Action", "8.2/10", "high"),
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
