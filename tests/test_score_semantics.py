from __future__ import annotations

from pathlib import Path

from src.app.score_semantics import SCORE_SEMANTIC_NAME, SCORE_LABEL_SHORT, format_match_score


def test_score_semantics_constants_are_unbounded() -> None:
    # Prevent regressions where we re-introduce rating-like or probability-like claims.
    assert "/10" not in SCORE_SEMANTIC_NAME
    assert "%" not in SCORE_SEMANTIC_NAME
    assert "relative" in SCORE_SEMANTIC_NAME.lower()
    assert SCORE_LABEL_SHORT == "Match score"


def test_format_match_score_is_unitless() -> None:
    assert format_match_score(None) == "—"
    assert format_match_score(1.23456) == "1.235"


def test_no_legacy_confidence_or_percent_match_strings_in_ui_files() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    cards_py = (repo_root / "src" / "app" / "components" / "cards.py").read_text(encoding="utf-8")
    assert "% Match" not in cards_py
    assert "Confidence" not in cards_py

    main_py = (repo_root / "app" / "main.py").read_text(encoding="utf-8")
    assert "Confidence" not in main_py
    assert "Match score" in main_py

    explanations_py = (
        repo_root / "src" / "app" / "components" / "explanations.py"
    ).read_text(encoding="utf-8")
    assert "/10" not in explanations_py
