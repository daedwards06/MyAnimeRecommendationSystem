"""Discover MAL IDs for post-snapshot (new) titles via Jikan public endpoints.

This script helps identify anime IDs that are likely missing from your frozen Kaggle snapshot
so you can fetch their metadata (via scripts/fetch_jikan.py) and include them in the candidate set.

Discovery sources (configurable):
- seasons/now           → currently airing
- seasons/upcoming      → upcoming season
- top/anime?page=1..N   → top charts (recent updates bubble up)
- seasons range         → crawl seasons from a start year/season up to current to harvest many recent IDs

Usage (PowerShell):
    python scripts/discover_new_ids.py --baseline data/raw/anime.csv --out data/raw/new_anime_ids_20251114.txt \
            --sources seasons_now seasons_upcoming top --top-pages 5 --throttle 0.70

Example with seasons range from 2020 and auto-cutoff from processed metadata:
    python scripts/discover_new_ids.py --baseline data/raw/anime.csv --out data/raw/new_ids.txt \
            --sources top --top-pages 3 --crawl-seasons-from-year 2020 --use-metadata-cutoff \
            --metadata-path data/processed/anime_metadata.parquet --throttle 0.70

Then fetch metadata for discovered IDs:
  python scripts/fetch_jikan.py --ids-file data/raw/new_anime_ids_20251114.txt --throttle 0.70 --checkpoint-interval 300 --snapshot-suffix 202511_new

Bulk crawl since a fixed year excluding already discovered IDs:
        python scripts/discover_new_ids.py --baseline data/raw/anime.csv --out data/raw/new_since_2019.txt \
                        --crawl-seasons-from-year 2019 --exclude-ids-file data/raw/new_anime_ids_20251114.txt \
                        --exclude-processed --throttle 0.70
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Iterable, Set, List, Tuple, Optional

import httpx
import pandas as pd


API = "https://api.jikan.moe/v4"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Discover likely post-snapshot MAL IDs via Jikan")
    ap.add_argument("--baseline", type=Path, default=Path("data/raw/anime.csv"), help="Kaggle baseline anime.csv")
    ap.add_argument("--out", type=Path, required=True, help="Output file path for discovered IDs (one per line)")
    ap.add_argument(
        "--sources",
        nargs="+",
        default=["seasons_now", "seasons_upcoming", "top"],
        choices=["seasons_now", "seasons_upcoming", "top"],
        help="Discovery sources to use",
    )
    ap.add_argument("--top-pages", type=int, default=5, help="Number of /top/anime pages to crawl if 'top' is selected")
    ap.add_argument("--throttle", type=float, default=0.70, help="Seconds to sleep between requests (polite crawling)")
    ap.add_argument("--max-retries", type=int, default=5, help="Maximum per-request retries on 429/5xx")
    ap.add_argument("--user-agent", type=str, default="MARS/DiscoverNewIds (+https://github.com/daedwards06)", help="HTTP User-Agent header")
    # Seasons range crawling options
    ap.add_argument("--crawl-seasons-from-year", type=int, default=None, help="If set, crawl seasons from this year up to the present")
    ap.add_argument("--from-season", type=str, default=None, choices=["winter", "spring", "summer", "fall"], help="Optional start season when using --crawl-seasons-from-year")
    ap.add_argument("--use-metadata-cutoff", action="store_true", help="Infer start year/season from processed metadata max aired_from for baseline IDs")
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"), help="Processed metadata parquet to compute cutoff")
    ap.add_argument("--exclude-processed", action="store_true", help="Exclude IDs already present in processed metadata")
    ap.add_argument("--exclude-ids-file", type=Path, default=None, help="Optional file of IDs to exclude (e.g., previously discovered new IDs)")
    return ap.parse_args()


def load_baseline_ids(path: Path) -> Set[int]:
    df = pd.read_csv(path)
    if "anime_id" not in df.columns:
        raise KeyError(f"Baseline file {path} missing 'anime_id' column")
    ids = pd.to_numeric(df["anime_id"], errors="coerce").dropna().astype(int).unique().tolist()
    return set(ids)


def load_processed_metadata_ids(path: Path) -> Set[int]:
    if not path.exists():
        return set()
    try:
        df = pd.read_parquet(path)
        if "anime_id" not in df.columns:
            return set()
        ids = pd.to_numeric(df["anime_id"], errors="coerce").dropna().astype(int).unique().tolist()
        return set(ids)
    except Exception:
        return set()


def max_aired_from_for_baseline(metadata_path: Path, baseline_ids: Set[int]) -> Optional[pd.Timestamp]:
    if not metadata_path.exists():
        return None
    try:
        df = pd.read_parquet(metadata_path)
        if "anime_id" not in df.columns or "aired_from" not in df.columns:
            return None
        df = df[df["anime_id"].isin(list(baseline_ids))].copy()
        if df.empty:
            return None
        ts = pd.to_datetime(df["aired_from"], errors="coerce")
        if ts.notna().any():
            return ts.max()
        return None
    except Exception:
        return None


def load_ids_file(path: Path | None) -> Set[int]:
    if path is None or not path.exists():
        return set()
    out: Set[int] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            out.add(int(s))
        except ValueError:
            continue
    return out


def fetch_json(client: httpx.Client, url: str, throttle: float, max_retries: int) -> dict:
    for attempt in range(1, max_retries + 1):
        r = client.get(url, timeout=30)
        if r.status_code in (429, 503):
            retry_after = r.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                time.sleep(int(retry_after))
            else:
                time.sleep(min(5.0, (2 ** attempt) * 0.5))
            continue
        if r.status_code == 404:
            return {"data": []}
        try:
            r.raise_for_status()
            data = r.json()
            time.sleep(throttle)
            return data
        except httpx.HTTPError:
            if attempt >= max_retries:
                raise
            time.sleep(min(5.0, (2 ** attempt) * 0.5))
    raise RuntimeError("fetch_json retry loop exhausted")


def discover_seasons_now(client: httpx.Client, throttle: float, max_retries: int) -> Set[int]:
    data = fetch_json(client, f"{API}/seasons/now", throttle, max_retries)
    items = data.get("data", [])
    return {int(x.get("mal_id")) for x in items if isinstance(x, dict) and x.get("mal_id")}


def discover_seasons_upcoming(client: httpx.Client, throttle: float, max_retries: int) -> Set[int]:
    data = fetch_json(client, f"{API}/seasons/upcoming", throttle, max_retries)
    items = data.get("data", [])
    return {int(x.get("mal_id")) for x in items if isinstance(x, dict) and x.get("mal_id")}


def discover_top(client: httpx.Client, pages: int, throttle: float, max_retries: int) -> Set[int]:
    out: Set[int] = set()
    for p in range(1, max(1, pages) + 1):
        data = fetch_json(client, f"{API}/top/anime?page={p}", throttle, max_retries)
        items = data.get("data", [])
        out.update(int(x.get("mal_id")) for x in items if isinstance(x, dict) and x.get("mal_id"))
    return out


SEASONS_ORDER = ["winter", "spring", "summer", "fall"]


def next_season(year: int, season: str) -> Tuple[int, str]:
    idx = SEASONS_ORDER.index(season)
    if idx == len(SEASONS_ORDER) - 1:
        return year + 1, SEASONS_ORDER[0]
    else:
        return year, SEASONS_ORDER[idx + 1]


def season_from_date(ts: pd.Timestamp) -> Tuple[int, str]:
    # Map month to season (JAN-MAR winter, APR-JUN spring, JUL-SEP summer, OCT-DEC fall)
    m = ts.month
    if m <= 3:
        return ts.year, "winter"
    elif m <= 6:
        return ts.year, "spring"
    elif m <= 9:
        return ts.year, "summer"
    else:
        return ts.year, "fall"


def discover_season(client: httpx.Client, year: int, season: str, throttle: float, max_retries: int) -> Set[int]:
    data = fetch_json(client, f"{API}/seasons/{year}/{season}", throttle, max_retries)
    items = data.get("data", [])
    return {int(x.get("mal_id")) for x in items if isinstance(x, dict) and x.get("mal_id")}


def discover_seasons_range(
    client: httpx.Client,
    start_year: int,
    start_season: str,
    throttle: float,
    max_retries: int,
) -> Set[int]:
    out: Set[int] = set()
    now = pd.Timestamp.utcnow()
    end_year, end_season = season_from_date(now)
    y, s = start_year, start_season
    while True:
        out |= discover_season(client, y, s, throttle, max_retries)
        if (y == end_year) and (s == end_season):
            break
        y, s = next_season(y, s)
    return out


def main() -> None:
    args = parse_args()
    baseline_ids = load_baseline_ids(args.baseline)
    print(f"[info] loaded baseline IDs: {len(baseline_ids)}")
    processed_ids: Set[int] = set()
    if args.exclude_processed or args.use_metadata_cutoff:
        processed_ids = load_processed_metadata_ids(args.metadata_path)
        if processed_ids:
            print(f"[info] loaded processed metadata IDs: {len(processed_ids)}")
    prior_discovered: Set[int] = load_ids_file(args.exclude_ids_file)
    if prior_discovered:
        print(f"[info] loaded prior discovered IDs to exclude: {len(prior_discovered)}")

    discovered: Set[int] = set()
    with httpx.Client(headers={"User-Agent": args.user_agent}) as client:
        if "seasons_now" in args.sources:
            print("[discover] seasons/now")
            discovered |= discover_seasons_now(client, args.throttle, args.max_retries)
        if "seasons_upcoming" in args.sources:
            print("[discover] seasons/upcoming")
            discovered |= discover_seasons_upcoming(client, args.throttle, args.max_retries)
        if "top" in args.sources:
            print(f"[discover] top/anime pages=1..{args.top_pages}")
            discovered |= discover_top(client, args.top_pages, args.throttle, args.max_retries)

        # Seasons range crawling if requested
        start_year: Optional[int] = args.crawl_seasons_from_year
        start_season: Optional[str] = args.from_season
        if args.use_metadata_cutoff:
            cutoff = max_aired_from_for_baseline(args.metadata_path, baseline_ids)
            if cutoff is not None:
                y, s = season_from_date(cutoff)
                # Start from the season AFTER the cutoff
                start_year, start_season = next_season(y, s)
                print(f"[cutoff] metadata-based cutoff at {cutoff.date()} -> starting {start_year} {start_season}")
            else:
                print("[cutoff] no usable cutoff found in metadata; falling back to provided --crawl-seasons-from-year if any")
        if start_year is not None:
            if start_season is None:
                # Default to winter if not specified
                start_season = "winter"
            print(f"[discover] seasons range from {start_year} {start_season} -> now")
            discovered |= discover_seasons_range(client, int(start_year), start_season, args.throttle, args.max_retries)

    # Exclude baseline and optionally already-processed
    exclude_ids = set(baseline_ids)
    if args.exclude_processed and processed_ids:
        exclude_ids |= processed_ids
    if prior_discovered:
        exclude_ids |= prior_discovered
    new_ids = sorted(i for i in discovered if i not in exclude_ids)
    excl_tags = ["baseline"]
    if args.exclude_processed:
        excl_tags.append("processed")
    if prior_discovered:
        excl_tags.append("prior")
    print(f"[result] discovered={len(discovered)}, new_vs_known={len(new_ids)} (excluded {','.join(excl_tags)})")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for i in new_ids:
            f.write(f"{i}\n")
    print(f"[save] {args.out} ({len(new_ids)} ids)")
    print("[next] run fetch_jikan.py with --ids-file on this output to fetch metadata")


if __name__ == "__main__":
    main()
