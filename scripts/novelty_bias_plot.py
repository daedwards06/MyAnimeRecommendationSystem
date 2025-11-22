#!/usr/bin/env python
"""Novelty / popularity bias plot for Phase 4.

Computes average popularity percentile of recommended items per model.
Requires a recommendations parquet (user_id, model, anime_id) and a popularity parquet
with columns anime_id, popularity_count.
Outputs a bar plot + JSON summary.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

OUT_JSON = Path("reports/artifacts/novelty_bias.json")
OUT_FIG = Path("reports/figures/phase4/novelty_bias.png")


def compute_popularity_percentile(pop: pd.Series) -> pd.Series:
    # Higher count -> lower novelty. Convert to percentile rank (1.0 = most popular)
    ranks = pop.rank(method="average", ascending=True)  # least popular gets lowest rank
    percentiles = ranks / ranks.max()
    return percentiles  # least popular ~ small value, most popular ~1


def aggregate(recs: pd.DataFrame, popularity: pd.DataFrame) -> pd.DataFrame:
    pop_series = popularity.set_index("anime_id")["popularity_count"].astype(float)
    percentiles = compute_popularity_percentile(pop_series)
    recs = recs.merge(percentiles.rename("pop_percentile"), left_on="anime_id", right_index=True, how="left")
    grouped = recs.groupby("model")["pop_percentile"].mean().rename("avg_pop_percentile")
    return grouped.reset_index()


def plot(df: pd.DataFrame) -> None:
    plt.figure(figsize=(6, 4))
    sns.set_palette("colorblind")
    # Assign hue explicitly to avoid future seaborn deprecation warning
    sns.barplot(data=df, x="model", y="avg_pop_percentile", hue="model", dodge=False, legend=False)
    plt.ylabel("Avg Popularity Percentile (lower = more novel)")
    plt.xlabel("Model")
    plt.title("Novelty / Popularity Bias")
    plt.tight_layout()
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_FIG, dpi=150)
    plt.close()


def main(args: argparse.Namespace) -> None:
    recs = pd.read_parquet(args.recommendations)
    pop = pd.read_parquet(args.popularity)
    required_recs = {"user_id", "model", "anime_id"}
    if missing := (required_recs - set(recs.columns)):
        raise SystemExit(f"Missing columns in recommendations: {missing}")
    if "popularity_count" not in pop.columns:
        raise SystemExit("Popularity file requires 'popularity_count' column")
    df = aggregate(recs, pop)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(df.to_dict(orient="list"), indent=2))
    plot(df)
    print(f"[ok] Saved novelty artifacts: {OUT_JSON}, {OUT_FIG}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Novelty / popularity bias plot")
    p.add_argument("--recommendations", default="data/processed/recommendations_sample.parquet")
    p.add_argument("--popularity", default="data/processed/popularity.parquet")
    main(p.parse_args())
