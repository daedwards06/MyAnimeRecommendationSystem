#!/usr/bin/env python
"""Aggregate per-model metrics JSON into one parquet for the Phase 4 ablation table.

Reads every metrics JSON under `experiments/metrics/`. Two shapes are accepted:

Flat (what `evaluate_knn_mf.py`, `evaluate_hybrid.py` and `evaluate_content_only.py` write):
{
  "model": "mf_sgd", "k": 10, "users_evaluated": 1000,
  "ndcg@k_mean": 0.0504, "map@k_mean": 0.0390,
  "item_coverage@k": 0.0711, "gini_index@k": 0.7841,
  "seed": 42, "generated_at": "2026-09-16T23:41:02+00:00"
}

Per-K (a single run reporting several K values):
{"model": "mf_sgd", "generated_at": "...", "users_evaluated": 1000,
 "metrics_by_k": [{"K": 10, "ndcg": ..., "map": ..., "coverage": ..., "gini": ...}]}

The directory accumulates every run ever made, so rows are deduplicated: the latest
`generated_at` wins per (model, K, users_evaluated). `--cohort` then restricts the output to a
single `users_evaluated`, because mixing cohorts in one table produces comparisons between runs
that sampled different users.

Runs that carry a `per_user` block ({"user_id": [...], "ndcg": [...], "map": [...]}) also feed a
long table, one row per (model, user), which the ablation resamples for its bootstrap intervals.

Outputs: `data/processed/phase4/metrics_by_k.parquet`,
`data/processed/phase4/per_user_metrics.parquet`

Usage:
    python scripts/aggregate_phase4_metrics.py --cohort 1000
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

REQUIRED_PER_K = {"K", "ndcg", "map", "coverage", "gini"}
FLAT_KEYS = {
    "ndcg": "ndcg@k_mean",
    "map": "map@k_mean",
    "coverage": "item_coverage@k",
    "gini": "gini_index@k",
}
OUTPUT_COLUMNS = [
    "model", "K", "ndcg", "map", "coverage", "gini",
    "users_evaluated", "seed", "generated_at", "source",
]
PER_USER_COLUMNS = ["model", "K", "users_evaluated", "user_id", "ndcg", "map"]
_FILENAME_TS = re.compile(r"_(\d{14})$")


class MetricCollisionError(SystemExit):
    """Two different models reported the same metric vector in one cohort."""


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_timestamp(obj: Dict[str, Any], path: Path) -> datetime:
    """Best available run time: explicit field, then the filename suffix, then file mtime."""
    for key in ("generated_at", "timestamp_utc"):
        raw = obj.get(key)
        if not raw:
            continue
        text = str(raw)
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
        try:
            return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    match = _FILENAME_TS.search(path.stem)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def extract_rows(obj: Dict[str, Any], path: Path) -> List[Dict[str, Any]]:
    model = obj.get("model") or obj.get("model_name")
    if not model:
        return []
    generated_at = parse_timestamp(obj, path)
    common = {
        "model": model,
        "users_evaluated": obj.get("users_evaluated"),
        "seed": obj.get("seed"),
        "generated_at": generated_at,
        "source": path.name,
        "per_user": obj.get("per_user"),
    }

    per_k = obj.get("metrics_by_k")
    if per_k:
        return [
            {**common, "K": e["K"], "ndcg": e["ndcg"], "map": e["map"],
             "coverage": e["coverage"], "gini": e["gini"]}
            for e in per_k
            if REQUIRED_PER_K.issubset(e.keys())
        ]

    if "k" not in obj or FLAT_KEYS["ndcg"] not in obj:
        return []
    return [{
        **common,
        "K": obj["k"],
        **{out: obj.get(src) for out, src in FLAT_KEYS.items()},
    }]


def dedupe_latest(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the most recent run per (model, K, users_evaluated)."""
    ordered = df.sort_values("generated_at")
    return ordered.drop_duplicates(subset=["model", "K", "users_evaluated"], keep="last")


