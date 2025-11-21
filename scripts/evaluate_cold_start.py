import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize

from src.models.constants import DATA_PROCESSED_DIR, METRICS_DIR, TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS
from src.eval.splits import build_validation, sample_user_ids
from src.eval.metrics import ndcg_at_k, average_precision_at_k


NEW_META_CANDIDATES = [
    DATA_PROCESSED_DIR / "anime_metadata_202511_new.parquet",
    DATA_PROCESSED_DIR / "anime_metadata_normalized.parquet",
    DATA_PROCESSED_DIR / "anime_metadata.parquet",
]


def _load_new_item_ids() -> set[int]:
    for p in NEW_META_CANDIDATES:
        if p.exists():
            df = pd.read_parquet(p)
            cols = set(df.columns)
            if "is_new" in cols:
                return set(df.loc[df["is_new"] == True, "anime_id"].astype(int).tolist())
            # if this is a pre-filtered file of only new items
            if df.shape[0] < 0.5 * pd.read_parquet(DATA_PROCESSED_DIR / "items.parquet").shape[0]:
                if "anime_id" in df.columns:
                    return set(df["anime_id"].astype(int).tolist())
    # Fallback: try items slice if exists
    items_path = DATA_PROCESSED_DIR / "items.parquet"
    if items_path.exists():
        return set()
    return set()


def _prepare_item_matrix(path: Path) -> tuple[pd.Index, np.ndarray]:
    df = pd.read_parquet(path)
    if "anime_id" in df.columns:
        df = df.set_index("anime_id")
    mat = df.to_numpy(dtype=np.float32, copy=False)
    mat = normalize(mat, axis=1)
    return df.index, mat


def _user_profile_cosine(item_index: pd.Index, item_mat: np.ndarray, user_seen: set[int], candidate_ids: set[int], top_k: int) -> list[int]:
    if not user_seen:
        return []
    idxs_seen = [int(np.where(item_index == i)[0][0]) for i in user_seen if i in set(item_index)]
    if not idxs_seen:
        return []
    prof = item_mat[idxs_seen].mean(axis=0)
    n = np.linalg.norm(prof)
    if n == 0:
        return []
    prof = prof / n
    sims = item_mat @ prof
    # restrict to candidate new items and exclude seen
    mask = np.full(sims.shape[0], -np.inf, dtype=np.float32)
    index_to_id = {i: int(item_index[i]) for i in range(len(item_index))}
    for i in range(len(sims)):
        iid = index_to_id[i]
        if iid in candidate_ids and iid not in user_seen:
            mask[i] = sims[i]
    sims = mask
    k = min(top_k, sims.shape[0])
    if k == 0:
        return []
    top_idx = np.argpartition(-sims, k - 1)[:k]
    top_idx = top_idx[np.argsort(-sims[top_idx])]
    return [int(item_index[i]) for i in top_idx if np.isfinite(sims[i])]


def main(k: int, sample_users: int):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = build_validation(interactions)
    users = sample_user_ids(val_df["user_id"].unique().tolist(), sample_users)

    # load new items ids
    new_item_ids = _load_new_item_ids()
    if not new_item_ids:
        print("Warning: No new item IDs found; cold-start evaluation may be empty.")

    tfidf_index, tfidf_mat = _prepare_item_matrix(DATA_PROCESSED_DIR / "item_features_tfidf.parquet")

    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()

    recs_cs = {}
    for u in users:
        seen = train_hist.get(u, set())
        recs_cs[u] = _user_profile_cosine(tfidf_index, tfidf_mat, seen, new_item_ids, k)

    ndcgs, maps = [], []
    nonempty = 0
    for u, items in recs_cs.items():
        if items:
            nonempty += 1
        rel = val_hist.get(u, set())
        ndcgs.append(ndcg_at_k(items, rel, k))
        maps.append(average_precision_at_k(items, rel, k))

    metrics = {
        "model": "cold_start_content_tfidf",
        "k": k,
        "users_evaluated": len(recs_cs),
        "users_with_recs": nonempty,
        "ndcg@k_mean": float(sum(ndcgs) / max(1, len(ndcgs))),
        "map@k_mean": float(sum(maps) / max(1, len(maps))),
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    (METRICS_DIR / f"cold_start_content_tfidf_{ts}.json").write_text(json.dumps(metrics, indent=2))
    out_csv = METRICS_DIR / "summary.csv"
    pd.DataFrame([metrics]).to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate cold-start recommendations restricted to new items (content-only TF-IDF)")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    args = parser.parse_args()
    main(args.k, args.sample_users)
