"""Canonical implementations of parsing utilities.

These functions handle the common patterns of parsing pipe-delimited strings,
lists, numpy arrays, and pandas DataFrames/Series into normalized formats.
Used across recommendation pipeline, diversity analysis, and UI components.
"""

from typing import Any, List

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore


def parse_pipe_set(val: object) -> set[str]:
    """Parse a value that might be a pipe-delimited string, list, set, or None into a set of strings.
    
    This function robustly handles multiple input types:
    - None or pandas NA → empty set
    - Empty string → empty set
    - Pipe-delimited string "Action|Drama|Comedy" → {"Action", "Drama", "Comedy"}
    - Single string "Action" → {"Action"}
    - List/tuple/set → coerced to set of strings
    - Other types → converted to string
    
    All values are stripped of whitespace and empty strings are filtered out.
    
    Args:
        val: Value to parse (str, list, set, None, pandas types, etc.)
    
    Returns:
        Set of non-empty string tokens
        
    Examples:
        >>> parse_pipe_set("Action|Drama")
        {'Action', 'Drama'}
        >>> parse_pipe_set(["Action", "Comedy"])
        {'Action', 'Comedy'}
        >>> parse_pipe_set(None)
        set()
        >>> parse_pipe_set("")
        set()
    """
    if val is None:
        return set()
    
    # Handle pandas NA values
    try:
        if pd is not None and pd.isna(val):
            return set()
    except Exception:
        pass

    # Handle string input (most common case)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return set()
        if "|" in s:
            return {x.strip() for x in s.split("|") if x and x.strip()}
        return {s}

    # Handle iterable types (list, tuple, set, numpy arrays, etc.)
    if hasattr(val, "__iter__") and not isinstance(val, str):
        out: set[str] = set()
        try:
            for x in val:  # type: ignore
                if not x:
                    continue
                sx = str(x).strip()
                if sx:
                    out.add(sx)
        except Exception:
            # If iteration fails, fall back to string conversion
            pass
        return out

    # Fallback: convert to string
    s = str(val).strip()
    return {s} if s else set()


def coerce_genres(val: Any) -> str:
    """Normalize a genres value to a pipe-delimited string.

    Robustly flattens list/tuple/set/ndarray (including nested structures) without
    relying on truth-value evaluation of array elements (avoids ambiguous truth value
    errors). Filters out None and blank string tokens.
    
    This is the inverse operation of parse_pipe_set - it takes various input formats
    and produces a canonical pipe-delimited string representation suitable for storage
    or display.
    
    Args:
        val: Value to coerce (str, list, tuple, set, numpy array, pandas Series, etc.)
    
    Returns:
        Pipe-delimited string (e.g., "Action|Drama|Comedy") or empty string if no valid values
        
    Examples:
        >>> coerce_genres(["Action", "Drama"])
        'Action|Drama'
        >>> coerce_genres("Action|Drama")
        'Action|Drama'
        >>> coerce_genres(None)
        ''
        >>> coerce_genres({"Horror", "Thriller"})
        'Horror|Thriller'  # Note: order may vary for sets
    """
    if val is None:
        return ""
    if isinstance(val, str):
        return val

    def _emit_tokens(obj: Any) -> List[str]:
        """Recursively extract string tokens from nested structures."""
        tokens: List[str] = []
        
        # Import locally to avoid global dependency if unused
        try:
            import numpy as _np  # type: ignore
        except Exception:  # noqa: BLE001
            _np = None  # type: ignore

        # Handle numpy arrays
        if _np is not None and isinstance(obj, _np.ndarray):
            flat = obj.ravel().tolist()
            for y in flat:
                if y is None:
                    continue
                sy = str(y).strip()
                if sy:
                    tokens.append(sy)
            return tokens

        # Handle list/tuple/set (potentially nested)
        if isinstance(obj, (list, tuple, set)):
            for x in obj:
                if x is None:
                    continue
                # Recursively handle nested structures
                if isinstance(x, (list, tuple, set)) or (_np is not None and isinstance(x, _np.ndarray)):
                    tokens.extend(_emit_tokens(x))
                else:
                    sx = str(x).strip()
                    if sx:
                        tokens.append(sx)
            return tokens

        # Handle pandas Series
        try:
            import pandas as _pd  # type: ignore
            if isinstance(obj, _pd.Series):
                for x in obj.tolist():
                    if x is None:
                        continue
                    tokens.extend(_emit_tokens(x))
                return tokens
        except Exception:  # noqa: BLE001
            pass

        # Fallback: convert to string
        so = str(obj).strip()
        if so:
            tokens.append(so)
        return tokens

    flat_tokens = _emit_tokens(val)
    return "|".join(flat_tokens)
