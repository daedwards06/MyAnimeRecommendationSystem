"""Summarize new title coverage and cold-start flags.

Given a file of discovered MAL IDs and the processed artifacts, report:
- How many of those IDs are present in processed metadata
- Among those, how many are flagged as post-snapshot and/or low-interaction
- A small breakdown (only post-snapshot, only low-interaction, both, neither)

Usage (PowerShell):
  python scripts\summarize_new_titles.py \
    --ids-file data\raw\new_anime_ids_20251114.txt \
    --metadata-path data\processed\anime_metadata.parquet \
    --items-path data\processed\items.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Set

import pandas as pd


def read_ids(path: Path) -> List[int]:
    ids: List[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            ids.append(int(s))
        except ValueError:
            continue
    return ids


def load_metadata_ids(path: Path) -> Set[int]:
    if not path.exists():
        return set()
    try:
        df = pd.read_parquet(path)
        if "anime_id" not in df.columns:
            return set()
        return set(pd.to_numeric(df["anime_id"], errors="coerce").dropna().astype(int).tolist())
    except Exception:
        return set()


def load_items(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.DataFrame()


def summarize(ids_file: Path, metadata_path: Path, items_path: Path) -> None:
    ids = read_ids(ids_file)
    total_ids = len(ids)
    print(f"[input] ids_file={ids_file} total_ids={total_ids}")

    meta_ids = load_metadata_ids(metadata_path)
    in_meta = [i for i in ids if i in meta_ids]
    print(f"[coverage] present_in_metadata={len(in_meta)} missing={total_ids - len(in_meta)}")

    items = load_items(items_path)
    if items.empty:
        print("[warn] items parquet not found or empty; skipping cold-start breakdown")
        return

    # Ensure columns
    for col in ["is_post_snapshot", "is_low_interaction", "is_cold_start", "cold_reason"]:
        if col not in items.columns:
            items[col] = None

    sub = items[items["anime_id"].isin(in_meta)].copy()
    n = len(sub)
    if n == 0:
        print("[warn] none of the discovered IDs are present in items.parquet; did you run build_features?")
        return

    post = sub["is_post_snapshot"].fillna(False).astype(bool)
    lowi = sub["is_low_interaction"].fillna(False).astype(bool)
    cold = sub["is_cold_start"].fillna(False).astype(bool)

    both = (post & lowi).sum()
    only_post = (post & ~lowi).sum()
    only_low = (~post & lowi).sum()
    neither = (~post & ~lowi).sum()

    print("[flags]")
    print(f"  items_considered={n}")
    print(f"  is_post_snapshot=True: {int(post.sum())}")
    print(f"  is_low_interaction=True: {int(lowi.sum())}")
    print(f"  is_cold_start=True: {int(cold.sum())}")
    print("[breakdown]")
    print(f"  only_post_snapshot: {int(only_post)}")
    print(f"  only_low_interaction: {int(only_low)}")
    print(f"  both_post_and_low: {int(both)}")
    print(f"  neither: {int(neither)}")
    # cold_reason breakdown if present
    if "cold_reason" in sub.columns:
        vc = (
            sub["cold_reason"].fillna("none").astype(str).value_counts(dropna=False).to_dict()
        )
        print("[cold_reason]")
        for k in sorted(vc.keys()):
            print(f"  {k}: {vc[k]}")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Summarize new title coverage and cold-start flags")
    ap.add_argument("--ids-file", type=Path, required=True)
    ap.add_argument("--metadata-path", type=Path, default=Path("data/processed/anime_metadata.parquet"))
    ap.add_argument("--items-path", type=Path, default=Path("data/processed/items.parquet"))
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    summarize(args.ids_file, args.metadata_path, args.items_path)


if __name__ == "__main__":
    main()
