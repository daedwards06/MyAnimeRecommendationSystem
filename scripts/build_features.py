"""Phase 2 feature build orchestrator.

This script cleans interactions, builds content features (multi-hot, TF-IDF, embeddings),
computes popularity/recency signals, flags cold-start items, and writes train/val/test splits.

Defaults follow paths and conventions documented in phase_2_implementation.md.

Usage (PowerShell):
  python scripts/build_features.py

Optional args:
  --ratings-path data/raw/rating.csv
  --kaggle-anime-path data/raw/anime.csv
  --metadata-path data/processed/anime_metadata.parquet
  --time-col timestamp
  --val 0.15 --test 0.15
  --tfidf-max 10000 --tfidf-ngram 1 2
  --embed-batch 256

Outputs (by default):
  data/processed/interactions.parquet
  data/processed/train.parquet
  data/processed/val.parquet
  data/processed/test.parquet
  data/processed/features/genres_multi_hot.parquet
  data/processed/item_features_tfidf.parquet
  data/processed/item_features_embeddings.parquet (if synopsis present)
  data/processed/items.parquet (basic item-level signals & flags)
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

import sys

# Ensure project root (which contains the 'src' package) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.data.cleaning import (
    SplitConfig,
    clean_interactions,
    load_anime,
    load_ratings,
    normalize_metadata,
    user_based_split,
)
from src.data.persist import to_parquet
from src.features import tags as feat_tags
from src.features import embeddings as feat_emb
from src.features import signals as feat_signals
from src.features import cold_start as feat_cold
from src.features import user_features as feat_user
from src.features import scaling as feat_scaling
from src.data.indexing import build_id_indices


def _detect_metadata_path() -> Optional[Path]:
    """Detect the most appropriate metadata parquet.

    Strategy:
    1) Gather known base candidates (processed then interim)
    2) Also include any suffixed snapshots matching anime_metadata_*.parquet
    3) Choose the most recently modified file among all existing candidates
    """
    base_candidates = [
        Path("data/processed/anime_metadata_normalized.parquet"),
        Path("data/processed/anime_metadata.parquet"),
        Path("data/interim/anime_metadata_normalized.parquet"),
        Path("data/interim/anime_metadata.parquet"),
    ]
    found: list[Path] = [p for p in base_candidates if p.exists()]

    # Include suffixed snapshots under processed and interim
    for root in [Path("data/processed"), Path("data/interim")]:
        if root.exists():
            found.extend([p for p in root.glob("anime_metadata_*.parquet") if p.is_file()])

    if not found:
        return None
    # Pick the most recently modified
    return max(found, key=lambda p: p.stat().st_mtime)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build Phase 2 features and splits")
    ap.add_argument("--ratings-path", type=Path, default=Path("data/raw/rating.csv"))
    ap.add_argument("--kaggle-anime-path", type=Path, default=Path("data/raw/anime.csv"))
    ap.add_argument("--metadata-path", type=Path, default=None, help="Path to enriched/normalized metadata parquet")
    ap.add_argument("--time-col", type=str, default=None, help="Optional timestamp column for time-aware split")
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--test", type=float, default=0.15)
    ap.add_argument("--tfidf-max", type=int, default=10000)
    ap.add_argument("--tfidf-ngram", nargs=2, type=int, default=[1, 2])
    ap.add_argument("--embed-batch", type=int, default=256)
    ap.add_argument("--snapshot-cutoff", type=str, default=None, help="YYYY-MM-DD; if set, items with aired_from >= cutoff are treated as post-snapshot")
    ap.add_argument("--low-interaction-threshold", type=int, default=5, help="Items with total interactions <= threshold are low-interaction")
    ap.add_argument("--data-version", type=str, default=None, help="Optional version tag recorded in artifacts manifest and items table")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    ratings_path: Path = args.ratings_path
    kaggle_anime_path: Path = args.kaggle_anime_path
    metadata_path: Optional[Path] = args.metadata_path
    if metadata_path is None:
        detected = _detect_metadata_path()
        if detected is None:
            raise FileNotFoundError(
                "Could not find metadata parquet. Provide --metadata-path or create one under data/processed/."
            )
        metadata_path = detected

    print(f"[load] ratings: {ratings_path}")
    interactions = load_ratings(ratings_path)
    print(f"[info] interactions raw shape: {interactions.shape}")

    print("[clean] interactions")
    interactions = clean_interactions(interactions)
    to_parquet(interactions, Path("data/processed/interactions.parquet"))
    print(f"[save] data/processed/interactions.parquet ({len(interactions)} rows)")

    print(f"[load] kaggle anime: {kaggle_anime_path}")
    kaggle_anime = load_anime(kaggle_anime_path)
    if "anime_id" in kaggle_anime.columns:
        kaggle_anime["anime_id"] = pd.to_numeric(kaggle_anime["anime_id"], errors="coerce").astype("Int64")
        kaggle_anime = kaggle_anime.dropna(subset=["anime_id"]).copy()
        kaggle_anime["anime_id"] = kaggle_anime["anime_id"].astype(int)
    print(f"[info] kaggle anime shape: {kaggle_anime.shape}")

    print(f"[load] metadata: {metadata_path}")
    meta = pd.read_parquet(metadata_path)
    # Ensure normalized list columns exist even if parquet isn't normalized
    meta = normalize_metadata(meta)
    print(f"[info] metadata shape: {meta.shape}")

    # Features: multi-hot and TF-IDF
    print("[feat] multi-hot genres/themes")
    multi_hot = feat_tags.build_multi_hot(meta)
    to_parquet(multi_hot, Path("data/processed/features/genres_multi_hot.parquet"))
    g_cols = [c for c in multi_hot.columns if c.startswith("genre_")]
    t_cols = [c for c in multi_hot.columns if c.startswith("theme_")]
    print(f"[save] features/genres_multi_hot.parquet (genres={len(g_cols)}, themes={len(t_cols)})")

    print("[feat] TF-IDF from tags (genres+themes)")
    tfidf, vec = feat_tags.build_tfidf_and_vectorizer(
        meta,
        max_features=int(args.tfidf_max),
        ngram_range=(int(args.tfidf_ngram[0]), int(args.tfidf_ngram[1])),
    )
    to_parquet(tfidf, Path("data/processed/item_features_tfidf.parquet"))
    tfidf_cols = [c for c in tfidf.columns if c.startswith("tfidf_")]
    if not tfidf_cols:
        print("[warn] TF-IDF produced no features (empty tags). Saved id-only frame.")
    else:
        print(f"[save] item_features_tfidf.parquet ({len(tfidf_cols)} features)")
    # Save vectorizer for reuse in app/inference
    vec_path = Path("data/processed/features/tfidf_vectorizer.joblib")
    feat_tags.save_tfidf_vectorizer(vec, vec_path)
    print(f"[save] TF-IDF vectorizer: {vec_path}")

    # Optional: embeddings if synopsis exists
    if "synopsis" in meta.columns:
        print("[feat] synopsis sentence-transformer embeddings")
        emb = feat_emb.generate_or_update_item_embeddings(
            meta,
            id_col="anime_id",
            text_col="synopsis",
            out_path=Path("data/processed/item_features_embeddings.parquet"),
            batch_size=int(args.embed_batch),
        )
        print(f"[save] item_features_embeddings.parquet ({len(emb)} rows)")
    else:
        print("[warn] 'synopsis' column not found in metadata; skipping embeddings generation")

    # Signals: popularity and recency
    print("[feat] popularity signals from interactions")
    pops = feat_signals.interaction_signals(interactions)
    print("[feat] recency signals from metadata")
    recency = feat_signals.recency_from_metadata(meta)

    # Cold-start flags
    print("[feat] cold-start flags")
    cold_flags = feat_cold.flag_cold_start(
        meta,
        kaggle_anime,
        interactions,
        snapshot_cutoff_date=args.snapshot_cutoff,
        low_interaction_threshold=int(args.low_interaction_threshold),
    )

    # Assemble a basic items table
    print("[assemble] items.parquet")
    items = (
        meta[["anime_id"]]
        .merge(pops, on="anime_id", how="left")
        .merge(recency, on="anime_id", how="left")
        .merge(cold_flags, on="anime_id", how="left")
    )
    # Optional add data_version tag
    if args.data_version:
        items["data_version"] = args.data_version
    to_parquet(items, Path("data/processed/items.parquet"))

    # User features
    print("[feat] user features")
    user_feats = feat_user.build_user_features(interactions, meta, time_col=args.time_col)
    to_parquet(user_feats, Path("data/processed/user_features.parquet"))
    print(f"[save] user_features.parquet ({len(user_feats)} rows)")

    # ID indexing
    print("[index] user/item indices")
    user_idx, item_idx = build_id_indices(interactions)
    to_parquet(user_idx, Path("data/processed/user_index.parquet"))
    to_parquet(item_idx, Path("data/processed/item_index.parquet"))
    print(f"[save] user_index.parquet ({len(user_idx)}), item_index.parquet ({len(item_idx)})")

    # Feature scaling stats for numeric item signals
    print("[stats] feature scaling snapshot")
    numeric_cols = [c for c in ["num_ratings", "mean_rating", "popularity", "days_since_release"] if c in items.columns]
    stats = feat_scaling.compute_feature_stats(items, numeric_cols)
    feat_scaling.save_feature_stats(stats, Path("data/processed/feature_stats.json"))
    print(f"[save] feature_stats.json (cols={list(stats.keys())})")

    # Quality slices
    print("[slices] item quality slices")
    slices_dir = Path("data/processed/slices")
    slices_dir.mkdir(parents=True, exist_ok=True)
    q = items[["anime_id", "popularity"]].copy()
    q_pop = pd.to_numeric(q["popularity"], errors="coerce")
    thresh = q_pop.quantile(0.90) if q_pop.notna().any() else None
    items_slices = items[["anime_id"]].copy()
    items_slices["slice_popular_top10"] = q_pop >= thresh if thresh is not None else False
    items_slices["slice_no_synopsis"] = ~meta["synopsis"].notna() if "synopsis" in meta.columns else False
    if "is_post_snapshot" in items.columns:
        items_slices["slice_post_snapshot"] = items["is_post_snapshot"].fillna(False)
    to_parquet(items_slices, slices_dir / "items_slices.parquet")
    # Simple summary JSON
    slice_summary = {
        "popular_top10_count": int(items_slices["slice_popular_top10"].sum()),
        "no_synopsis_count": int(items_slices["slice_no_synopsis"].sum()),
        "post_snapshot_count": int(items_slices.get("slice_post_snapshot", pd.Series(dtype=bool)).sum()) if "slice_post_snapshot" in items_slices.columns else 0,
    }
    import json
    (slices_dir / "items_slices_summary.json").write_text(json.dumps(slice_summary, indent=2), encoding="utf-8")
    print(f"[save] slices items_slices.parquet and summary json")

    # Splits
    print("[split] train/val/test")
    cfg = SplitConfig(val_ratio=float(args.val), test_ratio=float(args.test), time_col=args.time_col)
    train_df, val_df, test_df = user_based_split(interactions, cfg)
    to_parquet(train_df, Path("data/processed/train.parquet"))
    to_parquet(val_df, Path("data/processed/val.parquet"))
    to_parquet(test_df, Path("data/processed/test.parquet"))
    print(
        f"[save] splits train/val/test: {len(train_df)}/{len(val_df)}/{len(test_df)} (total={len(interactions)})"
    )

    # Artifacts manifest / versions
    print("[manifest] artifacts manifest")
    manifest = {
        "data_version": args.data_version,
        "vectorizer_path": str(vec_path),
        "artifacts": {
            "interactions": len(interactions),
            "items": len(items),
            "user_features": len(user_feats),
            "user_index": len(user_idx),
            "item_index": len(item_idx),
            "tfidf_features": len(tfidf_cols),
        },
    }
    import json
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    (Path("data/processed") / "artifacts_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("[done] Phase 2 feature build complete")


if __name__ == "__main__":
    main()
