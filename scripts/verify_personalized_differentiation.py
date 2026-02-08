#!/usr/bin/env python
"""Quick smoke test: verify Personalized mode produces different results for different seeds."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

# Load artifacts
from src.app.artifacts_loader import build_artifacts
from src.app.recommender import HybridComponents, HybridRecommender

bundle = build_artifacts()
metadata = bundle["metadata"]
mf_model = bundle["models"]["mf"]
mf_stem = bundle["models"].get("_mf_stem")

# Build components & recommender (mirrors app/main.py)
item_ids = np.array([mf_model.index_to_item[i] for i in range(len(mf_model.index_to_item))], dtype=np.int64)
user_factors = mf_model.P  # (num_users, n_factors)
item_factors = mf_model.Q  # (num_items, n_factors)
mf_scores = np.float32(mf_model.global_mean) + (user_factors @ item_factors.T).astype(np.float32)
components = HybridComponents(mf=mf_scores, knn=None, pop=None, item_ids=item_ids)

# Wire popularity if kNN model available
knn_model = bundle.get("models", {}).get("knn")
if knn_model and hasattr(knn_model, "item_pop") and hasattr(knn_model, "item_to_index"):
    pop_vec = np.zeros(len(item_ids), dtype=np.float32)
    for j, aid in enumerate(item_ids):
        idx = knn_model.item_to_index.get(int(aid))
        if idx is not None and 0 <= int(idx) < len(knn_model.item_pop):
            pop_vec[j] = float(knn_model.item_pop[int(idx)])
    components.pop = pop_vec

recommender = HybridRecommender(components)
mf_model = bundle["models"]["mf"]
mf_stem = bundle["models"].get("_mf_stem")

# Load user profile
profile_dir = "data/user_profiles"
profile_path = None
for fname in os.listdir(profile_dir):
    if fname.endswith(".json") and "relentless" in fname.lower():
        profile_path = os.path.join(profile_dir, fname)
        break
if profile_path is None:
    profiles = [f for f in os.listdir(profile_dir) if f.endswith(".json")]
    print(f"No Relentless profile found. Available: {profiles[:5]}")
    sys.exit(1)

with open(profile_path) as f:
    profile = json.load(f)
ratings = {int(k): v for k, v in profile.get("ratings", {}).items()}
watched_ids = {int(x) for x in profile.get("watched_ids", [])}
print(f"Profile: {profile['username']}, {len(ratings)} ratings")

# Generate user embedding
from src.models.user_embedding import generate_user_embedding

user_embedding = generate_user_embedding(
    ratings, mf_model, method="weighted_average", normalize=True
)
print(f"User embedding norm: {np.linalg.norm(user_embedding):.4f}")


# Find seed IDs
def find_id(title_substr):
    for col in ["title_english", "title_display"]:
        if col not in metadata.columns:
            continue
        mask = metadata[col].str.contains(title_substr, case=False, na=False)
        if mask.any():
            row = metadata[mask].iloc[0]
            return int(row["anime_id"]), (row.get("title_english") or row.get("title_display"))
    return None, None


romance_id, romance_title = find_id("One Final Thing")
action_id, action_title = find_id("Brotherhood")
if action_id is None:
    action_id, action_title = find_id("Fullmetal")

print(f"Romance seed: {romance_title} (ID {romance_id})")
print(f"Action seed: {action_title} (ID {action_id})")

if romance_id is None or action_id is None:
    print("ERROR: Could not find seed titles in metadata")
    sys.exit(1)

# Run seed pipeline with each seed
from src.app.scoring_pipeline import ScoringContext, run_seed_based_pipeline
from src.app.recommender import choose_weights
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids

weights = choose_weights("Balanced")
hygiene = build_ranked_candidate_hygiene_exclude_ids(metadata)


def run_with_seed(seed_id, seed_title, personalized=True, strength=1.0):
    ctx = ScoringContext(
        metadata=metadata,
        bundle=bundle,
        recommender=recommender,
        components=components,
        seed_ids=[seed_id],
        seed_titles=[seed_title],
        user_index=0,
        user_embedding=user_embedding if personalized else None,
        personalization_enabled=personalized,
        personalization_strength=strength,
        active_profile=profile,
        watched_ids=watched_ids,
        weights=weights,
        n_requested=200,
        top_n=15,
        mf_model=mf_model,
        mf_stem=mf_stem,
        user_embedding_meta={
            "mf_stem": mf_stem,
            "ratings_sig": "x",
            "profile_username": profile["username"],
        },
        ranked_hygiene_exclude_ids=hygiene,
    )
    result = run_seed_based_pipeline(ctx)
    return [(r["anime_id"], round(r["score"], 4)) for r in result.ranked_items[:10]]


def show_recs(label, recs):
    print(f"\n=== {label} ===")
    for aid, score in recs:
        row = metadata[metadata["anime_id"] == aid].iloc[0]
        title = row.get("title_english") or row.get("title_display", "?")
        genres = row.get("genres", "")
        print(f"  {score:.4f}  {title}  [{genres}]")


romance_recs = run_with_seed(romance_id, romance_title, personalized=True, strength=1.0)
show_recs("PERSONALIZED (100%) + Romance seed", romance_recs)

action_recs = run_with_seed(action_id, action_title, personalized=True, strength=1.0)
show_recs("PERSONALIZED (100%) + Action seed", action_recs)

# Overlap analysis
romance_ids = {r[0] for r in romance_recs}
action_ids = {r[0] for r in action_recs}
overlap = romance_ids & action_ids
print(f"\n--- Differentiation Analysis ---")
print(f"Overlap: {len(overlap)}/10 titles in common")
print(f"Unique to romance seed: {len(romance_ids - action_ids)}")
print(f"Unique to action seed: {len(action_ids - romance_ids)}")

if len(overlap) <= 3:
    print("PASS: Seeds produce meaningfully different recommendations")
elif len(overlap) <= 6:
    print("MODERATE: Some differentiation but could be stronger")
else:
    print("FAIL: Seeds produce nearly identical recommendations")

# Also test strength slider differentiation
print("\n\n=== STRENGTH SLIDER TEST (Romance seed) ===")
for strength in [0.0, 0.5, 1.0]:
    recs = run_with_seed(romance_id, romance_title, personalized=True, strength=strength)
    ids = [r[0] for r in recs[:5]]
    titles = []
    for aid in ids:
        row = metadata[metadata["anime_id"] == aid].iloc[0]
        titles.append(row.get("title_english") or row.get("title_display", "?"))
    print(f"\n  Strength {strength*100:.0f}%: {', '.join(titles[:3])}...")
