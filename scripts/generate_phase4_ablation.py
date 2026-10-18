#!/usr/bin/env python
"""Generate the Phase 4 ablation table at K=10 from one cohort.

Reads the parquet written by `aggregate_phase4_metrics.py` and writes CSV + Markdown with
raw metrics and relative lifts against both the popularity baseline and MF, which is the
strongest single model and therefore the comparison the hybrid has to answer.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import argparse
import pandas as pd
from src.eval.phase4_utils import compute_lifts

TARGET_K = 10
BASELINE_MODEL = "popularity"
REFERENCE_MODEL = "mf_sgd"
MODELS = [
    "popularity",
    "item_knn_sklearn",
    "mf_sgd",
    "hybrid_weighted",
    "hybrid_rrf",
    "content_tfidf",
    "content_embeddings",
]
METRICS = ["ndcg", "map", "coverage", "gini"]
LIFT_METRICS = ["ndcg", "map"]


def to_markdown_table(df: pd.DataFrame) -> str:
    """Render a Markdown table without `tabulate`, which is not a project dependency."""
    def fmt(value) -> str:
        if pd.isna(value):
            return "—"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    header = "| " + " | ".join(df.columns) + " |"
    rule = "|" + "|".join("---:" if i else ":---" for i, _ in enumerate(df.columns)) + "|"
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, rule, *rows])


def build_ablation(metrics: pd.DataFrame) -> pd.DataFrame:
    subset = metrics[(metrics["K"] == TARGET_K) & (metrics["model"].isin(MODELS))]
    if subset.empty:
        raise ValueError(f"No rows found for K={TARGET_K} and models {MODELS}.")

    cohorts = sorted(subset["users_evaluated"].dropna().unique().tolist())
    if len(cohorts) > 1:
        raise ValueError(
            f"Rows span multiple cohorts ({cohorts}); models evaluated on different user samples "
            "are not comparable. Re-run aggregate_phase4_metrics.py with --cohort."
        )

    lifts_vs_pop = compute_lifts(subset, baseline_model=BASELINE_MODEL, metrics=LIFT_METRICS)
    lifts_vs_mf = compute_lifts(subset, baseline_model=REFERENCE_MODEL, metrics=LIFT_METRICS)

    ablation = subset[["model", "users_evaluated", *METRICS]].copy()
    for frame in (lifts_vs_pop, lifts_vs_mf):
        lift_cols = [c for c in frame.columns if c.endswith("_pct")]
        ablation = ablation.merge(frame[["model", *lift_cols]], on="model", how="left")

    ablation = ablation.rename(columns={m: f"{m}@{TARGET_K}" for m in METRICS})
    return ablation.sort_values(f"ndcg@{TARGET_K}", ascending=False).reset_index(drop=True)


def main(args: argparse.Namespace) -> None:
    metrics = pd.read_parquet(args.metrics_path)
    ablation = build_ablation(metrics)
    markdown = to_markdown_table(ablation)

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    cohort = int(ablation["users_evaluated"].iloc[0])
    ablation.to_csv(out_csv, index=False)
    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"# Phase 4 Ablation (K={TARGET_K})\n\n")
        f.write(f"One cohort: {cohort} sampled users, seed 42, ranking over the full catalog.\n")
        f.write("Lifts are relative percentages against the popularity baseline and against MF.\n\n")
        f.write(markdown)
        f.write("\n")

    print(f"Wrote ablation CSV: {out_csv}")
    print(f"Wrote ablation Markdown: {out_md}")
    print(markdown)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-path", default="data/processed/phase4/metrics_by_k.parquet", help="Input metrics parquet path.")
    parser.add_argument("--output-csv", default="reports/phase4_ablation.csv", help="CSV output file.")
    parser.add_argument("--output-md", default="reports/phase4_ablation.md", help="Markdown output file.")
    main(parser.parse_args())