def explode_per_user(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (model, user) from the runs that recorded per-user vectors."""
    frames = []
    for row in df.itertuples(index=False):
        block = getattr(row, "per_user", None)
        if not isinstance(block, dict) or not block.get("user_id"):
            continue
        frames.append(pd.DataFrame({
            "model": row.model,
            "K": row.K,
            "users_evaluated": row.users_evaluated,
            "user_id": block["user_id"],
            "ndcg": block["ndcg"],
            "map": block["map"],
        }))
    if not frames:
        return pd.DataFrame(columns=PER_USER_COLUMNS)
    return pd.concat(frames, ignore_index=True)[PER_USER_COLUMNS]


def find_metric_collisions(df: pd.DataFrame) -> List[tuple[str, str, int, int]]:
    """Distinct models with a bit-identical (ndcg, map) pair in the same cohort at the same K.

    A real collision means one of the two runs is not the model its label says: a mislabeled
    write, or a blend whose weights collapsed it onto another model's ranking.
    """
    collisions = []
    for (k, users, ndcg, mapv), group in df.groupby(["K", "users_evaluated", "ndcg", "map"], dropna=False):
        models = sorted(set(group["model"]))
        if len(models) > 1:
            for i, a in enumerate(models):
                for b in models[i + 1:]:
                    collisions.append((a, b, int(k), int(users) if pd.notna(users) else -1))
    return collisions


def aggregate(metrics_dir: Path) -> pd.DataFrame:
    all_rows: List[Dict[str, Any]] = []
    for path in sorted(metrics_dir.glob("*.json")):
        try:
            obj = load_json(path)
        except Exception as e:
            print(f"WARN: failed to read {path}: {e}")
            continue
        if not isinstance(obj, dict):
            continue
        all_rows.extend(extract_rows(obj, path))
    if not all_rows:
        raise SystemExit(f"No metrics extracted from {metrics_dir}; expected flat or 'metrics_by_k' JSON.")
    df = pd.DataFrame(all_rows)
    df = df.dropna(subset=["model", "K", "ndcg", "map"])
    if df.empty:
        raise SystemExit("Aggregated DataFrame is empty after dropping rows without model/K/ndcg/map.")
    return dedupe_latest(df).sort_values(["model", "K", "users_evaluated"]).reset_index(drop=True)


def main(args: argparse.Namespace) -> None:
    metrics_dir = Path(args.metrics_dir)
    if not metrics_dir.exists():
        raise SystemExit(f"Metrics directory does not exist: {metrics_dir}")
    df = aggregate(metrics_dir)

    if args.cohort is not None:
        df = df[df["users_evaluated"] == args.cohort]
        if df.empty:
            available = sorted(aggregate(metrics_dir)["users_evaluated"].dropna().unique().tolist())
            raise SystemExit(f"No rows with users_evaluated={args.cohort}; available cohorts: {available}")

    collisions = find_metric_collisions(df)
    if collisions:
        lines = [f"  {a} and {b} report identical (ndcg, map) at K={k}, users={u}" for a, b, k, u in collisions]
        message = (
            "Metric collision: two differently-labeled models produced the same numbers.\n"
            + "\n".join(lines)
            + "\nOne of these runs is probably not the model it is labeled as. Diagnose before "
              "publishing, or re-run with --allow-metric-collisions if the match is understood."
        )
        if not args.allow_metric_collisions:
            raise MetricCollisionError(message)
        print(f"WARN: {message}")

    out = df.copy()
    out["generated_at"] = out["generated_at"].map(lambda t: t.isoformat())
    out = out[[c for c in OUTPUT_COLUMNS if c in out.columns]]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    cohorts = sorted(out["users_evaluated"].dropna().unique().tolist())
    print(f"Wrote aggregated metrics parquet: {out_path} (rows={len(out)}, cohorts={cohorts})")

    per_user = explode_per_user(df)
    per_user_path = Path(args.per_user_output)
    per_user.to_parquet(per_user_path, index=False)
    missing = sorted(set(df["model"]) - set(per_user["model"]))
    print(f"Wrote per-user metrics parquet: {per_user_path} (rows={len(per_user)})")
    if missing:
        print(f"WARN: no per-user vectors for {missing}; their intervals cannot be computed. Re-run their eval.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-dir", default="experiments/metrics", help="Directory containing model metric JSON files.")
    parser.add_argument("--output", default="data/processed/phase4/metrics_by_k.parquet", help="Output parquet path.")
    parser.add_argument("--per-user-output", default="data/processed/phase4/per_user_metrics.parquet", help="Per-user metrics parquet path.")
    parser.add_argument("--cohort", type=int, default=None, help="Keep only rows with this users_evaluated value.")
    parser.add_argument("--allow-metric-collisions", action="store_true", help="Warn instead of failing when two models share a metric vector.")
    main(parser.parse_args())
