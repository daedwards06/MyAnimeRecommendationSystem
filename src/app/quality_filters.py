"""Quality filters for recommendations to prevent poor matches.

This module provides filtering logic to exclude:
- Titles with insufficient data
- Titles with poor ratings
- Outliers that shouldn't be recommended
"""

from __future__ import annotations
import pandas as pd
from typing import Optional

# Quality thresholds - relaxed to avoid over-filtering
MIN_MEMBERS_COUNT = 200  # At least 200 MAL members (was 500)
MIN_MAL_SCORE = 4.0      # At least 4.0 rating (was 5.0) - below this is generally poor quality
MAX_POPULARITY_RANK = 23000  # Don't recommend extremely obscure titles (was 20000)

# Blacklist problematic titles (by anime_id) - for known bad data
BLACKLIST_IDS = [
    28489,  # Jigoku Koushien (no score, no synopsis, 422 members)
]


def passes_quality_filter(
    row: pd.Series,
    min_members: int = MIN_MEMBERS_COUNT,
    min_score: float = MIN_MAL_SCORE,
    max_pop_rank: int = MAX_POPULARITY_RANK,
    require_synopsis: bool = False  # Changed to False - some good anime have missing synopsis
) -> bool:
    """Check if an anime passes quality thresholds for recommendation.
    
    Parameters
    ----------
    row : pd.Series
        Anime metadata row
    min_members : int
        Minimum MAL members count
    min_score : float
        Minimum MAL score
    max_pop_rank : int
        Maximum popularity rank (higher = more obscure)
    require_synopsis : bool
        Whether to require a non-empty synopsis
        
    Returns
    -------
    bool
        True if passes all filters
    """
    anime_id = int(row.get('anime_id', -1))
    
    # Blacklist check
    if anime_id in BLACKLIST_IDS:
        return False
    
    # Members count check
    members = row.get('members_count')
    if pd.isna(members) or members < min_members:
        return False
    
    # MAL score check (allow NaN for cold-start, but if present must be >= threshold)
    mal_score = row.get('mal_score')
    if pd.notna(mal_score) and mal_score < min_score:
        return False
    
    # Popularity rank check (lower rank = more popular, so must be below threshold)
    pop_rank = row.get('mal_popularity')
    if pd.notna(pop_rank) and pop_rank > max_pop_rank:
        return False
    
    # Synopsis check
    if require_synopsis:
        synopsis = row.get('synopsis')
        if pd.isna(synopsis) or not str(synopsis).strip():
            return False
    
    return True


def apply_quality_filters(
    recommendations: list[dict],
    metadata: pd.DataFrame,
    verbose: bool = False
) -> list[dict]:
    """Filter recommendation list to remove low-quality matches.
    
    Parameters
    ----------
    recommendations : list[dict]
        List of recommendation dicts with 'anime_id' keys
    metadata : pd.DataFrame
        Full metadata DataFrame
    verbose : bool
        Whether to print filtering stats
        
    Returns
    -------
    list[dict]
        Filtered recommendations
    """
    filtered = []
    removed_count = 0
    removed_reasons = {}
    
    for rec in recommendations:
        anime_id = rec['anime_id']
        row = metadata[metadata['anime_id'] == anime_id]
        
        if row.empty:
            removed_count += 1
            removed_reasons['not_in_metadata'] = removed_reasons.get('not_in_metadata', 0) + 1
            continue
        
        row = row.iloc[0]
        
        if passes_quality_filter(row):
            filtered.append(rec)
        else:
            removed_count += 1
            # Identify reason
            if int(row['anime_id']) in BLACKLIST_IDS:
                removed_reasons['blacklisted'] = removed_reasons.get('blacklisted', 0) + 1
            elif pd.isna(row.get('members_count')) or row.get('members_count') < MIN_MEMBERS_COUNT:
                removed_reasons['too_few_members'] = removed_reasons.get('too_few_members', 0) + 1
            elif pd.notna(row.get('mal_score')) and row.get('mal_score') < MIN_MAL_SCORE:
                removed_reasons['low_score'] = removed_reasons.get('low_score', 0) + 1
            elif pd.notna(row.get('mal_popularity')) and row.get('mal_popularity') > MAX_POPULARITY_RANK:
                removed_reasons['too_obscure'] = removed_reasons.get('too_obscure', 0) + 1
            else:
                removed_reasons['missing_synopsis'] = removed_reasons.get('missing_synopsis', 0) + 1
    
    if verbose and removed_count > 0:
        print(f"Quality filter removed {removed_count} recommendations:")
        for reason, count in removed_reasons.items():
            print(f"  - {reason}: {count}")
    
    return filtered


__all__ = ['passes_quality_filter', 'apply_quality_filters', 'BLACKLIST_IDS']
