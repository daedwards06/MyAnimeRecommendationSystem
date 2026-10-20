"""Unit tests for app helper utilities (search, badges, explanations)."""

from __future__ import annotations

from src.app.badges import BAND_LABELS, badge_payload, band_counts, popularity_band
from src.app.components.tooltips import explain_popularity_band
from src.app.explanations import format_explanation
from src.app.search import fuzzy_search, normalize_title


def test_normalize_title():
    assert normalize_title("  Naruto ") == "naruto"


def test_format_explanation():
    s = format_explanation({"mf": 0.75, "knn": 0.2, "pop": 0.05})
    assert "Matrix factorization" in s and "Similar-item CF" in s and "%" in s


def test_badge_payload():
    payload = badge_payload(True, 0.3, {"action": 5}, ["drama", "action"])
    assert set(payload.keys()) == {"cold_start", "popularity_band", "novelty_ratio"}
    assert payload["popularity_band"] in {"Top 10%", "Top 25%", "Mid", "Long Tail"}


def test_band_counts_use_every_popularity_band():
    # Audit F1: Top 10% used to count as Mid and Long Tail never counted as a hidden gem.
    bands = [popularity_band(p) for p in (0.01, 0.05, 0.2, 0.3, 0.45, 0.6, 0.9)]
    assert band_counts(bands) == (3, 2, 2)


def test_every_popularity_band_has_a_name_and_specific_tooltip():
    for pct in (0.05, 0.2, 0.4, 0.8):
        band = popularity_band(pct)
        assert band in BAND_LABELS
        assert explain_popularity_band(band).startswith(f"**{BAND_LABELS[band]}")


def test_fuzzy_search_substring_fallback():
    # Query unlikely to match strongly; ensure substring fallback triggers.
    choices = [("Fullmetal Alchemist", 1), ("Naruto", 2), ("Bleach", 3)]
    res = fuzzy_search("metal", choices, limit=5)
    assert any("Fullmetal" in r[2] for r in res)
