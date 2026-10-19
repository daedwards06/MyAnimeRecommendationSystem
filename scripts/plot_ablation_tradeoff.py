#!/usr/bin/env python
"""Accuracy vs. coverage across the ablation variants: the README hero chart.

Reads `reports/phase4_ablation.csv` (K=10, one row per variant, with bootstrap CIs) and draws
NDCG@10 (x, with its 95% CI as a horizontal error bar) against Coverage@10 (y, log scale: the
variants span 0.6% to 17% of the catalog). Popularity, MF and the served blend are highlighted;
every point is labeled. With `reports/phase4_ablation_by_k.csv` alongside, it also draws NDCG@K
against K.

Outputs: reports/figures/ablation_accuracy_vs_coverage.png, reports/figures/ablation_ndcg_at_k.png

Usage:
    python scripts/plot_ablation_tradeoff.py
"""
from __future__ import annotations

import argparse
from itertools import pairwise
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

LABELS = {
    "popularity": "Popularity",
    "item_knn_sklearn": "Item-kNN (= Diversity preset)",
    "mf_sgd": "MF (FunkSVD)",
    "implicit_als": "Implicit ALS (offline only)",
    "hybrid_mf_knn": "MF + kNN, no popularity",
    "hybrid_weighted_tuned": "Hybrid, re-tuned (served)",
    "hybrid_weighted": "Hybrid, pre-0.6 weights",
    "hybrid_rrf": "Hybrid, RRF",
    "content_tfidf": "Content TF-IDF",
    "content_embeddings": "Content embeddings",
}
# The first three categorical slots of the reference palette, which hold up when every pair is
# on screen at once (a scatter); everything else recedes to gray.
HIGHLIGHT = {"popularity": "#eb6834", "mf_sgd": "#2a78d6", "hybrid_weighted_tuned": "#1baf7a"}
MUTED = "#8a8984"
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
# Label placement (offset in points, horizontal alignment) for points that sit in clusters at
# this cohort; anything not listed is labeled up and to the right.
LABEL_OFFSETS = {
    "item_knn_sklearn": ((-8, 7), "right"),
    "hybrid_mf_knn": ((9, 1), "left"),
    "hybrid_weighted_tuned": ((9, -13), "left"),
    "mf_sgd": ((-8, 7), "right"),
    "content_embeddings": ((0, -16), "center"),
    "hybrid_weighted": ((9, -11), "left"),
    "hybrid_rrf": ((9, -12), "left"),
}


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.xaxis.label.set_color(TEXT_SECONDARY)
    ax.yaxis.label.set_color(TEXT_SECONDARY)


def _label(model: str) -> str:
    return LABELS.get(model, model)


def plot_tradeoff(ablation: pd.DataFrame, out_path: Path, caption: str | None = None) -> Path:
    """NDCG@10 vs Coverage@10, one labeled point per variant, NDCG CI as a horizontal bar."""
    fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=SURFACE)
    _style(ax)
    has_ci = {"ndcg@10_ci_low", "ndcg@10_ci_high"} <= set(ablation.columns)
    # Gray points first so the highlighted ones draw on top.
    rows = sorted((r for _, r in ablation.iterrows()), key=lambda r: r["model"] in HIGHLIGHT)
    for r in rows:
        model, x, y = r["model"], r["ndcg@10"], r["coverage@10"]
        color = HIGHLIGHT.get(model, MUTED)
        if has_ci:
            ax.errorbar(
                x, y, xerr=[[x - r["ndcg@10_ci_low"]], [r["ndcg@10_ci_high"] - x]],
                fmt="none", ecolor=color, elinewidth=2, capsize=0, alpha=0.45, zorder=2,
            )
        ax.scatter([x], [y], s=70, color=color, edgecolors=SURFACE, linewidths=2, zorder=3)
        offset, ha = LABEL_OFFSETS.get(model, ((7, 6), "left"))
        ax.annotate(
            _label(model), (x, y), xytext=offset, textcoords="offset points", ha=ha, fontsize=9,
            color=TEXT if model in HIGHLIGHT else TEXT_SECONDARY,
            fontweight="bold" if model in HIGHLIGHT else "normal", zorder=4,
        )

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}" if v >= 0.01 else f"{v:.1%}"))
    ax.set_xlim(left=0)
    ax.set_xlabel("NDCG@10 (ranking accuracy; bar = 95% bootstrap CI)")
    ax.set_ylabel("Coverage@10 (share of catalog recommended, log scale)")
    ax.set_title("Accuracy vs. catalog coverage across model variants", loc="left", color=TEXT, fontsize=12, pad=12)
    if caption:
        fig.text(0.01, 0.01, caption, fontsize=8, color=TEXT_SECONDARY, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04 if caption else 0, 1, 1))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
    return out_path


