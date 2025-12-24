"""Train a LightFM collaborative filtering baseline on Phase 2 splits.

This script:
- Loads train/val/test interaction splits and user/item index mappings
- Builds sparse interaction matrices
- Trains a LightFM model (WARP/BPR/logistic/warp-kos)
- Evaluates Precision@K and Recall@K on val/test
- Optionally saves the fitted model to disk

Usage (PowerShell):
  python scripts/train_lightfm_baseline.py --epochs 20 --loss warp --no-components 64 --k 10 --save-model data/processed/models/lightfm_warp.pkl

Requirements:
- lightfm, scipy (installed via requirements.txt)
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure project root (which contains the 'src' package) is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import scipy.sparse as sp
from lightfm import LightFM
from lightfm.evaluation import precision_at_k, recall_at_k
import pickle


def _to_coo(df: pd.DataFrame, n_users: int, n_items: int) -> sp.coo_matrix:
    """Convert a (user_idx, item_idx) DataFrame into a COO implicit feedback matrix.

    Values are set to 1.0 for all observed interactions.
    """
    if df.empty:
        return sp.coo_matrix((n_users, n_items), dtype=np.float32)
    rows = df["user_idx"].to_numpy()
    cols = df["item_idx"].to_numpy()
    data = np.ones_like(rows, dtype=np.float32)
    return sp.coo_matrix((data, (rows, cols)), shape=(n_users, n_items))


def _map_to_indices(inter: pd.DataFrame, uix: pd.DataFrame, iix: pd.DataFrame) -> pd.DataFrame:
    """Attach user_idx and item_idx to interactions via inner join (drops OOV)."""
    out = inter.merge(uix, on="user_id", how="inner").merge(iix, on="anime_id", how="inner")
    return out[["user_id", "anime_id", "user_idx", "item_idx"]]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Train LightFM baseline on Phase 2 splits")
    ap.add_argument("--train", type=Path, default=Path("data/processed/train.parquet"))
    ap.add_argument("--val", type=Path, default=Path("data/processed/val.parquet"))
    ap.add_argument("--test", type=Path, default=Path("data/processed/test.parquet"))
    ap.add_argument("--user-index", type=Path, default=Path("data/processed/user_index.parquet"))
    ap.add_argument("--item-index", type=Path, default=Path("data/processed/item_index.parquet"))
    ap.add_argument("--loss", type=str, default="warp", choices=["warp", "bpr", "logistic", "warp-kos"])
    ap.add_argument("--no-components", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--learning-rate", type=float, default=0.05)
    ap.add_argument("--k", type=int, default=10, help="Top-K for metrics")
    ap.add_argument("--num-threads", type=int, default=4)
    ap.add_argument("--save-model", type=Path, default=None)
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    # Load splits and indices
    train = pd.read_parquet(args.train)[["user_id", "anime_id"]].drop_duplicates()
    val = pd.read_parquet(args.val)[["user_id", "anime_id"]].drop_duplicates()
    test = pd.read_parquet(args.test)[["user_id", "anime_id"]].drop_duplicates()
    uix = pd.read_parquet(args.user_index)  # user_id, user_idx
    iix = pd.read_parquet(args.item_index)  # anime_id, item_idx

    n_users = int(uix["user_idx"].max()) + 1 if len(uix) else 0
    n_items = int(iix["item_idx"].max()) + 1 if len(iix) else 0
    print(f"[load] train={len(train)} val={len(val)} test={len(test)} users={n_users} items={n_items}")

    # Map to idx space; drop OOV by inner join
    train_m = _map_to_indices(train, uix, iix)
    val_m = _map_to_indices(val, uix, iix)
    test_m = _map_to_indices(test, uix, iix)

    # Build sparse matrices
    train_mat = _to_coo(train_m, n_users, n_items).tocsr()
    val_mat = _to_coo(val_m, n_users, n_items).tocsr()
    test_mat = _to_coo(test_m, n_users, n_items).tocsr()

    # Initialize and fit model
    model = LightFM(loss=args.loss, no_components=int(args.no_components), learning_rate=float(args.learning_rate), random_state=42)
    print(f"[train] LightFM loss={args.loss} factors={args.no_components} lr={args.learning_rate} epochs={args.epochs}")
    model.fit(train_mat, epochs=int(args.epochs), num_threads=int(args.num_threads))

    # Evaluate
    K = int(args.k)
    print("[eval] computing metrics...")
    prec_val = precision_at_k(model, train_mat, val_mat, k=K, num_threads=int(args.num_threads)).mean()
    rec_val = recall_at_k(model, train_mat, val_mat, k=K, num_threads=int(args.num_threads)).mean()
    prec_test = precision_at_k(model, train_mat, test_mat, k=K, num_threads=int(args.num_threads)).mean()
    rec_test = recall_at_k(model, train_mat, test_mat, k=K, num_threads=int(args.num_threads)).mean()
    print(f"[val]  precision@{K}: {prec_val:.4f}  recall@{K}: {rec_val:.4f}")
    print(f"[test] precision@{K}: {prec_test:.4f} recall@{K}: {rec_test:.4f}")

    # Optional save
    if args.save_model:
        out = Path(args.save_model)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as f:
            pickle.dump(model, f)
        print(f"[save] model -> {out}")


if __name__ == "__main__":
    main()
