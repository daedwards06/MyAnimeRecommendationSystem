"""Regression tests for cold-start detection wiring.

These tests are intentionally lightweight (no artifact loading, no Streamlit runtime).
They verify that:
- The UI does not hard-code is_in_training=True.
- The Streamlit entrypoint computes membership using mf_model.item_to_index.
- Card render functions require an explicit is_in_training flag.
"""

from __future__ import annotations

import re
from pathlib import Path


def _read_repo_file(rel_path: str) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return (repo_root / rel_path).read_text(encoding="utf-8")


def test_no_hard_coded_is_in_training_true():
    main_py = _read_repo_file("app/main.py")
    cards_py = _read_repo_file("src/app/components/cards.py")

    assert "is_in_training=True" not in main_py
    assert "is_in_training=True" not in cards_py


def test_main_computes_training_membership_from_item_to_index():
    main_py = _read_repo_file("app/main.py")

    # We want the cold-start rule to be based on membership in item_to_index.
    assert "item_to_index" in main_py
    assert re.search(r"\bin\s+local_mf_model\.item_to_index\b", main_py) is not None


def test_cards_require_explicit_is_in_training_flag():
    cards_py = _read_repo_file("src/app/components/cards.py")

    # Ensure the new kw-only parameter exists in both renderers.
    # Allow for additional parameters after is_in_training (with comma)
    # Use DOTALL to handle multi-line function signatures
    assert re.search(r"def\s+render_card_grid\(.*\*,\s*is_in_training:\s*bool(?:,|\))", cards_py, re.DOTALL) is not None
    assert re.search(r"def\s+render_card\(.*\*,\s*is_in_training:\s*bool(?:,|\))", cards_py, re.DOTALL) is not None
