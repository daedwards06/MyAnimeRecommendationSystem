"""Diversity and novelty summary helpers for UI.

These utilities operate on recommendation outputs and lightweight
metadata to produce summary indicators:
  - coverage: unique recommended items / requested top-N
  - genre_exposure_ratio: unique genres in recs / total genres in catalog
  - avg_novelty: mean novelty ratio across recs (provided per item)
  - popularity_percentile: computed per item using a popularity score vector
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
import pandas as pd

from src.utils import coerce_genres


def compute_popularity_percentiles(pop_scores: np.ndarray) -> np.ndarray:
    """Return percentile array where lower scores indicate higher popularity.

    Percentile definition: rank / (n - 1) with rank 0 = most popular.
    """
    order = np.argsort(-pop_scores)  # descending popularity by score
    ranks = np.empty_like(order)
    ranks[order] = np.arange(len(pop_scores))
    denom = max(len(pop_scores) - 1, 1)
    return ranks / denom


def coverage(recs: list[dict[str, Any]]) -> float:
    if not recs:
        return 0.0
    unique_ids = {r["anime_id"] for r in recs}
    return len(unique_ids) / len(recs)


# Removed _coerce_genres - now using canonical version from src.utils.parsing as coerce_genres


def genre_exposure_ratio(recs: list[dict[str, Any]], metadata: pd.DataFrame) -> float:
    if not recs or metadata.empty:
        return 0.0
    all_catalog_genres: set[str] = set()
    if "genres" in metadata.columns:
        for raw in metadata["genres"].dropna():
            gstr = coerce_genres(raw)
            for g in gstr.split("|"):
                if g:
                    all_catalog_genres.add(g.lower())

    # Create indexed lookup for O(1) access (performance optimization)
    metadata_by_id = metadata.set_index("anime_id", drop=False)

    rec_genres: set[str] = set()
    for r in recs:
        try:
            row = metadata_by_id.loc[r["anime_id"]]
            gstr = coerce_genres(row.get("genres") if isinstance(row, pd.Series) else None)
        except KeyError:
            continue
        for g in gstr.split("|"):
            if g:
                rec_genres.add(g.lower())
    if not all_catalog_genres:
        return 0.0
    return len(rec_genres) / len(all_catalog_genres)


def build_user_genre_hist(ratings: Mapping[Any, Any], metadata: pd.DataFrame) -> dict[str, int]:
    """Build a simple user genre history histogram from profile ratings.

    The result is used for novelty calculations. If the user has no ratings
    (or none can be resolved into metadata), this returns an empty dict.
    """
    if not ratings or metadata.empty or "anime_id" not in metadata.columns:
        return {}

    # Create indexed lookup for O(1) access (performance optimization)
    try:
        meta_idx = metadata.set_index("anime_id", drop=False)
    except Exception:
        # If we can't create index, return empty hist rather than fall back to O(N) lookups
        return {}

    hist: dict[str, int] = {}
    for raw_anime_id in ratings.keys():
        try:
            anime_id = int(raw_anime_id)
        except Exception:
            continue

        try:
            row = meta_idx.loc[anime_id]
        except KeyError:
            # Item not in metadata - skip it
            continue

        gstr = coerce_genres(getattr(row, "get", lambda k, d=None: d)("genres"))
        for g in gstr.split("|"):
            gg = g.strip().lower()
            if not gg:
                continue
            hist[gg] = hist.get(gg, 0) + 1
    return hist


def average_novelty(recs: list[dict[str, Any]]) -> float | None:
    """Return average novelty ratio across recs, or None when unavailable."""
    if not recs:
        return None
    vals: list[float] = []
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


def genre_jaccard_similarity(a: dict[str, Any], b: dict[str, Any], metadata: pd.DataFrame | None = None) -> float:
    """Compute Jaccard similarity between two items based on genres.

    Args:
        a: First item dict (must have 'anime_id' or 'genres' key)
        b: Second item dict (must have 'anime_id' or 'genres' key)
        metadata: Optional metadata DataFrame for genre lookup

    Returns:
        Jaccard similarity in [0, 1]
    """
    def _get_genres(item: dict[str, Any]) -> set[str]:
        """Extract genre set from item dict or metadata."""
        # First try direct genres key
        if "genres" in item:
            gstr = coerce_genres(item["genres"])
            return {g.strip().lower() for g in gstr.split("|") if g.strip()}

        # Try explanation common_genres
        if "explanation" in item and "common_genres" in item["explanation"]:
            return {g.strip().lower() for g in item["explanation"]["common_genres"] if g.strip()}

        # Try metadata lookup if provided
        if metadata is not None and "anime_id" in item:
            try:
                aid = int(item["anime_id"])
                row = metadata[metadata["anime_id"] == aid]
                if not row.empty:
                    gstr = coerce_genres(row.iloc[0].get("genres"))
                    return {g.strip().lower() for g in gstr.split("|") if g.strip()}
            except (KeyError, ValueError, IndexError):
                pass

        return set()

    genres_a = _get_genres(a)
    genres_b = _get_genres(b)

    if not genres_a or not genres_b:
        return 0.0

    intersection = genres_a & genres_b
    union = genres_a | genres_b

    return len(intersection) / len(union) if union else 0.0


def embedding_cosine_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Compute cosine similarity between two items based on synopsis embeddings.

    Args:
        a: First item dict (must have '_synopsis_embedding' key)
        b: Second item dict (must have '_synopsis_embedding' key)

    Returns:
        Cosine similarity in [-1, 1] (typically [0, 1] for embeddings)
    """
    emb_a = a.get("_synopsis_embedding")
    emb_b = b.get("_synopsis_embedding")

    if emb_a is None or emb_b is None:
        return 0.0

    # Convert to numpy arrays if needed
    if not isinstance(emb_a, np.ndarray):
        emb_a = np.array(emb_a)
    if not isinstance(emb_b, np.ndarray):
        emb_b = np.array(emb_b)

    # Compute cosine similarity
    norm_a = np.linalg.norm(emb_a)
    norm_b = np.linalg.norm(emb_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(emb_a, emb_b) / (norm_a * norm_b))


