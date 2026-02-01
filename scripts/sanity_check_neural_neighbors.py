"""Sanity-check Phase 5 neural synopsis embedding neighbors (diagnostics only).

Purpose
-------
Answer the question:
  "Are there actually strong neural neighbors for a given seed anime_id in this
   dataset, before any Stage 1 admission or Stage 2 ranking logic?"

Constraints
-----------
- Windows runtime: NumPy only for similarity (no torch/transformers).
- Deterministic: stable ordering (ties broken by anime_id).
- Read-only: prints to stdout; does not write files or modify artifacts.

Usage (PowerShell)
------------------
  python scripts/sanity_check_neural_neighbors.py --anime-id 21 --topk 50

Notes
-----
This script intentionally bypasses all admission/ranking logic and inspects the
raw cosine neighborhood directly from the neural embeddings artifact.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app.artifacts_loader import build_artifacts
from src.app.synopsis_neural_embeddings import validate_synopsis_neural_embeddings_artifact


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sanity-check neural embedding neighbors for a seed anime_id")
    ap.add_argument("--anime-id", type=int, required=True, help="Seed anime_id")
    ap.add_argument("--topk", type=int, default=50, help="Number of neighbors to display")
    return ap.parse_args()


_BAD_STRINGS = {"", "nan", "none", "null"}


def _is_nonempty_text(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and not np.isfinite(val):
        return False
    s = str(val).strip()
    return s.lower() not in _BAD_STRINGS


def _safe_text(val: Any) -> str:
    if not _is_nonempty_text(val):
        return ""
    return str(val)


def _as_tokens(val: Any) -> list[str]:
    """Convert list-like / string-like metadata fields into display tokens."""
    if val is None:
        return []

    if isinstance(val, float) and not np.isfinite(val):
        return []

    if isinstance(val, (list, tuple, set, np.ndarray)):
        out: list[str] = []
        for x in val:
            s = str(x).strip()
            if s and s.lower() not in _BAD_STRINGS:
                out.append(s)
        return out

    # Sometimes columns can be pipe-delimited strings (after fallbacks).
    if isinstance(val, str):
        s = val.strip()
        if not s or s.lower() in _BAD_STRINGS:
            return []
        if "|" in s:
            toks = [t.strip() for t in s.split("|")]
            return [t for t in toks if t and t.lower() not in _BAD_STRINGS]
        return [s]

    s = str(val).strip()
    if not s or s.lower() in _BAD_STRINGS:
        return []
    return [s]


def _fmt_tokens(val: Any) -> str:
    toks = _as_tokens(val)
    return ", ".join(toks) if toks else ""


def _percentiles(x: np.ndarray, ps: list[float]) -> dict[float, float]:
    arr = np.asarray(x, dtype=np.float64)
    if arr.size == 0:
        return {p: float("nan") for p in ps}
    return {p: float(np.percentile(arr, p)) for p in ps}


def main() -> None:
    args = parse_args()

    seed_id = int(args.anime_id)
    topk = max(1, int(args.topk))

    bundle = build_artifacts()
    metadata = bundle["metadata"].copy()

    models = bundle["models"]
    if "synopsis_neural_embeddings" not in models:
        stems = [k for k in models.keys() if str(k).startswith("synopsis_neural_embeddings")]
        raise RuntimeError(
            "Neural embeddings artifact not loaded. "
            "Expected bundle['models']['synopsis_neural_embeddings'] to exist. "
            f"Found candidates: {sorted(stems)}"
        )

    art = validate_synopsis_neural_embeddings_artifact(models["synopsis_neural_embeddings"])
    stem = str(models.get("_synopsis_neural_embeddings_stem", "<unknown>"))

    # Build metadata index
    if "anime_id" not in metadata.columns:
        raise ValueError("Loaded metadata is missing anime_id")

    metadata = metadata.copy()
    metadata["anime_id"] = metadata["anime_id"].astype(int)
    meta_by_id = metadata.set_index("anime_id", drop=False)

    if seed_id not in art.anime_id_to_row:
        raise KeyError(f"Seed anime_id={seed_id} not present in neural embeddings artifact")

    seed_row = int(art.anime_id_to_row[seed_id])
    E = art.embeddings

    if seed_row < 0 or seed_row >= E.shape[0]:
        raise RuntimeError(f"Invalid seed row index: {seed_row}")

    seed_vec = E[seed_row].astype(np.float32, copy=False)
    seed_norm = float(np.linalg.norm(seed_vec))

    # Cosine similarity on normalized vectors -> dot product.
    sims = (E @ seed_vec).astype(np.float32, copy=False)
    sims = sims.copy()  # we will mutate self-sim

    # Exclude self.
    sims[seed_row] = -np.inf

    anime_ids = art.anime_ids.astype(np.int64, copy=False)

    # Stable ordering: sort by (-sim, anime_id).
    order = np.lexsort((anime_ids, -sims))
    top_idx = order[:topk]

    # Global diagnostics: vector coverage.
    norms = np.linalg.norm(E.astype(np.float64, copy=False), axis=1)
    zero_vec_count = int(np.sum(norms <= 1e-12))
    near_zero_vec_count = int(np.sum((norms > 1e-12) & (norms < 1e-3)))
    nonfinite_count = int(np.sum(~np.isfinite(norms)))

    # Similarity distribution (exclude seed row)
    sims_for_stats = (E @ seed_vec).astype(np.float64, copy=False)
    sims_for_stats = np.delete(sims_for_stats, seed_row)

    pct = _percentiles(sims_for_stats, [50, 90, 95, 99])
    max_sim = float(np.max(sims_for_stats)) if sims_for_stats.size else float("nan")

    # Catalog coverage diagnostics from metadata.
    has_synopsis_mask = metadata["synopsis"].apply(_is_nonempty_text) if "synopsis" in metadata.columns else None
    has_demo_mask = metadata["demographics"].apply(lambda v: len(_as_tokens(v)) > 0) if "demographics" in metadata.columns else None
    has_genres_mask = metadata["genres"].apply(lambda v: len(_as_tokens(v)) > 0) if "genres" in metadata.columns else None

    syn_count = int(has_synopsis_mask.sum()) if has_synopsis_mask is not None else 0
    demo_count = int(has_demo_mask.sum()) if has_demo_mask is not None else 0
    genre_count = int(has_genres_mask.sum()) if has_genres_mask is not None else 0

    # Seed summary
    seed_row_meta = meta_by_id.loc[seed_id] if seed_id in meta_by_id.index else None
    seed_title = "<missing in metadata>" if seed_row_meta is None else str(seed_row_meta.get("title_display", ""))
    seed_type = "" if seed_row_meta is None else str(seed_row_meta.get("type", ""))
    seed_syn = "" if seed_row_meta is None else _safe_text(seed_row_meta.get("synopsis", ""))
    seed_syn_len = len(seed_syn)

    print("== Phase 5 Neural Neighbor Sanity Check ==")
    print(f"seed_anime_id={seed_id}")
    print(f"artifact_stem={stem}")
    print(f"artifact_schema={art.schema} dim={art.dim} items={int(E.shape[0])} normalized={bool(art.normalized)}")
    print("")

    print("-- Seed metadata --")
    print(f"title: {seed_title}")
    print(f"type: {seed_type}")
    print(f"synopsis_length_chars: {seed_syn_len}")
    print(f"seed_embedding_norm: {seed_norm}")
    if seed_row_meta is not None:
        print(f"demographics: {_fmt_tokens(seed_row_meta.get('demographics'))}")
        print(f"genres: {_fmt_tokens(seed_row_meta.get('genres'))}")
        print(f"themes: {_fmt_tokens(seed_row_meta.get('themes'))}")
    print("")

    print("-- Global diagnostics --")
    print(f"embedding_norm_nonfinite_count: {nonfinite_count}")
    print(f"embedding_zero_vector_count (<=1e-12): {zero_vec_count}")
    print(f"embedding_near_zero_vector_count (1e-12..1e-3): {near_zero_vec_count}")
    print(f"catalog_count: {int(E.shape[0])}")
    print(f"catalog_with_nonempty_synopsis: {syn_count}")
    print(f"catalog_with_nonempty_demographics: {demo_count}")
    print(f"catalog_with_nonempty_genres: {genre_count}")
    print("similarity_percentiles (seed vs all, excl self):")
    print(
        "  "
        + " ".join(
            [
                f"p{int(k)}={pct[k]:.6f}" for k in [50, 90, 95, 99]
            ]
        )
        + f" max={max_sim:.6f}"
    )
    print("")

    print(f"-- Top-{topk} raw cosine neighbors (no admission/ranking) --")
    header = [
        "rank",
        "anime_id",
        "type",
        "cosine_sim",
        "has_synopsis",
        "synopsis_len",
        "demographics",
        "genres",
        "themes",
        "title",
    ]
    print("\t".join(header))

    for r, i in enumerate(top_idx.tolist(), start=1):
        aid = int(anime_ids[int(i)])
        sim = float(sims[int(i)])

        row = meta_by_id.loc[aid] if aid in meta_by_id.index else None
        title = "<missing in metadata>" if row is None else str(row.get("title_display", ""))
        typ = "" if row is None else str(row.get("type", ""))

        syn = "" if row is None else _safe_text(row.get("synopsis", ""))
        has_syn = bool(syn)
        syn_len = len(syn)

        demos = "" if row is None else _fmt_tokens(row.get("demographics"))
        genres = "" if row is None else _fmt_tokens(row.get("genres"))
        themes = "" if row is None else _fmt_tokens(row.get("themes"))

        # Tab-separated to keep it copy/paste friendly.
        print(
            "\t".join(
                [
                    str(r),
                    str(aid),
                    typ,
                    f"{sim:.10f}",
                    str(has_syn),
                    str(syn_len),
                    demos,
                    genres,
                    themes,
                    title,
                ]
            )
        )


if __name__ == "__main__":
    main()
