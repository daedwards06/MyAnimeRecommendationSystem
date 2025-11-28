"""Quick test of personalized recommendation logic without loading artifacts."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

print("=" * 60)
print("QUICK PERSONALIZATION TEST")
print("=" * 60)

# 1. Test user embedding generation
print("\n1. Testing user embedding generation...")
from src.models.user_embedding import generate_user_embedding

# Create mock MF model
class MockMFModel:
    def __init__(self):
        self.Q = np.random.randn(100, 64).astype(np.float32)  # 100 items, 64 dimensions
        self.item_to_index = {i: i for i in range(100)}
        self.index_to_item = {i: i for i in range(100)}
        self.global_mean = 7.0

# Generate mock ratings
ratings = {i: np.random.randint(5, 11) for i in range(20)}  # 20 rated anime
print(f"  Mock ratings: {len(ratings)} anime, scores {min(ratings.values())}-{max(ratings.values())}")

mf_model = MockMFModel()
embedding = generate_user_embedding(ratings, mf_model, method="weighted_average", normalize=True)
print(f"✓ Generated embedding: shape={embedding.shape}, norm={np.linalg.norm(embedding):.4f}")

# 2. Test personalized scoring
print("\n2. Testing personalized scoring...")
from src.models.user_embedding import compute_personalized_scores

scores = compute_personalized_scores(embedding, mf_model, exclude_anime_ids=[0, 1, 2])
print(f"✓ Computed {len(scores)} personalized scores")
print(f"  Score range: {min(scores.values()):.3f} to {max(scores.values()):.3f}")
print(f"  Excluded items: 0, 1, 2 (should not be in scores)")
assert 0 not in scores and 1 not in scores and 2 not in scores, "Exclusion failed!"
print("  ✓ Exclusion working correctly")

# 3. Test HybridRecommender.get_personalized_recommendations
print("\n3. Testing HybridRecommender.get_personalized_recommendations...")
from src.app.recommender import HybridComponents, HybridRecommender

# Create mock components
item_ids = np.arange(100)
pop_scores = np.random.rand(100).astype(np.float32)

components = HybridComponents(
    mf=None,  # Not using precomputed MF scores
    knn=None,
    pop=pop_scores,
    item_ids=item_ids,
)

recommender = HybridRecommender(components)
weights = {"mf": 0.7, "pop": 0.3}

recs = recommender.get_personalized_recommendations(
    user_embedding=embedding,
    mf_model=mf_model,
    n=10,
    weights=weights,
    exclude_item_ids=[0, 1, 2, 3, 4]
)

print(f"✓ Generated {len(recs)} recommendations")
print(f"  Requested: 10, Got: {len(recs)}")
assert len(recs) == 10, f"Expected 10 recs, got {len(recs)}"

# Check exclusions
rec_ids = [rec["anime_id"] for rec in recs]
excluded = [0, 1, 2, 3, 4]
for exc_id in excluded:
    assert exc_id not in rec_ids, f"Excluded ID {exc_id} found in recommendations!"
print(f"  ✓ All exclusions working: {excluded} not in recommendations")

# Print top 5
print("\n  Top 5 recommendations:")
for i, rec in enumerate(recs[:5], 1):
    print(f"    {i}. Anime {rec['anime_id']} - Score: {rec['score']:.4f}")

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
