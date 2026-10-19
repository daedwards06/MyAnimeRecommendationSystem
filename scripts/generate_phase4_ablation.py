#!/usr/bin/env python
"""Generate the Phase 4 ablation table from one cohort: the K=10 table, and every K the run has.

Reads the parquet written by `aggregate_phase4_metrics.py` and writes CSV + Markdown with
raw metrics and relative lifts against the popularity baseline, MF, and item-kNN.
`phase4_ablation.csv` is K=10 only (the README and model card quote it);
`phase4_ablation_by_k.csv` stacks the same columns for every K, with a `K` column.

With the per-user parquet alongside, each model also gets a 95% bootstrap CI on NDCG@10 and
MAP@10, and a *paired* bootstrap CI on its NDCG@10 difference from each reference model
(users resampled jointly, since every model is scored on the same cohort). A comparison whose
paired interval spans zero is a tie, whatever its point estimate says.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import argparse
import pandas as pd
from src.eval.bootstrap import bootstrap_mean_ci, paired_bootstrap_diff_ci
from src.eval.phase4_utils import compute_lifts

TARGET_K = 10
BASELINE_MODEL = "popularity"
REFERENCE_MODEL = "mf_sgd"
# The strongest single model; any blend has to beat it to be worth serving. Optional so a
# partial table still builds.
STRONGEST_SINGLE_MODEL = "item_knn_sklearn"
MODELS = [
    "popularity",
    "item_knn_sklearn",
    "mf_sgd",
    "implicit_als",
    "hybrid_mf_knn",
    "hybrid_weighted",
    "hybrid_weighted_legacy",
    "hybrid_weighted_tuned",
    "hybrid_rrf",
    "content_tfidf",
    "content_embeddings",
]
METRICS = ["ndcg", "map", "coverage", "gini"]
LIFT_METRICS = ["ndcg", "map"]
CI_METRICS = ["ndcg", "map"]


def references(models) -> list[str]:
    present = set(models)
    return [BASELINE_MODEL, REFERENCE_MODEL] + [m for m in (STRONGEST_SINGLE_MODEL,) if m in present]


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


def build_ablation(metrics: pd.DataFrame, k: int = TARGET_K) -> pd.DataFrame:
    subset = metrics[(metrics["K"] == k) & (metrics["model"].isin(MODELS))]
    if subset.empty:
        raise ValueError(f"No rows found for K={k} and models {MODELS}.")

    cohorts = sorted(subset["users_evaluated"].dropna().unique().tolist())
    if len(cohorts) > 1:
        raise ValueError(
            f"Rows span multiple cohorts ({cohorts}); models evaluated on different user samples "
            "are not comparable. Re-run aggregate_phase4_metrics.py with --cohort."
        )

    ablation = subset[["model", "users_evaluated", *METRICS]].copy()
    for ref in references(subset["model"]):
        frame = compute_lifts(subset, baseline_model=ref, metrics=LIFT_METRICS)
        lift_cols = [c for c in frame.columns if c.endswith("_pct")]
        ablation = ablation.merge(frame[["model", *lift_cols]], on="model", how="left")

    ablation = ablation.rename(columns={m: f"{m}@{k}" for m in METRICS})
    return ablation.sort_values(f"ndcg@{k}", ascending=False).reset_index(drop=True)


def add_intervals(ablation: pd.DataFrame, per_user: pd.DataFrame, k: int = TARGET_K) -> pd.DataFrame:
    """Attach bootstrap CIs computed from per-user vectors aligned on user_id."""
    per_user = per_user[(per_user["K"] == k) & (per_user["model"].isin(ablation["model"]))]
    wide = {m: per_user.pivot_table(index="user_id", columns="model", values=m) for m in CI_METRICS}
    missing = sorted(set(ablation["model"]) - set(wide["ndcg"].columns))
    if missing:
        raise ValueError(f"No per-user vectors for {missing}; re-run their evaluation before building intervals.")
    if wide["ndcg"].isna().any().any():
        raise ValueError("Models were scored on different users; paired intervals need one cohort.")

    out = ablation.copy()
    for m in CI_METRICS:
        col = f"{m}@{k}"
        lows, highs = [], []
        for model, point in zip(out["model"], out[col]):
            mean, low, high = bootstrap_mean_ci(wide[m][model].to_numpy())
            if abs(mean - point) > 1e-9:
                raise ValueError(f"{model}: per-user mean {mean} does not reproduce the reported {col} {point}")
            lows.append(low)
            highs.append(high)
        out[f"{col}_ci_low"] = lows
        out[f"{col}_ci_high"] = highs

    for ref in references(out["model"]):
        diffs, lows, highs = [], [], []
        for model in out["model"]:
            diff, low, high = paired_bootstrap_diff_ci(wide["ndcg"][model].to_numpy(), wide["ndcg"][ref].to_numpy())
            diffs.append(diff)
            lows.append(low)
            highs.append(high)
        out[f"ndcg_diff_vs_{ref}"] = diffs
        out[f"ndcg_diff_vs_{ref}_ci_low"] = lows
        out[f"ndcg_diff_vs_{ref}_ci_high"] = highs
    return out


def ablation_by_k(metrics: pd.DataFrame, per_user: pd.DataFrame) -> pd.DataFrame:
    """Every K in the run, long format: one row per (K, model), columns without the `@K` suffix."""
    frames = []
    for k in sorted(metrics.loc[metrics["model"].isin(MODELS), "K"].unique()):
        frame = add_intervals(build_ablation(metrics, k), per_user, k)
        frame.columns = [c.replace(f"@{k}", "") for c in frame.columns]
        frames.append(frame.assign(K=int(k)))
    out = pd.concat(frames, ignore_index=True)
    return out[["K", *[c for c in out.columns if c != "K"]]]


def by_k_markdown(by_k: pd.DataFrame) -> str:
    """NDCG with its interval, coverage and Gini at each K, one row per model."""
    order = by_k[by_k["K"] == TARGET_K].sort_values("ndcg", ascending=False)["model"].tolist()
    ks = sorted(by_k["K"].unique())
    view = pd.DataFrame({"model": order})
    for k in ks:
        at_k = by_k[by_k["K"] == k].set_index("model").reindex(order)
        view[f"ndcg@{k} [95% CI]"] = [
            "—" if pd.isna(n) else f"{n:.4f} [{lo:.4f}, {hi:.4f}]"
            for n, lo, hi in zip(at_k["ndcg"], at_k["ndcg_ci_low"], at_k["ndcg_ci_high"])
        ]
    for metric in ("coverage", "gini"):
        for k in ks:
            view[f"{metric}@{k}"] = by_k[by_k["K"] == k].set_index("model")[metric].reindex(order).to_numpy()
    return to_markdown_table(view)


def display_table(ablation: pd.DataFrame) -> pd.DataFrame:
    """The Markdown view: intervals folded into `[low, high]` cells; the CSV keeps every column."""
    def interval(low: float, high: float, signed: bool = False) -> str:
        fmt = "{:+.4f}" if signed else "{:.4f}"
        return f"[{fmt.format(low)}, {fmt.format(high)}]"

    view = pd.DataFrame({"model": ablation["model"], "users_evaluated": ablation["users_evaluated"]})
    for m in METRICS:
        col = f"{m}@{TARGET_K}"
        view[col] = ablation[col]
        if f"{col}_ci_low" in ablation.columns:
            view[f"{col} 95% CI"] = [interval(lo, hi) for lo, hi in zip(ablation[f"{col}_ci_low"], ablation[f"{col}_ci_high"])]
    for ref in references(ablation["model"]):
        view[f"ndcg_lift_vs_{ref}_pct"] = ablation[f"ndcg_lift_vs_{ref}_pct"]
        if f"ndcg_diff_vs_{ref}_ci_low" in ablation.columns:
            view[f"ndcg_diff_vs_{ref} 95% CI"] = [
                interval(lo, hi, signed=True)
                for lo, hi in zip(ablation[f"ndcg_diff_vs_{ref}_ci_low"], ablation[f"ndcg_diff_vs_{ref}_ci_high"])
            ]
    return view


def main(args: argparse.Namespace) -> None:
    metrics = pd.read_parquet(args.metrics_path)
    per_user = pd.read_parquet(args.per_user_path)
    ablation = add_intervals(build_ablation(metrics), per_user)
    markdown = to_markdown_table(display_table(ablation))
    by_k = ablation_by_k(metrics, per_user)

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    cohort = int(ablation["users_evaluated"].iloc[0])
    ablation.to_csv(out_csv, index=False)
    out_by_k = Path(args.output_by_k_csv)
    by_k.to_csv(out_by_k, index=False)
    with out_md.open("w", encoding="utf-8") as f:
        f.write(f"# Phase 4 Ablation (K={TARGET_K})\n\n")
        f.write(f"One cohort: {cohort} sampled users, seed 42, ranking over the full catalog.\n")
        f.write("Lifts are relative percentages against popularity, MF and item-kNN (the strongest single model).\n")
        f.write("Intervals are 95% percentile bootstrap (users resampled, 1,000 resamples, seed 42); the\n")
        f.write("`ndcg_diff` intervals are paired (same users resampled for both models), so an interval\n")
        f.write("that spans zero means the two models are not distinguishable on this cohort.\n")
        f.write("MAP lifts and every interval bound are in the CSV.\n\n")
        f.write("`implicit_als` is the offline implicit-feedback MF from `reports/mf_diagnostic.md`; it is not\n")
        f.write("served. `hybrid_mf_knn` is the re-tuned blend with its popularity term removed. The app's\n")
        f.write("Diversity preset is item-kNN alone (`{knn: 1.0}`), so offline it is the `item_knn_sklearn` row.\n\n")
        f.write(markdown)
        f.write("\n")
        ks = ", ".join(str(k) for k in sorted(by_k["K"].unique()))
        f.write(f"\n## Across K ({ks})\n\n")
        f.write("Same cohort and protocol; the interval is the bootstrap CI on NDCG@K. Every column, including\n")
        f.write(f"MAP and the paired differences at each K, is in `{out_by_k.as_posix()}`.\n\n")
        f.write(by_k_markdown(by_k))
        f.write("\n")

    print(f"Wrote ablation CSV: {out_csv}")
    print(f"Wrote ablation by K CSV: {out_by_k}")
    print(f"Wrote ablation Markdown: {out_md}")
    print(markdown)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-path", default="data/processed/phase4/metrics_by_k.parquet", help="Input metrics parquet path.")
    parser.add_argument("--per-user-path", default="data/processed/phase4/per_user_metrics.parquet", help="Per-user metrics parquet path.")
    parser.add_argument("--output-csv", default="reports/phase4_ablation.csv", help="CSV output file.")
    parser.add_argument("--output-by-k-csv", default="reports/phase4_ablation_by_k.csv", help="CSV output for every K.")
    parser.add_argument("--output-md", default="reports/phase4_ablation.md", help="Markdown output file.")
    main(parser.parse_args())
