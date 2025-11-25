"""Diversity and novelty summary helpers for UI.

These utilities operate on recommendation outputs and lightweight
metadata to produce summary indicators:
  - coverage: unique recommended items / requested top-N
  - genre_exposure_ratio: unique genres in recs / total genres in catalog
  - avg_novelty: mean novelty ratio across recs (provided per item)
  - popularity_percentile: computed per item using a popularity score vector
"""

from __future__ import annotations

from typing import Iterable, List, Dict, Any
import numpy as np
import pandas as pd


def compute_popularity_percentiles(pop_scores: np.ndarray) -> np.ndarray:
    """Return percentile array where lower scores indicate higher popularity.

    Percentile definition: rank / (n - 1) with rank 0 = most popular.
    """
    order = np.argsort(-pop_scores)  # descending popularity by score
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(pop_scores))
    denom = max(len(pop_scores) - 1, 1)
    return ranks / denom


def coverage(recs: List[Dict[str, Any]]) -> float:
    if not recs:
        return 0.0
    unique_ids = {r["anime_id"] for r in recs}
    return len(unique_ids) / len(recs)


def _coerce_genres(val: Any) -> str:
    """Normalize a genres value to a pipe-delimited string.

    Robustly flattens list/tuple/set/ndarray (including nested) without
    relying on truth-value evaluation of array elements (avoids ambiguous
    truth value errors). Filters out None and blank string tokens.
    """
    if val is None:
        return ""
    if isinstance(val, str):
        return val

    def _emit_tokens(obj: Any) -> List[str]:
        tokens: List[str] = []
        # Import locally to avoid global dependency if unused.
        try:
            import numpy as _np  # type: ignore
        except Exception:  # noqa: BLE001
            _np = None  # type: ignore

        if _np is not None and isinstance(obj, _np.ndarray):
            flat = obj.ravel().tolist()
            for y in flat:
                if y is None:
                    continue
                sy = str(y).strip()
                if sy:
                    tokens.append(sy)
            return tokens

        if isinstance(obj, (list, tuple, set)):
            for x in obj:
                if x is None:
                    continue
                if isinstance(x, (list, tuple, set)) or (_np is not None and isinstance(x, _np.ndarray)):
                    tokens.extend(_emit_tokens(x))
                else:
                    sx = str(x).strip()
                    if sx:
                        tokens.append(sx)
            return tokens

        # pandas Series
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

        so = str(obj).strip()
        if so:
            tokens.append(so)
        return tokens

    flat_tokens = _emit_tokens(val)
    return "|".join(flat_tokens)


def genre_exposure_ratio(recs: List[Dict[str, Any]], metadata: pd.DataFrame) -> float:
    if not recs or metadata.empty:
        return 0.0
    all_catalog_genres: set[str] = set()
    if "genres" in metadata.columns:
        for raw in metadata["genres"].dropna():
            gstr = _coerce_genres(raw)
            for g in gstr.split("|"):
                if g:
                    all_catalog_genres.add(g.lower())
    rec_genres: set[str] = set()
    for r in recs:
        row = metadata.loc[metadata["anime_id"] == r["anime_id"]]
        if row.empty:
            continue
        gstr = _coerce_genres(row.iloc[0].get("genres"))
        for g in gstr.split("|"):
            if g:
                rec_genres.add(g.lower())
    if not all_catalog_genres:
        return 0.0
    return len(rec_genres) / len(all_catalog_genres)


def average_novelty(recs: List[Dict[str, Any]]) -> float:
    if not recs:
        return 0.0
    vals = []
    for r in recs:
        badge = r.get("badges")
        if badge and "novelty_ratio" in badge:
            vals.append(float(badge["novelty_ratio"]))
    if not vals:
        return 0.0
    return float(np.mean(vals))


__all__ = [
    "compute_popularity_percentiles",
    "coverage",
    "genre_exposure_ratio",
    "average_novelty",
]
