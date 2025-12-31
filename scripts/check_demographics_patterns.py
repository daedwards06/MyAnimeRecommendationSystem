"""Analyze patterns for rows missing `demographics`.

Compares missing vs present demographics across:
- aired_from year (and decade bins)
- type
- members_count / mal_popularity availability

Run:
  C:\\Users\\dedwa\\Anaconda3\\python.exe scripts\\check_demographics_patterns.py
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def _to_list(val) -> list[str]:
    if val is None:
        return []
    try:
        if pd.isna(val):
            return []
    except Exception:
        pass

    # Common cases when reading parquet:
    # - list/tuple
    # - numpy arrays (including empty arrays)
    # - other iterables
    if isinstance(val, (list, tuple, set, np.ndarray)):
        return [str(x).strip() for x in list(val) if x is not None and str(x).strip()]

    # pyarrow scalars sometimes expose .as_py()
    if hasattr(val, "as_py"):
        try:
            return _to_list(val.as_py())
        except Exception:
            pass

    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        parts = [p.strip() for p in s.split("|")]
        return [p for p in parts if p]

    # Last resort: treat generic iterables (but not strings/dicts) as list-like.
    if isinstance(val, Iterable) and not isinstance(val, (str, bytes, dict)):
        try:
            return [str(x).strip() for x in list(val) if x is not None and str(x).strip()]
        except Exception:
            pass

    s = str(val).strip()
    return [s] if s else []


def _bin_year(y: float | int | None) -> str:
    try:
        if y is None or pd.isna(y):
            return "unknown"
        y = int(y)
    except Exception:
        return "unknown"

    if y < 1970:
        return "<1970"
    if y < 1980:
        return "1970s"
    if y < 1990:
        return "1980s"
    if y < 2000:
        return "1990s"
    if y < 2010:
        return "2000s"
    if y < 2020:
        return "2010s"
    if y < 2030:
        return "2020s"
    return ">=2030"


def main() -> int:
    df = pd.read_parquet(
        "data/processed/anime_metadata.parquet",
        columns=[
            "anime_id",
            "title_display",
            "type",
            "aired_from",
            "episodes",
            "members_count",
            "mal_popularity",
            "demographics",
        ],
    )

    demo_len = df["demographics"].apply(_to_list).apply(len)
    missing = demo_len.eq(0)

    df = df.copy()
    df["_demo_missing"] = missing

    aired = pd.to_datetime(df["aired_from"], errors="coerce", utc=True)
    df["_year"] = aired.dt.year
    df["_year_bin"] = df["_year"].apply(_bin_year)

    total = int(len(df))
    miss = int(df["_demo_missing"].sum())
    present = total - miss

    print("Overall")
    print(f"  total_rows: {total}")
    print(f"  missing_demographics: {miss} ({(miss/total*100 if total else 0):.2f}%)")
    print(f"  present_demographics: {present} ({(present/total*100 if total else 0):.2f}%)")

    # --- Year/decade patterns ---
    print("\nMissing rate by year bin")
    g = df.groupby("_year_bin", dropna=False)["_demo_missing"].agg(["count", "sum"]).rename(columns={"sum": "missing"})
    g["missing_rate"] = g["missing"] / g["count"]
    g = g.sort_values(["missing_rate", "count"], ascending=[False, False])
    for idx, r in g.iterrows():
        print(f"  {idx:8s}  count={int(r['count']):5d}  missing={int(r['missing']):5d}  rate={float(r['missing_rate'])*100:6.2f}%")

    print("\nMissing rate by year (top 15 years by count)")
    yg = df.dropna(subset=["_year"]).groupby(df["_year"].astype("Int64"))["_demo_missing"].agg(["count", "sum"]).rename(columns={"sum": "missing"})
    yg["missing_rate"] = yg["missing"] / yg["count"]
    yg = yg.sort_values("count", ascending=False).head(15)
    for year, r in yg.iterrows():
        print(f"  {int(year)}  count={int(r['count']):5d}  missing={int(r['missing']):5d}  rate={float(r['missing_rate'])*100:6.2f}%")

    # Specific question: after 2020?
    after_2020 = df[df["_year"].fillna(0).astype(int) >= 2020]
    if len(after_2020) > 0:
        m = int(after_2020["_demo_missing"].sum())
        t = int(len(after_2020))
        print("\nCohort: aired_from >= 2020")
        print(f"  rows: {t}")
        print(f"  missing_demographics: {m} ({(m/t*100 if t else 0):.2f}%)")

    # --- Type patterns ---
    print("\nMissing rate by type")
    tg = df.groupby(df["type"].fillna("unknown"))["_demo_missing"].agg(["count", "sum"]).rename(columns={"sum": "missing"})
    tg["missing_rate"] = tg["missing"] / tg["count"]
    tg = tg.sort_values(["missing_rate", "count"], ascending=[False, False])
    for t, r in tg.head(20).iterrows():
        print(f"  {str(t):10s}  count={int(r['count']):5d}  missing={int(r['missing']):5d}  rate={float(r['missing_rate'])*100:6.2f}%")

    # --- Metadata completeness / popularity proxies ---
    def pct_missing_col(col: str) -> None:
        s = df[col]
        is_missing = s.isna()
        g = df.groupby("_demo_missing", dropna=False)[col].apply(lambda x: float(x.isna().mean()))
        miss_rate_if_missing_demo = float(g.get(True, 0.0))
        miss_rate_if_present_demo = float(g.get(False, 0.0))
        print(f"  {col}: pct-null when demo-missing={miss_rate_if_missing_demo*100:.2f}% vs demo-present={miss_rate_if_present_demo*100:.2f}%")

    print("\nNull-rate comparisons (higher => generally less complete rows)")
    for col in ["members_count", "mal_popularity", "episodes", "type", "aired_from", "title_display"]:
        pct_missing_col(col)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
