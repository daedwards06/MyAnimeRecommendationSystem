from __future__ import annotations

from pathlib import Path

from src.app.score_semantics import (
    SCORE_LABEL_SHORT,
    SCORE_SEMANTIC_NAME,
    format_match_score,
    format_user_friendly_score,
    match_rank,
)
from src.app.theme_tokens import TIER_TOKENS, TOKENS


def test_score_semantics_constants_are_unbounded() -> None:
    # Prevent regressions where we re-introduce rating-like or probability-like claims.
    assert "/10" not in SCORE_SEMANTIC_NAME
    assert "%" not in SCORE_SEMANTIC_NAME
    assert "relative" in SCORE_SEMANTIC_NAME.lower()
    assert SCORE_LABEL_SHORT == "Match score"


def test_format_match_score_is_unitless() -> None:
    assert format_match_score(None) == "—"
    assert format_match_score(1.23456) == "1.235"


def test_format_user_friendly_score_tiers_at_boundaries() -> None:
    scores = [float(x) for x in range(8, 0, -1)]  # 8 items -> 2 per quartile
    expected = [
        "Top match", "Top match",
        "Strong match", "Strong match",
        "Good match", "Good match",
        "Worth a look", "Worth a look",
    ]
    assert [format_user_friendly_score(s, scores)[0] for s in scores] == expected


def test_format_user_friendly_score_uneven_run_length() -> None:
    scores = [float(x) for x in range(10, 0, -1)]
    labels = [format_user_friendly_score(s, scores)[0] for s in scores]
    assert labels[0] == "Top match"
    assert labels[2] == "Top match"
    assert labels[3] == "Strong match"
    assert labels[-1] == "Worth a look"


def test_format_user_friendly_score_tuple_contract() -> None:
    scores = [4.0, 3.0, 2.0, 1.0]
    results = [format_user_friendly_score(s, scores) for s in scores]
    assert all(isinstance(r, tuple) and len(r) == 3 and all(isinstance(x, str) for x in r) for r in results)
    assert [r[0] for r in results] == ["Top match", "Strong match", "Good match", "Worth a look"]
    assert [r[2] for r in results] == [TOKENS["color"][t] for t in TIER_TOKENS]


def test_format_user_friendly_score_has_no_percentage() -> None:
    scores = [1.0, 0.9, 0.8, 0.7, 0.6]
    for s in scores:
        display, _, _ = format_user_friendly_score(s, scores)
        assert "%" not in display


def test_format_user_friendly_score_tooltip_contains_rank_and_raw() -> None:
    scores = [1.0, 0.9, 0.8, 0.7, 0.6]
    _, tooltip, _ = format_user_friendly_score(0.8, scores)
    assert "Rank 3 of 5 in this run" in tooltip
    assert "0.800" in tooltip


def test_format_user_friendly_score_single_item() -> None:
    display, tooltip, color = format_user_friendly_score(0.75, [0.75])
    assert display == "Top match"
    assert "Rank 1 of 1" in tooltip
    assert color == TOKENS["color"]["tier_top"]


def test_format_user_friendly_score_empty_scores() -> None:
    display, tooltip, color = format_user_friendly_score(0.5, [])
    assert display == "—"
    assert color == TOKENS["color"]["tier_look"]


def test_match_rank_is_one_based_and_ties_share_rank() -> None:
    scores = [0.5, 0.9, 0.9, 0.1]
    assert match_rank(0.9, scores) == 1
    assert match_rank(0.5, scores) == 3
    assert match_rank(0.1, scores) == 4


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


def test_cards_use_tiered_match_label_with_rank() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cards_py = (repo_root / "src" / "app" / "components" / "cards.py").read_text(encoding="utf-8")

    assert "format_user_friendly_score" in cards_py
    assert "match_rank" in cards_py
    assert "% Match" not in cards_py
