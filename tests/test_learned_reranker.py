"""Tests for the Task 2.3 learned reranker: feature frame shape, label leakage, tiny-fixture training."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import pytest
from joblib import load
from scipy.sparse import csr_matrix

from src.models.learned_reranker import (
    FEATURES,
    ItemSide,
    ServedReranker,
    blend_scores,
    build_feature_frame,
    ranked_lists,
    save_reranker,
    train_ranker,
)

N_ITEMS = 30
WEIGHTS = {"mf": 0.05, "knn": 0.95, "pop": 0.0003}


@pytest.fixture
def items() -> ItemSide:
    rng = np.random.default_rng(0)
    ids = np.arange(100, 100 + N_ITEMS)
    genres = [["Action", "Drama"][: 1 + i % 2] if i % 3 else ["Comedy"] for i in range(N_ITEMS)]
    metadata = pd.DataFrame({
        "anime_id": ids,
        "genres": genres,
        "themes": [["School"] if i % 4 == 0 else [] for i in range(N_ITEMS)],
        "mal_score": np.linspace(5.0, 9.0, N_ITEMS),
        "members_count": np.arange(N_ITEMS) * 1000.0,
        "episodes": np.full(N_ITEMS, 12.0),
        "aired_from": ["2015-04-01T00:00:00+00:00"] * N_ITEMS,
        "type": ["TV", "Movie"] * (N_ITEMS // 2),
    })
    tfidf = csr_matrix(rng.random((N_ITEMS, 8)) * (rng.random((N_ITEMS, 8)) > 0.5))
    # Neural embeddings deliberately miss the last item: it must get a zero row, not a crash.
    neural_ids = ids[:-1]
    neural = rng.normal(size=(N_ITEMS - 1, 4))
    pop = {int(a): float(N_ITEMS - k) for k, a in enumerate(ids)}
    return ItemSide.build(ids, pop, metadata, tfidf_ids=ids, tfidf_matrix=tfidf,
                          neural_ids=neural_ids, neural_matrix=neural)


def _scorers(n_items: int):
    def mf(u: int) -> np.ndarray:
        if u == 3:  # a user MF never saw
            return np.full(n_items, np.nan)
        return np.random.default_rng(u).normal(7.0, 1.0, n_items)

    def knn(u: int) -> np.ndarray:
        return np.random.default_rng(1000 + u).uniform(-0.5, 0.5, n_items)

    return {"mf": mf, "knn": knn}


@pytest.fixture
def histories() -> tuple[dict[int, list[int]], dict[int, set[int]]]:
    train_hist = {0: [100, 101, 102], 1: [110, 111], 2: [120], 3: [105, 106, 107, 108]}
    holdout = {0: {103}, 1: {112}, 2: {125}, 3: {109}}
    return train_hist, holdout


def test_frame_shape_groups_and_candidates(items, histories):
    train_hist, holdout = histories
    frame = build_feature_frame([0, 1, 2, 3], items, _scorers(N_ITEMS), train_hist, holdout, WEIGHTS, n_candidates=10)

    assert len(frame) == 4 * 10
    assert set(FEATURES) | {"user_id", "anime_id", "label"} == set(frame.columns)
    # Users are contiguous, in input order, each in blend order.
    assert frame["user_id"].drop_duplicates().tolist() == [0, 1, 2, 3]
    for u, part in frame.groupby("user_id"):
        assert part["blend_rank"].tolist() == list(range(10))
        assert part["blend_score"].is_monotonic_decreasing
        assert not set(part["anime_id"]) & set(train_hist[u])
        assert part["history_len"].unique().tolist() == [len(train_hist[u])]
    # The MF-unknown user keeps NaN MF features rather than a fake score.
    assert frame.loc[frame["user_id"] == 3, "mf_score"].isna().all()


def test_candidates_are_the_blend_top_n(items, histories):
    train_hist, holdout = histories
    scorers = _scorers(N_ITEMS)
    frame = build_feature_frame([0], items, scorers, train_hist, holdout, WEIGHTS, n_candidates=5)

    blend = blend_scores(scorers["mf"](0), scorers["knn"](0), items.pop, WEIGHTS)
    for i in train_hist[0]:
        blend[items.pos[i]] = -np.inf
    expected = [int(items.item_ids[j]) for j in np.argsort(-blend)[:5]]
    assert frame["anime_id"].tolist() == expected
    assert ranked_lists(frame) == {0: expected}


def test_held_out_items_never_reach_the_features(items, histories):
    """Swap every user's held-out item: only `label` may change."""
    train_hist, holdout = histories
    scorers = _scorers(N_ITEMS)
    a = build_feature_frame([0, 1, 2, 3], items, scorers, train_hist, holdout, WEIGHTS, n_candidates=N_ITEMS)
    other = {u: {int(items.item_ids[-1 - u])} for u in holdout}
    b = build_feature_frame([0, 1, 2, 3], items, scorers, train_hist, other, WEIGHTS, n_candidates=N_ITEMS)

    pd.testing.assert_frame_equal(a.drop(columns="label"), b.drop(columns="label"))
    assert not a["label"].equals(b["label"])
    for u, target in holdout.items():
        assert a.loc[(a["user_id"] == u) & (a["label"] == 1), "anime_id"].tolist() == sorted(target)


