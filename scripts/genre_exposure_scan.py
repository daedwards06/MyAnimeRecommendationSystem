#!/usr/bin/env python
"""Genre exposure scan: compare genre distribution in recommendations vs catalog.

Inputs:
  --recommendations parquet with columns: user_id, model, anime_id (top-K per user per model)
  --items parquet with columns: anime_id, genres (pipe-delimited str or list)
Outputs:
  reports/artifacts/genre_exposure.json (ratios + distributions)
  reports/figures/phase4/genre_exposure_ratio.png (bar plot of recommendation/catalog ratio per genre for selected model)
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns

OUT_JSON = Path("reports/artifacts/genre_exposure.json")
OUT_FIG = Path("reports/figures/phase4/genre_exposure_ratio.png")


def _explode_genres(df: pd.DataFrame, col: str = "genres") -> pd.Series:
    """Return exploded genre Series.

    Accepts list/tuple/set/ndarray of genres or pipe/semicolon/comma-delimited strings.
    Robust to existing list-like values (avoids pd.isna on arrays which raised earlier ValueError).
    """
    delimiters = ["|", ";", ","]

    def _split(x):
        if x is None:
            return []
        # List-like containers
        if isinstance(x, (list, tuple, set, np.ndarray)):
            return [str(g).strip() for g in x if str(g).strip()]
        # Pandas NA (scalar) case
        try:
            if pd.isna(x):  # safe for scalars
                return []
        except Exception:
            # If pd.isna failed (e.g., object array), fall through to string parsing
            pass
        s = str(x)
        for d in delimiters:
            if d in s:
                parts = [p.strip() for p in s.split(d) if p.strip()]
                return parts
        return [s.strip()] if s.strip() else []

    df_local = df.copy()
    df_local[col] = df_local[col].apply(_split)
    exploded = df_local.explode(col)[col]
    # Drop empty strings just in case
    return exploded[exploded != ""]


def compute_distributions(items: pd.DataFrame, recs: pd.DataFrame, model: str) -> dict:
    catalog_genres = _explode_genres(items).value_counts(normalize=True)
    recs_model = recs[recs["model"] == model]
    rec_genres = _explode_genres(recs_model.merge(items[["anime_id", "genres"]], on="anime_id", how="left"))
    rec_dist = rec_genres.value_counts(normalize=True)
    genres_union = sorted(set(catalog_genres.index) | set(rec_dist.index))
    rows = []
    for g in genres_union:
        cat_p = catalog_genres.get(g, 0.0)
        rec_p = rec_dist.get(g, 0.0)
        ratio = rec_p / cat_p if cat_p > 0 else None
        rows.append({"genre": g, "catalog_pct": cat_p, "recs_pct": rec_p, "ratio": ratio})
    return {"model": model, "genres": rows}


def plot_ratio(data: dict) -> None:
    df = pd.DataFrame(data["genres"])
    df = df.dropna(subset=["ratio"]).sort_values("ratio", ascending=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x="ratio", y="genre", color="#4C72B0")
    plt.xlabel("Recommendation / Catalog Share Ratio")
    plt.ylabel("Genre")
    plt.title(f"Genre Exposure Ratio (Model={data['model']})")
    plt.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_FIG, dpi=150)
    plt.close()


def main(args: argparse.Namespace) -> None:
    recs = pd.read_parquet(args.recommendations)
    items = pd.read_parquet(args.items)
    required_recs = {"user_id", "model", "anime_id"}
    miss = required_recs - set(recs.columns)
    if miss:
        raise SystemExit(f"Missing recommendation columns: {miss}")
    genre_col = args.genre_column
    if genre_col not in items.columns:
        # Attempt automatic detection
        candidates = [c for c in items.columns if "genre" in c.lower()]
        if candidates:
            genre_col = candidates[0]
        else:
            raise SystemExit(f"Items file must contain '{genre_col}' column or another genre* column")
    # Normalize to 'genres' expected downstream
    if genre_col != "genres":
        items = items.rename(columns={genre_col: "genres"})
    result = compute_distributions(items, recs, args.model)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2))
    plot_ratio(result)
    print(f"[ok] Saved genre exposure artifacts: {OUT_JSON}, {OUT_FIG}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Genre exposure scan")
    p.add_argument("--recommendations", default="data/processed/recommendations_sample.parquet")
    p.add_argument("--items", default="data/processed/anime_metadata_normalized.parquet")
    p.add_argument("--model", default="hybrid")
    p.add_argument("--genre-column", default="genres", help="Column name in items parquet containing genre info (default 'genres').")
    main(p.parse_args())
