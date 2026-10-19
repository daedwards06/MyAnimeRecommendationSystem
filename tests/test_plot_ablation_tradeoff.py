"""The ablation trade-off plot renders from a small frame and writes PNGs."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


plot_ablation_tradeoff = _load_script("plot_ablation_tradeoff")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _fixture() -> pd.DataFrame:
    return pd.DataFrame({
        "model": ["popularity", "mf_sgd", "item_knn_sklearn"],
        "users_evaluated": [1000, 1000, 1000],
        "ndcg@10": [0.035, 0.028, 0.063],
        "ndcg@10_ci_low": [0.026, 0.020, 0.051],
        "ndcg@10_ci_high": [0.044, 0.038, 0.078],
        "coverage@10": [0.0056, 0.067, 0.117],
    })


def test_tradeoff_plot_writes_a_png(tmp_path: Path):
    out = plot_ablation_tradeoff.plot_tradeoff(_fixture(), tmp_path / "fig" / "tradeoff.png", caption="1,000 users")

    assert out.read_bytes()[:8] == PNG_MAGIC


def test_tradeoff_plot_runs_without_intervals(tmp_path: Path):
    frame = _fixture().drop(columns=["ndcg@10_ci_low", "ndcg@10_ci_high"])

    out = plot_ablation_tradeoff.plot_tradeoff(frame, tmp_path / "tradeoff.png")

    assert out.read_bytes()[:8] == PNG_MAGIC


def test_ndcg_by_k_plot_writes_a_png(tmp_path: Path):
    by_k = pd.concat(
        [_fixture().rename(columns={"ndcg@10": "ndcg"}).assign(K=k, ndcg=lambda f, k=k: f["ndcg"] * k / 10) for k in (5, 10, 20)],
        ignore_index=True,
    )

    out = plot_ablation_tradeoff.plot_ndcg_by_k(by_k, tmp_path / "by_k.png")

    assert out.read_bytes()[:8] == PNG_MAGIC
