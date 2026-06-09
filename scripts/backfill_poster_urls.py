"""Backfill the ``poster_url`` (remote CDN) field on the processed metadata.

The app prefers a local thumbnail (``data/processed/images/posters/*_thumb.webp``)
but falls back to the remote ``poster_url`` when the thumbnail is not shipped
(slim deployments — see ``src/app/components/cards.py``). Items whose thumbnails
were populated by the disk-based repair path never received a ``poster_url``,
so this script fills it from the cached Jikan responses in ``data/raw/jikan``.

Run:
    python scripts/backfill_poster_urls.py
    python scripts/backfill_poster_urls.py --dry-run
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

PROCESSED_PATH = Path("data/processed/anime_metadata.parquet")
JIKAN_CACHE_DIR = Path("data/raw/jikan")


def poster_url_from_cache(anime_id: int) -> str | None:
    """Return the best remote poster URL from the cached Jikan record, or None."""
    path = JIKAN_CACHE_DIR / f"{anime_id}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    images = data.get("images", {}) or {}
    webp = images.get("webp", {}) if isinstance(images, dict) else {}
    jpg = images.get("jpg", {}) if isinstance(images, dict) else {}
    # Prefer larger / webp for quality, matching scripts/enrich_images.py.
    candidates = [
        webp.get("large_image_url"),
        jpg.get("large_image_url"),
        webp.get("image_url"),
        jpg.get("image_url"),
        webp.get("small_image_url"),
        jpg.get("small_image_url"),
    ]
    return next((c for c in candidates if isinstance(c, str) and c.startswith("http")), None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report coverage without writing.")
    args = parser.parse_args()

    if not PROCESSED_PATH.exists():
        raise SystemExit(f"Metadata parquet not found: {PROCESSED_PATH}")

    df = pd.read_parquet(PROCESSED_PATH)
    if "poster_url" not in df.columns:
        df["poster_url"] = None

    def is_usable(v: object) -> bool:
        return isinstance(v, str) and v.startswith("http")

    before = int(df["poster_url"].apply(is_usable).sum())
    filled = 0
    for pos, anime_id in enumerate(df["anime_id"].astype(int)):
        if is_usable(df.iat[pos, df.columns.get_loc("poster_url")]):
            continue
        url = poster_url_from_cache(int(anime_id))
        if url:
            df.iat[pos, df.columns.get_loc("poster_url")] = url
            filled += 1

    after = int(df["poster_url"].apply(is_usable).sum())
    n = len(df)
    print(f"rows={n}")
    print(f"poster_url usable before: {before} ({100 * before / n:.1f}%)")
    print(f"poster_url filled from cache: {filled}")
    print(f"poster_url usable after:  {after} ({100 * after / n:.1f}%)")

    if args.dry_run:
        print("[dry-run] no changes written")
        return

    if filled:
        df.to_parquet(PROCESSED_PATH, index=False)
        print(f"wrote {PROCESSED_PATH}")
    else:
        print("nothing to fill; parquet unchanged")


if __name__ == "__main__":
    main()
