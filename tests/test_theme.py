"""Tests for the theme design token system."""

from __future__ import annotations

import pytest

from src.app.theme import COLORS, ELEVATION, SPACING, TYPE_SCALE, get_theme


def test_get_theme_returns_all_groups():
    """Verify get_theme() returns all expected token groups."""
    theme = get_theme()

    expected_keys = {"colors", "spacing", "type_scale", "elevation", "mode"}
    assert expected_keys.issubset(theme.keys()), f"Missing keys: {expected_keys - theme.keys()}"


def test_colors_has_all_categories():
    """Verify COLORS dict contains all expected categories."""
    theme = get_theme()
    colors = theme["colors"]

    # Brand colors
    assert "primary" in colors
    assert "primary_dark" in colors
    assert "primary_light" in colors
    assert "primary_bg" in colors
    assert "primary_border" in colors
    assert "accent" in colors
    assert "accent_alt" in colors

    # Surface colors
    assert "bg" in colors
    assert "bg_alt" in colors
    assert "surface" in colors
    assert "surface_alt" in colors
    assert "surface_elevated" in colors
    assert "border" in colors
    assert "border_light" in colors

    # Text colors
    assert "text_primary" in colors
    assert "text_secondary" in colors
    assert "text_dark" in colors
    assert "text_muted" in colors
    assert "text_inverse" in colors

    # Semantic colors
    assert "success" in colors
    assert "warn" in colors
    assert "error" in colors
    assert "info" in colors

    # Data visualization colors
    assert "popular" in colors
    assert "midrange" in colors
    assert "longtail" in colors


def test_colors_are_valid_hex():
    """Verify all color values are valid hex color codes."""
    theme = get_theme()
    colors = theme["colors"]

    for key, value in colors.items():
        assert isinstance(value, str), f"Color {key} is not a string: {value}"
        assert value.startswith("#"), f"Color {key} does not start with #: {value}"
        assert len(value) in (4, 7), f"Color {key} has invalid length: {value}"
        # Verify hex characters (case-insensitive)
        hex_chars = value[1:]
        assert all(c in "0123456789ABCDEFabcdef" for c in hex_chars), \
            f"Color {key} has invalid hex characters: {value}"


def test_spacing_values_are_ints():
    """Verify all spacing values are positive integers."""
    theme = get_theme()
    spacing = theme["spacing"]

    assert len(spacing) > 0, "Spacing dict is empty"
    for key, value in spacing.items():
        assert isinstance(value, int), f"Spacing {key} is not an int: {value}"
        assert value > 0, f"Spacing {key} is not positive: {value}"


def test_spacing_scale_is_ordered():
    """Verify spacing values form an ascending scale."""
    theme = get_theme()
    spacing = theme["spacing"]

    expected_order = ["xxs", "xs", "sm", "md", "lg", "xl", "xxl", "xxxl"]
    values = [spacing[key] for key in expected_order if key in spacing]

    # Check that values are in ascending order
    assert values == sorted(values), f"Spacing scale is not ordered: {values}"


def test_type_scale_values_are_strings():
    """Verify all typography scale values are valid CSS rem values."""
    theme = get_theme()
    type_scale = theme["type_scale"]

    assert len(type_scale) > 0, "Type scale dict is empty"
    for key, value in type_scale.items():
        assert isinstance(value, str), f"Type scale {key} is not a string: {value}"
        assert value.endswith("rem"), f"Type scale {key} does not end with 'rem': {value}"
        # Verify the numeric part is valid
        numeric_part = value[:-3]
        try:
            float(numeric_part)
        except ValueError:
            pytest.fail(f"Type scale {key} has invalid numeric part: {value}")


def test_elevation_values_are_strings():
    """Verify all elevation values are valid CSS box-shadow strings."""
    theme = get_theme()
    elevation = theme["elevation"]

    assert len(elevation) > 0, "Elevation dict is empty"
    for key, value in elevation.items():
        assert isinstance(value, str), f"Elevation {key} is not a string: {value}"
        assert len(value) > 0, f"Elevation {key} is empty"
        # Check that it contains box-shadow-like content
        assert any(keyword in value.lower() for keyword in ["px", "rgba", "rgb"]), \
            f"Elevation {key} does not look like a box-shadow: {value}"


def test_theme_mode_is_light():
    """Verify theme mode is set to light."""
    theme = get_theme()
    assert theme["mode"] == "light"


def test_colors_constant_matches_theme():
    """Verify COLORS constant matches what get_theme() returns."""
    theme = get_theme()
    assert theme["colors"] == COLORS


def test_spacing_constant_matches_theme():
    """Verify SPACING constant matches what get_theme() returns."""
    theme = get_theme()
    assert theme["spacing"] == SPACING


def test_type_scale_constant_matches_theme():
    """Verify TYPE_SCALE constant matches what get_theme() returns."""
    theme = get_theme()
    assert theme["type_scale"] == TYPE_SCALE


def test_elevation_constant_matches_theme():
    """Verify ELEVATION constant matches what get_theme() returns."""
    theme = get_theme()
    assert theme["elevation"] == ELEVATION


def test_primary_colors_are_distinct():
    """Verify primary brand colors are distinct from each other."""
    theme = get_theme()
    colors = theme["colors"]

    primary_variants = [
        colors["primary"],
        colors["primary_dark"],
        colors["primary_light"],
        colors["primary_bg"],
        colors["primary_border"],
    ]

    # All should be unique
    assert len(primary_variants) == len(set(primary_variants)), \
        "Primary color variants are not distinct"


def test_data_viz_colors_are_distinct():
    """Verify data visualization colors are distinct for clarity."""
    theme = get_theme()
    colors = theme["colors"]

    viz_colors = [
        colors["popular"],
        colors["midrange"],
        colors["longtail"],
    ]

    # All should be unique
    assert len(viz_colors) == len(set(viz_colors)), \
        "Data visualization colors are not distinct"
