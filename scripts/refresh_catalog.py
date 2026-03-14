"""End-to-end catalog refresh: discover new anime, fetch metadata, rebuild all artifacts.

Chains the individual pipeline scripts in the correct order so that new anime
(e.g. a freshly-aired 2026 season) are fully integrated into the recommendation
system with a single command.

Usage (PowerShell):
  # Full refresh — discover + fetch + rebuild everything:
  python scripts/refresh_catalog.py

  # Fetch a specific season only (skip discover):
  python scripts/refresh_catalog.py --season 2026 winter

  # Fetch specific IDs only:
  python scripts/refresh_catalog.py --ids 12345 67890

  # Skip model retraining (metadata + features only):
  python scripts/refresh_catalog.py --skip-models

  # Skip synopsis artifact rebuild:
  python scripts/refresh_catalog.py --skip-synopsis

  # Skip image enrichment:
  python scripts/refresh_catalog.py --skip-images

Steps executed (in order):
  1. Discover new IDs       (scripts/discover_new_ids.py)   [unless --season/--ids given]
  2. Fetch Jikan metadata   (scripts/fetch_jikan.py)
  3. Rebuild features       (scripts/build_features.py)
  4. Rebuild synopsis TF-IDF artifact
  5. Rebuild synopsis embeddings artifact
  6. Retrain CF models      (scripts/save_artifacts.py)     [unless --skip-models]
  7. Enrich images          (scripts/enrich_images.py)      [unless --skip-images]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _run(label: str, cmd: list[str], *, required: bool = True) -> bool:
    """Run a subprocess, print status, return True on success."""
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"  STEP: {label}")
    print(f"  CMD:  {' '.join(cmd)}")
    print(separator)

    result = subprocess.run(cmd, cwd=str(ROOT))

    if result.returncode != 0:
        status = "FAILED" if required else "SKIPPED (non-critical)"
        print(f"  >> {label}: {status} (exit code {result.returncode})")
        if required:
            return False
    else:
        print(f"  >> {label}: OK")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="End-to-end catalog refresh pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--season", nargs=2, metavar=("YEAR", "SEASON"),
                        help="Fetch a specific season (e.g. 2026 winter) instead of discovering")
    parser.add_argument("--ids", nargs="*", type=int,
                        help="Fetch specific anime IDs instead of discovering")
    parser.add_argument("--skip-models", action="store_true",
                        help="Skip CF model retraining")
    parser.add_argument("--skip-synopsis", action="store_true",
                        help="Skip synopsis artifact rebuild")
    parser.add_argument("--skip-images", action="store_true",
                        help="Skip image enrichment")
    parser.add_argument("--throttle", type=float, default=0.70,
                        help="Seconds between Jikan API requests (default: 0.70)")
    parser.add_argument("--checkpoint-interval", type=int, default=300,
                        help="Checkpoint interval for fetch_jikan (default: 300)")
    args = parser.parse_args()

    py = sys.executable
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    snapshot_suffix = datetime.now(timezone.utc).strftime("%Y%m")
    steps_ok: list[str] = []
    steps_fail: list[str] = []
    t0 = time.monotonic()

    # ── Step 1: Discover or resolve target IDs ─────────────────────────────
    ids_file: str | None = None

    if args.ids:
        # User provided explicit IDs — write to a temp file for fetch_jikan
        ids_file = str(ROOT / "data" / "raw" / f"refresh_ids_{ts}.txt")
        Path(ids_file).parent.mkdir(parents=True, exist_ok=True)
        Path(ids_file).write_text(
            "\n".join(str(i) for i in args.ids), encoding="utf-8"
        )
        print(f"Using {len(args.ids)} user-provided IDs → {ids_file}")
        steps_ok.append("Resolve IDs")

    elif args.season:
        # Season mode — fetch_jikan handles discovery internally
        print(f"Season mode: {args.season[0]} {args.season[1]}")
        steps_ok.append("Resolve season")

    else:
        # Full discovery
        ids_file = str(ROOT / "data" / "raw" / f"new_anime_ids_{ts}.txt")
        ok = _run("Discover new IDs", [
            py, str(SCRIPTS / "discover_new_ids.py"),
            "--baseline", str(ROOT / "data" / "raw" / "anime.csv"),
            "--out", ids_file,
            "--sources", "seasons_now", "seasons_upcoming", "top",
            "--top-pages", "5",
            "--exclude-processed",
        ])
        if ok:
            # Report count
            try:
                count = sum(1 for line in Path(ids_file).read_text(encoding="utf-8").splitlines() if line.strip())
                print(f"  Discovered {count} new IDs")
            except Exception:
                count = -1
            steps_ok.append("Discover new IDs")
            if count == 0:
                print("  No new IDs found. Skipping fetch, proceeding to rebuild.")
                ids_file = None  # signal to skip fetch
        else:
            steps_fail.append("Discover new IDs")
            print("Discovery failed. Aborting.")
            return 1

    # ── Step 2: Fetch metadata from Jikan ──────────────────────────────────
    skip_fetch = not args.season and not args.ids and ids_file is None
    if skip_fetch:
        print("\n  No new IDs to fetch. Skipping Jikan fetch step.")
        steps_ok.append("Fetch Jikan metadata (skipped — nothing new)")
    else:
        fetch_cmd = [
            py, str(SCRIPTS / "fetch_jikan.py"),
            "--throttle", str(args.throttle),
            "--checkpoint-interval", str(args.checkpoint_interval),
            "--snapshot-suffix", snapshot_suffix,
        ]
        if args.season:
            fetch_cmd += ["--season", args.season[0], args.season[1]]
        elif ids_file:
            fetch_cmd += ["--ids-file", ids_file]

        ok = _run("Fetch Jikan metadata", fetch_cmd)
        (steps_ok if ok else steps_fail).append("Fetch Jikan metadata")
        if not ok:
            print("Fetch failed. Aborting.")
            return 1

    # ── Step 3: Rebuild features ───────────────────────────────────────────
    ok = _run("Build features", [py, str(SCRIPTS / "build_features.py")])
    (steps_ok if ok else steps_fail).append("Build features")
    if not ok:
        print("Feature build failed. Aborting.")
        return 1

    # ── Step 4–5: Synopsis artifacts ───────────────────────────────────────
    if not args.skip_synopsis:
        ok = _run("Build synopsis TF-IDF artifact", [
            py, str(SCRIPTS / "build_synopsis_tfidf_artifact.py"),
        ])
        (steps_ok if ok else steps_fail).append("Synopsis TF-IDF")

        ok = _run("Build synopsis embeddings artifact", [
            py, str(SCRIPTS / "build_synopsis_embeddings_artifact.py"),
        ])
        (steps_ok if ok else steps_fail).append("Synopsis embeddings")
    else:
        print("\n  Skipping synopsis artifacts (--skip-synopsis)")

    # ── Step 6: Retrain CF models ──────────────────────────────────────────
    if not args.skip_models:
        ok = _run("Retrain CF models", [py, str(SCRIPTS / "save_artifacts.py")])
        (steps_ok if ok else steps_fail).append("Retrain CF models")
    else:
        print("\n  Skipping model retraining (--skip-models)")

    # ── Step 7: Enrich images ──────────────────────────────────────────────
    if not args.skip_images:
        ok = _run("Enrich images", [
            py, str(SCRIPTS / "enrich_images.py"), "--limit", "500",
        ], required=False)
        (steps_ok if ok else steps_fail).append("Enrich images")
    else:
        print("\n  Skipping image enrichment (--skip-images)")

    # ── Summary ────────────────────────────────────────────────────────────
    elapsed = time.monotonic() - t0
    mins, secs = divmod(int(elapsed), 60)
    print("\n" + "=" * 60)
    print("  REFRESH COMPLETE")
    print("=" * 60)
    print(f"  Elapsed : {mins}m {secs}s")
    print(f"  Passed  : {', '.join(steps_ok) if steps_ok else '(none)'}")
    if steps_fail:
        print(f"  Failed  : {', '.join(steps_fail)}")
    print("=" * 60)

    return 1 if steps_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