def _spread(values: list[float], gap: float) -> list[float]:
    """Nudge sorted label positions apart so no two are closer than `gap`, keeping their order."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = list(values)
    for prev, cur in pairwise(order):
        out[cur] = max(out[cur], out[prev] + gap)
    return out


def plot_ndcg_by_k(by_k: pd.DataFrame, out_path: Path, caption: str | None = None) -> Path:
    """NDCG@K against K, one line per variant, highlighted ones in color, all labeled at the right end."""
    fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=SURFACE)
    _style(ax)
    ks = sorted(by_k["K"].unique())
    models = sorted(by_k["model"].unique(), key=lambda m: m in HIGHLIGHT)
    ends = []
    for model in models:
        line = by_k[by_k["model"] == model].sort_values("K")
        color = HIGHLIGHT.get(model, MUTED)
        ax.plot(line["K"], line["ndcg"], color=color, linewidth=2, marker="o", markersize=6,
                markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3 if model in HIGHLIGHT else 2)
        ends.append((model, line["K"].iloc[-1], line["ndcg"].iloc[-1]))
    gap = 0.045 * by_k["ndcg"].max()
    for (model, k, y), label_y in zip(ends, _spread([e[2] for e in ends], gap)):
        ax.plot([k + 0.2, k + 0.8], [y, label_y], color=GRID, linewidth=1, zorder=1)
        ax.text(
            k + 0.8, label_y, _label(model), va="center", zorder=5,
            bbox={"boxstyle": "square,pad=0.15", "facecolor": SURFACE, "edgecolor": "none"},
            fontsize=8.5, color=TEXT if model in HIGHLIGHT else TEXT_SECONDARY,
            fontweight="bold" if model in HIGHLIGHT else "normal",
        )
    ax.set_xticks(ks)
    ax.set_xlim(min(ks) - 1, max(ks) + 9)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("K (length of the recommendation list)")
    ax.set_ylabel("NDCG@K")
    ax.set_title("NDCG@K by model variant", loc="left", color=TEXT, fontsize=12, pad=12)
    if caption:
        fig.text(0.01, 0.01, caption, fontsize=8, color=TEXT_SECONDARY, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04 if caption else 0, 1, 1))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
    return out_path


def main(args: argparse.Namespace) -> None:
    ablation = pd.read_csv(args.ablation_csv)
    cohort = int(ablation["users_evaluated"].iloc[0])
    caption = f"{cohort:,} validation users, seed 42, full-catalog ranking, models fit on the train split only."
    print(f"Saved: {plot_tradeoff(ablation, Path(args.output), caption)}")
    by_k_path = Path(args.by_k_csv)
    if by_k_path.exists():
        print(f"Saved: {plot_ndcg_by_k(pd.read_csv(by_k_path), Path(args.output_by_k), caption)}")
    else:
        print(f"WARN: {by_k_path} not found; skipped the NDCG@K plot.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ablation-csv", default="reports/phase4_ablation.csv")
    parser.add_argument("--by-k-csv", default="reports/phase4_ablation_by_k.csv")
    parser.add_argument("--output", default="reports/figures/ablation_accuracy_vs_coverage.png")
    parser.add_argument("--output-by-k", default="reports/figures/ablation_ndcg_at_k.png")
    main(parser.parse_args())
