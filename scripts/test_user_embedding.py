"""
Test user embedding generation with real profile
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import pandas as pd
import numpy as np
from src.data.user_profiles import load_profile
from src.models.user_embedding import generate_user_embedding, compute_personalized_scores, get_user_taste_profile

print("=" * 60)
print("USER EMBEDDING TEST")
print("=" * 60)

# Load profile
print("\n1. Loading profile...")
profile = load_profile("Relentless649")
if not profile:
    print("❌ Profile not found")
    sys.exit(1)

print(f"✓ Loaded profile: {profile['username']}")
print(f"  - Watched: {len(profile['watched_ids'])} anime")
print(f"  - Ratings: {len(profile['ratings'])} entries")
print(f"  - Avg rating: {profile['stats']['avg_rating']:.2f}/10")

# Load MF model
print("\n2. Loading MF model...")
model_path = Path("models/mf_sgd_v2025.11.21_202756.joblib")
mf_model = joblib.load(model_path)
print(f"✓ Loaded MF model")
print(f"  - User factors: {mf_model.P.shape}")
print(f"  - Item factors: {mf_model.Q.shape}")
print(f"  - Latent dimensions: {mf_model.n_factors}")

# Generate user embedding
print("\n3. Generating user embedding...")
user_embedding = generate_user_embedding(
    ratings_dict=profile['ratings'],
    mf_model=mf_model,
    method="weighted_average",
    normalize=True
)
print(f"✓ Generated embedding: shape={user_embedding.shape}, dtype={user_embedding.dtype}")
print(f"  - Norm: {np.linalg.norm(user_embedding):.4f}")
print(f"  - Mean: {user_embedding.mean():.4f}")
print(f"  - Std: {user_embedding.std():.4f}")
print(f"  - Min: {user_embedding.min():.4f}, Max: {user_embedding.max():.4f}")

# Compute personalized scores
print("\n4. Computing personalized scores...")
watched_ids = set(profile['watched_ids'])
personalized_scores = compute_personalized_scores(
    user_embedding=user_embedding,
    mf_model=mf_model,
    exclude_anime_ids=watched_ids
)
print(f"✓ Computed {len(personalized_scores)} scores")

# Show top 10 recommendations
print("\n5. Top 10 Personalized Recommendations:")
top_recs = sorted(personalized_scores.items(), key=lambda x: x[1], reverse=True)[:10]

# Load metadata to show titles
metadata = pd.read_parquet("data/processed/anime_metadata.parquet")

for rank, (anime_id, score) in enumerate(top_recs, 1):
    row = metadata[metadata['anime_id'] == anime_id]
    if not row.empty:
        title = row.iloc[0]['title_primary']
        genres = row.iloc[0].get('genres', '')
        if isinstance(genres, str):
            genre_str = genres.replace('|', ', ')
        else:
            genre_str = ', '.join(str(g) for g in genres[:3]) if hasattr(genres, '__iter__') else ''
        
        print(f"  {rank:2d}. {title[:50]:50s} | Score: {score:6.3f} | {genre_str[:30]}")

# Taste profile
print("\n6. Analyzing taste profile...")
taste_profile = get_user_taste_profile(
    ratings_dict=profile['ratings'],
    metadata_df=metadata,
    top_n_genres=5
)
print(f"✓ Overall avg rating: {taste_profile['avg_rating']}/10")
print(f"\nTop 5 favorite genres:")
for genre, avg_rating in taste_profile['top_genres']:
    print(f"  - {genre:20s}: {avg_rating:.1f}/10")

print(f"\nRating distribution:")
for range_str, count in taste_profile['rating_distribution'].items():
    print(f"  {range_str}: {count:3d} anime")

print("\n" + "=" * 60)
print("✓ USER EMBEDDING TEST COMPLETE")
print("=" * 60)
