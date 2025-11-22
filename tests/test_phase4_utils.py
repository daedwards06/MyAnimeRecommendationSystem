from __future__ import annotations
import numpy as np
import pandas as pd
from src.eval.phase4_utils import compute_lifts, json_safe


def test_compute_lifts_zero_baseline():
    df = pd.DataFrame([
        {"model": "popularity", "ndcg": 0.0, "map": 0.02, "coverage": 0.01},
        {"model": "mf", "ndcg": 0.05, "map": 0.03, "coverage": 0.06},
    ])
    out = compute_lifts(df, baseline_model="popularity", metrics=["ndcg", "map", "coverage"])
    pop_row = out[out["model"] == "popularity"].iloc[0]
    mf_row = out[out["model"] == "mf"].iloc[0]
    assert pop_row["ndcg_lift_vs_popularity_pct"] is None
    assert mf_row["ndcg_lift_vs_popularity_pct"] is None  # baseline ndcg was zero => None
    assert mf_row["map_lift_vs_popularity_pct"] == ((0.03 - 0.02) / 0.02) * 100


def test_json_safe_numpy_scalars():
    obj = {"a": np.int64(5), "b": np.float64(3.14), "c": [np.int64(2), np.float64(1.5)]}
    conv = json_safe(obj)
    assert isinstance(conv["a"], int)
    assert isinstance(conv["b"], float)
    assert isinstance(conv["c"][0], int)
    assert isinstance(conv["c"][1], float)
