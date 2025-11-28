"""
Quick test for explanation generation
"""
import sys
sys.path.insert(0, ".")

from src.app.artifacts_loader import build_artifacts
from src.data.user_profiles import load_profile
from src.app.components.explanations import generate_explanation
import pandas as pd

# Load artifacts
print("Loading artifacts...")
bundle = build_artifacts()
metadata = bundle["metadata"]

# Load profile
print("Loading profile...")
profile = load_profile("Relentless649")
if not profile:
    print("Profile not found!")
    sys.exit(1)

print(f"Profile loaded: {profile['username']}")
print(f"Ratings: {len(profile.get('ratings', {}))}")

# Test explanation generation for a few anime
test_anime_ids = [1, 5, 6]  # Common anime IDs

for anime_id in test_anime_ids:
    anime_row = metadata[metadata['anime_id'] == anime_id]
    if anime_row.empty:
        print(f"\nAnime {anime_id}: Not found in metadata")
        continue
    
    title = anime_row.iloc[0].get('title_english', 'Unknown')
    print(f"\n{'='*60}")
    print(f"Anime: {title} (ID: {anime_id})")
    print(f"{'='*60}")
    
    # Generate explanation
    explanation = generate_explanation(
        anime_id=anime_id,
        personalized_score=8.5,  # Mock score
        user_profile=profile,
        metadata_df=metadata,
        top_n_genres=3
    )
    
    if explanation:
        print(f"✓ Explanation: {explanation}")
    else:
        print("✗ No explanation generated")

print("\n" + "="*60)
print("Test complete!")
