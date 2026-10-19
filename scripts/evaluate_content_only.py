import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import random
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize

from src.models.constants import DATA_PROCESSED_DIR, METRICS_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS
from src.eval.eval_artifacts import run_metadata
from src.eval.splits import build_validation, sample_user_ids
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.eval.metrics_extra import item_coverage, gini_index


def _build_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return build_validation(df)


def _prepare_item_matrix(path: Path, feature_prefix: str | None = None) -> tuple[pd.Index, np.ndarray]:
    df = pd.read_parquet(path)
    if "anime_id" in df.columns:
        df = df.set_index("anime_id")
    if feature_prefix:
        cols = [c for c in df.columns if c.startswith(feature_prefix)]
        df = df[cols]
    mat = df.to_numpy(dtype=np.float32, copy=False)
    # Row-normalize for cosine
    mat = normalize(mat, axis=1)
    return df.index, mat


def _user_profile_cosine(item_index: pd.Index, item_mat: np.ndarray, user_seen: set[int], top_k: int) -> list[int]:
    if not user_seen:
        return []
    # Build user profile as mean of seen item vectors (normalized rows already); then L2-normalize
    ids = [i for i in user_seen if i in set(item_index)]
    if not ids:
        return []
    idxs = [int(np.where(item_index == i)[0][0]) for i in ids]
    prof = item_mat[idxs].mean(axis=0)
    n = np.linalg.norm(prof)
    if n == 0:
        return []
    prof = prof / n
    sims = item_mat @ prof
    sims[idxs] = -np.inf  # exclude seen
    k = min(top_k, sims.shape[0])
    top_idx = np.argpartition(-sims, k - 1)[:k]
    top_idx = top_idx[np.argsort(-sims[top_idx])]
    return [int(item_index[i]) for i in top_idx if np.isfinite(sims[i])]


def main(ks: list[int], sample_users: int):
    ks = sorted(set(ks))
    k_max = ks[-1]
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = _build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    # Load item feature matrices
    tfidf_index, tfidf_mat = _prepare_item_matrix(DATA_PROCESSED_DIR / "item_features_tfidf.parquet")
    emb_index, emb_mat = _prepare_item_matrix(DATA_PROCESSED_DIR / "item_features_embeddings.parquet")

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    # Ranked once at the largest K; a cosine top-K is a prefix of it.
    recs_tfidf, recs_emb = {}, {}
    for u in users:
        seen = train_hist.get(u, set())
        recs_tfidf[u] = _user_profile_cosine(tfidf_index, tfidf_mat, seen, k_max)
        recs_emb[u] = _user_profile_cosine(emb_index, emb_mat, seen, k_max)

    def _eval(name: str, recs: dict[int, list[int]], k: int):
        ndcgs, maps = [], []
        for u, items in recs.items():
            rel = val_hist.get(u, set())
            ndcgs.append(ndcg_at_k(items, rel, k))
            maps.append(average_precision_at_k(items, rel, k))
        return {
            "model": name,
            "k": k,
            "users_evaluated": len(recs),
            "ndcg@k_mean": float(sum(ndcgs) / max(1, len(ndcgs))),
            "map@k_mean": float(sum(maps) / max(1, len(maps))),
            "per_user": {"user_id": [int(u) for u in recs], "ndcg": ndcgs, "map": maps},
        }

    total_items = int(interactions["anime_id"].nunique())
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    summary = []
    for k in ks:
        meta = run_metadata(k=k, sample_users=sample_users)
        for name, full in (("content_tfidf", recs_tfidf), ("content_embeddings", recs_emb)):
            recs = {u: r[:k] for u, r in full.items()}
            m = _eval(name, recs, k)
            m["item_coverage@k"] = item_coverage(recs, total_items)
            m["gini_index@k"] = gini_index(recs)
            m.update(meta)
            (METRICS_DIR / f"{name}_k{k}_{ts}.json").write_text(json.dumps(m, indent=2))
            summary.append({key: v for key, v in m.items() if key != "per_user"})

    out_csv = METRICS_DIR / "summary.csv"
    pd.DataFrame(summary).to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False)

    print(pd.DataFrame(summary)[["model", "k", "ndcg@k_mean", "map@k_mean", "item_coverage@k", "gini_index@k"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate content-only recommenders (TF-IDF and embeddings)")
    parser.add_argument("--k", type=int, nargs="+", default=[TOP_K_DEFAULT], help="One or more K values")
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    args = parser.parse_args()
    main(args.k, args.sample_users)
