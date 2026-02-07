"""Stage 0: seed-conditioned candidate generation (Phase 5 quality upgrade).

Goal
----
Constrain the candidate universe for seed-based ranked recommendations *before*
any Stage 1 admission or Stage 2 scoring runs, to prevent off-theme catalog
pollution from swamping ranking heuristics.

Stage 0 pool definition (Option 1: semantic-first)
-------------------------------------------------
Union of three deterministic tiers:
    Tier A) Neural semantic neighbors (primary): top-K by cosine similarity
    Tier B) Strict metadata overlap (precision confirmer):
                    - genre_weighted_overlap >= min_genre_overlap
                        OR
                    - theme_overlap_ratio >= min_theme_overlap
                    Notes: missing themes never penalize; they only help when present.
    Tier C) Small popularity backfill (safety): top-N popular items

Then:
    - Dedupe by anime_id
    - Apply ranked hygiene exclusions + seed/watched exclusions
    - Enforce hard cap with stable truncation (A -> B -> C priority)

This module is shared by Streamlit and the golden harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from src.app.synopsis_neural_embeddings import compute_seed_topk_neighbors


@dataclass(frozen=True)
class Stage0Diagnostics:
    # NOTE:
    # - raw tier counts are computed BEFORE hygiene exclusions and BEFORE cap.
    # - after_hygiene is computed AFTER exclusions but BEFORE cap.
    # - after_cap is the final candidate universe returned downstream.

    stage0_pool_raw: int
    stage0_from_neural_raw: int
    stage0_from_meta_strict_raw: int
    stage0_from_popularity_raw: int

    stage0_after_hygiene: int
    stage0_after_cap: int

    # Final pool membership counts (after cap).
    stage0_from_neural: int
    stage0_from_meta_strict: int
    stage0_from_popularity: int

    # Overlap diagnostics (after cap; overlaps may not sum to stage0_after_cap).
    stage0_neural_only: int
    stage0_meta_only: int
    stage0_pop_only: int
    stage0_neural_and_meta: int


def _parse_pipe_set(val: object) -> set[str]:
    if val is None:
        return set()
    try:
        if pd.isna(val):
            return set()
    except Exception:
        pass

    if isinstance(val, str):
        s = val.strip()
        if not s:
            return set()
        if "|" in s:
            return {x.strip() for x in s.split("|") if x and x.strip()}
        return {s}

    if hasattr(val, "__iter__") and not isinstance(val, str):
        out: set[str] = set()
        try:
            for x in val:  # type: ignore[assignment]
                if not x:
                    continue
                sx = str(x).strip()
                if sx:
                    out.add(sx)
        except Exception:
            return set()
        return out

    s = str(val).strip()
    return {s} if s else set()


def _seed_union_set(metadata: pd.DataFrame, *, seed_ids: Sequence[int], col: str) -> set[str]:
    if metadata is None or metadata.empty or not seed_ids or "anime_id" not in metadata.columns:
        return set()
    if col not in metadata.columns:
        return set()
    seed_set = {int(x) for x in seed_ids}
    out: set[str] = set()
    try:
        df = metadata.loc[metadata["anime_id"].astype(int).isin(seed_set), [col]]
    except Exception:
        return set()
    for v in df[col].tolist():
        out.update(_parse_pipe_set(v))
    return out


def _top_popular_ids(
    *,
    item_ids: np.ndarray,
    pop_scores: np.ndarray | None,
    topn: int,
) -> list[int]:
    if pop_scores is None:
        return []
    k = max(0, int(topn))
    if k <= 0:
        return []
    try:
        scores = np.asarray(pop_scores, dtype=np.float32)
        ids = np.asarray(item_ids, dtype=np.int64)
        if scores.ndim != 1 or ids.ndim != 1 or scores.shape[0] != ids.shape[0] or scores.shape[0] <= 0:
            return []
    except Exception:
        return []

    n = int(scores.shape[0])
    if k >= n:
        idx = np.arange(n, dtype=np.int32)
    else:
        idx = np.argpartition(scores, -k)[-k:]

    pairs: list[tuple[int, float]] = []
    for i in idx.tolist():
        try:
            aid = int(ids[int(i)])
            s = float(scores[int(i)])
        except Exception:
            continue
        if not np.isfinite(s):
            continue
        pairs.append((aid, s))

    pairs.sort(key=lambda x: (-float(x[1]), int(x[0])))
    return [int(aid) for aid, _ in pairs[:k]]


def build_stage0_seed_candidate_pool(
    *,
    metadata: pd.DataFrame,
    seed_ids: Sequence[int],
    ranked_hygiene_exclude_ids: set[int],
    watched_ids: set[int] | None,
    neural_artifact: Any | None,
    neural_topk: int,
    meta_min_genre_overlap: float,
    meta_min_theme_overlap: float,
    popularity_backfill: int,
    pool_cap: int,
    pop_item_ids: np.ndarray | None = None,
    pop_scores: np.ndarray | None = None,
) -> tuple[list[int], Mapping[int, dict[str, bool]], Stage0Diagnostics]:
    """Build Stage 0 candidate IDs and source-membership flags.

    Returns:
            - stage0_ids: deterministic list of candidate anime_ids (after hygiene + cap)
            - flags_by_id: anime_id -> {from_neural, from_meta_strict, from_popularity}
            - diagnostics: Stage0Diagnostics
    """

    seeds = {int(x) for x in (seed_ids or [])}
    watched = {int(x) for x in (watched_ids or set())}
    exclude = {int(x) for x in (ranked_hygiene_exclude_ids or set())}

    blocked = set()
    blocked.update(seeds)
    blocked.update(watched)
    blocked.update(exclude)

    # A) Neural neighbors (primary)
    neural_pairs: list[tuple[int, float]] = []
    if neural_artifact is not None and int(neural_topk) > 0:
        try:
            neural_pairs = compute_seed_topk_neighbors(neural_artifact, seed_ids=seeds, topk=int(neural_topk))
        except Exception:
            neural_pairs = []

    # Deterministic ordering (even if upstream changes): (-sim, anime_id)
    try:
        neural_pairs.sort(key=lambda x: (-float(x[1]), int(x[0])))
    except Exception:
        pass

    neural_ids: list[int] = []
    neural_set: set[int] = set()
    neural_sim_by_id: dict[int, float] = {}
    for aid, sim in neural_pairs:
        ai = int(aid)
        if ai > 0:
            neural_ids.append(ai)
            neural_set.add(ai)
            if ai not in neural_sim_by_id:
                neural_sim_by_id[ai] = float(sim)

    # B) Strict metadata overlap (genre_weighted_overlap OR theme_overlap_ratio)
    seed_genres = _seed_union_set(metadata, seed_ids=seed_ids, col="genres")
    seed_themes = _seed_union_set(metadata, seed_ids=seed_ids, col="themes")

    # Phase 4/5 weighted genre overlap (consistent with the harness):
    # raw_overlap = sum(weights[g] for g in candidate_genres)
    # max_possible = |G_seed_union| * num_seeds
    # weighted_overlap = raw_overlap / max_possible
    seed_genre_weights: dict[str, int] = {}
    if metadata is not None and not metadata.empty and seed_ids and "anime_id" in metadata.columns and "genres" in metadata.columns:
        seed_set = {int(x) for x in seed_ids}
        try:
            seed_rows = metadata.loc[metadata["anime_id"].astype(int).isin(seed_set), ["genres"]]
        except Exception:
            seed_rows = None
        if seed_rows is not None and not getattr(seed_rows, "empty", True):
            for v in seed_rows["genres"].tolist():
                for g in _parse_pipe_set(v):
                    if g:
                        seed_genre_weights[g] = int(seed_genre_weights.get(g, 0) + 1)

    def _theme_overlap_ratio(seed_t: set[str], cand_t: set[str]) -> float | None:
        if not seed_t or not cand_t:
            return None
        denom = len(seed_t)
        if denom <= 0:
            return None
        return float(len(set(seed_t) & set(cand_t)) / float(denom))

    meta_strict_match: set[int] = set()

    if metadata is not None and not metadata.empty and "anime_id" in metadata.columns:
        has_genres = "genres" in metadata.columns
        has_themes = "themes" in metadata.columns
        denom = float(len(seed_genres) * max(1, len(seeds)))
        if denom <= 0.0:
            denom = 0.0

        min_g = float(meta_min_genre_overlap)
        min_t = float(meta_min_theme_overlap)

        for row in metadata.itertuples(index=False):
            try:
                aid = int(getattr(row, "anime_id"))
            except Exception:
                continue
            if aid <= 0:
                continue

            g_ok = False
            t_ok = False

            # Genre weighted overlap: never penalize missing genres; it just can't help.
            if has_genres and seed_genres and denom > 0.0:
                try:
                    gset = _parse_pipe_set(getattr(row, "genres"))
                    raw = 0
                    for g in gset:
                        raw += int(seed_genre_weights.get(g, 0))
                    w = float(raw) / float(denom)
                    g_ok = bool(w >= float(min_g))
                except Exception:
                    g_ok = False

            # Theme overlap ratio: missing themes never penalize; only helps when present.
            if has_themes and seed_themes:
                try:
                    tset = _parse_pipe_set(getattr(row, "themes"))
                    tr = _theme_overlap_ratio(seed_themes, tset)
                    t_ok = bool(tr is not None and float(tr) >= float(min_t))
                except Exception:
                    t_ok = False

            if g_ok or t_ok:
                meta_strict_match.add(int(aid))

    # C) Popularity backfill (optional)
    pop_ids: list[int] = []
    if pop_item_ids is not None and pop_scores is not None and int(popularity_backfill) > 0:
        pop_ids = _top_popular_ids(item_ids=pop_item_ids, pop_scores=pop_scores, topn=int(popularity_backfill))

    # Build source flags (dedup by key)
    flags: dict[int, dict[str, bool]] = {}

    def _flag(aid: int, key: str) -> None:
        if aid <= 0:
            return
        cur = flags.get(aid)
        if cur is None:
            cur = {
                "from_neural": False,
                "from_meta_strict": False,
                "from_popularity": False,
            }
            flags[aid] = cur
        cur[key] = True

    for aid in neural_set:
        _flag(int(aid), "from_neural")
    for aid in meta_strict_match:
        _flag(int(aid), "from_meta_strict")
    for aid in pop_ids:
        _flag(int(aid), "from_popularity")

    # Compute raw union size BEFORE hygiene/cap for diagnostics.
    # (Deduped across sources; includes items that may be seeds/watched/excluded.)
    raw_union: set[int] = set()
    raw_union.update({int(x) for x in neural_set if int(x) > 0})
    raw_union.update({int(x) for x in meta_strict_match if int(x) > 0})
    raw_union.update({int(x) for x in pop_ids if int(x) > 0})
    raw_union_size = int(len(raw_union))

    # After-hygiene universe (before cap): union of tiers, then hygiene exclusions.
    after_hygiene_set: set[int] = set()
    after_hygiene_set.update({int(x) for x in neural_set if int(x) > 0 and int(x) not in blocked})
    after_hygiene_set.update({int(x) for x in meta_strict_match if int(x) > 0 and int(x) not in blocked})
    after_hygiene_set.update({int(x) for x in pop_ids if int(x) > 0 and int(x) not in blocked})
    after_hygiene_size = int(len(after_hygiene_set))

    # Stable union + truncation: A -> B -> C priority.
    cap = max(0, int(pool_cap))
    if cap <= 0:
        cap = 0

    final_ids: list[int] = []
    seen: set[int] = set()

    def _try_add(aid: int) -> None:
        if cap and len(final_ids) >= cap:
            return
        if aid <= 0 or aid in seen or aid in blocked:
            return
        final_ids.append(int(aid))
        seen.add(int(aid))

    # A: neural neighbors in similarity order.
    for aid in neural_ids:
        _try_add(int(aid))
        if cap and len(final_ids) >= cap:
            break

    # B: strict metadata overlap (sorted by anime_id for determinism)
    for aid in sorted(meta_strict_match):
        _try_add(int(aid))
        if cap and len(final_ids) >= cap:
            break

    # C: popularity backfill order.
    for aid in pop_ids:
        _try_add(int(aid))
        if cap and len(final_ids) >= cap:
            break

    after_cap_size = int(len(final_ids))

    # Compute diagnostics over the final pool.
    from_neural = 0
    from_meta = 0
    from_pop = 0
    neural_only = 0
    meta_only = 0
    pop_only = 0
    neural_and_meta = 0

    for aid in final_ids:
        f = flags.get(int(aid), {})
        fn = bool(f.get("from_neural"))
        fm = bool(f.get("from_meta_strict"))
        fp = bool(f.get("from_popularity"))

        if fn:
            from_neural += 1
        if fm:
            from_meta += 1
        if fp:
            from_pop += 1

        if fn and fm:
            neural_and_meta += 1
        if fn and (not fm) and (not fp):
            neural_only += 1
        if fm and (not fn) and (not fp):
            meta_only += 1
        if fp and (not fn) and (not fm):
            pop_only += 1

    diag = Stage0Diagnostics(
        stage0_pool_raw=int(raw_union_size),
        stage0_from_neural_raw=int(len(neural_set)),
        stage0_from_meta_strict_raw=int(len(meta_strict_match)),
        stage0_from_popularity_raw=int(len({int(x) for x in pop_ids if int(x) > 0})),
        stage0_after_hygiene=int(after_hygiene_size),
        stage0_after_cap=int(after_cap_size),
        stage0_from_neural=int(from_neural),
        stage0_from_meta_strict=int(from_meta),
        stage0_from_popularity=int(from_pop),
        stage0_neural_only=int(neural_only),
        stage0_meta_only=int(meta_only),
        stage0_pop_only=int(pop_only),
        stage0_neural_and_meta=int(neural_and_meta),
    )

    return final_ids, flags, diag
