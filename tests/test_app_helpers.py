"""Unit tests for app helper utilities (search, badges, explanations)."""

from __future__ import annotations

from src.app.badges import badge_payload
from src.app.explanations import format_explanation
from src.app.search import fuzzy_search, normalize_title


def test_normalize_title():
    assert normalize_title("  Naruto ") == "naruto"


def test_format_explanation():
    s = format_explanation({"mf": 0.75, "knn": 0.2, "pop": 0.05})
    assert "CF" in s and "%" in s


def test_badge_payload():
    payload = badge_payload(True, 0.3, {"action": 5}, ["drama", "action"])
    assert set(payload.keys()) == {"cold_start", "popularity_band", "novelty_ratio"}
    assert payload["popularity_band"] in {"Top 10%", "Top 25%", "Mid", "Long Tail"}


def test_fuzzy_search_substring_fallback():
    # Query unlikely to match strongly; ensure substring fallback triggers.
    choices = [("Fullmetal Alchemist", 1), ("Naruto", 2), ("Bleach", 3)]
    res = fuzzy_search("metal", choices, limit=5)
    assert any("Fullmetal" in r[2] for r in res)
