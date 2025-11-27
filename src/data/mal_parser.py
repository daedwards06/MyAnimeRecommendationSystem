"""
MyAnimeList XML Export Parser

Parses MAL export XML files and maps anime entries to internal database IDs.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


def parse_mal_export(
    xml_path: Path | str,
    metadata_df,
    include_statuses: Optional[Set[str]] = None,
    default_rating: float = 7.0,
    use_default_for_unrated: bool = True
) -> Dict:
    """
    Parse a MyAnimeList XML export file.
    
    Args:
        xml_path: Path to the MAL XML export file
        metadata_df: DataFrame with anime metadata (must have 'anime_id' and 'title_primary' columns)
        include_statuses: Set of statuses to include (e.g., {'Completed', 'Watching'}).
                         Defaults to {'Completed', 'Watching', 'On-Hold'} if None.
        default_rating: Default rating to use for unrated anime when use_default_for_unrated=True
        use_default_for_unrated: Whether to assign default_rating to unrated completed anime
    
    Returns:
        Dictionary containing:
        - username: MAL username
        - mal_username: MAL username (same as username)
        - watched_ids: List of internal anime_ids
        - ratings: Dict mapping anime_id -> rating (1-10 scale)
        - status_map: Dict mapping anime_id -> status string
        - unmatched: List of dicts with MAL entries that couldn't be matched to our DB
        - stats: Dictionary with import statistics
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    # Default statuses to include
    if include_statuses is None:
        include_statuses = {'Completed', 'Watching', 'On-Hold'}
    
    # Parse XML
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML file: {e}")
    
    # Extract user info
    myinfo = root.find('myinfo')
    if myinfo is None:
        raise ValueError("XML file missing <myinfo> section")
    
    username_elem = myinfo.find('user_name')
    username = username_elem.text if username_elem is not None else "unknown_user"
    
    # Build lookup: MAL ID -> internal anime_id
    mal_id_to_internal = {}
    title_to_internal = {}
    
    for _, row in metadata_df.iterrows():
        anime_id = int(row['anime_id'])
        mal_id_to_internal[anime_id] = anime_id  # MAL IDs match our anime_ids (from Jikan)
        
        # Also build title lookup for fuzzy matching fallback
        title = str(row.get('title_primary', '')).lower().strip()
        if title:
            title_to_internal[title] = anime_id
    
    # Parse anime entries
    watched_ids = []
    ratings = {}
    status_map = {}
    unmatched = []
    
    rated_count = 0
    unrated_count = 0
    
    for anime_elem in root.findall('anime'):
        # Extract fields
        mal_id_elem = anime_elem.find('series_animedb_id')
        title_elem = anime_elem.find('series_title')
        score_elem = anime_elem.find('my_score')
        status_elem = anime_elem.find('my_status')
        
        if mal_id_elem is None or title_elem is None:
            continue
        
        try:
            mal_id = int(mal_id_elem.text)
        except (ValueError, TypeError):
            continue
        
        title = title_elem.text or ""
        status = status_elem.text if status_elem is not None else "Unknown"
        
        # Filter by status
        if status not in include_statuses:
            continue
        
        # Try to match to internal ID
        internal_id = None
        
        # Primary: Direct MAL ID lookup
        if mal_id in mal_id_to_internal:
            internal_id = mal_id_to_internal[mal_id]
        else:
            # Fallback: Title matching (case-insensitive)
            title_lower = title.lower().strip()
            if title_lower in title_to_internal:
                internal_id = title_to_internal[title_lower]
        
        # Handle unmatched
        if internal_id is None:
            unmatched.append({
                'mal_id': mal_id,
                'title': title,
                'status': status,
                'score': score_elem.text if score_elem is not None else None
            })
            logger.warning(f"Could not match MAL ID {mal_id} ({title}) to internal database")
            continue
        
        # Add to watched list
        watched_ids.append(internal_id)
        status_map[internal_id] = status
        
        # Handle ratings
        score_text = score_elem.text if score_elem is not None else None
        try:
            score = float(score_text) if score_text else 0.0
        except (ValueError, TypeError):
            score = 0.0
        
        if score > 0:
            ratings[internal_id] = score
            rated_count += 1
        else:
            # Unrated entry
            unrated_count += 1
            if use_default_for_unrated and status == 'Completed':
                ratings[internal_id] = default_rating
    
    # Calculate statistics
    total_watched = len(watched_ids)
    avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0.0
    
    stats = {
        'total_watched': total_watched,
        'rated_count': rated_count,
        'unrated_count': unrated_count,
        'avg_rating': round(avg_rating, 2),
        'unmatched_count': len(unmatched),
        'status_breakdown': {}
    }
    
    # Status breakdown
    for status in include_statuses:
        count = sum(1 for s in status_map.values() if s == status)
        if count > 0:
            stats['status_breakdown'][status] = count
    
    logger.info(f"Parsed MAL export for {username}: {total_watched} anime, {rated_count} rated, {len(unmatched)} unmatched")
    
    return {
        'username': username,
        'mal_username': username,
        'watched_ids': watched_ids,
        'ratings': ratings,
        'status_map': status_map,
        'unmatched': unmatched,
        'stats': stats
    }


def get_mal_export_summary(xml_path: Path | str) -> Dict:
    """
    Quick summary of a MAL export file without full parsing.
    
    Returns basic stats about the export (total anime, ratings, statuses).
    Useful for preview before full import.
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML file: {e}")
    
    # Extract user info
    myinfo = root.find('myinfo')
    if myinfo is None:
        return {'error': 'Missing myinfo section'}
    
    username_elem = myinfo.find('user_name')
    username = username_elem.text if username_elem is not None else "unknown"
    
    total_anime_elem = myinfo.find('user_total_anime')
    total_anime = int(total_anime_elem.text) if total_anime_elem is not None else 0
    
    total_completed_elem = myinfo.find('user_total_completed')
    total_completed = int(total_completed_elem.text) if total_completed_elem is not None else 0
    
    total_watching_elem = myinfo.find('user_total_watching')
    total_watching = int(total_watching_elem.text) if total_watching_elem is not None else 0
    
    total_onhold_elem = myinfo.find('user_total_onhold')
    total_onhold = int(total_onhold_elem.text) if total_onhold_elem is not None else 0
    
    total_dropped_elem = myinfo.find('user_total_dropped')
    total_dropped = int(total_dropped_elem.text) if total_dropped_elem is not None else 0
    
    total_plantowatch_elem = myinfo.find('user_total_plantowatch')
    total_plantowatch = int(total_plantowatch_elem.text) if total_plantowatch_elem is not None else 0
    
    # Count rated entries
    rated_count = 0
    for anime_elem in root.findall('anime'):
        score_elem = anime_elem.find('my_score')
        if score_elem is not None:
            try:
                score = float(score_elem.text) if score_elem.text else 0
                if score > 0:
                    rated_count += 1
            except (ValueError, TypeError):
                pass
    
    return {
        'username': username,
        'total_anime': total_anime,
        'total_completed': total_completed,
        'total_watching': total_watching,
        'total_onhold': total_onhold,
        'total_dropped': total_dropped,
        'total_plantowatch': total_plantowatch,
        'rated_count': rated_count,
        'unrated_count': total_anime - rated_count
    }
