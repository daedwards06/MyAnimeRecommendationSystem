"""Discovery-mode franchise cap for seed-based ranked recommendations.

This module implements a deterministic, post-score selection step that limits
franchise-dominance (sequels/spin-offs) using the existing `title_overlap`
heuristic.

Contract
--------
- Selection-only: does NOT alter scores.
- Deterministic: stable input order is preserved; tie-break should be handled
  upstream (typically score desc, then anime_id asc).
- Safe: intended to run after ranked hygiene filters (do not bypass hygiene).

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

from src.app.constants import FRANCHISE_STRONG_MATCH_ENABLED, FRANCHISE_STRONG_MATCH_MIN_SEED_LEN


SeedRankingMode = str  # "completion" | "discovery" (validated upstream)


@dataclass(frozen=True)
class FranchiseCapDiagnostics:
    seed_ranking_mode: str
    franchise_cap_threshold: float
    franchise_cap_top20: int
    franchise_cap_top50: int

    top20_franchise_like_count_before: int
    top20_franchise_like_count_after: int
    top50_franchise_like_count_before: int
    top50_franchise_like_count_after: int

    franchise_items_dropped_count: int
    franchise_items_dropped_count_top20: int
    franchise_items_dropped_count_top50: int
    franchise_items_dropped_examples_top5: list[dict[str, Any]]

    # Optional debug-only diagnostics (not intended for core UI display).
    franchise_seed_norm: str
    franchise_like_examples_top10: list[dict[str, Any]]
    franchise_overlap_audit_top10: list[dict[str, Any]]


def _normalize_phrase(s: str) -> str:
    """Normalize titles for deterministic phrase containment checks.

    Rules:
    - lowercase
    - strip punctuation/symbols (keep letters/numbers/spaces)
    - collapse whitespace
    """

    raw = str(s or "").strip().lower()
    if not raw:
        return ""

    # Replace non-alnum with spaces; keep Unicode letters/digits.
    out_chars: list[str] = []
    for ch in raw:
        if ch.isalnum():
            out_chars.append(ch)
        else:
            out_chars.append(" ")

    norm = "".join(out_chars)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def _boundary_contains(*, haystack: str, needle: str) -> bool:
    """True if `needle` appears as a whole-phrase boundary match in `haystack`.

    Boundary means: start/end or spaces around the match.
    """

    h = str(haystack or "")
    n = str(needle or "")
    if not h or not n:
        return False

    start = 0
    while True:
        idx = h.find(n, start)
        if idx < 0:
            return False
        left_ok = idx == 0 or h[idx - 1] == " "
        end = idx + len(n)
        right_ok = end == len(h) or h[end] == " "
        if left_ok and right_ok:
            return True
        start = idx + 1


def _classify_franchise_like(
    *,
    mode: str,
    seed_titles: Optional[list[str]],
    candidate_title: str,
    title_overlap_value: float,
    threshold: float,
) -> tuple[bool, str, str, str]:
    """Return (franchise_like, reason, seed_norm, candidate_norm).

    Discovery-mode classifier:
      - strong match: normalized phrase containment (startswith or boundary substring)
      - fallback: title_overlap >= threshold

    Completion-mode classifier:
      - overlap only (strong match disabled)
    """

    mode_norm = str(mode or "").strip().lower()
    seed_norm = ""
    cand_norm = _normalize_phrase(candidate_title)

    # Fallback overlap heuristic (available in all modes).
    ov = float(title_overlap_value)
    fallback = bool(ov >= float(threshold))

    # Strong rule is Discovery-only.
    if mode_norm != "discovery":
        return bool(fallback), ("overlap" if fallback else ""), seed_norm, cand_norm

    strong_enabled = bool(FRANCHISE_STRONG_MATCH_ENABLED)
    min_len = max(0, int(FRANCHISE_STRONG_MATCH_MIN_SEED_LEN))
    if not strong_enabled or not seed_titles:
        return bool(fallback), ("overlap" if fallback else ""), seed_norm, cand_norm

    # Prefer the longest normalized seed phrase (multi-seed: pick most specific).
    seed_norms = [
        _normalize_phrase(st)
        for st in (seed_titles or [])
        if _normalize_phrase(st)
    ]
    if not seed_norms:
        return bool(fallback), ("overlap" if fallback else ""), seed_norm, cand_norm

    seed_norm = max(seed_norms, key=len)
    if len(seed_norm) < int(min_len):
        return bool(fallback), ("overlap" if fallback else ""), seed_norm, cand_norm

    # Strong match: startswith OR boundary-contained full phrase.
    strong = bool(cand_norm.startswith(seed_norm) or _boundary_contains(haystack=cand_norm, needle=seed_norm))
    if strong:
        return True, "strong_match", seed_norm, cand_norm

    if fallback:
        return True, "overlap", seed_norm, cand_norm

    return False, "", seed_norm, cand_norm


def _count_franchise_like(
    items: list[dict[str, Any]],
    *,
    k: int,
    classify: Callable[[dict[str, Any]], bool],
) -> int:
    if not items:
        return 0
    kk = max(0, int(k))
    out = 0
    for it in items[:kk]:
        try:
            if bool(classify(it)):
                out += 1
        except Exception:
            continue
    return int(out)


def apply_franchise_cap(
    items_sorted: list[dict[str, Any]],
    *,
    n: int,
    seed_ranking_mode: SeedRankingMode,
    seed_titles: Optional[list[str]] = None,
    title_overlap: Callable[[dict[str, Any]], float],
    title: Callable[[dict[str, Any]], str],
    anime_id: Callable[[dict[str, Any]], int],
    neural_sim: Optional[Callable[[dict[str, Any]], float]] = None,
    threshold: float,
    cap_top20: int,
    cap_top50: int,
) -> tuple[list[dict[str, Any]], FranchiseCapDiagnostics]:
    """Return selected items and franchise-cap diagnostics.

    Parameters
    ----------
    items_sorted:
        Full candidate list already sorted in final score order.
    n:
        Number of items to return.
    seed_ranking_mode:
        "completion" (no cap) or "discovery" (cap enabled).
    title_overlap/title/anime_id/neural_sim:
        Accessors over `items_sorted`.

    Notes
    -----
    - Caps apply to the *output prefix* (top-20 and top-50). For n > 20, the
      top-20 cap is still enforced within the first 20 returned.
    """

    mode = str(seed_ranking_mode or "").strip().lower()
    mode = mode if mode in {"completion", "discovery"} else "completion"

    n_req = max(0, int(n))
    # Diagnostics should include meaningful top-50 counts even when the caller only
    # requests top-20 results. To keep diagnostics consistent, we compute them
    # from an internal selection up to at least 50 (when possible) and return the
    # caller-requested prefix.
    n_diag = min(len(items_sorted), max(n_req, 50))

    def _is_franchise_like(it: dict[str, Any]) -> bool:
        try:
            ov = float(title_overlap(it))
        except Exception:
            ov = 0.0
        try:
            cand_title = str(title(it) or "")
        except Exception:
            cand_title = ""
        is_like, _, _, _ = _classify_franchise_like(
            mode=mode,
            seed_titles=seed_titles,
            candidate_title=cand_title,
            title_overlap_value=float(ov),
            threshold=float(threshold),
        )
        return bool(is_like)

    top20_before = _count_franchise_like(items_sorted, k=20, classify=_is_franchise_like)
    top50_before = _count_franchise_like(items_sorted, k=50, classify=_is_franchise_like)

    # Capture some explainable examples from the pre-cap list.
    franchise_like_examples: list[dict[str, Any]] = []
    overlap_audit_rows: list[dict[str, Any]] = []
    franchise_seed_norm = ""
    pre_cap_slice = items_sorted[: min(len(items_sorted), 50)]
    for it in pre_cap_slice:
        try:
            aid = int(anime_id(it))
        except Exception:
            aid = 0
        try:
            ov = float(title_overlap(it))
        except Exception:
            ov = 0.0
        try:
            t = str(title(it) or "")
        except Exception:
            t = ""
        is_like, reason, seed_norm, cand_norm = _classify_franchise_like(
            mode=mode,
            seed_titles=seed_titles,
            candidate_title=t,
            title_overlap_value=float(ov),
            threshold=float(threshold),
        )
        if seed_norm and not franchise_seed_norm:
            franchise_seed_norm = str(seed_norm)
        if not is_like:
            continue
        ex: dict[str, Any] = {
            "anime_id": int(aid),
            "title": str(t),
            "reason": str(reason or ""),
            "title_overlap": float(ov),
        }
        # Debug-only norms (safe for harness logs; not intended for core UI).
        ex["seed_norm"] = str(seed_norm)
        ex["candidate_norm"] = str(cand_norm)
        if neural_sim is not None:
            try:
                ex["neural_sim"] = float(neural_sim(it))
            except Exception:
                ex["neural_sim"] = 0.0
        franchise_like_examples.append(ex)
        if len(franchise_like_examples) >= 10:
            break

    # Top-10 by title_overlap (for audit tables; includes both like/unlike).
    ov_rows: list[tuple[float, int, dict[str, Any]]] = []
    for it in pre_cap_slice:
        try:
            aid = int(anime_id(it))
        except Exception:
            aid = 0
        try:
            ov = float(title_overlap(it))
        except Exception:
            ov = 0.0
        try:
            t = str(title(it) or "")
        except Exception:
            t = ""
        is_like, reason, seed_norm, cand_norm = _classify_franchise_like(
            mode=mode,
            seed_titles=seed_titles,
            candidate_title=t,
            title_overlap_value=float(ov),
            threshold=float(threshold),
        )
        row: dict[str, Any] = {
            "anime_id": int(aid),
            "title": str(t),
            "title_overlap": float(ov),
            "franchise_like": bool(is_like),
            "reason": str(reason or ""),
            "seed_norm": str(seed_norm or ""),
            "candidate_norm": str(cand_norm or ""),
        }
        if neural_sim is not None:
            try:
                row["neural_sim"] = float(neural_sim(it))
            except Exception:
                row["neural_sim"] = 0.0
        ov_rows.append((float(ov), int(aid), row))

    ov_rows.sort(key=lambda x: (-float(x[0]), int(x[1])))
    overlap_audit_rows = [r for _, _, r in ov_rows[:10]]

    selected_full: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    dropped_top20 = 0
    dropped_top50 = 0

    if mode != "discovery":
        selected_full = list(items_sorted[:n_diag])
    else:
        cap20 = max(0, int(cap_top20))
        cap50 = max(0, int(cap_top50))
        franchise_kept = 0

        # Stable pass: keep order; skip additional franchise-like items once caps are met.
        for it in items_sorted:
            if len(selected_full) >= int(n_diag):
                break

            try:
                aid = int(anime_id(it))
            except Exception:
                aid = 0

            try:
                ov = float(title_overlap(it))
            except Exception:
                ov = 0.0

            try:
                cand_title = str(title(it) or "")
            except Exception:
                cand_title = ""

            is_franchise_like, reason, seed_norm, cand_norm = _classify_franchise_like(
                mode=mode,
                seed_titles=seed_titles,
                candidate_title=cand_title,
                title_overlap_value=float(ov),
                threshold=float(threshold),
            )

            if seed_norm and not franchise_seed_norm:
                franchise_seed_norm = str(seed_norm)

            # Determine which cap applies at this output position.
            next_pos = int(len(selected_full) + 1)
            cap_here: Optional[int]
            if next_pos <= 20:
                cap_here = cap20
            elif next_pos <= 50:
                cap_here = cap50
            else:
                cap_here = None

            if is_franchise_like and cap_here is not None and franchise_kept >= int(cap_here):
                if next_pos <= 20:
                    dropped_top20 += 1
                if next_pos <= 50:
                    dropped_top50 += 1
                ex: dict[str, Any] = {
                    "anime_id": aid,
                    "title": str(cand_title or ""),
                    "title_overlap": float(ov),
                    "reason": str(reason or ""),
                    "seed_norm": str(seed_norm or ""),
                    "candidate_norm": str(cand_norm or ""),
                    "cap_pos": int(next_pos),
                }
                if neural_sim is not None:
                    try:
                        ex["neural_sim"] = float(neural_sim(it))
                    except Exception:
                        ex["neural_sim"] = 0.0
                dropped.append(ex)
                continue

            selected_full.append(it)
            if is_franchise_like:
                franchise_kept += 1

    selected_out = list(selected_full[:n_req])

    top20_after = _count_franchise_like(selected_full, k=20, classify=_is_franchise_like)
    top50_after = _count_franchise_like(selected_full, k=50, classify=_is_franchise_like)

    diag = FranchiseCapDiagnostics(
        seed_ranking_mode=mode,
        franchise_cap_threshold=float(threshold),
        franchise_cap_top20=int(cap_top20),
        franchise_cap_top50=int(cap_top50),
        top20_franchise_like_count_before=int(top20_before),
        top20_franchise_like_count_after=int(top20_after),
        top50_franchise_like_count_before=int(top50_before),
        top50_franchise_like_count_after=int(top50_after),
        franchise_items_dropped_count=int(len(dropped)),
        franchise_items_dropped_count_top20=int(dropped_top20),
        franchise_items_dropped_count_top50=int(dropped_top50),
        franchise_items_dropped_examples_top5=list(dropped[:5]),
        franchise_seed_norm=str(franchise_seed_norm or ""),
        franchise_like_examples_top10=list(franchise_like_examples[:10]),
        franchise_overlap_audit_top10=list(overlap_audit_rows[:10]),
    )

    return selected_out, diag


__all__ = [
    "FranchiseCapDiagnostics",
    "apply_franchise_cap",
]
