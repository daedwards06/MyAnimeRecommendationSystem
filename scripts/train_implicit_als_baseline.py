"""Train an Implicit ALS baseline on Phase 2 splits and report metrics.

Usage (PowerShell):
  python scripts/train_implicit_als_baseline.py --factors 128 --iterations 20 --k 10

Requires: implicit (already in requirements.txt)
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import scipy.sparse as sp
import implicit
from implicit.evaluation import precision_at_k, recall_at_k


def _map_to_indices(df: pd.DataFrame, uix: pd.DataFrame, iix: pd.DataFrame) -> pd.DataFrame:
    out = df.merge(uix, on="user_id", how="inner").merge(iix, on="anime_id", how="inner")
    return out[["user_idx", "item_idx"]]


def _build_csr(df_idx: pd.DataFrame, n_users: int, n_items: int) -> sp.csr_matrix:
    if df_idx.empty:
        return sp.csr_matrix((n_users, n_items), dtype=np.float32)
    rows = df_idx["user_idx"].to_numpy()
    cols = df_idx["item_idx"].to_numpy()
    data = np.ones(len(rows), dtype=np.float32)
    mat = sp.coo_matrix((data, (rows, cols)), shape=(n_users, n_items), dtype=np.float32)
    return mat.tocsr()


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train Implicit ALS baseline on Phase 2 splits")
    ap.add_argument("--train", type=Path, default=Path("data/processed/train.parquet"))
    ap.add_argument("--val", type=Path, default=Path("data/processed/val.parquet"))
    ap.add_argument("--test", type=Path, default=Path("data/processed/test.parquet"))
    ap.add_argument("--user-index", type=Path, default=Path("data/processed/user_index.parquet"))
    ap.add_argument("--item-index", type=Path, default=Path("data/processed/item_index.parquet"))
    ap.add_argument("--factors", type=int, default=128)
    ap.add_argument("--iterations", type=int, default=20)
    ap.add_argument("--regularization", type=float, default=0.01)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--use-cpu", action="store_true", help="Force CPU even if CUDA available")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    # Load data
    train = pd.read_parquet(args.train)[["user_id", "anime_id"]].drop_duplicates()
    val = pd.read_parquet(args.val)[["user_id", "anime_id"]].drop_duplicates()
    test = pd.read_parquet(args.test)[["user_id", "anime_id"]].drop_duplicates()
    uix = pd.read_parquet(args.user_index)  # user_id, user_idx
    iix = pd.read_parquet(args.item_index)  # anime_id, item_idx

    n_users = int(uix["user_idx"].max()) + 1 if len(uix) else 0
    n_items = int(iix["item_idx"].max()) + 1 if len(iix) else 0

    print(f"[load] train={len(train)} val={len(val)} test={len(test)} users={n_users} items={n_items}")

    # Map to indices
    train_m = _map_to_indices(train, uix, iix)
    val_m = _map_to_indices(val, uix, iix)
    test_m = _map_to_indices(test, uix, iix)

    # Build CSR interactions
    train_mat = _build_csr(train_m, n_users, n_items)
    val_mat = _build_csr(val_m, n_users, n_items)
    test_mat = _build_csr(test_m, n_users, n_items)

    # Implicit ALS expects item-user in some APIs; we'll use model.fit with (item_users, user_items)
    user_items = train_mat
    item_users = train_mat.T.tocsr()

    # Select CPU/CUDA model
    use_cuda = (not args.use_cpu) and implicit.cuda.HAS_CUDA
    if use_cuda:
        ModelClass = implicit.cuda.CuALS
        print("[train] Using CUDA ALS")
    else:
        ModelClass = implicit.als.AlternatingLeastSquares
        print("[train] Using CPU ALS")

    model = ModelClass(
        factors=int(args.factors),
        iterations=int(args.iterations),
        regularization=float(args.regularization),
        random_state=42,
    )
    model.fit(item_users)

    # Evaluate
    K = int(args.k)
    print("[eval] computing metrics...")
    # implicit.evaluation functions expect user_items CSR
    prec_val = precision_at_k(model, user_items, val_mat, K).mean()
    rec_val = recall_at_k(model, user_items, val_mat, K).mean()
    prec_test = precision_at_k(model, user_items, test_mat, K).mean()
    rec_test = recall_at_k(model, user_items, test_mat, K).mean()
    print(f"[val]  precision@{K}: {prec_val:.4f}  recall@{K}: {rec_val:.4f}")
    print(f"[test] precision@{K}: {prec_test:.4f} recall@{K}: {rec_test:.4f}")


if __name__ == "__main__":
    main()
