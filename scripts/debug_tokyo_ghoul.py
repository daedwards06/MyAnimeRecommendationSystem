"""Debug Tokyo Ghoul recommendations to see what's being filtered."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from src.app.quality_filters import apply_quality_filters, passes_quality_filter

# Load metadata
df = pd.read_parquet('data/processed/anime_metadata.parquet')

# Find Tokyo Ghoul
tg = df[df['title_display'].str.contains('Tokyo Ghoul', case=False, na=False)].head(1)
if tg.empty:
    print("❌ Tokyo Ghoul not found")
    exit()

tg_id = int(tg.iloc[0]['anime_id'])
tg_genres = tg.iloc[0]['genres']
print(f"Tokyo Ghoul: ID={tg_id}")
print(f"Genres: {tg_genres}")

# Simulate seed-based recommendations (genre overlap)
print(f"\n{'='*80}")
print("SIMULATING SEED-BASED RECOMMENDATIONS")
print(f"{'='*80}")

# Get genre set
if isinstance(tg_genres, str):
    seed_genres = set([g.strip() for g in tg_genres.split('|') if g.strip()])
else:
    seed_genres = set([str(g) for g in tg_genres if g])

print(f"Seed genres: {seed_genres}")

# Find similar titles
similar = []
for idx, row in df.iterrows():
    aid = int(row['anime_id'])
    if aid == tg_id:
        continue
    
    row_genres = row.get('genres')
    if isinstance(row_genres, str):
        item_genres = set([g.strip() for g in row_genres.split('|') if g.strip()])
    elif hasattr(row_genres, '__iter__'):
        item_genres = set([str(g) for g in row_genres if g])
    else:
        continue
    
    overlap = len(seed_genres & item_genres)
    if overlap > 0:
        similar.append({
            'anime_id': aid,
            'title': row['title_display'],
            'overlap': overlap,
            'genres': item_genres,
            'members': row.get('members_count'),
            'score': row.get('mal_score'),
            'pop_rank': row.get('mal_popularity'),
            'passes_filter': passes_quality_filter(row)
        })

# Sort by overlap
similar.sort(key=lambda x: x['overlap'], reverse=True)

print(f"\nFound {len(similar)} titles with genre overlap")

# Show top 20 before filtering
print(f"\n{'='*80}")
print("TOP 20 SIMILAR TITLES (BEFORE QUALITY FILTER)")
print(f"{'='*80}")

for i, item in enumerate(similar[:20], 1):
    passes = "✓" if item['passes_filter'] else "✗"
    print(f"{i}. {passes} {item['title']}")
    print(f"   Overlap: {item['overlap']}, Members: {item['members']:,.0f}, Score: {item['score']}, Pop Rank: {item['pop_rank']}")

# Apply quality filter
print(f"\n{'='*80}")
print("AFTER QUALITY FILTER")
print(f"{'='*80}")

rec_dicts = [{'anime_id': s['anime_id'], 'score': float(s['overlap'])} for s in similar[:50]]
filtered = apply_quality_filters(rec_dicts, df, verbose=True)

print(f"\nOriginal recommendations: {len(rec_dicts)}")
print(f"After quality filter: {len(filtered)}")

if filtered:
    print(f"\nTop 10 after filtering:")
    for i, rec in enumerate(filtered[:10], 1):
        title_row = df[df['anime_id'] == rec['anime_id']].iloc[0]
        print(f"{i}. {title_row['title_display']}")
        print(f"   Members: {title_row['members_count']:,.0f}, Score: {title_row['mal_score']}")
else:
    print("\n❌ ALL RECOMMENDATIONS FILTERED OUT!")
    print("\nChecking why...")
    
    # Analyze why they're being filtered
    for item in similar[:20]:
        if not item['passes_filter']:
            reasons = []
            if pd.isna(item['members']) or item['members'] < 200:
                reasons.append(f"<200 members ({item['members']})")
            if pd.notna(item['score']) and item['score'] < 4.0:
                reasons.append(f"<4.0 score ({item['score']})")
            if pd.notna(item['pop_rank']) and item['pop_rank'] > 23000:
                reasons.append(f">23k rank ({item['pop_rank']})")
            
            print(f"\n✗ {item['title']}")
            print(f"  Reasons: {', '.join(reasons) if reasons else 'Unknown'}")
