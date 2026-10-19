"""Design tokens for the 90s anime redesign: the single source for colors, fonts, and shape.

``.streamlit/config.toml`` ``[theme]`` and ``app/styles/tokens.css`` are generated from this
module by ``scripts/build_theme.py``; ``tests/test_theme_tokens.py`` fails if either is edited
by hand or if a text pair drops below WCAG AA (4.5:1).
"""

from __future__ import annotations

TOKENS: dict[str, dict[str, str]] = {
    "color": {
        "bg": "#110D14",  # plum black
        "panel": "#1E1823",
        "ink": "#050307",  # outlines, and the subtitle text outline
        "text": "#F4ECE2",  # warm off-white
        "text_muted": "#B0A6B8",
        "signal": "#FF4A4A",  # signal red: primary action
        "on_signal": "#110D14",  # white on signal is 3.3:1, fails
        "subtitle": "#FFD84A",  # fansub yellow: explanation line, highlights
        "cyan": "#4FD3E6",  # links and secondary accent
        "focus": "#FFD84A",
        "tier_top": "#4FD3E6",
        "tier_strong": "#FFD84A",
        "tier_good": "#FF8F5A",
        "tier_look": "#A9A0B4",
    },
    "font": {
        "display": (
            "'Shippori Mincho B1', 'Hiragino Mincho ProN', 'Yu Mincho', 'Times New Roman', serif"
        ),
        "body": (
            "'M PLUS Rounded 1c', 'Hiragino Maru Gothic ProN', Meiryo, 'Segoe UI', "
            "system-ui, sans-serif"
        ),
        "mono": "ui-monospace, 'Cascadia Code', Consolas, 'Courier New', monospace",
    },
    "radius": {
        "sm": "4px",
        "md": "8px",
        "pill": "999px",
    },
    "border": {
        "thin": "1px",
    },
    "space": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
    },
}

TIER_TOKENS: tuple[str, ...] = ("tier_top", "tier_strong", "tier_good", "tier_look")

_C = TOKENS["color"]

TEXT_PAIRS: list[tuple[str, str]] = [
    (_C["text"], _C["bg"]),
    (_C["text"], _C["panel"]),
    (_C["text_muted"], _C["bg"]),
    (_C["text_muted"], _C["panel"]),
    (_C["signal"], _C["bg"]),
    (_C["signal"], _C["panel"]),
    (_C["subtitle"], _C["bg"]),
    (_C["subtitle"], _C["panel"]),
    (_C["cyan"], _C["bg"]),
    (_C["cyan"], _C["panel"]),
    (_C["on_signal"], _C["signal"]),
    *((_C[t], _C["panel"]) for t in TIER_TOKENS),
    *((_C[t], _C["bg"]) for t in TIER_TOKENS),
]

# What the deployed app still renders until Phase 2 switches it to TOKENS: the Streamlit theme
# in Task 2.2, the tier badge colors in Task 2.4. Kept here so the generated config.toml and the
# badges already read from this module; not in TEXT_PAIRS because they fail 4.5:1 (audit F3).
LIVE: dict[str, dict[str, str]] = {
    "streamlit_theme": {
        "primaryColor": "#6C63FF",
        "backgroundColor": "#FAFBFC",
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#1A1A2E",
        "font": "sans serif",
    },
    "tier_colors": {
        "tier_top": "#27AE60",
        "tier_strong": "#3498DB",
        "tier_good": "#E67E22",
        "tier_look": "#95A5A6",
    },
    # The light palette app/styles/*.css paints with (as --mars-live-*) until Task 2.2.
    "color": {
        "text_primary": "#1A1A2E",
        "text_secondary": "#4A5568",
        "text_dark": "#2D3748",
        "text_muted": "#A0AEC0",
        "text_inverse": "#FFFFFF",
        "primary": "#6C63FF",
        "primary_dark": "#5A52D5",
        "primary_bg": "#F0EFFF",
        "primary_border": "#D6D3FF",
        "accent_alt": "#4ECDC4",
        "bg": "#FAFBFC",
        "bg_alt": "#F7FAFC",
        "surface_alt": "#F0F2F6",
        "border": "#E2E8F0",
        "border_light": "#EDF2F7",
        "success": "#48BB78",
        "warn": "#ECC94B",
        "error": "#FC8181",
        "info": "#63B3ED",
        "purple": "#B794F4",
        "popular": "#FC8181",
        "midrange": "#63B3ED",
        "longtail": "#B794F4",
        "notice_bg_from": "#FFF3CD",
        "notice_bg_to": "#FCF8E3",
        "notice_border": "#F0AD4E",
        "notice_text": "#8A6D3B",
        "mmr_lambda": "#B0B0B0",
        "mmr_note": "#888888",
        "skeleton": "#2A2F36",
    },
    # Taste-profile charts and their legend rows.
    "chart": {
        "high": "#27AE60",
        "mid": "#3498DB",
        "ok": "#F39C12",
        "low": "#95A5A6",
        "bad": "#E74C3C",
    },
    "shadow": {
        "card": "0 1px 3px rgba(0,0,0,0.06)",
        "card_hover": "0 8px 24px rgba(0,0,0,0.08)",
        "button_hover": "0 4px 12px rgba(108, 99, 255, 0.18)",
        "pill_hover": "0 3px 10px rgba(108, 99, 255, 0.25)",
    },
}

# Badge backgrounds: the badge color at alpha 0x15.
_TINT_ALPHA = "15"


def css_var(group: str, key: str) -> str:
    return f"--mars-{group}-{key.replace('_', '-')}"


def _live_css_values() -> dict[str, str]:
    values = {**LIVE["color"], **LIVE["tier_colors"]}
    tinted = {**LIVE["tier_colors"], "primary": LIVE["color"]["primary"]}
    values.update({f"{k}_tint": v + _TINT_ALPHA for k, v in tinted.items()})
    values.update({f"chart_{k}": v for k, v in LIVE["chart"].items()})
    values.update({f"shadow_{k}": v for k, v in LIVE["shadow"].items()})
    return values


def render_tokens_css() -> str:
    lines = [
        "/* Generated by scripts/build_theme.py from src/app/theme_tokens.py. Do not edit. */",
        ":root {",
    ]
    for group, values in TOKENS.items():
        for key, value in values.items():
            lines.append(f"  {css_var(group, key)}: {value};")
    for key, value in _live_css_values().items():
        lines.append(f"  {css_var('live', key)}: {value};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def streamlit_theme() -> dict[str, str]:
    return dict(LIVE["streamlit_theme"])


def _relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(fg: str, bg: str) -> float:
    hi, lo = sorted((_relative_luminance(fg), _relative_luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


__all__ = [
    "LIVE",
    "TEXT_PAIRS",
    "TIER_TOKENS",
    "TOKENS",
    "contrast_ratio",
    "css_var",
    "render_tokens_css",
    "streamlit_theme",
]
