"""Check how populated the `demographics` field is in the main metadata parquet.

Scans `data/processed/anime_metadata.parquet` in batches (so it works even if the
file is large) and reports:
- total rows
- rows with empty/missing demographics
- rows with >=1 demographic label
- distribution of list lengths
- most common labels (presence per anime)

Run:
  C:\\Users\\dedwa\\Anaconda3\\python.exe scripts\\check_demographics_coverage.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def _to_list(val: Any) -> list[str]:
    if val is None:
        return []

    # pyarrow list scalars often show up as python lists already
    if isinstance(val, (list, tuple)):
        return [str(x).strip() for x in val if x is not None and str(x).strip()]

    # pandas/pyarrow may pass strings or other scalars
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        parts = [p.strip() for p in s.split("|")]
        return [p for p in parts if p]

    s = str(val).strip()
    return [s] if s else []


def _iter_demographics_batches(parquet_path: Path, *, batch_size: int = 8192) -> Iterable[list[Any]]:
    try:
        import pyarrow.parquet as pq
    except Exception as e:  # pragma: no cover
        raise RuntimeError("pyarrow is required to scan parquet in batches") from e

    pf = pq.ParquetFile(parquet_path)
    for batch in pf.iter_batches(batch_size=batch_size, columns=["demographics"]):
        col = batch.column(0)
        # Convert to python objects with minimal overhead.
        yield col.to_pylist()


def main() -> int:
    parquet_path = Path("data/processed/anime_metadata.parquet")
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing {parquet_path}")

    total = 0
    nonempty = 0
    empty = 0
    len_counts: Counter[int] = Counter()
    label_presence: Counter[str] = Counter()

    for values in _iter_demographics_batches(parquet_path):
        for v in values:
            total += 1
            lst = _to_list(v)
            n = len(lst)
            len_counts[n] += 1
            if n == 0:
                empty += 1
                continue
            nonempty += 1
            for label in set(lst):
                label_presence[label] += 1

    pct_nonempty = (nonempty / total * 100.0) if total else 0.0
    pct_empty = (empty / total * 100.0) if total else 0.0

    print("Demographics coverage")
    print(f"  total_rows: {total}")
    print(f"  nonempty_rows: {nonempty} ({pct_nonempty:.2f}%)")
    print(f"  empty_or_null_rows: {empty} ({pct_empty:.2f}%)")

    print("\nList length distribution (len -> count)")
    for ln in sorted(len_counts.keys())[:15]:
        print(f"  {ln}: {len_counts[ln]}")
    if len(len_counts) > 15:
        print("  ...")

    print("\nTop demographics labels (presence per anime)")
    for label, cnt in label_presence.most_common(20):
        print(f"  {label}: {cnt} ({(cnt/total*100.0 if total else 0.0):.2f}%)")

    print(f"\nDistinct labels: {len(label_presence)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
