"""
Test script for MAL parser with real export data
"""

import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.mal_parser import parse_mal_export, get_mal_export_summary
from src.data.user_profiles import save_profile, load_profile, list_profiles

# Paths
XML_PATH = Path("data/raw/animelist_1764220912_-_13722155.xml")
METADATA_PATH = Path("data/processed/anime_metadata.parquet")

def test_summary():
    """Test quick summary without full parsing"""
    print("=" * 60)
    print("MAL EXPORT SUMMARY")
    print("=" * 60)
    
    summary = get_mal_export_summary(XML_PATH)
    
    print(f"Username: {summary['username']}")
    print(f"Total Anime: {summary['total_anime']}")
    print(f"  - Completed: {summary['total_completed']}")
    print(f"  - Watching: {summary['total_watching']}")
    print(f"  - On-Hold: {summary['total_onhold']}")
    print(f"  - Dropped: {summary['total_dropped']}")
    print(f"  - Plan to Watch: {summary['total_plantowatch']}")
    print(f"\nRatings:")
    print(f"  - Rated: {summary['rated_count']}")
    print(f"  - Unrated: {summary['unrated_count']}")
    print()

def test_full_parse():
    """Test full parsing with metadata matching"""
    print("=" * 60)
    print("FULL PARSE TEST")
    print("=" * 60)
    
    # Load metadata
    print("Loading metadata...")
    metadata = pd.read_parquet(METADATA_PATH)
    print(f"Loaded {len(metadata)} anime from metadata")
    
    # Parse with default settings (Completed, Watching, On-Hold)
    print("\nParsing MAL export...")
    result = parse_mal_export(
        xml_path=XML_PATH,
        metadata_df=metadata,
        include_statuses={'Completed', 'Watching', 'On-Hold'},
        use_default_for_unrated=True,
        default_rating=7.0
    )
    
    print(f"\nUsername: {result['username']}")
    print(f"Watched Anime: {len(result['watched_ids'])}")
    print(f"Rated Anime: {len(result['ratings'])}")
    print(f"\nStats:")
    for key, value in result['stats'].items():
        if key == 'status_breakdown':
            print(f"  Status breakdown:")
            for status, count in value.items():
                print(f"    - {status}: {count}")
        else:
            print(f"  {key}: {value}")
    
    if result['unmatched']:
        print(f"\n⚠️  Unmatched Anime ({len(result['unmatched'])}):")
        for entry in result['unmatched'][:5]:  # Show first 5
            print(f"  - MAL ID {entry['mal_id']}: {entry['title']} (Status: {entry['status']})")
        if len(result['unmatched']) > 5:
            print(f"  ... and {len(result['unmatched']) - 5} more")
    
    # Show sample ratings
    print(f"\nSample Ratings (first 10):")
    for i, (anime_id, rating) in enumerate(list(result['ratings'].items())[:10]):
        anime_row = metadata[metadata['anime_id'] == anime_id]
        if not anime_row.empty:
            title = anime_row.iloc[0]['title_primary']
            print(f"  {anime_id:6d} - {rating:3.1f}/10 - {title}")
    
    return result

def test_profile_save_load(profile_data):
    """Test saving and loading profile"""
    print("\n" + "=" * 60)
    print("PROFILE SAVE/LOAD TEST")
    print("=" * 60)
    
    username = profile_data['username']
    
    # Save profile
    print(f"\nSaving profile for {username}...")
    profile_path = save_profile(username, profile_data)
    print(f"✓ Saved to {profile_path}")
    
    # List profiles
    print("\nAvailable profiles:")
    profiles = list_profiles()
    for p in profiles:
        print(f"  - {p}")
    
    # Load profile
    print(f"\nLoading profile for {username}...")
    loaded = load_profile(username)
    
    if loaded:
        print(f"✓ Loaded successfully")
        print(f"  - Watched: {len(loaded['watched_ids'])} anime")
        print(f"  - Ratings: {len(loaded['ratings'])} entries")
        print(f"  - Avg Rating: {loaded['stats']['avg_rating']}")
        print(f"  - Import Date: {loaded['import_date']}")
    else:
        print("✗ Failed to load profile")

if __name__ == "__main__":
    # Run tests
    test_summary()
    profile_data = test_full_parse()
    test_profile_save_load(profile_data)
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS COMPLETE")
    print("=" * 60)
