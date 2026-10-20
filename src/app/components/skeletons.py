"""Card-shaped loading skeletons; the classes live in app/styles/components.css."""
from __future__ import annotations

_SKELETON_CARD = (
    "<div class='mars-skel-card'>"
    "<div class='mars-skel-poster'></div>"
    "<div class='mars-skel-lines'>"
    "<div class='mars-skel-line mars-skel-line-title'></div>"
    "<div class='mars-skel-line'></div>"
    "<div class='mars-skel-line mars-skel-line-short'></div>"
    "</div>"
    "</div>"
)


def card_skeleton_html(count: int = 3) -> str:
    """``count`` list-view card placeholders, hidden from screen readers."""
    if count <= 0:
        return ""
    return f"<div class='mars-skel-list' aria-hidden='true'>{_SKELETON_CARD * count}</div>"
