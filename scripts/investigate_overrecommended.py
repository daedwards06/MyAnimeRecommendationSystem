"""Investigate titles that appear frequently but seem to be poor matches.

This script helps diagnose why certain anime are over-recommended:
- Check their popularity scores
- Examine their feature distributions
- Look at their collaborative filtering scores
- Identify potential data quality issues
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Suspicious titles reported by user
SUSPICIOUS_TITLES = [
    "Gantz",
    "Azusa Will Help!",
    "Jigoku Koushien",
    "Accel World: Acchel World",
    "Tree in the Sun"
]

def investigate_titles():
    """Investigate why certain titles are over-recommended."""
    
    # Load metadata
    metadata_path = Path("data/processed/anime_metadata.parquet")
    if not metadata_path.exists():
        print(f"❌ Metadata not found at {metadata_path}")
        return
    
    df = pd.read_parquet(metadata_path)
    print(f"📊 Loaded {len(df)} anime titles\n")
    
    # Find suspicious titles (fuzzy match)
    print("=" * 80)
    print("🔍 INVESTIGATING SUSPICIOUS TITLES")
    print("=" * 80)
    
    for title in SUSPICIOUS_TITLES:
        print(f"\n{'─' * 80}")
        print(f"📺 Searching for: {title}")
        print(f"{'─' * 80}")
        
        # Try exact match first
        matches = df[df['title_display'].str.contains(title, case=False, na=False)]
        
        if matches.empty:
            # Try other title fields
            for col in ['title_english', 'title_primary', 'title_japanese']:
                if col in df.columns:
                    matches = df[df[col].str.contains(title, case=False, na=False)]
                    if not matches.empty:
                        break
        
        if matches.empty:
            print(f"❌ Not found in metadata")
            continue
        
        for idx, row in matches.iterrows():
            print(f"\n✓ Found: {row['title_display']}")
            print(f"  anime_id: {row['anime_id']}")
            
            # Basic stats
            print(f"\n  📊 BASIC STATS:")
            print(f"    MAL Score: {row.get('mal_score', 'N/A')}")
            print(f"    MAL Rank: {row.get('mal_rank', 'N/A')}")
            print(f"    MAL Popularity: {row.get('mal_popularity', 'N/A')}")
            print(f"    Members: {row.get('members_count', 'N/A'):,}" if pd.notna(row.get('members_count')) else "    Members: N/A")
            print(f"    Status: {row.get('status', 'N/A')}")
            print(f"    Episodes: {row.get('episodes', 'N/A')}")
            
            # Genres
            genres = row.get('genres', '')
            if isinstance(genres, str):
                genre_list = [g.strip() for g in genres.split('|') if g.strip()]
            elif hasattr(genres, '__iter__'):
                genre_list = [str(g) for g in genres if g]
            else:
                genre_list = []
            print(f"    Genres: {', '.join(genre_list) if genre_list else 'None'}")
            
            # Themes
            themes = row.get('themes', '')
            if isinstance(themes, str):
                theme_list = [t.strip() for t in themes.split('|') if t.strip()]
            elif hasattr(themes, '__iter__'):
                theme_list = [str(t) for t in themes if t]
            else:
                theme_list = []
            print(f"    Themes: {', '.join(theme_list) if theme_list else 'None'}")
            
            # Synopsis
            synopsis = row.get('synopsis', '')
            if pd.notna(synopsis) and synopsis:
                print(f"\n  📝 SYNOPSIS:")
                print(f"    {str(synopsis)[:200]}..." if len(str(synopsis)) > 200 else f"    {synopsis}")
            
            # Check if it's in training data
            print(f"\n  🔍 POTENTIAL ISSUES:")
            
            # Low MAL score
            if pd.notna(row.get('mal_score')) and row['mal_score'] < 6.0:
                print(f"    ⚠️  Low MAL score ({row['mal_score']:.2f}) - users don't rate it highly")
            
            # Low popularity
            if pd.notna(row.get('mal_popularity')) and row['mal_popularity'] > 10000:
                print(f"    ⚠️  Low popularity rank ({row['mal_popularity']:,}) - obscure title")
            
            # Few members
            if pd.notna(row.get('members_count')) and row['members_count'] < 1000:
                print(f"    ⚠️  Very few members ({row['members_count']:,}) - limited data")
            
            # Few/no genres
            if len(genre_list) == 0:
                print(f"    ⚠️  No genres - missing metadata")
            elif len(genre_list) > 8:
                print(f"    ⚠️  Too many genres ({len(genre_list)}) - noisy metadata")
            
            # Missing synopsis
            if not pd.notna(synopsis) or not synopsis:
                print(f"    ⚠️  Missing synopsis - can't do content-based filtering")
    
    # Overall statistics
    print(f"\n\n{'=' * 80}")
    print(f"📈 OVERALL STATISTICS")
    print(f"{'=' * 80}")
    
    print(f"\nMAL Score distribution:")
    print(df['mal_score'].describe())
    
    print(f"\nMAL Popularity distribution:")
    print(df['mal_popularity'].describe())
    
    print(f"\nMembers count distribution:")
    print(df['members_count'].describe())
    
    # Find other potential problematic titles
    print(f"\n\n{'=' * 80}")
    print(f"🔎 OTHER POTENTIALLY PROBLEMATIC TITLES")
    print(f"{'=' * 80}")
    
    # Low score, high in popularity index (paradox)
    problematic = df[
        (df['mal_score'] < 5.5) & 
        (df['mal_popularity'] < 5000)
    ].sort_values('mal_popularity')
    
    if not problematic.empty:
        print(f"\n⚠️  Titles with LOW scores but HIGH popularity (paradox - might be over-recommended):")
        for idx, row in problematic.head(10).iterrows():
            print(f"  - {row['title_display']}: Score={row['mal_score']:.2f}, Pop Rank={row['mal_popularity']:,}")
    
    # Very obscure but might have data artifacts
    obscure = df[
        (df['members_count'] < 500) & 
        (df['mal_popularity'] > 15000)
    ].sort_values('members_count')
    
    if not obscure.empty:
        print(f"\n⚠️  Very obscure titles (might get recommended due to data sparsity):")
        for idx, row in obscure.head(10).iterrows():
            members = row['members_count'] if pd.notna(row['members_count']) else 0
            print(f"  - {row['title_display']}: {members:,} members, Pop Rank={row.get('mal_popularity', 'N/A')}")


if __name__ == "__main__":
    investigate_titles()
