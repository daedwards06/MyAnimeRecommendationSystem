"""Fetch anime metadata from Jikan API with caching, chunking, and progress logging.

Usage (PowerShell):
  python scripts/fetch_jikan.py --ids 1 20 1735
  python scripts/fetch_jikan.py --ids-file data/raw/anime_ids.txt
  python scripts/fetch_jikan.py --season 2025 winter

Features:
- Caches raw JSON in data/raw/jikan/<id>.json
- Throttles requests; retries with backoff on 429/5xx
- Normalizes selected fields into a parquet at data/processed/anime_metadata.parquet
- Supports appending new entries and versioned snapshots via --snapshot-suffix
- Optional chunk processing to respect rate limits and allow resumable batches
- Periodic progress logging with cache-hit/fetch counts and 429 counters
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime, timezone
import random
from pathlib import Path
from typing import Iterable, List, Dict, Any

import httpx
import pandas as pd

BASE_URL = "https://api.jikan.moe/v4"
RAW_DIR = Path("data/raw/jikan")
PROCESSED_PATH = Path("data/processed/anime_metadata.parquet")
DEFAULT_THROTTLE = 0.35  # seconds between successful requests
MAX_RETRIES = 5

FIELDS = [
    "anime_id","title_primary","synopsis","genres","themes","demographics","studios","producers",
    "source_material","episodes","status","aired_from","aired_to","mal_score","mal_rank","mal_popularity","members_count","retrieved_at"
]


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, client: httpx.Client, counters: Dict[str, int] | None = None) -> Dict[str, Any]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.get(url, timeout=30)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "3"))
                if counters is not None:
                    counters["429"] = counters.get("429", 0) + 1
                time.sleep(retry_after)
                continue
            if resp.status_code == 404:
                # Some MAL IDs from historical datasets may no longer exist or be removed.
                # Treat as a non-fatal miss: return empty data and continue.
                if counters is not None:
                    counters["404"] = counters.get("404", 0) + 1
                return {"data": {}}
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            if attempt == MAX_RETRIES:
                raise
            sleep = 2 ** attempt * 0.5
            time.sleep(sleep)
    raise RuntimeError("Unexpected fetch_json loop exit")


def fetch_anime_full(anime_id: int, client: httpx.Client, counters: Dict[str, int] | None = None) -> Dict[str, Any]:
    url = f"{BASE_URL}/anime/{anime_id}/full"
    data = fetch_json(url, client, counters=counters)
    return data.get("data", {})


def normalize_record(anime_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "anime_id": anime_id,
        "title_primary": data.get("title"),
        "synopsis": data.get("synopsis"),
        "genres": [g.get("name") for g in data.get("genres", [])],
        "themes": [t.get("name") for t in data.get("themes", [])],
        "demographics": [d.get("name") for d in data.get("demographics", [])],
        "studios": [s.get("name") for s in data.get("studios", [])],
        "producers": [p.get("name") for p in data.get("producers", [])],
        "source_material": data.get("source"),
        "episodes": data.get("episodes"),
        "status": data.get("status"),
        "aired_from": data.get("aired", {}).get("from"),
        "aired_to": data.get("aired", {}).get("to"),
        "mal_score": data.get("score"),
        "mal_rank": data.get("rank"),
        "mal_popularity": data.get("popularity"),
        "members_count": data.get("members"),
    "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def read_ids_file(path: Path) -> List[int]:
    return [int(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and line.strip().isdigit()]


def fetch_season(year: int, season: str, client: httpx.Client) -> List[int]:
    # season one of: winter, spring, summer, fall
    url = f"{BASE_URL}/seasons/{year}/{season.lower()}"
    data = fetch_json(url, client)
    ids = []
    for item in data.get("data", []):
        mal_id = item.get("mal_id")
        if mal_id is not None:
            ids.append(int(mal_id))
    return ids


def load_existing_processed() -> pd.DataFrame:
    if PROCESSED_PATH.exists():
        try:
            return pd.read_parquet(PROCESSED_PATH)
        except Exception:
            return pd.DataFrame(columns=FIELDS)
    return pd.DataFrame(columns=FIELDS)


def write_snapshot(df: pd.DataFrame, suffix: str | None = None) -> None:
    if suffix:
        snap_path = PROCESSED_PATH.parent / f"anime_metadata_{suffix}.parquet"
        df.to_parquet(snap_path, index=False)
    df.to_parquet(PROCESSED_PATH, index=False)


def write_checkpoint(df: pd.DataFrame) -> None:
    """Write a checkpoint of current combined metadata without creating a versioned snapshot.

    This allows long single-run executions to persist progress periodically.
    """
    df.to_parquet(PROCESSED_PATH, index=False)


def main(argv: Iterable[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch and normalize Jikan anime metadata")
    parser.add_argument("--ids", nargs="*", type=int, help="Anime IDs to fetch")
    parser.add_argument("--ids-file", type=str, help="Path to file containing anime IDs (one per line)")
    parser.add_argument("--season", nargs=2, metavar=("YEAR", "SEASON"), help="Fetch all anime in a given season")
    parser.add_argument("--throttle", type=float, default=DEFAULT_THROTTLE, help="Seconds between requests")
    parser.add_argument("--snapshot-suffix", type=str, help="Optional suffix to write a versioned snapshot file")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore cache and refetch even if raw JSON exists")
    parser.add_argument("--checkpoint-interval", type=int, default=0, help="Every N processed IDs, write a checkpoint to processed parquet (0 disables)")
    parser.add_argument("--chunk-size", type=int, default=0, help="If >0, process only this many IDs after skipping previous chunks")
    parser.add_argument("--chunk-index", type=int, default=0, help="Zero-based chunk index used with --chunk-size")
    parser.add_argument("--log-interval", type=int, default=50, help="Log progress every N processed IDs")

    args = parser.parse_args(list(argv) if argv is not None else None)
    ensure_dirs()

    target_ids: List[int] = []
    if args.ids:
        target_ids.extend(args.ids)
    if args.ids_file:
        target_ids.extend(read_ids_file(Path(args.ids_file)))
    if args.season:
        year = int(args.season[0])
        season = args.season[1]
        with httpx.Client() as client:
            season_ids = fetch_season(year, season, client)
            target_ids.extend(season_ids)

    if not target_ids:
        print("No anime IDs provided. Use --ids, --ids-file or --season.", file=sys.stderr)
        return 1

    # Deduplicate
    target_ids = sorted(set(target_ids))

    # Apply chunk slicing if requested
    if args.chunk_size and args.chunk_size > 0:
        start = args.chunk_size * args.chunk_index
        end = start + args.chunk_size
        total = len(target_ids)
        target_ids = target_ids[start:end]
        print(f"Chunk mode: chunk_size={args.chunk_size} chunk_index={args.chunk_index} -> processing {len(target_ids)} of {total} IDs (range {start}:{end})")

    existing_df = load_existing_processed()
    existing_ids = set(existing_df["anime_id"].astype(int).tolist()) if not existing_df.empty else set()

    records: List[Dict[str, Any]] = []
    counters: Dict[str, int] = {"fetched": 0, "cache_hit": 0, "429": 0, "404": 0}
    with httpx.Client() as client:
        for idx, aid in enumerate(target_ids, start=1):
            raw_path = RAW_DIR / f"{aid}.json"
            data: Dict[str, Any]
            if raw_path.exists() and not args.force_refresh:
                try:
                    data = json.loads(raw_path.read_text(encoding="utf-8")).get("data", {})
                    counters["cache_hit"] += 1
                except json.JSONDecodeError:
                    data = fetch_anime_full(aid, client, counters=counters)
                    counters["fetched"] += 1
            else:
                data = fetch_anime_full(aid, client, counters=counters)
                raw_path.write_text(
                    json.dumps({"retrieved_at": datetime.now(timezone.utc).isoformat(), "data": data}, ensure_ascii=False),
                    encoding="utf-8",
                )
                counters["fetched"] += 1
                # Throttle with small jitter to avoid synchronization
                time.sleep(args.throttle + random.uniform(0, 0.15))
            records.append(normalize_record(aid, data))

            if idx % args.log_interval == 0 or idx == len(target_ids):
                pct = (idx / len(target_ids)) * 100 if target_ids else 0
                print(f"Progress: {idx}/{len(target_ids)} ({pct:0.1f}%) | fetched={counters['fetched']} cache={counters['cache_hit']} 429={counters['429']} 404={counters['404']}")

            # Periodic checkpointing
            if args.checkpoint_interval and (idx % args.checkpoint_interval == 0):
                tmp_df = pd.DataFrame(records)
                combined_tmp = pd.concat([existing_df, tmp_df], ignore_index=True)
                combined_tmp = combined_tmp.drop_duplicates(subset=["anime_id"], keep="last")
                write_checkpoint(combined_tmp)
                print(f"Checkpoint saved at {idx} processed items -> {PROCESSED_PATH}")

    new_df = pd.DataFrame(records)
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["anime_id"], keep="last")

    write_snapshot(combined, args.snapshot_suffix)
    print(f"Run complete. Added/updated {len(records)} records | cumulative {len(combined)} | fetched={counters['fetched']} cache_hits={counters['cache_hit']} 429_responses={counters['429']} 404_missing={counters['404']}")
    if args.snapshot_suffix:
        print(f"Snapshot also written with suffix: {args.snapshot_suffix}")
    if args.chunk_size and args.chunk_size > 0:
        print("Reminder: increment --chunk-index for next batch or remove --chunk-size to process remaining IDs.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
