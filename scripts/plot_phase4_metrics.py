#!/usr/bin/env python
"""Plot Phase 4 evaluation curves.

Generates ranking metric (NDCG@K, MAP@K) and diversity metric (Coverage@K, Gini@K)
plots for a set of models. Input expected: parquet produced by
`scripts/aggregate_phase4_metrics.py`.

Output directory: reports/figures/phase4/
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

MODELS_DISPLAY_ORDER = ["popularity", "mf", "hybrid", "content_tfidf"]
# Colorblind-safe palette derived from seaborn colorblind palette
_cb_colors = sns.color_palette("colorblind", n_colors=len(MODELS_DISPLAY_ORDER))
PALETTE = {m: _cb_colors[i] for i, m in enumerate(MODELS_DISPLAY_ORDER)}
METRICS = ["ndcg", "map", "coverage", "gini"]


def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    required = {"model", "K", "ndcg", "map", "coverage", "gini"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in metrics file: {missing}")
    return df[df["model"].isin(MODELS_DISPLAY_ORDER)].copy()


def plot_curve(df: pd.DataFrame, metric: str, out_dir: Path) -> Path:
    plt.figure(figsize=(7, 5))
    sns.lineplot(
        data=df,
        x="K",
        y=metric,
        hue="model",
        palette=PALETTE,
        marker="o",
    )
    plt.title(f"{metric.upper()} vs K")
    plt.grid(axis="y", alpha=0.25)
    plt.xlabel("K")
    plt.ylabel(metric.upper())
    plt.legend(title="Model")
    out_path = out_dir / f"{metric}_vs_k.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def main(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_metrics(Path(args.metrics_path))

    for metric in METRICS:
        p = plot_curve(df, metric, out_dir)
        print(f"Saved: {p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-path", default="data/processed/phase4/metrics_by_k.parquet", help="Input parquet path.")
    parser.add_argument("--output-dir", default="reports/figures/phase4", help="Directory for output figures.")
    main(parser.parse_args())
