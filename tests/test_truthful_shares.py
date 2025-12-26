from __future__ import annotations

import numpy as np

from src.app.recommender import HybridComponents, HybridRecommender, compute_component_shares
from src.app.explanations import format_explanation


def test_component_shares_sum_to_one_for_used_components():
    mf = np.asarray([[1.0, 2.0, 3.0]], dtype=np.float32)
    knn = np.asarray([[0.2, 0.5, 0.1]], dtype=np.float32)
    pop = np.asarray([0.1, 0.1, 0.2], dtype=np.float32)
    item_ids = np.asarray([10, 11, 12], dtype=np.int64)
    rec = HybridRecommender(HybridComponents(mf=mf, knn=knn, pop=pop, item_ids=item_ids))

    weights = {"mf": 0.6, "knn": 0.3, "pop": 0.1}
    recs = rec.get_top_n_for_user(0, n=3, weights=weights)
    assert len(recs) == 3

    for r in recs:
        shares = r["explanation"]
        used = shares.get("_used", ["mf", "knn", "pop"])
        s = sum(float(shares.get(k, 0.0)) for k in used)
        assert abs(s - 1.0) <= 0.005


def test_weight_preset_changes_affect_shares_for_at_least_one_item():
    mf = np.asarray([[1.0, 2.0, 3.0]], dtype=np.float32)
    knn = np.asarray([[1.5, 0.1, 0.1]], dtype=np.float32)
    pop = np.asarray([0.1, 0.1, 0.1], dtype=np.float32)
    item_ids = np.asarray([10, 11, 12], dtype=np.int64)
    rec = HybridRecommender(HybridComponents(mf=mf, knn=knn, pop=pop, item_ids=item_ids))

    # Pick a stable item index and compare shares directly.
    item_index = 0
    a = rec.explain_item(0, item_index, {"mf": 0.9, "knn": 0.1, "pop": 0.0})
    b = rec.explain_item(0, item_index, {"mf": 0.5, "knn": 0.5, "pop": 0.0})

    # At least one of mf/knn shares should change.
    assert (abs(a.get("mf", 0.0) - b.get("mf", 0.0)) > 1e-6) or (
        abs(a.get("knn", 0.0) - b.get("knn", 0.0)) > 1e-6
    )


def test_negative_raw_contributions_are_not_shown_as_negative_share():
    shares = compute_component_shares({"mf": -1.0, "knn": 2.0, "pop": 0.0}, used_components=["mf", "knn"])
    assert shares["mf"] == 0.0
    assert shares["knn"] == 1.0


def test_format_explanation_hides_unused_components():
    # Only mf+pop are used; knn should not appear in the formatted string.
    s = format_explanation({"mf": 0.8, "knn": 0.2, "pop": 0.2, "_used": ["mf", "pop"]})
    assert "knn" not in s
