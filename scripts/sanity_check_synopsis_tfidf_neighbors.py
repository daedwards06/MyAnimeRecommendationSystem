"""Sanity-check synopsis TF-IDF alignment (Phase 4 semantic signal).

This is a deterministic diagnostic tool to validate that the synopsis TF-IDF
artifact's row index alignment matches anime_id and metadata titles.

It:
- loads metadata parquet
- loads the synopsis TF-IDF joblib artifact
- for each requested anime_id (or exact title_display), prints:
  - the seed title
  - a synopsis snippet
  - top-K TF-IDF neighbors with cosine similarity

Usage (PowerShell):
  python scripts/sanity_check_synopsis_tfidf_neighbors.py --titles "My Hero Academia" "Attack on Titan"
  python scripts/sanity_check_synopsis_tfidf_neighbors.py --anime-ids 31964 16498

Optional:
  --artifact-path models/synopsis_tfidf_vYYYY.MM.DD_HHMMSS.joblib
  --top-k 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app.synopsis_tfidf import choose_synopsis_text, validate_synopsis_tfidf_artifact


def _pick_default_artifact(models_dir: Path) -> Path:
    # Prefer timestamped artifacts; fall back to any synopsis_tfidf_*.joblib.
    cands = sorted(models_dir.glob("synopsis_tfidf_*.joblib"))
    if not cands:
        raise FileNotFoundError(f"No synopsis TF-IDF artifacts found in {models_dir}")
    # Deterministic: lexicographically last tends to be newest with vYYYY.MM.DD...
    return cands[-1]


def _resolve_titles_exact(metadata: pd.DataFrame, titles: list[str]) -> list[int]:
    title_to_id = {
        str(t): int(a)
        for t, a in zip(metadata["title_display"].astype(str).tolist(), metadata["anime_id"].astype(int).tolist())
    }
    out: list[int] = []
    for t in titles:
        if t not in title_to_id:
            raise KeyError(
                f"Title not found by exact title_display: {t!r}. "
                "Pass --anime-ids directly or use the exact title_display string from metadata."
            )
        out.append(int(title_to_id[t]))
    return out


def _cosine_neighbors_from_row(X, row_idx: int, top_k: int) -> tuple[np.ndarray, np.ndarray]:
    # TF-IDF vectors are L2-normalized, so cosine similarity is dot product.
    q = X[int(row_idx)]
    sims = q.dot(X.T).toarray().ravel().astype(np.float32)
    # Exclude self
    sims[int(row_idx)] = -1.0
    # Top-K indices
    k = max(1, int(top_k))
    nn_idx = np.argpartition(-sims, kth=min(k - 1, len(sims) - 1))[:k]
    nn_idx = nn_idx[np.argsort(-sims[nn_idx], kind="mergesort")]
    return nn_idx.astype(np.int64), sims[nn_idx]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sanity-check synopsis TF-IDF neighbor alignment")
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"))
    ap.add_argument("--models-dir", type=Path, default=Path("models"))
    ap.add_argument("--artifact-path", type=Path, default=None)
    ap.add_argument("--anime-ids", type=int, nargs="*", default=[])
    ap.add_argument("--titles", type=str, nargs="*", default=[])
    ap.add_argument("--top-k", type=int, default=5)
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    meta_path: Path = args.metadata_path
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata parquet not found: {meta_path}")

    metadata = pd.read_parquet(meta_path)
    if "anime_id" not in metadata.columns or "title_display" not in metadata.columns:
        raise ValueError("metadata must include anime_id and title_display")

    art_path = args.artifact_path
    if art_path is None:
        art_path = _pick_default_artifact(args.models_dir)

    if not art_path.exists():
        raise FileNotFoundError(f"TF-IDF artifact not found: {art_path}")

    obj = joblib.load(art_path)
    art = validate_synopsis_tfidf_artifact(obj)

    ids: list[int] = []
    if args.titles:
        ids.extend(_resolve_titles_exact(metadata, [str(x) for x in args.titles]))
    ids.extend([int(x) for x in (args.anime_ids or [])])

    # de-dupe while preserving order
    seen: set[int] = set()
    uniq_ids: list[int] = []
    for aid in ids:
        if aid in seen:
            continue
        seen.add(aid)
        uniq_ids.append(int(aid))

    if not uniq_ids:
        raise ValueError("Provide --anime-ids and/or --titles")

    meta_by_id = metadata.set_index(metadata["anime_id"].astype(int), drop=False)

    print(f"[meta] {meta_path} shape={metadata.shape}")
    print(f"[tfidf] {art_path} schema={art.schema} items={len(art.anime_ids)} vocab={art.vocab_size}")

    for seed_id in uniq_ids:
        if int(seed_id) not in art.anime_id_to_row:
            print(f"\n== seed anime_id={seed_id} ==")
            print("  [WARN] seed not present in TF-IDF artifact (no row)")
            continue

        row = meta_by_id.loc[int(seed_id)] if int(seed_id) in meta_by_id.index else None
        title = "<missing in metadata>" if row is None else str(row.get("title_display", ""))
        synopsis = "" if row is None else choose_synopsis_text(row)
        synopsis_snip = (synopsis[:220] + "...") if synopsis and len(synopsis) > 220 else synopsis

        print(f"\n== seed anime_id={seed_id} | {title} ==")
        if synopsis_snip:
            print(f"synopsis: {synopsis_snip}")

        seed_row_idx = int(art.anime_id_to_row[int(seed_id)])
        nn_idx, nn_sims = _cosine_neighbors_from_row(art.tfidf_matrix, seed_row_idx, top_k=int(args.top_k))

        print(f"top-{int(args.top_k)} neighbors:")
        for r, (i, sim) in enumerate(zip(nn_idx.tolist(), nn_sims.tolist()), start=1):
            aid = int(art.anime_ids[int(i)])
            row2 = meta_by_id.loc[aid] if aid in meta_by_id.index else None
            t2 = "<missing in metadata>" if row2 is None else str(row2.get("title_display", ""))
            print(f"  {r:>2d}. sim={float(sim):.4f} anime_id={aid} title={t2}")


if __name__ == "__main__":
    main()
