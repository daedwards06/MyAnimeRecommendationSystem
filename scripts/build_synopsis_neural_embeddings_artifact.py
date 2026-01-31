"""WSL2-only: build a Phase 5 neural synopsis embeddings artifact.

Reads:
  - data/processed/anime_metadata.parquet

Writes:
  - models/synopsis_neural_embeddings_<version>.joblib
  - updates data/processed/artifacts_manifest.json (non-destructive append)

This script is intended to be run inside WSL2 (Ubuntu). It uses
sentence-transformers + torch for offline embedding computation.

Determinism:
  - Stable iteration order by anime_id (mergesort)
  - Fixed model id (default: sentence-transformers/all-MiniLM-L6-v2)
  - Fixed preprocessing/truncation
  - CPU inference only

Usage (WSL2):
  python scripts/build_synopsis_neural_embeddings_artifact.py

Options:
  --metadata-path data/processed/anime_metadata.parquet
  --models-dir models
  --manifest-path data/processed/artifacts_manifest.json
  --out-stem synopsis_neural_embeddings
  --model-name sentence-transformers/all-MiniLM-L6-v2
  --batch-size 64
  --max-chars 512
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


def _utc_suffix() -> str:
    return datetime.now(timezone.utc).strftime("v%Y.%m.%d_%H%M%S")


def _is_wsl() -> bool:
    # Conservative: allow WSL1/WSL2.
    if os.name == "nt":
        return False
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except Exception:
        return False


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build synopsis neural embeddings artifact (WSL2-only)")
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"))
    ap.add_argument("--models-dir", type=Path, default=Path("models"))
    ap.add_argument("--manifest-path", type=Path, default=Path("data/processed/artifacts_manifest.json"))
    ap.add_argument("--out-stem", type=str, default="synopsis_neural_embeddings")
    ap.add_argument("--model-name", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--max-chars", type=int, default=512)
    return ap.parse_args()


def _normalize_ws(text: str) -> str:
    # Collapse any whitespace to single spaces.
    return " ".join(str(text or "").split()).strip()


def _truncate(text: str, *, max_chars: int, suffix: str = "…") -> str:
    s = str(text or "")
    if len(s) > int(max_chars):
        return s[: int(max_chars)] + str(suffix)
    return s


def main() -> None:
    if not _is_wsl():
        raise RuntimeError(
            "This builder is WSL-only. Run it inside WSL2 (Ubuntu) so Windows runtime remains torch-free."
        )

    # Keep tokenizers/threads deterministic-ish.
    os.environ.setdefault("PYTHONHASHSEED", "0")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")

    args = parse_args()

    meta_path: Path = args.metadata_path
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata parquet not found: {meta_path}")

    import numpy as np
    import pandas as pd
    import joblib

    # Heavy deps are imported only in this WSL2 builder.
    import torch  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore

    from src.app.synopsis_neural_embeddings import build_artifact_from_embeddings

    torch.manual_seed(0)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass

    print(f"[load] {meta_path}")
    meta = pd.read_parquet(meta_path)
    print(f"[info] metadata shape: {meta.shape}")

    if "anime_id" not in meta.columns:
        raise ValueError("Metadata parquet is missing required column: anime_id")

    work = meta.copy()
    work["anime_id"] = pd.to_numeric(work["anime_id"], errors="coerce").astype("Int64")
    work = work.dropna(subset=["anime_id"]).copy()
    work["anime_id"] = work["anime_id"].astype(int)
    work = work.sort_values("anime_id", kind="mergesort")

    # Text policy: synopsis only.
    syn = work.get("synopsis")
    if syn is None:
        work["_synopsis_text"] = ""
    else:
        work["_synopsis_text"] = syn.astype(str).fillna("")

    max_chars = int(args.max_chars)
    texts_raw = work["_synopsis_text"].tolist()

    texts: list[str] = []
    has_text_mask: list[bool] = []
    for t in texts_raw:
        s = _normalize_ws(t)
        if not s:
            texts.append("")
            has_text_mask.append(False)
        else:
            texts.append(_truncate(s, max_chars=max_chars))
            has_text_mask.append(True)

    model_name = str(args.model_name)
    print(f"[model] loading: {model_name} (cpu)")
    model = SentenceTransformer(model_name, device="cpu")

    # Encode only non-empty docs; missing synopsis becomes a deterministic zero vector.
    nonempty_idx = [i for i, ok in enumerate(has_text_mask) if ok]
    print(f"[encode] non-empty synopses: {len(nonempty_idx)} / {len(texts)}")

    # Determine embedding dim via a tiny encode.
    probe = model.encode(["probe"], convert_to_numpy=True, normalize_embeddings=True)
    dim = int(probe.shape[1])

    E = np.zeros((len(texts), dim), dtype=np.float32)
    if nonempty_idx:
        batch_texts = [texts[i] for i in nonempty_idx]
        emb = model.encode(
            batch_texts,
            batch_size=int(args.batch_size),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).astype(np.float32, copy=False)
        if emb.shape[1] != dim:
            raise RuntimeError(f"Unexpected embedding dim {emb.shape[1]} (expected {dim})")
        for j, i in enumerate(nonempty_idx):
            E[int(i)] = emb[int(j)]

    anime_ids = work["anime_id"].to_numpy(dtype=np.int64, copy=True)

    # Version capture (best-effort; do not fail build if missing).
    versions: dict[str, str] = {
        "numpy": getattr(np, "__version__", ""),
        "pandas": getattr(pd, "__version__", ""),
    }
    try:
        import sentence_transformers  # type: ignore

        versions["sentence-transformers"] = getattr(sentence_transformers, "__version__", "")
    except Exception:
        versions["sentence-transformers"] = ""
    try:
        import transformers  # type: ignore

        versions["transformers"] = getattr(transformers, "__version__", "")
    except Exception:
        versions["transformers"] = ""
    try:
        versions["torch"] = getattr(torch, "__version__", "")
    except Exception:
        versions["torch"] = ""

    preprocessing = {
        "whitespace_collapse": True,
        "strip": True,
        "truncate": {"max_chars": int(max_chars), "suffix": "…"},
        "missing_synopsis": "zero_vector",
        "text_field": "synopsis",
    }

    print("[build] artifact")
    artifact = build_artifact_from_embeddings(
        anime_ids=anime_ids,
        embeddings=E,
        model_name=model_name,
        model_library_versions=versions,
        text_preprocessing=preprocessing,
    )

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

    manifest.setdefault("synopsis_neural_embeddings", []).append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[manifest] updated: {manifest_path}")


if __name__ == "__main__":
    main()
