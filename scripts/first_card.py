"""First-card detector shared by `check_live_app.py` and `capture_ui_baseline.py`.

The first card is the "N recommendations" header plus a loaded poster image in the app's main
area. Both are searched in every frame, so the same detector works on the deployed app (which
renders inside an iframe) and on a local `streamlit run`.

Requires Playwright, which is not in requirements.txt:
    pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Page

HEADER_RE = re.compile(r"^\s*\d+ recommendations\s*$")
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


def frame_has_first_card(frame: Frame, header_re: re.Pattern[str] = HEADER_RE) -> bool:
    return bool(frame.evaluate(_FIRST_CARD_JS, header_re.pattern))


def page_has_first_card(page: Page, header_re: re.Pattern[str] = HEADER_RE) -> bool:
    for frame in page.frames:
        try:
            if frame_has_first_card(frame, header_re):
                return True
        except PlaywrightError:
            continue  # frame detached or navigating mid-check
    return False


def wait_for_first_card(
    page: Page,
    timeout_s: float,
    *,
    start: float | None = None,
    header_re: re.Pattern[str] = HEADER_RE,
    on_poll: Callable[[], None] | None = None,
) -> float | None:
    """Seconds from `start` (a `time.monotonic()` reading; default now) to the first card.

    Returns None if no card appears within `timeout_s` of `start`. `on_poll` runs before each
    check, e.g. to click a sleep page's wake button.
    """
    start = time.monotonic() if start is None else start
    while time.monotonic() - start < timeout_s:
        if on_poll is not None:
            on_poll()
        if page_has_first_card(page, header_re):
            return time.monotonic() - start
        time.sleep(POLL_S)
    return None
