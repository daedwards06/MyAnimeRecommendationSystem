"""Open the deployed app in a headless browser and wait for the first recommendation card.

Keeps the Streamlit Community Cloud demo awake (`.github/workflows/keep-awake.yml`) and times
what a first-time visitor waits for. A plain HTTP request does not count as a visit: a sleeping
app still answers `curl` with 200, and only a browser session wakes it.

The first card is the "N recommendations" header plus a loaded poster image in the app's main
area. Both are searched in every frame, so the same detector works on the deployed app (which
renders inside an iframe) and on a local `streamlit run`.

Prints `time_to_first_card_s` and `was_asleep`; exits 1 and saves a screenshot on timeout.
When `GITHUB_STEP_SUMMARY` is set, the result is also appended to the job summary.

Requires Playwright, which is not in requirements.txt:
    pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Page, sync_playwright

DEFAULT_URL = "https://myanimerecommendationsystem-x6rqm6vqjmbr2ij8i8yk3b.streamlit.app/"
HEADER_RE = re.compile(r"^\s*\d+ recommendations\s*$")
WAKE_BUTTON_RE = re.compile(r"get this app back up", re.IGNORECASE)
POLL_S = 0.5


# Outside the sidebar rather than inside `stMain`: older Streamlit releases have no `stMain`
# test id, and requirements.txt only floors the version.
_FIRST_CARD_JS = """
(pattern) => {
  const re = new RegExp(pattern);
  const outsideSidebar = (e) => !e.closest('[data-testid=stSidebar]');
  const header = [...document.querySelectorAll('body *')].some(
    (e) => e.children.length === 0 && re.test(e.textContent) && outsideSidebar(e)
  );
  const poster = [...document.querySelectorAll('[data-testid=stImageContainer] img')].some(
    (e) => e.complete && e.naturalWidth > 0 && outsideSidebar(e)
  );
  return header && poster;
}
"""


def _frame_has_first_card(frame: Frame) -> bool:
    return bool(frame.evaluate(_FIRST_CARD_JS, HEADER_RE.pattern))


def _click_wake_button(page: Page) -> bool:
    for frame in page.frames:
        try:
            button = frame.get_by_role("button", name=WAKE_BUTTON_RE)
            if button.count() and button.first.is_visible():
                button.first.click()
                return True
        except PlaywrightError:
            continue
    return False


def check(url: str, timeout_s: float, screenshot: Path, channel: str | None) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        start = time.monotonic()
        page.goto(url, wait_until="domcontentloaded", timeout=int(timeout_s * 1000))

        was_asleep = False
        wake_clicked_at: float | None = None
        first_card_at: float | None = None
        while time.monotonic() - start < timeout_s:
            if not was_asleep and _click_wake_button(page):
                was_asleep = True
                wake_clicked_at = time.monotonic() - start
                print(f"sleep page found; wake button clicked at {wake_clicked_at:.1f} s", flush=True)
            found = False
            for frame in page.frames:
                try:
                    if _frame_has_first_card(frame):
                        found = True
                        break
                except PlaywrightError:
                    continue  # frame detached or navigating mid-check
            if found:
                first_card_at = time.monotonic() - start
                break
            time.sleep(POLL_S)

        if first_card_at is None:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot), full_page=True)
        browser.close()

    return {
        "url": url,
        "ok": first_card_at is not None,
        "time_to_first_card_s": first_card_at,
        "was_asleep": was_asleep,
        "wake_clicked_at_s": wake_clicked_at,
        "timeout_s": timeout_s,
        "screenshot": str(screenshot) if first_card_at is None else None,
    }


def _summary_markdown(result: dict) -> str:
    status = "first card shown" if result["ok"] else f"**no card within {result['timeout_s']:.0f} s**"
    ttfc = f"{result['time_to_first_card_s']:.1f} s" if result["ok"] else "—"
    lines = [
        "### Live demo check",
        "",
        "| Result | Time to first card | Was asleep |",
        "|:---|---:|:---:|",
        f"| {status} | {ttfc} | {'yes' if result['was_asleep'] else 'no'} |",
        "",
    ]
    if result["was_asleep"] and result["ok"]:
        lines.append(
            "The app was asleep: this time is a cold-start reading for "
            "docs/DEPLOYMENT.md § Performance."
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=300.0, help="seconds (default 300)")
    parser.add_argument("--screenshot", type=Path, default=Path("check_live_app_failure.png"))
    parser.add_argument(
        "--channel",
        default=None,
        help="browser channel, e.g. msedge to use the installed Edge instead of Playwright's Chromium",
    )
    args = parser.parse_args()

    result = check(args.url, args.timeout, args.screenshot, args.channel)

    ttfc = result["time_to_first_card_s"]
    print(f"time_to_first_card_s={ttfc:.1f}" if ttfc is not None else "time_to_first_card_s=none")
    print(f"was_asleep={str(result['was_asleep']).lower()}")
    if not result["ok"]:
        print(f"timed out after {args.timeout:.0f} s; screenshot saved to {result['screenshot']}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(_summary_markdown(result))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
