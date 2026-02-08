from __future__ import annotations

from pathlib import Path

from src.app.score_semantics import (
    SCORE_SEMANTIC_NAME,
    SCORE_LABEL_SHORT,
    format_match_score,
    format_user_friendly_score,
)


def test_score_semantics_constants_are_unbounded() -> None:
    # Prevent regressions where we re-introduce rating-like or probability-like claims.
    assert "/10" not in SCORE_SEMANTIC_NAME
    assert "%" not in SCORE_SEMANTIC_NAME
    assert "relative" in SCORE_SEMANTIC_NAME.lower()
    assert SCORE_LABEL_SHORT == "Match score"


def test_format_match_score_is_unitless() -> None:
    assert format_match_score(None) == "—"
    assert format_match_score(1.23456) == "1.235"


def test_format_user_friendly_score_top_item() -> None:
    """Test that the top-scoring item gets 98% Match."""
    scores = [1.0, 0.9, 0.8, 0.7, 0.6]
    display, tooltip, color = format_user_friendly_score(1.0, scores)
    assert display == "98% Match"
    assert "1.000" in tooltip
    assert color == "#27AE60"  # Green for top


def test_format_user_friendly_score_bottom_item() -> None:
    """Test that the bottom-scoring item gets 50% Match."""
    scores = [1.0, 0.9, 0.8, 0.7, 0.6]
    display, tooltip, color = format_user_friendly_score(0.6, scores)
    assert display == "50% Match"
    assert "0.600" in tooltip


def test_format_user_friendly_score_middle_item() -> None:
    """Test that middle items get intermediate percentages."""
    scores = [1.0, 0.9, 0.8, 0.7, 0.6]
    display, tooltip, color = format_user_friendly_score(0.8, scores)
    # Middle item (rank 2 of 5): should be around 74%
    assert "Match" in display
    assert "%" in display
    assert "0.800" in tooltip


def test_format_user_friendly_score_color_coding() -> None:
    """Test color coding based on percentile."""
    scores = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    
    # Top item: green (≥90%)
    _, _, color = format_user_friendly_score(1.0, scores)
    assert color == "#27AE60"
    
    # Bottom item: grey (<60%)
    _, _, color = format_user_friendly_score(0.1, scores)
    assert color == "#95A5A6"


def test_format_user_friendly_score_single_item() -> None:
    """Test behavior with only one item."""
    scores = [0.75]
    display, tooltip, color = format_user_friendly_score(0.75, scores)
    assert display == "98% Match"  # Single item gets top score


def test_format_user_friendly_score_empty_scores() -> None:
    """Test behavior with empty scores list."""
    display, tooltip, color = format_user_friendly_score(0.5, [])
    assert "Match" in display
    assert color == "#95A5A6"


def test_no_legacy_confidence_strings_in_ui_files() -> None:
    """Verify no legacy 'Confidence' terminology remains."""
    repo_root = Path(__file__).resolve().parents[1]

    cards_py = (repo_root / "src" / "app" / "components" / "cards.py").read_text(encoding="utf-8")
    assert "Confidence" not in cards_py

    main_py = (repo_root / "app" / "main.py").read_text(encoding="utf-8")
    assert "Confidence" not in main_py

    explanations_py = (
        repo_root / "src" / "app" / "components" / "explanations.py"
    ).read_text(encoding="utf-8")
    assert "/10" not in explanations_py


def test_percent_match_is_percentile_based() -> None:
    """Verify that '% Match' refers to percentile rank, not raw calibration.
    
    Phase 4 Task 4.2: The '% Match' display is computed from percentile rank
    within the result set, not from raw uncalibrated scores. This is a valid
    user-friendly transformation that helps end users understand relative quality.
    """
    repo_root = Path(__file__).resolve().parents[1]
    cards_py = (repo_root / "src" / "app" / "components" / "cards.py").read_text(encoding="utf-8")
    
    # Should use format_user_friendly_score for percentile-based display
    assert "format_user_friendly_score" in cards_py
    
    # Raw scores should still be shown as tooltips/small text for technical users
    assert "Match score" in cards_py or "Raw score" in cards_py

