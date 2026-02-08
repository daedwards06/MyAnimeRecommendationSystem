"""Tests for src/utils/parsing.py parsing utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.utils.parsing import coerce_genres, parse_pipe_set


# ============================================================================
# Tests for parse_pipe_set
# ============================================================================

def test_parse_pipe_set_none():
    """parse_pipe_set(None) should return empty set."""
    result = parse_pipe_set(None)
    assert result == set()


def test_parse_pipe_set_empty_string():
    """parse_pipe_set('') should return empty set."""
    result = parse_pipe_set("")
    assert result == set()


def test_parse_pipe_set_whitespace_only():
    """parse_pipe_set with only whitespace should return empty set."""
    result = parse_pipe_set("   ")
    assert result == set()


def test_parse_pipe_set_single():
    """parse_pipe_set('Action') should return {'Action'}."""
    result = parse_pipe_set("Action")
    assert result == {"Action"}


def test_parse_pipe_set_multiple():
    """parse_pipe_set('Action|Drama|Comedy') should return {'Action', 'Drama', 'Comedy'}."""
    result = parse_pipe_set("Action|Drama|Comedy")
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_with_spaces():
    """parse_pipe_set should strip whitespace from tokens."""
    result = parse_pipe_set(" Action | Drama | Comedy ")
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_with_empty_tokens():
    """parse_pipe_set should filter out empty tokens between pipes."""
    result = parse_pipe_set("Action||Drama|  |Comedy")
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_list_input():
    """parse_pipe_set should handle list input."""
    result = parse_pipe_set(["Action", "Drama", "Comedy"])
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_tuple_input():
    """parse_pipe_set should handle tuple input."""
    result = parse_pipe_set(("Action", "Drama", "Comedy"))
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_set_input():
    """parse_pipe_set should handle set input (idempotent)."""
    result = parse_pipe_set({"Action", "Drama", "Comedy"})
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_list_with_none():
    """parse_pipe_set should filter out None from lists."""
    result = parse_pipe_set(["Action", None, "Drama"])
    assert result == {"Action", "Drama"}


def test_parse_pipe_set_list_with_empty():
    """parse_pipe_set should filter out empty strings from lists."""
    result = parse_pipe_set(["Action", "", "Drama"])
    assert result == {"Action", "Drama"}


def test_parse_pipe_set_numpy_array():
    """parse_pipe_set should handle numpy arrays."""
    arr = np.array(["Action", "Drama", "Comedy"])
    result = parse_pipe_set(arr)
    assert result == {"Action", "Drama", "Comedy"}


def test_parse_pipe_set_pandas_na():
    """parse_pipe_set should return empty set for pandas NA."""
    result = parse_pipe_set(pd.NA)
    assert result == set()


def test_parse_pipe_set_mixed_types_in_list():
    """parse_pipe_set should convert non-string items to strings."""
    result = parse_pipe_set([1, 2.5, "Action", True])
    assert result == {"1", "2.5", "Action", "True"}


def test_parse_pipe_set_number():
    """parse_pipe_set should convert numbers to strings."""
    result = parse_pipe_set(42)
    assert result == {"42"}


def test_parse_pipe_set_float():
    """parse_pipe_set should convert floats to strings."""
    result = parse_pipe_set(3.14)
    assert result == {"3.14"}


# ============================================================================
# Tests for coerce_genres
# ============================================================================

def test_coerce_genres_none():
    """coerce_genres(None) should return empty string."""
    result = coerce_genres(None)
    assert result == ""


def test_coerce_genres_string():
    """coerce_genres should pass through strings unchanged."""
    result = coerce_genres("Action|Drama")
    assert result == "Action|Drama"


def test_coerce_genres_empty_string():
    """coerce_genres('') should return empty string."""
    result = coerce_genres("")
    assert result == ""


def test_coerce_genres_list():
    """coerce_genres should convert list to pipe-delimited string."""
    result = coerce_genres(["Action", "Drama", "Comedy"])
    assert result == "Action|Drama|Comedy"


def test_coerce_genres_tuple():
    """coerce_genres should convert tuple to pipe-delimited string."""
    result = coerce_genres(("Action", "Drama", "Comedy"))
    assert result == "Action|Drama|Comedy"


def test_coerce_genres_set():
    """coerce_genres should convert set to pipe-delimited string."""
    result = coerce_genres({"Action", "Drama"})
    # Sets don't guarantee order, so check both tokens are present
    tokens = result.split("|")
    assert set(tokens) == {"Action", "Drama"}


def test_coerce_genres_numpy_array():
    """coerce_genres should handle numpy arrays."""
    arr = np.array(["Action", "Drama", "Comedy"])
    result = coerce_genres(arr)
    assert result == "Action|Drama|Comedy"


def test_coerce_genres_numpy_2d_array():
    """coerce_genres should flatten 2D numpy arrays."""
    arr = np.array([["Action", "Drama"], ["Comedy", "Horror"]])
    result = coerce_genres(arr)
    tokens = result.split("|")
    assert set(tokens) == {"Action", "Drama", "Comedy", "Horror"}


def test_coerce_genres_nested_list():
    """coerce_genres should recursively flatten nested lists."""
    result = coerce_genres([["Action", "Drama"], ["Comedy"]])
    assert result == "Action|Drama|Comedy"


def test_coerce_genres_mixed_nested():
    """coerce_genres should handle mixed nested structures."""
    result = coerce_genres([["Action", "Drama"], "Comedy", ["Horror"]])
    assert result == "Action|Drama|Comedy|Horror"


def test_coerce_genres_with_none_in_list():
    """coerce_genres should filter out None values."""
    result = coerce_genres(["Action", None, "Drama"])
    assert result == "Action|Drama"


def test_coerce_genres_with_empty_in_list():
    """coerce_genres should filter out empty strings."""
    result = coerce_genres(["Action", "", "Drama"])
    assert result == "Action|Drama"


def test_coerce_genres_pandas_series():
    """coerce_genres should handle pandas Series."""
    series = pd.Series(["Action", "Drama", "Comedy"])
    result = coerce_genres(series)
    assert result == "Action|Drama|Comedy"


def test_coerce_genres_all_none():
    """coerce_genres with list of all None should return empty string."""
    result = coerce_genres([None, None])
    assert result == ""


def test_coerce_genres_all_empty():
    """coerce_genres with list of all empty strings should return empty string."""
    result = coerce_genres(["", "", ""])
    assert result == ""


def test_coerce_genres_numbers_in_list():
    """coerce_genres should convert numbers to strings."""
    result = coerce_genres([1, 2, 3])
    assert result == "1|2|3"


def test_coerce_genres_mixed_types():
    """coerce_genres should handle mixed types."""
    result = coerce_genres([1, "Action", 2.5, True])
    assert result == "1|Action|2.5|True"


def test_coerce_genres_deeply_nested():
    """coerce_genres should handle deeply nested structures."""
    result = coerce_genres([[["Action"]], [["Drama", ["Comedy"]]]])
    assert result == "Action|Drama|Comedy"


# ============================================================================
# Round-trip tests
# ============================================================================

def test_roundtrip_simple():
    """coerce_genres -> parse_pipe_set should be a round-trip for simple lists."""
    original = ["Action", "Drama", "Comedy"]
    pipe_str = coerce_genres(original)
    parsed = parse_pipe_set(pipe_str)
    assert parsed == set(original)


def test_roundtrip_with_spaces():
    """Round-trip should preserve content but normalize whitespace."""
    original = [" Action ", "  Drama  ", "Comedy"]
    pipe_str = coerce_genres(original)
    parsed = parse_pipe_set(pipe_str)
    # Whitespace should be stripped
    assert parsed == {"Action", "Drama", "Comedy"}


def test_idempotent_parse_pipe_set():
    """parse_pipe_set should be idempotent on its output."""
    original = "Action|Drama|Comedy"
    parsed1 = parse_pipe_set(original)
    parsed2 = parse_pipe_set(parsed1)  # parse the set
    assert parsed1 == parsed2


def test_idempotent_coerce_genres():
    """coerce_genres should be idempotent on pipe-delimited strings."""
    original = "Action|Drama|Comedy"
    coerced1 = coerce_genres(original)
    coerced2 = coerce_genres(coerced1)
    assert coerced1 == coerced2


# ============================================================================
# Edge case tests
# ============================================================================

def test_parse_pipe_set_unicode():
    """parse_pipe_set should handle unicode strings."""
    result = parse_pipe_set("アクション|ドラマ|コメディ")
    assert result == {"アクション", "ドラマ", "コメディ"}


def test_coerce_genres_unicode():
    """coerce_genres should handle unicode strings."""
    result = coerce_genres(["アクション", "ドラマ", "コメディ"])
    assert result == "アクション|ドラマ|コメディ"


def test_parse_pipe_set_special_chars():
    """parse_pipe_set should handle special characters."""
    result = parse_pipe_set("Sci-Fi|Slice of Life|Coming-of-Age")
    assert result == {"Sci-Fi", "Slice of Life", "Coming-of-Age"}


def test_coerce_genres_special_chars():
    """coerce_genres should handle special characters."""
    result = coerce_genres(["Sci-Fi", "Slice of Life", "Coming-of-Age"])
    assert result == "Sci-Fi|Slice of Life|Coming-of-Age"


def test_parse_pipe_set_single_pipe():
    """parse_pipe_set with just a pipe should return empty set."""
    result = parse_pipe_set("|")
    assert result == set()


def test_parse_pipe_set_multiple_pipes():
    """parse_pipe_set with multiple pipes and no content should return empty set."""
    result = parse_pipe_set("|||")
    assert result == set()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
