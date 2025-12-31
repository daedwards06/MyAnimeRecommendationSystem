"""Build a deterministic synopsis embeddings similarity artifact (Phase 4 experiment).

Reads:
  - data/processed/anime_metadata.parquet

Writes:
  - models/synopsis_embeddings_<version>.joblib
  - updates data/processed/artifacts_manifest.json (non-destructive append)

Usage (PowerShell):
  python scripts/build_synopsis_embeddings_artifact.py

Optional:
  --metadata-path data/processed/anime_metadata.parquet
  --out-stem synopsis_embeddings
  --model-name sentence-transformers/all-MiniLM-L6-v2
  --batch-size 64
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import pandas as pd

from src.app.synopsis_embeddings import (
    build_synopsis_embeddings_artifact,
    validate_synopsis_embeddings_artifact,
    DEFAULT_SENTENCE_TRANSFORMERS_MODEL,
)


# Windows-specific: some Python stacks end up with multiple OpenMP runtimes
# (e.g., MKL + torch). For the artifact build script (offline), we allow the
# process to continue.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _utc_suffix() -> str:
    return datetime.now(timezone.utc).strftime("v%Y.%m.%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build synopsis embeddings artifact")
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"))
    ap.add_argument("--models-dir", type=Path, default=Path("models"))
    ap.add_argument("--manifest-path", type=Path, default=Path("data/processed/artifacts_manifest.json"))
    ap.add_argument("--out-stem", type=str, default="synopsis_embeddings")
    ap.add_argument("--model-name", type=str, default=DEFAULT_SENTENCE_TRANSFORMERS_MODEL)
    ap.add_argument("--batch-size", type=int, default=64)
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    meta_path: Path = args.metadata_path
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata parquet not found: {meta_path}")

    print(f"[load] {meta_path}")
    meta = pd.read_parquet(meta_path)
    print(f"[info] metadata shape: {meta.shape}")

    print(f"[build] synopsis embeddings (model={args.model_name})")
    artifact = build_synopsis_embeddings_artifact(meta, model_name=str(args.model_name), batch_size=int(args.batch_size))
    artifact = validate_synopsis_embeddings_artifact(artifact)

    args.models_dir.mkdir(parents=True, exist_ok=True)
    version = _utc_suffix()
    out_path = args.models_dir / f"{args.out_stem}_{version}.joblib"

    joblib.dump(artifact, out_path, compress=3)
    print(f"[save] {out_path} (dim={artifact.dim}, items={len(artifact.anime_ids)})")

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
        "model_name": artifact.model_name,
        "model_library_versions": artifact.model_library_versions,
        "text_field": artifact.text_field,
        "text_preprocessing": artifact.text_preprocessing,
        "dim": int(artifact.dim),
        "normalized": bool(artifact.normalized),
        "config_hash": artifact.config_hash,
        "anime_ids_hash": artifact.anime_ids_hash,
        "build_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    manifest.setdefault("synopsis_embeddings", []).append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[manifest] updated: {manifest_path}")


if __name__ == "__main__":
    main()
