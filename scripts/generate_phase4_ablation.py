#!/usr/bin/env python
"""Generate Phase 4 ablation table comparing models at K=10.

Outputs CSV + Markdown with relative lifts vs popularity baseline.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.eval.phase4_utils import compute_lifts

TARGET_K = 10
BASELINE_MODEL = "popularity"
MODELS = ["popularity", "mf", "hybrid", "content_tfidf"]
METRICS = ["ndcg", "map", "coverage"]


def to_markdown_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False, floatfmt=".4f")


def main(args: argparse.Namespace) -> None:
    metrics = pd.read_parquet(args.metrics_path)
    subset = metrics[(metrics["K"] == TARGET_K) & (metrics["model"].isin(MODELS))]
    if subset.empty:
        raise ValueError("No rows found for target K and models.")
    ablation_raw = compute_lifts(subset,
                                 baseline_model=BASELINE_MODEL,
                                 metrics=METRICS)
    # Rename metric columns with @10 suffix for clarity
    rename = {m: f"{m}@10" for m in METRICS}
    ablation = ablation_raw.rename(columns=rename)

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    ablation.to_csv(out_csv, index=False)
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Phase 4 Ablation (K=10)\n\n")
        f.write(to_markdown_table(ablation))
        f.write("\n")

    print(f"Wrote ablation CSV: {out_csv}")
    print(f"Wrote ablation Markdown: {out_md}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-path", default="data/processed/phase4/metrics_by_k.parquet", help="Input metrics parquet path.")
    parser.add_argument("--output-csv", default="reports/phase4_ablation.csv", help="CSV output file.")
    parser.add_argument("--output-md", default="reports/phase4_ablation.md", help="Markdown output file.")
    main(parser.parse_args())
