"""Shared Stage 1 shortlist construction helpers.

This module centralizes deterministic shortlist building for ranked paths.

Phase 5 refinement
------------------
Force-include top-K neural neighbors into the Stage 1 shortlist to avoid losing
high-similarity in-franchise items (often Movies/OVAs with episodes=1) to
conservative type/episodes gates.

Key constraints:
- Never bypass ranked hygiene (exclude_ids).
- Deterministic: stable sort, tie-break by anime_id.
- Conservative defaults; configurable via env vars in src.app.constants.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from src.app.constants import FORCE_NEURAL_MIN_SIM, FORCE_NEURAL_TOPK, force_neural_enable_for_semantic_mode


@dataclass(frozen=True)
class ForcedPoolDiagnostics:
    forced_count: int
    sim_min: float
    sim_mean: float
    sim_max: float


def select_forced_neural_pairs(
    neural_sims_by_id: Mapping[int, float],
    *,
    seed_ids: Iterable[int],
    exclude_ids: set[int],
    watched_ids: set[int] | None = None,
    topk: int = FORCE_NEURAL_TOPK,
    min_sim: float = FORCE_NEURAL_MIN_SIM,
) -> list[tuple[int, float]]:
    """Return [(anime_id, sim)] for the top-K neural neighbors.

    This is seed-conditioned (uses the provided similarity map) and applies only
    ranked hygiene filters (exclude_ids) plus seed/watched exclusions.

    Deterministic ordering: sim desc, anime_id asc.
    """

    if not neural_sims_by_id:
        return []

    seeds = {int(x) for x in (seed_ids or [])}
    watched = {int(x) for x in (watched_ids or set())}
    excl = {int(x) for x in (exclude_ids or set())}

    thr = float(min_sim)
    pairs: list[tuple[int, float]] = []

    for aid_raw, sim_raw in (neural_sims_by_id or {}).items():
        try:
            aid = int(aid_raw)
        except Exception:
            continue
        if aid <= 0 or aid in seeds or aid in watched or aid in excl:
            continue
        try:
            sim = float(sim_raw)
        except Exception:
            continue
        if sim < thr:
            continue
        pairs.append((aid, sim))

    pairs.sort(key=lambda x: (-float(x[1]), int(x[0])))
    k = max(0, int(topk))
    if k <= 0:
        return []
    return pairs[:k]


def forced_pool_stats(pairs: Sequence[tuple[int, float]]) -> ForcedPoolDiagnostics:
    if not pairs:
        return ForcedPoolDiagnostics(forced_count=0, sim_min=0.0, sim_mean=0.0, sim_max=0.0)
    sims = np.asarray([float(s) for _, s in pairs], dtype=np.float64)
    return ForcedPoolDiagnostics(
        forced_count=int(sims.size),
        sim_min=float(sims.min()) if sims.size else 0.0,
        sim_mean=float(sims.mean()) if sims.size else 0.0,
        sim_max=float(sims.max()) if sims.size else 0.0,
    )


def build_stage1_shortlist(
    *,
    pool_a: Sequence[dict[str, Any]],
    pool_b: Sequence[dict[str, Any]],
    shortlist_k: int,
    k_sem: int,
    k_meta: int,
    forced_first: Sequence[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Build the deterministic Stage 1 shortlist.

    Behavior matches existing Phase 4 mixture logic:
    - (Optional) forced-first pool is inserted at the top (deduped).
    - Take up to k_sem from Pool A.
    - Take up to k_meta from Pool B.
    - Backfill deterministically: B then A.

    Returns: (shortlist, forced_added_count)
    """

    target = max(0, int(shortlist_k))
    if target <= 0:
        return ([], 0)

    k_sem_i = max(0, int(k_sem))
    k_meta_i = max(0, int(k_meta))

    shortlist: list[dict[str, Any]] = []
    seen: set[int] = set()

    def _try_add(it: dict[str, Any], *, pool_label: str) -> bool:
        try:
            aid = int(it.get("anime_id", 0))
        except Exception:
            return False
        if aid <= 0 or aid in seen:
            return False

        s1 = it.get("_stage1")
        if isinstance(s1, dict):
            # Preserve existing report semantics: A=semantic, B=meta, C=backfill.
            s1.update({"pool": str(pool_label)})
        shortlist.append(it)
        seen.add(aid)
        return True

    forced_added = 0
    if forced_first:
        for it in forced_first:
            if len(shortlist) >= target:
                break
            if _try_add(it, pool_label="A"):
                forced_added += 1

    a_taken = 0
    a_i = 0
    while a_i < len(pool_a) and a_taken < k_sem_i and len(shortlist) < target:
        it = pool_a[a_i]
        a_i += 1
        if _try_add(it, pool_label="A"):
            a_taken += 1

    b_taken = 0
    b_i = 0
    while b_i < len(pool_b) and b_taken < k_meta_i and len(shortlist) < target:
        it = pool_b[b_i]
        b_i += 1
        if _try_add(it, pool_label="B"):
            b_taken += 1

    while b_i < len(pool_b) and len(shortlist) < target:
        it = pool_b[b_i]
        b_i += 1
        _try_add(it, pool_label="C")

    while a_i < len(pool_a) and len(shortlist) < target:
        it = pool_a[a_i]
        a_i += 1
        _try_add(it, pool_label="C")

    return (shortlist, int(forced_added))


def force_neural_enabled(*, semantic_mode: str) -> bool:
    return bool(force_neural_enable_for_semantic_mode(semantic_mode))
