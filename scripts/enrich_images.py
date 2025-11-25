"""Enrich anime metadata with poster image thumbnails from Jikan.

Scaffold script: fetches poster URLs, downloads original images (if missing or expired),
creates resized thumbnails, and updates processed metadata parquet with new fields.

Usage (PowerShell):
  python scripts/enrich_images.py --age-threshold-days 30 --limit 500
  python scripts/enrich_images.py --force-refresh --ids-file data/raw/anime_ids.txt

This script is intentionally minimal; production refinements (parallelism,
robust retries, palette extraction) can be added later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, List, Dict, Any

import httpx
import socket
import os
import pandas as pd

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover
    Image = None  # type: ignore

BASE_URL = "https://api.jikan.moe/v4"
PROCESSED_PATH = Path("data/processed/anime_metadata.parquet")
IMAGES_DIR = Path("data/processed/images/posters")
FIELDS_NEW = [
    "poster_url",
    "poster_thumb_url",
    "image_last_fetched",
    "image_attribution",
    "image_md5",
]
DEFAULT_THROTTLE = 0.75
MAX_RETRIES = 4
CONNECT_BACKOFF_BASE = 1.5
THUMB_WIDTH = 180


def ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_metadata() -> pd.DataFrame:
    if PROCESSED_PATH.exists():
        try:
            return pd.read_parquet(PROCESSED_PATH)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_metadata(df: pd.DataFrame) -> None:
    df.to_parquet(PROCESSED_PATH, index=False)


def repair_from_files(df: pd.DataFrame) -> pd.DataFrame:
    """Repair metadata from existing files on disk.

    - Detect thumbnails in `IMAGES_DIR/*_thumb.webp`
    - If present, set `poster_thumb_url` relative path
    - If matching original exists, compute md5 and set `image_md5`
    - Set `image_last_fetched` from file mtime (UTC ISO)
    - Ensure `image_attribution` is populated
    """
    if df.empty:
        return df
    thumb_files = list(IMAGES_DIR.glob("*_thumb.webp"))
    if not thumb_files:
        return df
    existing = df.set_index("anime_id")
    for tf in thumb_files:
        stem = tf.name.replace("_thumb.webp", "")
        if not stem.isdigit():
            continue
        aid = int(stem)
        rel = tf.relative_to(PROCESSED_PATH.parent).as_posix()
        if aid not in existing.index:
            continue
        # Update fields
        existing.at[aid, "poster_thumb_url"] = rel
        # Attribution default
        if pd.isna(existing.at[aid, "image_attribution"]) if "image_attribution" in existing.columns else True:
            existing.loc[aid, "image_attribution"] = "Images via Jikan / MyAnimeList"
        # mtime as last fetched
        try:
            mtime = datetime.fromtimestamp(tf.stat().st_mtime, tz=timezone.utc).isoformat()
            existing.loc[aid, "image_last_fetched"] = mtime
        except Exception:
            pass
        # md5 from original if available
        orig = IMAGES_DIR / f"{aid}_orig"
        if orig.exists():
            try:
                existing.loc[aid, "image_md5"] = hash_bytes(orig.read_bytes())
            except Exception:
                pass
    return existing.reset_index()


def fetch_full(anime_id: int, client: httpx.Client) -> Dict[str, Any]:
    """Fetch full anime record with resilient retry/backoff.

    Gracefully handles transient DNS / connect errors by exponential backoff
    and returns an empty dict on persistent failure instead of aborting the run.
    """
    url = f"{BASE_URL}/anime/{anime_id}/full"
    import time as _t, random as _r
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.get(url, timeout=30)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", "2"))
                _t.sleep(wait + _r.uniform(0, 0.25))
                continue
            if resp.status_code == 404:
                return {}
            resp.raise_for_status()
            return resp.json().get("data", {})
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:
            backoff = CONNECT_BACKOFF_BASE ** attempt + _r.uniform(0, 0.5)
            print(f"[warn] connect/read error anime_id={anime_id} attempt={attempt}/{MAX_RETRIES}: {e} -> backoff {backoff:0.2f}s")
            _t.sleep(backoff)
        except httpx.HTTPError as e:
            # Other HTTP errors (e.g. 5xx) -> short backoff then retry
            backoff = 0.75 * attempt + _r.uniform(0, 0.5)
            if attempt == MAX_RETRIES:
                print(f"[warn] persistent HTTP error anime_id={anime_id}: {e} -> giving up")
                return {}
            print(f"[warn] http error anime_id={anime_id} attempt={attempt}/{MAX_RETRIES}: {e} -> backoff {backoff:0.2f}s")
            _t.sleep(backoff)
    return {}


def extract_image_info(data: Dict[str, Any]) -> Dict[str, Any]:
    images = data.get("images", {}) or {}
    # Prefer larger images for better quality (webp large > jpg large > fallback to standard)
    webp = images.get("webp", {}) if isinstance(images, dict) else {}
    jpg = images.get("jpg", {}) if isinstance(images, dict) else {}
    # candidate order: prioritize large_image_url for better quality
    candidates = [
        webp.get("large_image_url"),
        jpg.get("large_image_url"),
        webp.get("image_url"),
        jpg.get("image_url"),
        webp.get("small_image_url"),
        jpg.get("small_image_url"),
    ]
    poster_url = next((c for c in candidates if c), None)
    return {
        "poster_url": poster_url,
        "image_attribution": "Images via Jikan / MyAnimeList",
    }


def download_image(url: str, dest: Path) -> Path | None:
    if not url:
        return None
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=30)
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "")
            if not ctype.startswith("image"):
                return None
            dest.write_bytes(resp.content)
            return dest
    except Exception:
        return None


def make_thumbnail(src: Path, dest: Path, width: int = THUMB_WIDTH) -> Path | None:
    if Image is None or not src.exists():
        return None
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w > width:
                ratio = width / float(w)
                new_size = (width, int(h * ratio))
                im = im.resize(new_size)
            im.save(dest, format="WEBP", quality=85, method=6)
            return dest
    except Exception:
        return None


def hash_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def process_record(row: Dict[str, Any], client: httpx.Client, age_threshold: int, force: bool) -> Dict[str, Any]:
    anime_id = int(row.get("anime_id"))
    existing_last = row.get("image_last_fetched")
    needs_refresh = True
    if existing_last and not force:
        try:
            last_dt = datetime.fromisoformat(str(existing_last))
            if datetime.now(timezone.utc) - last_dt < timedelta(days=age_threshold):
                needs_refresh = False
        except Exception:
            pass
    poster_url = row.get("poster_url") if not needs_refresh else None
    image_md5 = row.get("image_md5")

    if needs_refresh:
        data = fetch_full(anime_id, client)
        info = extract_image_info(data)
        poster_url = info.get("poster_url")
        attribution = info.get("image_attribution")
    else:
        attribution = row.get("image_attribution")

    thumb_rel = None
    if poster_url:
        original_path = IMAGES_DIR / f"{anime_id}_orig"
        thumb_path = IMAGES_DIR / f"{anime_id}_thumb.webp"
        downloaded = download_image(poster_url, original_path)
        if downloaded is not None:
            # hash & thumbnail
            data_bytes = downloaded.read_bytes()
            image_md5 = hash_bytes(data_bytes)
            thumb_out = make_thumbnail(downloaded, thumb_path)
            if thumb_out is not None:
                thumb_rel = thumb_out.relative_to(PROCESSED_PATH.parent).as_posix()
    return {
        "poster_url": poster_url,
        "poster_thumb_url": thumb_rel,
        "image_last_fetched": datetime.now(timezone.utc).isoformat(),
        "image_attribution": attribution,
        "image_md5": image_md5,
    }


def main(argv: Iterable[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Enrich metadata with poster images & thumbnails")
    parser.add_argument("--ids", nargs="*", type=int, help="Explicit anime IDs to process (override metadata list)")
    parser.add_argument("--ids-file", type=str, help="File containing anime IDs (one per line)")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N IDs (0 = all)")
    parser.add_argument("--age-threshold-days", type=int, default=30, help="Days before refetching an existing image")
    parser.add_argument("--force-refresh", action="store_true", help="Ignore age threshold and refetch all")
    parser.add_argument("--log-interval", type=int, default=50, help="Progress log interval")
    parser.add_argument("--throttle", type=float, default=DEFAULT_THROTTLE, help="Delay between remote fetches")
    parser.add_argument("--chunk-size", type=int, default=0, help="If >0, process IDs in chunks of this size (use with --chunk-index)")
    parser.add_argument("--chunk-index", type=int, default=0, help="Zero-based chunk index when using --chunk-size")
    parser.add_argument("--skip-existing", action="store_true", help="Skip rows that already have a thumbnail (unless --force-refresh)")
    parser.add_argument("--checkpoint-interval", type=int, default=250, help="Write incremental progress every N processed IDs to avoid large-loss on failure")
    parser.add_argument("--repair-from-files", action="store_true", help="Scan image folder to backfill metadata for already-downloaded thumbnails")
    parser.add_argument("--repair-only", action="store_true", help="Run repair step and exit without any network calls")

    args = parser.parse_args(list(argv) if argv is not None else None)
    ensure_dirs()

    df = load_metadata()
    if df.empty and not args.ids and not args.ids_file:
        print("No metadata available and no explicit IDs provided.", file=sys.stderr)
        return 1

    # Optional repair step before any network work
    if args.repair_from_files:
        before = int(df["poster_thumb_url"].notna().sum()) if "poster_thumb_url" in df.columns else 0
        df = repair_from_files(df)
        after = int(df["poster_thumb_url"].notna().sum()) if "poster_thumb_url" in df.columns else 0
        if after > before:
            save_metadata(df)
        print(f"Repair-from-files complete: restored {after - before} thumbnails (now {after} present)")
        if args.repair_only:
            return 0

    id_source: List[int] = []
    if args.ids:
        id_source.extend(args.ids)
    if args.ids_file:
        path = Path(args.ids_file)
        if path.exists():
            id_source.extend([int(l.strip()) for l in path.read_text(encoding="utf-8").splitlines() if l.strip().isdigit()])
    if not id_source:
        id_source = [int(x) for x in df["anime_id"].tolist()]
    id_source = sorted(set(id_source))
    if args.limit and args.limit > 0:
        id_source = id_source[: args.limit]

    # Chunk slicing (optional) -------------------------------------------------
    if args.chunk_size and args.chunk_size > 0:
        start = args.chunk_size * args.chunk_index
        end = start + args.chunk_size
        total = len(id_source)
        id_source = id_source[start:end]
        print(f"Chunk mode: chunk_size={args.chunk_size} chunk_index={args.chunk_index} -> processing {len(id_source)} of {total} IDs (range {start}:{end})")

    updated_rows: List[Dict[str, Any]] = []
    counters = {"fetched": 0, "skipped": 0}
    import time as _t

    with httpx.Client(headers={"User-Agent": "MyAnimeRecommendationSystem/0.1"}) as client:
        for idx, aid in enumerate(id_source, start=1):
            existing_row = df.loc[df["anime_id"] == aid].to_dict(orient="records")
            base_row = existing_row[0] if existing_row else {"anime_id": aid}

            # Optional skip if already enriched and not forcing refresh
            if args.skip_existing and not args.force_refresh and base_row.get("poster_thumb_url"):
                counters["skipped"] += 1
                if idx % args.log_interval == 0 or idx == len(id_source):
                    pct = idx / len(id_source) * 100
                    print(f"Progress: {idx}/{len(id_source)} ({pct:0.1f}%) fetched={counters['fetched']} skipped={counters['skipped']} (skipped existing)")
                continue

            enriched = process_record(base_row, client, age_threshold=args.age_threshold_days, force=args.force_refresh)
            base_row.update(enriched)
            updated_rows.append(base_row)
            if enriched.get("poster_url"):
                counters["fetched"] += 1
            else:
                counters["skipped"] += 1
            if idx % args.log_interval == 0 or idx == len(id_source):
                pct = idx / len(id_source) * 100
                print(f"Progress: {idx}/{len(id_source)} ({pct:0.1f}%) fetched={counters['fetched']} skipped={counters['skipped']}")
            # Periodic checkpoint save -------------------------------------------------
            if args.checkpoint_interval and idx % args.checkpoint_interval == 0:
                checkpoint_df = pd.DataFrame(updated_rows)
                if not checkpoint_df.empty:
                    existing = df.set_index("anime_id")
                    enriched_partial = checkpoint_df.set_index("anime_id")
                    for col in enriched_partial.columns:
                        if col not in existing.columns:
                            existing[col] = None
                    existing.update(enriched_partial)
                    new_ids = enriched_partial.index.difference(existing.index)
                    if len(new_ids) > 0:
                        existing = pd.concat([existing, enriched_partial.loc[new_ids]], axis=0)
                    df = existing.reset_index()
                    save_metadata(df)
                    print(f"[checkpoint] saved after {idx} processed (fetched={counters['fetched']} skipped={counters['skipped']})")
                    updated_rows = []  # clear buffer after checkpoint merge
            # Throttle with slight jitter to avoid synchronization bursts
            import random as _r
            _t.sleep(args.throttle + _r.uniform(0, 0.12))

    updated_df = pd.DataFrame(updated_rows)
    # Correct merge logic: preserve all original rows and update/enrich matching anime_id entries.
    if df.empty:
        merged = updated_df
    else:
        # Set indices for update operation
        existing = df.set_index("anime_id")
        enriched = updated_df.set_index("anime_id")
        # Add any new columns to existing
        for col in enriched.columns:
            if col not in existing.columns:
                existing[col] = None
        # Update existing rows with enriched values
        existing.update(enriched)
        # Include any new anime IDs not previously present
        new_ids = enriched.index.difference(existing.index)
        if len(new_ids) > 0:
            existing = pd.concat([existing, enriched.loc[new_ids]], axis=0)
        merged = existing.reset_index()

    save_metadata(merged)
    print(f"Image enrichment complete. processed={len(id_source)} fetched={counters['fetched']} skipped={counters['skipped']} -> {PROCESSED_PATH} | total_rows={len(merged)}")
    if args.chunk_size and args.chunk_size > 0:
        print("Reminder: increment --chunk-index for next batch or remove --chunk-size to process remaining IDs.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
