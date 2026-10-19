"""Capture the pre-redesign UI: full-page screenshots per mode and width, plus first-card timing.

Drives a running app (default a local `streamlit run app/main.py`) through Seed-based (the
default seed), Personalized (a demo profile) and Browse (one genre) at desktop and phone
widths, and writes `docs/redesign/baseline/{seed,personalized,browse}_{W}x{H}.png`.

Timing is local warm time to first card on a fresh browser context, using the detector shared
with `check_live_app.py`: one warm-up visit (discarded, it may pay the model load) and then
`--runs` timed visits, written to `timing.json` with median and range.

Requires Playwright, which is not in requirements.txt:
    pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import io
import json
import re
import statistics
import sys
import time
from datetime import date
from pathlib import Path

from first_card import HEADER_RE, wait_for_first_card
from PIL import Image
from playwright.sync_api import Browser, Page, sync_playwright

DEFAULT_URL = "http://localhost:8501"
OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "redesign" / "baseline"
VIEWPORTS = [(1440, 900), (390, 844)]
DEMO_PROFILE_LABEL = "Action Adventurer"
BROWSE_GENRE = "Action"
BROWSE_HEADER_RE = re.compile(r"^\s*\d+ titles\s*$")
MAX_PNG_BYTES = 1_000_000

# The main area scrolls inside this section, not the document, so a full-page screenshot has to
# grow the viewport to its scroll height first.
_MAIN_SCROLL_HEIGHT_JS = """
() => {
  const main = document.querySelector('[data-testid=stAppViewContainer] section.main')
    || document.querySelector('[data-testid=stAppViewContainer]');
  return main ? main.scrollHeight : document.body.scrollHeight;
}
"""
_IMAGES_LOADED_JS = "() => [...document.images].every((img) => img.complete)"


def _wait_idle(page: Page, timeout_s: float, quiet_s: float = 1.5) -> None:
    """Wait until Streamlit's running indicator has been absent for `quiet_s`."""
    status = page.locator("[data-testid=stStatusWidget]")
    deadline = time.monotonic() + timeout_s
    quiet_since: float | None = None
    while time.monotonic() < deadline:
        if status.count() and status.first.is_visible():
            quiet_since = None
        elif quiet_since is None:
            quiet_since = time.monotonic()
        elif time.monotonic() - quiet_since >= quiet_s:
            return
        time.sleep(0.25)
    raise TimeoutError(f"app still running after {timeout_s:.0f} s")


def _open_sidebar(page: Page) -> bool:
    control = page.locator("[data-testid=stSidebarCollapsedControl] button")
    if control.count() and control.first.is_visible():
        control.first.click()
        page.locator("[data-testid=stSidebar][aria-expanded=true]").wait_for()
        # The sidebar slides in; clicks inside it miss until it has settled on screen.
        page.wait_for_function(
            "() => document.querySelector('[data-testid=stSidebar]').getBoundingClientRect().left >= 0"
        )
        page.wait_for_timeout(500)
        return True
    return False


def _close_sidebar(page: Page) -> None:
    if page.locator("[data-testid=stSidebar][aria-expanded=true]").count():
        page.locator("[data-testid=stSidebarCollapseButton] button").first.click()
        page.locator("[data-testid=stSidebar][aria-expanded=false]").wait_for()


def _select_mode(page: Page, label: str) -> None:
    _open_sidebar(page)
    page.locator("[data-testid=stSidebar] [data-testid=stRadio]").get_by_text(label, exact=True).click()


def _drive_personalized(page: Page, timeout_s: float) -> None:
    _select_mode(page, "For me")
    _wait_idle(page, timeout_s)
    _open_sidebar(page)
    page.locator("[data-testid=stSidebar]").get_by_role("button", name=DEMO_PROFILE_LABEL).click()
    _wait_idle(page, timeout_s)
    page.get_by_text(re.compile(r"^Excluded \d+ already-watched titles$")).wait_for(timeout=timeout_s * 1000)


def _drive_browse(page: Page, timeout_s: float) -> None:
    _select_mode(page, "Browse")
    _wait_idle(page, timeout_s)
    _open_sidebar(page)
    genre = page.locator("[data-testid=stSidebar] [data-testid=stMultiSelect]").filter(has_text="Filter by Genre")
    # The combobox input can be zero-width at phone width; click its container and type.
    genre.locator("[data-baseweb=select]").click()
    page.keyboard.type(BROWSE_GENRE)
    page.get_by_role("option", name=BROWSE_GENRE, exact=True).click()
    page.keyboard.press("Escape")
    _wait_idle(page, timeout_s)


