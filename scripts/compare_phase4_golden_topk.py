"""Compare top-k results for specific queries across two Phase 4 golden JSON artifacts.

Usage:
  python scripts/compare_phase4_golden_topk.py \
    --before reports/artifacts/phase4_golden_queries_YYYYMMDDHHMMSS.json \
    --after  reports/artifacts/phase4_golden_queries_YYYYMMDDHHMMSS.json \
        --query one_piece --query tokyo_ghoul --k 20

To print a clean side-by-side diff table:
    python scripts/compare_phase4_golden_topk.py \
        --before reports/artifacts/phase4_golden_queries_YYYYMMDDHHMMSS.json \
        --after  reports/artifacts/phase4_golden_queries_YYYYMMDDHHMMSS.json \
        --query cowboy_bebop --k 10 --side-by-side
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pick_query(doc: Any, query_id: str) -> dict[str, Any]:
    if isinstance(doc, dict):
        for key in ("queries", "items", "results", "golden_queries"):
            v = doc.get(key)
            if isinstance(v, list):
                for q in v:
                    if not isinstance(q, dict):
                        continue
                    qid = q.get("query_id")
                    if qid is None:
                        qid = q.get("id")
                    if qid == query_id:
                        return q
        v = doc.get(query_id)
        if isinstance(v, dict):
            return v
    raise KeyError(f"query_id not found: {query_id}")


def _extract_recs(q: dict[str, Any]) -> list[Any]:
    for key in ("topk", "recommendations", "results", "top", "ranked"):
        v = q.get(key)
        if isinstance(v, list):
            return v

    for v in q.values():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "anime_id" in v[0]:
            return v

    raise KeyError("could not find recommendations list")


def _extract_topk(q: dict[str, Any], k: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    recs = _extract_recs(q)
    for rank, r in enumerate(recs[:k], start=1):
        if isinstance(r, dict):
            out.append(
                {
                    "rank": r.get("rank", rank),
                    "anime_id": r.get("anime_id"),
                    "title": r.get("title") or r.get("name"),
                    "type": r.get("type"),
                }
            )
        else:
            out.append({"rank": rank, "value": r})
    return out


def _get_violation_count(q: dict[str, Any]) -> int | None:
    for key in ("violation_count",):
        v = q.get(key)
        if isinstance(v, int):
            return v

    for key in ("violations", "hygiene_violations"):
        v = q.get(key)
        if isinstance(v, list):
            return len(v)

    d = q.get("diagnostics")
    if isinstance(d, dict) and isinstance(d.get("violation_count"), int):
        return int(d["violation_count"])

    return None


def _get_semantic_mode(q: dict[str, Any]) -> str | None:
    d = q.get("diagnostics")
    if isinstance(d, dict):
        v = d.get("semantic_mode")
        if isinstance(v, str):
            return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--query", action="append", required=True)
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument(
        "--side-by-side",
        action="store_true",
        help="Print a rank-aligned before/after table (clean diff view).",
    )
    ap.add_argument(
        "--metadata",
        default="data/processed/anime_metadata.parquet",
        help="Path to processed anime metadata parquet for title/type lookup.",
    )
    args = ap.parse_args()

    before = _load_json(args.before)
    after = _load_json(args.after)

    meta = pd.read_parquet(args.metadata)
    # Use display title when available, fallback to primary.
    meta_title = (
        meta["title_display"].fillna("").where(meta["title_display"].notna(), "")
    )
    title_map = dict(zip(meta["anime_id"].astype(int), meta_title.where(meta_title != "", meta["title_primary"]).tolist()))
    type_map = dict(zip(meta["anime_id"].astype(int), meta.get("type").tolist()))

    for qid in args.query:
        qb = _pick_query(before, qid)
        qa = _pick_query(after, qid)

        print(f"\n=== {qid} ===")
        print(f"before violation_count: {_get_violation_count(qb)} mode: {_get_semantic_mode(qb)}")
        print(f"after  violation_count: {_get_violation_count(qa)} mode: {_get_semantic_mode(qa)}")

        if args.side_by_side:
            b = _extract_topk(qb, args.k)
            a = _extract_topk(qa, args.k)
            rows: list[dict[str, Any]] = []
            for i in range(args.k):
                rb = b[i] if i < len(b) else {}
                ra = a[i] if i < len(a) else {}

                bid = rb.get("anime_id")
                aid = ra.get("anime_id")

                bid_int = int(bid) if bid is not None else None
                aid_int = int(aid) if aid is not None else None

                btitle = rb.get("title") or (title_map.get(bid_int) if bid_int is not None else None)
                atitle = ra.get("title") or (title_map.get(aid_int) if aid_int is not None else None)
                btype = rb.get("type") or (type_map.get(bid_int) if bid_int is not None else None)
                atype = ra.get("type") or (type_map.get(aid_int) if aid_int is not None else None)

                rows.append(
                    {
                        "rank": i + 1,
                        "before_id": bid,
                        "before_type": btype,
                        "before_title": btitle,
                        "after_id": aid,
                        "after_type": atype,
                        "after_title": atitle,
                        "changed": bool(bid != aid),
                    }
                )

            df = pd.DataFrame(rows)
            print("\n-- side-by-side top{k} --".format(k=args.k))
            print(df.to_string(index=False))
            continue

        print("\n-- before top{k} --".format(k=args.k))
        for r in _extract_topk(qb, args.k):
            if "anime_id" in r:
                aid = r.get("anime_id")
                aid_int = int(aid) if aid is not None else None
                title = r.get("title") or (title_map.get(aid_int) if aid_int is not None else None)
                atype = r.get("type") or (type_map.get(aid_int) if aid_int is not None else None)
                print(r["rank"], aid, atype, title)
            else:
                print(r["rank"], r.get("value"))

        print("\n-- after top{k} --".format(k=args.k))
        for r in _extract_topk(qa, args.k):
            if "anime_id" in r:
                aid = r.get("anime_id")
                aid_int = int(aid) if aid is not None else None
                title = r.get("title") or (title_map.get(aid_int) if aid_int is not None else None)
                atype = r.get("type") or (type_map.get(aid_int) if aid_int is not None else None)
                print(r["rank"], aid, atype, title)
            else:
                print(r["rank"], r.get("value"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
