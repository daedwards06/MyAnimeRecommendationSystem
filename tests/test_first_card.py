"""The first-card detector fires on header + main-area poster and times out without either."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright is not in requirements; detector test runs locally")
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("first_card", ROOT / "scripts" / "first_card.py")
assert spec is not None and spec.loader is not None
first_card = importlib.util.module_from_spec(spec)
sys.modules["first_card"] = first_card
spec.loader.exec_module(first_card)

# 1x1 opaque PNG, so the <img> loads with naturalWidth > 0 and no network.
PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
HEADER = "<span>12 recommendations</span>"
POSTER = f"<div data-testid='stImageContainer'><img src='{PIXEL}'></div>"


def _page(main: str, sidebar: str = "") -> str:
    return f"<html><body><section data-testid='stSidebar'>{sidebar}</section><main>{main}</main></body></html>"


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.skip(f"Chromium not installed for Playwright: {exc}")
        yield browser.new_page()
        browser.close()


def test_fires_with_header_and_poster(page):
    page.set_content(_page(HEADER + POSTER))
    elapsed = first_card.wait_for_first_card(page, timeout_s=5)
    assert elapsed is not None and elapsed < 5


@pytest.mark.parametrize(
    "main, sidebar",
    [
        (HEADER, ""),  # no poster
        (POSTER, ""),  # no header
        (HEADER, POSTER),  # poster only in the sidebar
        ("<span>12 titles</span>" + POSTER, ""),  # Browse header, default pattern
    ],
    ids=["no-poster", "no-header", "sidebar-poster", "titles-header"],
)
def test_times_out_without_first_card(page, main, sidebar):
    page.set_content(_page(main, sidebar))
    assert first_card.wait_for_first_card(page, timeout_s=1.2) is None


def test_custom_header_pattern(page):
    page.set_content(_page("<span>40 titles</span>" + POSTER))
    header_re = re.compile(r"^\s*\d+ (recommendations|titles)\s*$")
    assert first_card.wait_for_first_card(page, timeout_s=5, header_re=header_re) is not None
