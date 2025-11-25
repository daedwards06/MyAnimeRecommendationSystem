"""Design tokens for Streamlit app theming.

Provides centralized color palette, spacing scale, typography sizes, and elevation values.
Future extensions: dark mode alternative palette & semantic states mapping.
"""
from __future__ import annotations

COLORS = {
    "primary": "#3D5AFE",  # Indigo A200
    "accent": "#FF6D00",   # Orange for interactive highlights
    "bg": "#0F1116",
    "surface": "#1E2128",
    "surface_alt": "#272B33",
    "border": "#3A3F47",
    "text_primary": "#F5F7FA",
    "text_muted": "#A5AFB9",
    "success": "#2EBD85",
    "warn": "#F9A825",
    "error": "#EF5350",
    "info": "#29B6F6",
    "highlight": "#7C4DFF",
}

SPACING = {  # pixel values
    "xxs": 2,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

TYPE_SCALE = {  # CSS rem suggestions (Streamlit markdown will interpret sizes inline)
    "h1": "1.75rem",
    "h2": "1.40rem",
    "h3": "1.15rem",
    "body": "0.95rem",
    "small": "0.80rem",
}

ELEVATION = {  # simple shadow/elevation tokens (used in custom HTML blocks if added later)
    "card": "0 2px 4px rgba(0,0,0,0.25)",
    "overlay": "0 4px 12px rgba(0,0,0,0.35)",
}

DARK_MODE_ENABLED = False  # placeholder toggle; future: dynamic palette selection


def get_theme() -> dict:
    """Return current theme tokens (extendable for mode switching)."""
    return {
        "colors": COLORS,
        "spacing": SPACING,
        "type_scale": TYPE_SCALE,
        "elevation": ELEVATION,
        "mode": "dark" if DARK_MODE_ENABLED else "light",
    }

__all__ = ["get_theme", "COLORS", "SPACING", "TYPE_SCALE", "ELEVATION"]