def _save_full_page(page: Page, path: Path, width: int, height: int, timeout_s: float) -> int:
    page.set_viewport_size({"width": width, "height": max(height, int(page.evaluate(_MAIN_SCROLL_HEIGHT_JS)))})
    page.wait_for_function(_IMAGES_LOADED_JS, timeout=timeout_s * 1000)
    _wait_idle(page, timeout_s, quiet_s=0.5)
    png = page.screenshot(full_page=True, animations="disabled")
    page.set_viewport_size({"width": width, "height": height})

    # Palette quantisation keeps tall, poster-heavy pages under the size cap.
    img = Image.open(io.BytesIO(png)).convert("RGB")
    for colors in (256, 128, 64):
        buf = io.BytesIO()
        img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).save(buf, format="PNG", optimize=True)
        if buf.tell() <= MAX_PNG_BYTES:
            break
    path.write_bytes(buf.getvalue())
    return buf.tell()


def capture_screenshots(browser: Browser, url: str, out_dir: Path, timeout_s: float) -> list[dict]:
    shots: list[dict] = []
    for width, height in VIEWPORTS:
        for mode, driver, header_re in (
            ("seed", None, HEADER_RE),
            ("personalized", _drive_personalized, HEADER_RE),
            ("browse", _drive_browse, BROWSE_HEADER_RE),
        ):
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            if wait_for_first_card(page, timeout_s) is None:
                raise TimeoutError(f"no first card on landing at {width}x{height}")
            if driver is not None:
                # At phone width the sidebar is collapsed on landing and re-collapses after
                # reruns; each step reopens it and it is closed again for the screenshot.
                phone = _open_sidebar(page)
                driver(page, timeout_s)
                if phone:
                    _close_sidebar(page)
            if wait_for_first_card(page, timeout_s, header_re=header_re) is None:
                raise TimeoutError(f"no first card in {mode} at {width}x{height}")
            path = out_dir / f"{mode}_{width}x{height}.png"
            size = _save_full_page(page, path, width, height, timeout_s)
            print(f"{path.name}: {size / 1000:.0f} kB", flush=True)
            shots.append({"file": path.name, "mode": mode, "viewport": [width, height], "bytes": size})
            context.close()
    return shots


def time_first_card(browser: Browser, url: str, runs: int, timeout_s: float) -> dict:
    readings: list[float] = []
    for i in range(runs + 1):
        context = browser.new_context(viewport={"width": VIEWPORTS[0][0], "height": VIEWPORTS[0][1]})
        page = context.new_page()
        start = time.monotonic()
        page.goto(url, wait_until="domcontentloaded")
        elapsed = wait_for_first_card(page, timeout_s, start=start)
        context.close()
        if elapsed is None:
            raise TimeoutError(f"no first card within {timeout_s:.0f} s on timing run {i}")
        label = "warm-up (discarded)" if i == 0 else f"run {i}"
        print(f"{label}: {elapsed:.1f} s", flush=True)
        if i == 0:
            warmup = elapsed
        else:
            readings.append(elapsed)
    return {
        "metric": "time_to_first_card_s",
        "load": "local warm",
        "viewport": list(VIEWPORTS[0]),
        "mode": "Seed-based (default seed)",
        "warmup_discarded_s": round(warmup, 2),
        "runs_s": [round(r, 2) for r in readings],
        "median_s": round(statistics.median(readings), 2),
        "range_s": [round(min(readings), 2), round(max(readings), 2)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--runs", type=int, default=3, help="timed runs after the warm-up (default 3)")
    parser.add_argument("--timeout", type=float, default=180.0, help="seconds per wait (default 180)")
    parser.add_argument("--channel", default=None, help="browser channel, e.g. msedge")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel, headless=True)
        timing = time_first_card(browser, args.url, args.runs, args.timeout)
        shots = capture_screenshots(browser, args.url, args.out, args.timeout)
        browser.close()

    timing.update({"url": args.url, "date": date.today().isoformat(), "screenshots": shots})
    (args.out / "timing.json").write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
    print(f"median {timing['median_s']:.1f} s, range {timing['range_s'][0]:.1f}–{timing['range_s'][1]:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
