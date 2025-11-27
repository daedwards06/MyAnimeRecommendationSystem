"""
Quick test to verify profile loading and exclusion logic
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.user_profiles import load_profile, list_profiles

print("=" * 60)
print("PROFILE TEST")
print("=" * 60)

# List available profiles
profiles = list_profiles()
print(f"\nAvailable profiles: {profiles}")

if profiles:
    # Load first profile
    profile_name = profiles[0]
    print(f"\nLoading profile: {profile_name}")
    
    profile = load_profile(profile_name)
    if profile:
        print(f"✓ Loaded successfully")
        print(f"  Username: {profile['username']}")
        print(f"  Watched anime: {len(profile['watched_ids'])}")
        print(f"  Rated anime: {len(profile['ratings'])}")
        print(f"  Avg rating: {profile.get('stats', {}).get('avg_rating', 0):.2f}")
        
        # Show first few watched IDs
        watched_ids = profile['watched_ids'][:10]
        print(f"\n  First 10 watched IDs: {watched_ids}")
        
        # Simulate exclusion check
        test_ids = [1, 2, 3, 32998, 22199, 11111]  # Mix of IDs, some from profile
        print(f"\n  Testing exclusion logic:")
        for anime_id in test_ids:
            is_watched = anime_id in profile['watched_ids']
            status = "❌ EXCLUDE" if is_watched else "✓ Include"
            print(f"    ID {anime_id}: {status}")
    else:
        print("✗ Failed to load profile")
else:
    print("\n⚠️  No profiles found. Run test_mal_parser.py first to create a profile.")

print("\n" + "=" * 60)
print("✓ TEST COMPLETE")
print("=" * 60)
