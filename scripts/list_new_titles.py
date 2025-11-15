"""List titles that are new relative to the Kaggle baseline.

This compares processed metadata against baseline anime.csv and prints/saves
the titles that are present in metadata but not in the baseline.

Features:
- Optional substring filter on title (case-insensitive)
- Optional restriction to a provided IDs file (e.g., discovered IDs)
- Sort by members_count (desc) or mal_popularity (rank asc) or aired_from (desc)
- Save full results to CSV while printing a top-N preview

Usage (PowerShell):
  python scripts\list_new_titles.py \
    --baseline data\raw\anime.csv \
    --metadata-path data\processed\anime_metadata.parquet \
    --top-n 50 --sort-by members --out data\reports\new_titles.csv

  # Restrict to discovered IDs and search a substring
  python scripts\list_new_titles.py \
    --baseline data\raw\anime.csv \
    --metadata-path data\processed\anime_metadata_202511_new.parquet \
    --ids-file data\raw\new_anime_ids_20251114.txt \
    --contains "attack" --top-n 25 --sort-by popularity
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Set

import pandas as pd


def load_baseline_ids(path: Path) -> Set[int]:
    df = pd.read_csv(path)
    if "anime_id" not in df.columns:
        raise KeyError(f"Baseline file {path} missing 'anime_id' column")
    ids = pd.to_numeric(df["anime_id"], errors="coerce").dropna().astype(int).unique().tolist()
    return set(ids)


def load_metadata(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    # Ensure core fields exist
    for col in [
        "anime_id",
        "title_primary",
        "title_display",
        "title_english",
        "aired_from",
        "mal_popularity",
        "members_count",
    ]:
        if col not in df.columns:
            df[col] = None
    df["anime_id"] = pd.to_numeric(df["anime_id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["anime_id"]).copy()
    df["anime_id"] = df["anime_id"].astype(int)
    df["aired_from"] = pd.to_datetime(df["aired_from"], errors="coerce")
    return df


def read_ids_file(path: Path | None) -> Set[int]:
    if path is None:
        return set()
    if not path.exists():
        return set()
    ids: List[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            ids.append(int(s))
        except ValueError:
            continue
    return set(ids)


def list_new_titles(
    baseline_path: Path,
    metadata_path: Path,
    ids_file: Path | None,
    contains: str | None,
    sort_by: str,
    top_n: int,
    out_path: Path | None,
) -> None:
    baseline_ids = load_baseline_ids(baseline_path)
    meta = load_metadata(metadata_path)
    restrict_ids = read_ids_file(ids_file)

    # New vs baseline
    df = meta[~meta["anime_id"].isin(baseline_ids)].copy()

    # Restrict to provided IDs if present
    if restrict_ids:
        df = df[df["anime_id"].isin(restrict_ids)].copy()

    # Decide which title to show and filter on
    title_col = "title_display" if "title_display" in df.columns else ("title_english" if "title_english" in df.columns else "title_primary")
    # Substring filter on title
    if contains:
        df = df[df[title_col].fillna("").str.contains(contains, case=False, na=False)]

    # Sorting
    if sort_by == "members":
        df = df.sort_values(["members_count", "title_primary"], ascending=[False, True])
    elif sort_by == "popularity":
        # mal_popularity is rank (lower is more popular)
        df = df.sort_values(["mal_popularity", "title_primary"], ascending=[True, True])
    elif sort_by == "aired":
        df = df.sort_values(["aired_from"], ascending=[False])

    # Print preview
    preview_cols = ["anime_id", title_col, "aired_from", "mal_popularity", "members_count"]
    print(f"[counts] new_vs_baseline={len(df)}")
    print("[preview]")
    print(df[preview_cols].head(top_n).to_string(index=False))

    # Save full results
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"[save] {out_path} ({len(df)} rows)")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="List titles new relative to baseline")
    ap.add_argument("--baseline", type=Path, default=Path("data/raw/anime.csv"))
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"))
    ap.add_argument("--ids-file", type=Path, default=None, help="Optional: restrict results to IDs in this file")
    ap.add_argument("--contains", type=str, default=None, help="Optional: case-insensitive substring to filter title")
    ap.add_argument("--sort-by", type=str, choices=["members", "popularity", "aired"], default="members")
    ap.add_argument("--top-n", type=int, default=50)
    ap.add_argument("--out", type=Path, default=None, help="Optional: path to save the full list as CSV")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    list_new_titles(
        baseline_path=args.baseline,
        metadata_path=args.metadata_path,
        ids_file=args.ids_file,
        contains=args.contains,
        sort_by=args.sort_by,
        top_n=int(args.top_n),
        out_path=args.out,
    )


if __name__ == "__main__":
    main()
