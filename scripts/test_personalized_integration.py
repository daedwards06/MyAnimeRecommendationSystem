"""Test personalized recommendation integration.

This script verifies that personalized recommendations work correctly
by comparing seed-based and personalized recommendations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from src.app.artifacts_loader import build_artifacts
from src.app.recommender import HybridComponents, HybridRecommender
from src.app.constants import BALANCED_WEIGHTS
from src.data.user_profiles import load_profile
from src.models.user_embedding import generate_user_embedding, get_user_taste_profile

print("=" * 60)
print("PERSONALIZED INTEGRATION TEST")
print("=" * 60)

# 1. Load artifacts
print("\n1. Loading artifacts...")
bundle = build_artifacts()
metadata = bundle["metadata"]
models = bundle["models"]
print(f"✓ Loaded metadata: {len(metadata)} anime")
print(f"✓ Loaded {len(models)} models")

# 2. Load user profile
print("\n2. Loading user profile...")
profile = load_profile("Relentless649")
if not profile:
    print("✗ Failed to load profile")
    sys.exit(1)

ratings = profile.get("ratings", {})
watched_ids = profile.get("watched_ids", [])
print(f"✓ Profile: {profile['username']}")
print(f"  - Ratings: {len(ratings)}")
print(f"  - Watched: {len(watched_ids)}")
print(f"  - Avg rating: {profile.get('stats', {}).get('avg_rating', 0):.2f}/10")

# 3. Generate user embedding
print("\n3. Generating user embedding...")
mf_model = models.get("mf")
if not mf_model:
    print("✗ MF model not found")
    sys.exit(1)

user_embedding = generate_user_embedding(
    ratings_dict=ratings,
    mf_model=mf_model,
    method="weighted_average",
    normalize=True
)
print(f"✓ Generated embedding: shape={user_embedding.shape}, norm={np.linalg.norm(user_embedding):.4f}")

# 4. Initialize HybridRecommender
print("\n4. Initializing HybridRecommender...")
mf_scores = models.get("mf_scores")
knn_scores = models.get("knn_scores")
pop_scores = models.get("pop_scores")
item_ids = bundle.get("item_ids")

components = HybridComponents(
    mf=mf_scores,
    knn=knn_scores,
    pop=pop_scores,
    item_ids=item_ids,
)
recommender = HybridRecommender(components)
print(f"✓ HybridRecommender initialized")

# 5. Get seed-based recommendations (user_index=0 as placeholder)
print("\n5. Getting seed-based recommendations...")
user_index = 0  # Placeholder
seed_recs = recommender.get_top_n_for_user(
    user_index=user_index,
    n=10,
    weights=BALANCED_WEIGHTS,
    exclude_item_ids=watched_ids
)
print(f"✓ Generated {len(seed_recs)} seed-based recommendations")

# 6. Get personalized recommendations
print("\n6. Getting personalized recommendations...")
personalized_recs = recommender.get_personalized_recommendations(
    user_embedding=user_embedding,
    mf_model=mf_model,
    n=10,
    weights=BALANCED_WEIGHTS,
    exclude_item_ids=watched_ids
)
print(f"✓ Generated {len(personalized_recs)} personalized recommendations")

# 7. Compare recommendations
print("\n7. Comparing recommendations...")
print("\nSeed-based Top 5:")
for i, rec in enumerate(seed_recs[:5], 1):
    anime_id = rec["anime_id"]
    row = metadata[metadata["anime_id"] == anime_id].iloc[0]
    title = row.get("title_display", "Unknown")
    genres = row.get("genres", "")
    print(f"  {i}. {title[:50]:<50} | Score: {rec['score']:.3f} | {genres[:30]}")

print("\nPersonalized Top 5:")
for i, rec in enumerate(personalized_recs[:5], 1):
    anime_id = rec["anime_id"]
    row = metadata[metadata["anime_id"] == anime_id].iloc[0]
    title = row.get("title_display", "Unknown")
    genres = row.get("genres", "")
    print(f"  {i}. {title[:50]:<50} | Score: {rec['score']:.3f} | {genres[:30]}")

# 8. Analyze taste profile
print("\n8. Analyzing taste profile...")
taste_profile = get_user_taste_profile(ratings, metadata, top_n_genres=5)
print(f"\nTop 5 favorite genres:")
for genre, score in taste_profile["favorite_genres"][:5]:
    print(f"  - {genre:<20}: {score:.1f}/10")

print(f"\nRating distribution:")
for bucket, count in taste_profile["rating_distribution"].items():
    print(f"  - {bucket}: {count} anime")

print("\n" + "=" * 60)
print("✓ PERSONALIZED INTEGRATION TEST COMPLETE")
print("=" * 60)
