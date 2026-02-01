"""Compare top-K recommendations between two Phase 4 golden artifact JSONs.

Usage (PowerShell):
    C:/Users/dedwa/Anaconda3/python.exe scripts/compare_golden_top20.py \
    --before reports/artifacts/phase4_golden_queries_20260201013913.json \
    --after  reports/artifacts/phase4_golden_queries_20260201021802.json \
    --query one_piece --query tokyo_ghoul --k 20

Notes:
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def _stdout_utf8() -> None:
    try:
        # Python 3.7+
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_query(obj: dict[str, Any], qid: str) -> dict[str, Any] | None:
    for q in obj.get("queries", []):
        if q.get("id") == qid:
            return q
    return None


def _rec_title(rec: dict[str, Any]) -> str:
    meta = rec.get("meta") or {}
    return (
        meta.get("title_display")
        or meta.get("title")
        or rec.get("title")
        or "(missing title)"
    )


def _topk_titles(q: dict[str, Any], k: int) -> list[str]:
    recs = q.get("recommendations") or []
    return [_rec_title(r) for r in recs[:k]]


def _diag_summary(q: dict[str, Any]) -> str:
    d = q.get("diagnostics") or {}
    parts: list[str] = []

    if "semantic_mode" in d:
        parts.append(f"semantic_mode={d.get('semantic_mode')}")
    if "semantic_confidence_tier" in d:
        parts.append(
            f"sem_conf=({d.get('semantic_confidence_source')}/{d.get('semantic_confidence_tier')}) {d.get('semantic_confidence_score'):.3f}"
        )

    if "seed_has_shounen_demo" in d:
        parts.append(f"seed_has_shounen_demo={d.get('seed_has_shounen_demo')}")
    if "seed_demo_tokens" in d:
        parts.append(f"seed_demo_tokens={d.get('seed_demo_tokens')}")

    if "demo_override_admitted_count" in d:
        parts.append(f"demo_override_admitted={d.get('demo_override_admitted_count')}")
    if "demo_override_used_in_top20_count" in d:
        parts.append(f"demo_override_top20={d.get('demo_override_used_in_top20_count')}")

    if "blocked_due_to_overlap_count" in d:
        parts.append(f"blocked_overlap={d.get('blocked_due_to_overlap_count')}")
    if "blocked_due_to_low_sim_count" in d:
        parts.append(f"blocked_low_sim={d.get('blocked_due_to_low_sim_count')}")

    return ", ".join(parts)


def _print_list(label: str, titles: list[str]) -> None:
    print(label)
    for i, t in enumerate(titles, start=1):
        print(f"  {i:>2}. {t}")


def _set_diff(before: Iterable[str], after: Iterable[str]) -> tuple[list[str], list[str]]:
    b = set(before)
    a = set(after)
    added = sorted(a - b)
    removed = sorted(b - a)
    return added, removed


def main() -> int:
    _stdout_utf8()

    p = argparse.ArgumentParser(description="Diff top-K titles between two golden artifacts")
    p.add_argument("--before", required=True, type=Path)
    p.add_argument("--after", required=True, type=Path)
    p.add_argument("--query", action="append", default=[], help="Query id (repeatable)")
    p.add_argument("--k", type=int, default=20)

    args = p.parse_args()

    before = _load_json(args.before)
    after = _load_json(args.after)

    qids = args.query
    if not qids:
        # Default: compare all query ids present in both.
        before_ids = {q.get("id") for q in before.get("queries", [])}
        after_ids = {q.get("id") for q in after.get("queries", [])}
        qids = sorted(x for x in (before_ids & after_ids) if isinstance(x, str))

    for qid in qids:
        qb = _find_query(before, qid)
        qa = _find_query(after, qid)
        if not qb or not qa:
            print(f"\n== {qid} ==")
            print("  Missing query in before/after artifact")
            continue

        tb = _topk_titles(qb, args.k)
        ta = _topk_titles(qa, args.k)

        overlap = len(set(tb) & set(ta))
        added, removed = _set_diff(tb, ta)

        print(f"\n== {qid} ==")
        print(f"before: {_diag_summary(qb)}")
        print(f"after : {_diag_summary(qa)}")
        print(f"top{args.k} overlap: {overlap}/{args.k}")

        _print_list(f"\nTop {args.k} (before)", tb)
        _print_list(f"\nTop {args.k} (after)", ta)

        print("\nAdded (set diff)")
        for t in added:
            print(f"  + {t}")

        print("\nRemoved (set diff)")
        for t in removed:
            print(f"  - {t}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