def test_holdout_inside_train_history_is_refused(items, histories):
    train_hist, holdout = histories
    leaked = {**holdout, 0: {train_hist[0][0]}}
    with pytest.raises(ValueError, match="train history"):
        build_feature_frame([0], items, _scorers(N_ITEMS), train_hist, leaked, WEIGHTS)


def _synthetic_frame(n_users: int, n_cands: int, seed: int) -> pd.DataFrame:
    """Random features; the positive is the candidate with the highest `genre_overlap`."""
    rng = np.random.default_rng(seed)
    n = n_users * n_cands
    frame = pd.DataFrame(rng.random((n, len(FEATURES))), columns=list(FEATURES))
    frame["user_id"] = np.repeat(np.arange(n_users), n_cands)
    frame["anime_id"] = np.tile(np.arange(n_cands), n_users)
    frame["blend_rank"] = np.tile(np.arange(n_cands, dtype=float), n_users)
    best = frame.groupby("user_id")["genre_overlap"].transform("max")
    frame["label"] = (frame["genre_overlap"] == best).astype(np.int8)
    return frame


def test_ranker_trains_on_a_tiny_fixture(tmp_path):
    pytest.importorskip("lightgbm")
    train, val, test = _synthetic_frame(120, 15, 0), _synthetic_frame(30, 15, 1), _synthetic_frame(40, 15, 2)
    model = train_ranker(train, val, seed=0, params={"n_estimators": 60, "min_child_samples": 5})

    lists = ranked_lists(test, model.predict(test[list(FEATURES)]))
    positive = test[test["label"] == 1].set_index("user_id")["anime_id"]
    hit_at_1 = np.mean([lists[u][0] == positive[u] for u in lists])
    assert hit_at_1 > 0.5  # chance is 1 in 15

    served = ServedReranker(model=model, features=list(FEATURES), pop={}, weights=WEIGHTS)
    path = save_reranker(served, tmp_path)
    assert re.fullmatch(r"learned_reranker_v\d{4}\.\d{2}\.\d{2}_\d{6}\.joblib", path.name)
    assert isinstance(load(path), ServedReranker)


def test_served_scores_match_the_training_features(items, histories):
    """The app scores the blend's candidates through `ServedReranker.score`; it must build the
    exact frame the ranker was trained on, or serving drifts from what was measured."""
    pytest.importorskip("lightgbm")
    train_hist, holdout = histories
    scorers = _scorers(N_ITEMS)
    frame = build_feature_frame([0, 1, 2], items, scorers, train_hist, holdout, WEIGHTS, n_candidates=12)
    model = train_ranker(frame, seed=0, params={"n_estimators": 10, "min_child_samples": 1})
    pop = {int(a): float(p) for a, p in zip(items.item_ids, items.pop)}
    served = ServedReranker(model=model, features=list(FEATURES), pop=pop, weights=WEIGHTS)

    part = frame[frame["user_id"] == 1]
    got = served.score(items, scorers["mf"](1), scorers["knn"](1), train_hist[1], part["anime_id"].tolist())
    np.testing.assert_allclose(got, model.predict(part[list(FEATURES)]))


def test_training_needs_a_user_with_a_positive():
    pytest.importorskip("lightgbm")
    frame = _synthetic_frame(5, 4, 0).assign(label=0)
    with pytest.raises(ValueError, match="held-out item"):
        train_ranker(frame)
