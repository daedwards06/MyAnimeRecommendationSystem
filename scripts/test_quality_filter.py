"""Test quality filter impact on recommendations."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.app.quality_filters import passes_quality_filter, MIN_MEMBERS_COUNT, MIN_MAL_SCORE

df = pd.read_parquet('data/processed/anime_metadata.parquet')

# Test Tokyo Ghoul similar anime
tg = df[df['title_display'].str.contains('Tokyo Ghoul', case=False, na=False)].head(1)
if not tg.empty:
    print('Tokyo Ghoul:', tg[['anime_id', 'title_display', 'genres']].iloc[0])
    genres = str(tg.iloc[0]['genres'])
    print(f'\nGenres: {genres}')

print('\n' + '='*80)
print('FILTER IMPACT ANALYSIS')
print('='*80)

# Check overall filtering impact
total = len(df)
passed = sum(1 for _, row in df.iterrows() if passes_quality_filter(row))
filtered_out = total - passed

print(f'\nTotal anime: {total}')
print(f'Pass filter: {passed} ({passed/total*100:.1f}%)')
print(f'Filtered out: {filtered_out} ({filtered_out/total*100:.1f}%)')

# Breakdown by reason
print('\n' + '-'*80)
print('FILTERED OUT BY REASON:')
print('-'*80)

too_few_members = sum(1 for _, row in df.iterrows() if pd.isna(row.get('members_count')) or row.get('members_count') < MIN_MEMBERS_COUNT)
low_score = sum(1 for _, row in df.iterrows() if pd.notna(row.get('mal_score')) and row.get('mal_score') < MIN_MAL_SCORE)
too_obscure = sum(1 for _, row in df.iterrows() if pd.notna(row.get('mal_popularity')) and row.get('mal_popularity') > 20000)
no_synopsis = sum(1 for _, row in df.iterrows() if pd.isna(row.get('synopsis')) or not str(row.get('synopsis')).strip())

print(f'Too few members (<{MIN_MEMBERS_COUNT}): {too_few_members}')
print(f'Low MAL score (<{MIN_MAL_SCORE}): {low_score}')
print(f'Too obscure (>20k rank): {too_obscure}')
print(f'Missing synopsis: {no_synopsis}')

# Check Action genre specifically
print('\n' + '-'*80)
print('ACTION GENRE ANALYSIS (similar to Tokyo Ghoul):')
print('-'*80)

action = df[df['genres'].str.contains('Action', case=False, na=False)]
action_passed = sum(1 for _, row in action.iterrows() if passes_quality_filter(row))

print(f'Total Action anime: {len(action)}')
print(f'Pass filter: {action_passed} ({action_passed/len(action)*100:.1f}%)')
print(f'Filtered out: {len(action) - action_passed}')

print('\nMembers distribution for Action anime:')
print(action['members_count'].describe())

print('\nScore distribution for Action anime:')
print(action['mal_score'].describe())
