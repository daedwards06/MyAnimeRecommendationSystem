"""Build a deterministic synopsis TF-IDF similarity artifact (Phase 4 experiment).

Reads:
  - data/processed/anime_metadata.parquet

Writes:
  - models/synopsis_tfidf_<version>.joblib
  - updates data/processed/artifacts_manifest.json (non-destructive append)

Usage (PowerShell):
  python scripts/build_synopsis_tfidf_artifact.py

Optional:
  --metadata-path data/processed/anime_metadata.parquet
  --out-stem synopsis_tfidf
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import pandas as pd

from src.app.synopsis_tfidf import build_synopsis_tfidf_artifact, validate_synopsis_tfidf_artifact


def _utc_suffix() -> str:
    return datetime.now(timezone.utc).strftime("v%Y.%m.%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build synopsis TF-IDF artifact")
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"))
    ap.add_argument("--models-dir", type=Path, default=Path("models"))
    ap.add_argument("--manifest-path", type=Path, default=Path("data/processed/artifacts_manifest.json"))
    ap.add_argument("--out-stem", type=str, default="synopsis_tfidf")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    meta_path: Path = args.metadata_path
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata parquet not found: {meta_path}")

    print(f"[load] {meta_path}")
    meta = pd.read_parquet(meta_path)
    print(f"[info] metadata shape: {meta.shape}")

    print("[build] synopsis TF-IDF")
    artifact = build_synopsis_tfidf_artifact(meta)
    artifact = validate_synopsis_tfidf_artifact(artifact)

    args.models_dir.mkdir(parents=True, exist_ok=True)
    version = _utc_suffix()
    out_path = args.models_dir / f"{args.out_stem}_{version}.joblib"

    joblib.dump(artifact, out_path, compress=3)
    print(f"[save] {out_path} (vocab={artifact.vocab_size}, items={len(artifact.anime_ids)})")

    # Non-destructive manifest update.
    manifest_path: Path = args.manifest_path
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}

    entry = {
        "stem": out_path.stem,
        "path": str(out_path.as_posix()),
        "created_utc": artifact.created_utc,
        "schema": artifact.schema,
        "vocab_size": int(artifact.vocab_size),
        "vectorizer_params": artifact.vectorizer_params,
        "text_field": artifact.text_field,
    }
    manifest.setdefault("synopsis_tfidf", []).append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[manifest] updated: {manifest_path}")


if __name__ == "__main__":
    main()
