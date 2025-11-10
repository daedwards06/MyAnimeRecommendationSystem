"""Extract a deduplicated list of anime IDs from raw Kaggle CSVs.

By default, searches data/raw/ for common filenames and column headers.
Supports both Kaggle 2020 schema (anime.csv with MAL_ID) and rating.csv/ratings.csv with anime_id.

Examples (PowerShell):
  python scripts/extract_anime_ids.py --limit 200
  python scripts/extract_anime_ids.py --anime-csv data/raw/anime.csv --ratings-csv data/raw/rating.csv --out data/raw/anime_ids.txt
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from typing import Iterable, Set, Optional

RAW_DIR = Path("data/raw")
DEFAULT_OUT = RAW_DIR / "anime_ids.txt"


def find_default_file(candidates: list[str]) -> Optional[Path]:
    for name in candidates:
        p = RAW_DIR / name
        if p.exists():
            return p
    return None


def read_ids_from_anime_csv(path: Path) -> Set[int]:
    ids: Set[int] = set()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Prefer MAL_ID if present; else fallback to anime_id
        key = None
        headers = [h.strip() for h in reader.fieldnames or []]
        if "MAL_ID" in headers:
            key = "MAL_ID"
        elif "anime_id" in headers:
            key = "anime_id"
        else:
            return ids
        for row in reader:
            val = row.get(key)
            if val is None or val == "":
                continue
            try:
                ids.add(int(val))
            except ValueError:
                continue
    return ids


def read_ids_from_ratings_csv(path: Path) -> Set[int]:
    ids: Set[int] = set()
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = [h.strip() for h in reader.fieldnames or []]
        key = "anime_id" if "anime_id" in headers else None
        if key is None:
            return ids
        for row in reader:
            val = row.get(key)
            if val is None or val == "":
                continue
            try:
                ids.add(int(val))
            except ValueError:
                continue
    return ids


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract anime IDs from raw CSVs")
    parser.add_argument("--anime-csv", type=str, help="Path to anime metadata CSV (e.g., anime.csv)")
    parser.add_argument("--ratings-csv", type=str, help="Path to ratings CSV (e.g., rating.csv or ratings.csv)")
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT), help="Output path for anime_ids.txt")
    parser.add_argument("--limit", type=int, default=0, help="If >0, limit number of IDs written")
    args = parser.parse_args(list(argv) if argv is not None else None)

    anime_csv = Path(args.anime_csv) if args.anime_csv else find_default_file(["anime.csv", "animes.csv"])  # some dumps vary
    ratings_csv = Path(args.ratings_csv) if args.ratings_csv else find_default_file(["rating.csv", "ratings.csv"])  # singular/plural

    if anime_csv is None and ratings_csv is None:
        print("No input files found in data/raw. Provide --anime-csv or --ratings-csv.")
        return 1

    ids: Set[int] = set()
    if anime_csv and anime_csv.exists():
        ids |= read_ids_from_anime_csv(anime_csv)
    if ratings_csv and ratings_csv.exists():
        ids |= read_ids_from_ratings_csv(ratings_csv)

    if not ids:
        print("No anime IDs found. Check CSV headers and paths.")
        return 2

    sorted_ids = sorted(ids)
    if args.limit and args.limit > 0:
        sorted_ids = sorted_ids[: args.limit]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(str(x) for x in sorted_ids), encoding="utf-8")
    print(f"Wrote {len(sorted_ids)} anime IDs to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