def mmr_rerank(
    candidates: list[dict],
    similarity_fn: Callable[[dict, dict], float],
    lambda_param: float = 0.3,
    top_n: int = 10,
) -> list[dict]:
    """Maximal Marginal Relevance reranking (Carbonell & Goldstein, 1998).

    Iteratively selects items that maximize:
        MMR(i) = λ * relevance(i) - (1 - λ) * max_similarity(i, selected)

    This algorithm balances relevance (score) with diversity by penalizing
    items that are too similar to already-selected items.

    Reference:
        Carbonell, J., & Goldstein, J. (1998). "The use of MMR, diversity-based
        reranking for reordering documents and producing summaries."
        Proceedings of SIGIR-98.

    Args:
        candidates: Scored items with "score" key (relevance) and feature vectors
        similarity_fn: Pairwise similarity function between two candidate dicts
        lambda_param: Trade-off parameter (0=max diversity, 1=pure relevance)
        top_n: Number of items to select

    Returns:
        Reranked list of top_n items (or fewer if candidates is smaller)
    """
    if not candidates:
        return []

    # Handle edge cases
    if len(candidates) <= top_n:
        # If we have fewer candidates than requested, return all in original order
        return candidates[:top_n]

    if lambda_param >= 0.999:
        # Pure relevance mode (λ ≈ 1.0) — no diversity, return top-N by score
        return candidates[:top_n]

    # Normalize lambda to [0, 1]
    lambda_param = max(0.0, min(1.0, float(lambda_param)))

    selected: list[dict] = []
    remaining = list(candidates)  # Work with a copy

    # First item: highest relevance score
    # (Candidates should already be sorted by score descending)
    selected.append(remaining.pop(0))

    # Iteratively select remaining items
    while len(selected) < top_n and remaining:
        best_mmr_score = float("-inf")
        best_idx = 0

        for idx, candidate in enumerate(remaining):
            relevance = float(candidate.get("score", 0.0))

            # Compute max similarity to already-selected items
            max_sim = 0.0
            for selected_item in selected:
                try:
                    sim = similarity_fn(candidate, selected_item)
                    max_sim = max(max_sim, sim)
                except Exception:
                    # If similarity computation fails, assume 0 similarity
                    pass

            # MMR score: balance relevance and diversity
            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_sim

            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_idx = idx

        # Move best item from remaining to selected
        selected.append(remaining.pop(best_idx))

    return selected


__all__ = [
    "average_novelty",
    "build_user_genre_hist",
    "compute_popularity_percentiles",
    "coverage",
    "embedding_cosine_similarity",
    "genre_exposure_ratio",
    "genre_jaccard_similarity",
    "mmr_rerank",
]
