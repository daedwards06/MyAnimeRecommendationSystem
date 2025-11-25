"""Title search & normalization utilities (fuzzy + substring fallback)."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

try:
    from rapidfuzz import process, fuzz  # type: ignore
    _RAPIDFUZZ_AVAILABLE = True
except Exception:  # noqa: BLE001
    _RAPIDFUZZ_AVAILABLE = False
    from difflib import get_close_matches  # fallback


def normalize_title(s: str) -> str:
    return s.strip().lower()


def fuzzy_search(
    query: str,
    choices: Sequence[Tuple[str, int]],
    limit: int = 10,
    min_score: int = 60,
) -> List[Tuple[int, float, str]]:
    """Fuzzy search titles returning (anime_id, score, matched_title).

    Falls back to substring and difflib if rapidfuzz is unavailable.
    """
    q = normalize_title(query)
    if not q:
        return []

    if _RAPIDFUZZ_AVAILABLE:
        results = process.extract(
            q,
            [c[0] for c in choices],
            scorer=fuzz.WRatio,
            limit=limit,
        )
        out: List[Tuple[int, float, str]] = []
        for title, score, idx in results:
            if score >= min_score:
                out.append((choices[idx][1], float(score), choices[idx][0]))
        if not out:  # substring fallback
            for t, aid in choices:
                if q in t.lower():
                    out.append((aid, 100.0, t))
        return out[:limit]

    # difflib fallback
    all_titles = [c[0] for c in choices]
    close = get_close_matches(q, all_titles, n=limit, cutoff=min_score / 100.0)
    mapped: List[Tuple[int, float, str]] = []
    for title in close:
        # approximate score not provided; assign nominal value
        for original, aid in choices:
            if original == title:
                mapped.append((aid, 80.0, original))
                break
    if not mapped:
        for t, aid in choices:
            if q in t.lower():
                mapped.append((aid, 100.0, t))
    return mapped[:limit]


__all__ = ["fuzzy_search", "normalize_title"]
