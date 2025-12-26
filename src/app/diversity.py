"""Diversity and novelty summary helpers for UI.

These utilities operate on recommendation outputs and lightweight
metadata to produce summary indicators:
  - coverage: unique recommended items / requested top-N
  - genre_exposure_ratio: unique genres in recs / total genres in catalog
  - avg_novelty: mean novelty ratio across recs (provided per item)
  - popularity_percentile: computed per item using a popularity score vector
"""

from __future__ import annotations

from typing import Iterable, List, Dict, Any, Optional, Mapping
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


def build_user_genre_hist(ratings: Mapping[Any, Any], metadata: pd.DataFrame) -> Dict[str, int]:
    """Build a simple user genre history histogram from profile ratings.

    The result is used for novelty calculations. If the user has no ratings
    (or none can be resolved into metadata), this returns an empty dict.
    """
    if not ratings or metadata.empty or "anime_id" not in metadata.columns:
        return {}

    try:
        meta_idx = metadata.set_index("anime_id", drop=False)
    except Exception:
        meta_idx = metadata

    hist: Dict[str, int] = {}
    for raw_anime_id in ratings.keys():
        try:
            anime_id = int(raw_anime_id)
        except Exception:
            continue

        try:
            row = meta_idx.loc[anime_id]
        except Exception:
            # Fall back to slower lookup when index isn't available.
            row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
            if row_df.empty:
                continue
            row = row_df.iloc[0]

        gstr = _coerce_genres(getattr(row, "get", lambda k, d=None: d)("genres"))
        for g in gstr.split("|"):
            gg = g.strip().lower()
            if not gg:
                continue
            hist[gg] = hist.get(gg, 0) + 1
    return hist


def average_novelty(recs: List[Dict[str, Any]]) -> Optional[float]:
    """Return average novelty ratio across recs, or None when unavailable."""
    if not recs:
        return None
    vals: List[float] = []
    for r in recs:
        badge = r.get("badges")
        if not badge:
            continue
        if "novelty_ratio" not in badge:
            continue
        v = badge.get("novelty_ratio")
        if v is None:
            continue
        vals.append(float(v))
    if not vals:
        return None
    return float(np.mean(vals))


__all__ = [
    "compute_popularity_percentiles",
    "coverage",
    "genre_exposure_ratio",
    "build_user_genre_hist",
    "average_novelty",
]
