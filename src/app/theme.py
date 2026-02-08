"""Design tokens for Streamlit app theming.

Provides centralized color palette, spacing scale, typography sizes, and elevation values.
All components should import from here rather than hardcoding colors.
"""
from __future__ import annotations

COLORS = {
    # Brand
    "primary": "#6C63FF",        # Indigo / main accent
    "primary_light": "#A5A0FF",  # Lighter variant for hover/backgrounds
    "primary_bg": "#F0EFFF",     # Very light for tinted backgrounds
    "accent": "#FF6B6B",         # Coral for warm highlights
    "accent_alt": "#4ECDC4",     # Teal for secondary accent

    # Surfaces
    "bg": "#FAFBFC",
    "surface": "#FFFFFF",
    "surface_alt": "#F0F2F6",
    "surface_elevated": "#FFFFFF",
    "border": "#E2E8F0",
    "border_light": "#EDF2F7",

    # Text
    "text_primary": "#1A1A2E",
    "text_secondary": "#4A5568",
    "text_muted": "#A0AEC0",
    "text_inverse": "#FFFFFF",

    # Semantic
    "success": "#48BB78",
    "success_bg": "#F0FFF4",
    "warn": "#ECC94B",
    "warn_bg": "#FFFFF0",
    "error": "#FC8181",
    "error_bg": "#FFF5F5",
    "info": "#63B3ED",
    "info_bg": "#EBF8FF",

    # Data visualization
    "popular": "#FC8181",
    "midrange": "#63B3ED",
    "longtail": "#B794F4",
    "score_high": "#48BB78",
    "score_mid": "#6C63FF",
    "score_low": "#A0AEC0",
}

SPACING = {
    "xxs": 2,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
    "xxxl": 48,
}

TYPE_SCALE = {
    "h1": "2.00rem",
    "h2": "1.50rem",
    "h3": "1.20rem",
    "body": "1.00rem",
    "small": "0.875rem",
    "caption": "0.75rem",
}

ELEVATION = {
    "card": "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
    "card_hover": "0 10px 15px rgba(0,0,0,0.08), 0 4px 6px rgba(0,0,0,0.04)",
    "overlay": "0 20px 25px rgba(0,0,0,0.10), 0 10px 10px rgba(0,0,0,0.04)",
}


def get_theme() -> dict:
    """Return current theme tokens."""
    return {
        "colors": COLORS,
        "spacing": SPACING,
        "type_scale": TYPE_SCALE,
        "elevation": ELEVATION,
        "mode": "light",
    }

__all__ = ["get_theme", "COLORS", "SPACING", "TYPE_SCALE", "ELEVATION"]
