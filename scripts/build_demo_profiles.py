#!/usr/bin/env python
"""Build the read-only demo taste profiles from ``data/samples/personas.json``.

Each persona becomes ``data/user_profiles/demo_<slug>_profile.json`` in the regular profile
schema plus ``demo: true``. Titles are the persona's liked examples plus a seeded sample of the
most popular titles in its favourite genres, restricted to the MF item index so every rating
feeds the user embedding (otherwise "For me" is gated off).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import argparse
import json
import random
import re
from collections import Counter

import joblib
import pandas as pd

from src.app.constants import DEFAULT_MF_MODEL_STEM, METADATA_PARQUET, PERSONAS_JSON
from src.data.user_profiles import PROFILES_DIR

SEED = 42
TARGET_TITLES = 30
POOL_SIZE = 60
MIN_GENRE_OVERLAP = 2
# A one-click demo should not open on fan-service titles.
EXCLUDED_GENRES = {"ecchi", "erotica", "hentai"}
# Liked examples get 10; the rest cycle through this so the embedding sees real spread.
RATING_PATTERN = [9, 8, 10, 7, 8, 9, 7, 8]
# Fixed so reruns are byte-identical.
IMPORT_DATE = "2026-10-18T00:00:00"


def slugify(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def _genres(value) -> set[str]:
    if value is None or isinstance(value, float):
        return set()
    if isinstance(value, str):
        return {g.strip().lower() for g in value.split("|") if g.strip()}
    return {str(g).strip().lower() for g in value if g}


def build_profile(
    persona: dict, metadata: pd.DataFrame, mf_item_ids: set[int], exclude_ids: set[int]
) -> dict:
    favorites = {g.lower() for g in persona["favorite_genres"]}
    liked = [int(i) for i in persona["liked_example_ids"] if int(i) in mf_item_ids]

    meta = metadata[metadata["anime_id"].isin(mf_item_ids)].copy()
    meta["overlap"] = meta["genres"].map(lambda g: len(_genres(g) & favorites))
    meta["excluded"] = meta["genres"].map(lambda g: bool(_genres(g) & EXCLUDED_GENRES))
    pool = (
        meta[
            (meta["overlap"] >= MIN_GENRE_OVERLAP)
            & ~meta["excluded"]
            & ~meta["anime_id"].isin(set(liked) | exclude_ids)
        ]
        .sort_values(["members_count", "anime_id"], ascending=[False, True])
        .head(POOL_SIZE)["anime_id"]
        .astype(int)
        .tolist()
    )
    rng = random.Random(SEED)
    picked = sorted(rng.sample(pool, TARGET_TITLES - len(liked)), key=pool.index)

    ratings = {aid: 10 for aid in liked}
    for i, aid in enumerate(picked):
        ratings[aid] = RATING_PATTERN[i % len(RATING_PATTERN)]

    ids = [*liked, *picked]
    slug = slugify(persona["label"])
    return {
        "username": f"demo_{slug}",
        "mal_username": f"demo_{slug}",
        "demo": True,
        "label": persona["label"],
        "preference_summary": persona.get("preference_summary", ""),
        "watched_ids": ids,
        "ratings": {str(aid): ratings[aid] for aid in ids},
        "status_map": {str(aid): "Completed" for aid in ids},
        "import_date": IMPORT_DATE,
        "stats": {
            "total_watched": len(ids),
            "rated_count": len(ids),
            "unrated_count": 0,
            "avg_rating": round(sum(ratings.values()) / len(ratings), 2),
            "unmatched_count": 0,
            "status_breakdown": dict(Counter(["Completed"] * len(ids))),
        },
    }


def build_profiles(personas: list[dict], metadata: pd.DataFrame, mf_item_ids: set[int]) -> list[dict]:
    profiles: list[dict] = []
    used: set[int] = set()
    for persona in personas:
        profile = build_profile(persona, metadata, mf_item_ids, used)
        used |= set(profile["watched_ids"])
        profiles.append(profile)
    return profiles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mf-model", default=str(ROOT / "models" / f"{DEFAULT_MF_MODEL_STEM}.joblib"))
    parser.add_argument("--out-dir", default=str(PROFILES_DIR))
    args = parser.parse_args()

    personas = json.loads((ROOT / PERSONAS_JSON).read_text(encoding="utf-8"))
    metadata = pd.read_parquet(
        ROOT / "data" / "processed" / METADATA_PARQUET, columns=["anime_id", "genres", "members_count"]
    )
    mf = joblib.load(args.mf_model)
    mf_item_ids = {int(i) for i in mf.item_to_index}

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for profile in build_profiles(personas, metadata, mf_item_ids):
        path = out_dir / f"{profile['username']}_profile.json"
        path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        in_index = sum(int(k) in mf_item_ids for k in profile["ratings"])
        print(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: "
              f"{len(profile['ratings'])} ratings, {in_index} in MF index, avg {profile['stats']['avg_rating']}")


if __name__ == "__main__":
    main()
