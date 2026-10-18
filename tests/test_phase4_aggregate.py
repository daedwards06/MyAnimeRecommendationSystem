"""Tests for the Phase 4 metrics aggregator and ablation table builder.

The published ablation was once ten rows all labeled `popularity`, spanning three cohorts, with
the headline lift computed against a duplicate baseline row. These tests pin the three
behaviours that prevent that: latest-wins dedupe, single-cohort output, and a guard on two
models reporting the same numbers.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


aggregate_phase4_metrics = _load_script("aggregate_phase4_metrics")
generate_phase4_ablation = _load_script("generate_phase4_ablation")


def _write_metrics(directory: Path, name: str, **fields) -> Path:
    payload = {
        "model": fields.pop("model"),
        "k": fields.pop("k", 10),
        "users_evaluated": fields.pop("users_evaluated", 1000),
        "ndcg@k_mean": fields.pop("ndcg", 0.05),
        "map@k_mean": fields.pop("map", 0.03),
        "item_coverage@k": fields.pop("coverage", 0.07),
        "gini_index@k": fields.pop("gini", 0.78),
    }
    payload.update(fields)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_extract_rows_reads_flat_schema(tmp_path: Path):
    path = _write_metrics(tmp_path, "mf_sgd_20260101000000", model="mf_sgd", ndcg=0.0504, seed=42)
    rows = aggregate_phase4_metrics.extract_rows(json.loads(path.read_text()), path)
    assert len(rows) == 1
    assert rows[0]["model"] == "mf_sgd"
    assert rows[0]["K"] == 10
    assert rows[0]["ndcg"] == 0.0504
    assert rows[0]["seed"] == 42


def test_extract_rows_reads_per_k_schema(tmp_path: Path):
    path = tmp_path / "mf_sgd_20260101000000.json"
    path.write_text(json.dumps({
        "model": "mf_sgd",
        "users_evaluated": 1000,
        "metrics_by_k": [
            {"K": 5, "ndcg": 0.04, "map": 0.03, "coverage": 0.05, "gini": 0.77},
            {"K": 10, "ndcg": 0.05, "map": 0.04, "coverage": 0.07, "gini": 0.78},
        ],
    }), encoding="utf-8")
    rows = aggregate_phase4_metrics.extract_rows(json.loads(path.read_text()), path)
    assert [r["K"] for r in rows] == [5, 10]


def test_extract_rows_skips_files_without_a_model(tmp_path: Path):
    path = tmp_path / "hybrid_examples_20260101000000.json"
    path.write_text(json.dumps({"14593": {"mf": [1, 2, 3]}}), encoding="utf-8")
    assert aggregate_phase4_metrics.extract_rows(json.loads(path.read_text()), path) == []


def test_timestamp_falls_back_to_filename(tmp_path: Path):
    path = _write_metrics(tmp_path, "mf_sgd_20251121202534", model="mf_sgd")
    stamp = aggregate_phase4_metrics.parse_timestamp(json.loads(path.read_text()), path)
    assert (stamp.year, stamp.month, stamp.day) == (2025, 11, 21)


def test_aggregate_keeps_latest_run_per_model_and_cohort(tmp_path: Path):
    _write_metrics(tmp_path, "mf_sgd_20251117164339", model="mf_sgd", ndcg=0.0413)
    _write_metrics(tmp_path, "mf_sgd_20251121202534", model="mf_sgd", ndcg=0.0497)
    df = aggregate_phase4_metrics.aggregate(tmp_path)
    assert len(df) == 1
    assert df.iloc[0]["ndcg"] == 0.0497


def test_aggregate_keeps_cohorts_apart(tmp_path: Path):
    _write_metrics(tmp_path, "popularity_20260101000000", model="popularity", users_evaluated=500, ndcg=0.0438)
    _write_metrics(tmp_path, "popularity_20260102000000", model="popularity", users_evaluated=1000, ndcg=0.0412)
    df = aggregate_phase4_metrics.aggregate(tmp_path)
    assert sorted(df["users_evaluated"]) == [500, 1000]


def test_metric_collision_between_two_models_is_detected():
    df = pd.DataFrame([
        {"model": "popularity", "K": 10, "users_evaluated": 1000, "ndcg": 0.0412, "map": 0.0279},
        {"model": "hybrid_weighted", "K": 10, "users_evaluated": 1000, "ndcg": 0.0412, "map": 0.0279},
    ])
    collisions = aggregate_phase4_metrics.find_metric_collisions(df)
    assert collisions == [("hybrid_weighted", "popularity", 10, 1000)]


def test_no_collision_when_models_differ():
    df = pd.DataFrame([
        {"model": "popularity", "K": 10, "users_evaluated": 1000, "ndcg": 0.0412, "map": 0.0279},
        {"model": "mf_sgd", "K": 10, "users_evaluated": 1000, "ndcg": 0.0504, "map": 0.0390},
    ])
    assert aggregate_phase4_metrics.find_metric_collisions(df) == []


def _ablation_frame(**overrides) -> pd.DataFrame:
    rows = [
        {"model": "popularity", "K": 10, "users_evaluated": 1000, "ndcg": 0.04, "map": 0.02, "coverage": 0.006, "gini": 0.73},
        {"model": "mf_sgd", "K": 10, "users_evaluated": 1000, "ndcg": 0.05, "map": 0.04, "coverage": 0.071, "gini": 0.78},
        {"model": "hybrid_weighted", "K": 10, "users_evaluated": 1000, "ndcg": 0.048, "map": 0.038, "coverage": 0.066, "gini": 0.79},
    ]
    frame = pd.DataFrame(rows)
    return frame.assign(**overrides) if overrides else frame


def test_ablation_uses_real_model_names_and_sorts_by_ndcg():
    ablation = generate_phase4_ablation.build_ablation(_ablation_frame())
    assert list(ablation["model"]) == ["mf_sgd", "hybrid_weighted", "popularity"]
    assert "gini@10" in ablation.columns
    assert "users_evaluated" in ablation.columns


def test_ablation_carries_lifts_against_both_baselines():
    ablation = generate_phase4_ablation.build_ablation(_ablation_frame())
    hybrid = ablation[ablation["model"] == "hybrid_weighted"].iloc[0]
    assert hybrid["ndcg_lift_vs_popularity_pct"] == pytest.approx((0.048 - 0.04) / 0.04 * 100)
    assert hybrid["ndcg_lift_vs_mf_sgd_pct"] == pytest.approx((0.048 - 0.05) / 0.05 * 100)


def test_ablation_refuses_mixed_cohorts():
    frame = _ablation_frame()
    frame.loc[frame["model"] == "popularity", "users_evaluated"] = 300
    with pytest.raises(ValueError, match="multiple cohorts"):
        generate_phase4_ablation.build_ablation(frame)


def test_markdown_table_has_one_row_per_model():
    ablation = generate_phase4_ablation.build_ablation(_ablation_frame())
    markdown = generate_phase4_ablation.to_markdown_table(ablation)
    body = [line for line in markdown.splitlines()[2:] if line.strip()]
    assert len(body) == 3
    assert [line.split("|")[1].strip() for line in body] == ["mf_sgd", "hybrid_weighted", "popularity"]
