#!/usr/bin/env python
"""Generate sample per-user top-K recommendations for multiple models.

Outputs parquet: data/processed/recommendations_sample.parquet
Columns: user_id, model, anime_id
Also writes popularity counts: data/processed/popularity.parquet

Models included:
  - popularity
  - mf
  - hybrid (weighted)
  - content_tfidf (user profile cosine over TF-IDF vectors)

Prerequisites:
  data/processed/interactions.parquet
  data/processed/item_features_tfidf.parquet
  mf_sgd_v1.0.joblib (optional; will train if missing)
  item_knn_sklearn_v1.0.joblib (optional)
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize
from joblib import load

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, DEFAULT_SAMPLE_USERS, TOP_K_DEFAULT, DEFAULT_HYBRID_WEIGHTS
from src.eval.splits import build_validation, sample_user_ids
from src.models.baselines import popularity_scores
from src.models.mf_sgd import FunkSVDRecommender
from src.models.knn_sklearn import ItemKNNRecommender
from src.models.hybrid import weighted_blend

OUT_RECS = DATA_PROCESSED_DIR / "recommendations_sample.parquet"
OUT_POP = DATA_PROCESSED_DIR / "popularity.parquet"


def _load_tfidf_matrix() -> tuple[pd.Index, np.ndarray]:
    path = DATA_PROCESSED_DIR / "item_features_tfidf.parquet"
    df = pd.read_parquet(path)
    if "anime_id" in df.columns:
        df = df.set_index("anime_id")
    mat = normalize(df.to_numpy(dtype=np.float32, copy=False), axis=1)
    return df.index, mat


def _user_profile_cosine(item_index: pd.Index, item_mat: np.ndarray, seen: set[int], top_k: int) -> list[int]:
    if not seen:
        return []
    valid = [i for i in seen if i in set(item_index)]
    if not valid:
        return []
    idxs = [int(np.where(item_index == i)[0][0]) for i in valid]
    prof = item_mat[idxs].mean(axis=0)
    n = np.linalg.norm(prof)
    if n == 0:
        return []
    prof = prof / n
    sims = item_mat @ prof
    for i in valid:
        loc = np.where(item_index == i)[0]
        if loc.size:
            sims[int(loc[0])] = -np.inf
    k = min(top_k, sims.shape[0])
    top_idx = np.argpartition(-sims, k - 1)[:k]
    top_idx = top_idx[np.argsort(-sims[top_idx])]
    return [int(item_index[i]) for i in top_idx if np.isfinite(sims[i])]


def main(k: int, sample_users: int, w_mf: float, w_knn: float, w_pop: float):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    # Load / fit models
    mf_path = MODELS_DIR / "mf_sgd_v1.0.joblib"
    knn_path = MODELS_DIR / "item_knn_sklearn_v1.0.joblib"
    if mf_path.exists():
        mf_model: FunkSVDRecommender = load(mf_path)
    else:
        mf_model = FunkSVDRecommender().fit(train_df)
    if knn_path.exists():
        knn_model: ItemKNNRecommender = load(knn_path)
    else:
        knn_model = ItemKNNRecommender().fit(train_df)

    pop_series = popularity_scores(train_df)
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    tfidf_index, tfidf_mat = _load_tfidf_matrix()

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    rows = []
    for u in users:
        seen = train_hist.get(u, set())
        # Popularity
        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}
        pop_top = sorted(pop_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        for i, _ in pop_top:
            rows.append({"user_id": u, "model": "popularity", "anime_id": int(i)})
        # MF
        mf_scores_arr = mf_model.predict_user(u)
        for it in seen:
            if mf_model.item_to_index and it in mf_model.item_to_index:
                mf_scores_arr[mf_model.item_to_index[it]] = -np.inf
        mf_top_idx = np.argpartition(-mf_scores_arr, range(min(k, len(mf_scores_arr))))[:k]
        mf_top_idx = mf_top_idx[np.argsort(-mf_scores_arr[mf_top_idx])]
        for idx in mf_top_idx:
            if np.isfinite(mf_scores_arr[idx]):
                rows.append({"user_id": u, "model": "mf", "anime_id": int(mf_model.index_to_item[idx])})
        # TF-IDF content
        tfidf_recs = _user_profile_cosine(tfidf_index, tfidf_mat, seen, k)
        for i in tfidf_recs:
            rows.append({"user_id": u, "model": "content_tfidf", "anime_id": int(i)})
        # Hybrid (weighted blend)
        mf_scores = {mf_model.index_to_item[i]: float(s) for i, s in enumerate(mf_scores_arr) if np.isfinite(s)}
        knn_scores = knn_model.score_all(u, exclude_seen=True)
        sources = {"mf": mf_scores, "knn": knn_scores, "pop": pop_scores}
        weights = {"mf": w_mf, "knn": w_knn, "pop": w_pop}
        hybrid_recs = weighted_blend(sources, weights, top_k=k)
        for i in hybrid_recs:
            rows.append({"user_id": u, "model": "hybrid", "anime_id": int(i)})

    df_out = pd.DataFrame(rows)
    OUT_RECS.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(OUT_RECS, index=False)
    # Popularity counts parquet
    pop_df = pop_series.reset_index()
    pop_df.columns = ["anime_id", "popularity_count"]
    pop_df.to_parquet(OUT_POP, index=False)
    print(f"[ok] Wrote {OUT_RECS} and {OUT_POP} (users={len(users)}, k={k})")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate sample recommendations for Phase 4 analysis")
    p.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    p.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    p.add_argument("--w-mf", type=float, default=DEFAULT_HYBRID_WEIGHTS["mf"])
    p.add_argument("--w-knn", type=float, default=DEFAULT_HYBRID_WEIGHTS["knn"])
    p.add_argument("--w-pop", type=float, default=DEFAULT_HYBRID_WEIGHTS["pop"])
    args = p.parse_args()
    main(args.k, args.sample_users, args.w_mf, args.w_knn, args.w_pop)
