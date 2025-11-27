"""
User Profile Management

Handles saving, loading, and managing user watchlist profiles.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Profile directory
PROFILES_DIR = Path(__file__).parent.parent.parent / "data" / "user_profiles"


def ensure_profiles_dir() -> Path:
    """Ensure the profiles directory exists."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILES_DIR


def save_profile(username: str, profile_data: Dict) -> Path:
    """
    Save a user profile to disk.
    
    Args:
        username: Username for the profile (used as filename)
        profile_data: Dictionary containing profile data:
            - watched_ids: List of anime_ids
            - ratings: Dict of anime_id -> rating
            - status_map: Dict of anime_id -> status string
            - mal_username: Original MAL username
            - stats: Statistics dictionary
    
    Returns:
        Path to the saved profile file
    """
    ensure_profiles_dir()
    
    # Build full profile with metadata
    full_profile = {
        'username': username,
        'mal_username': profile_data.get('mal_username', username),
        'watched_ids': profile_data.get('watched_ids', []),
        'ratings': {str(k): v for k, v in profile_data.get('ratings', {}).items()},  # JSON keys must be strings
        'status_map': {str(k): v for k, v in profile_data.get('status_map', {}).items()},
        'import_date': datetime.now().isoformat(),
        'stats': profile_data.get('stats', {})
    }
    
    # Save to file
    profile_path = PROFILES_DIR / f"{username}_profile.json"
    
    try:
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(full_profile, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved profile for {username} to {profile_path}")
        return profile_path
    
    except Exception as e:
        logger.error(f"Failed to save profile for {username}: {e}")
        raise


def load_profile(username: str) -> Optional[Dict]:
    """
    Load a user profile from disk.
    
    Args:
        username: Username of the profile to load
    
    Returns:
        Profile dictionary if found, None otherwise
    """
    profile_path = PROFILES_DIR / f"{username}_profile.json"
    
    if not profile_path.exists():
        logger.warning(f"Profile not found for {username}")
        return None
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Convert string keys back to integers for watched_ids
        if 'ratings' in profile_data:
            profile_data['ratings'] = {int(k): v for k, v in profile_data['ratings'].items()}
        
        if 'status_map' in profile_data:
            profile_data['status_map'] = {int(k): v for k, v in profile_data['status_map'].items()}
        
        logger.info(f"Loaded profile for {username} ({len(profile_data.get('watched_ids', []))} anime)")
        return profile_data
    
    except Exception as e:
        logger.error(f"Failed to load profile for {username}: {e}")
        return None


def list_profiles() -> List[str]:
    """
    List all available profile usernames.
    
    Returns:
        List of usernames (without the _profile.json suffix)
    """
    ensure_profiles_dir()
    
    profiles = []
    for profile_path in PROFILES_DIR.glob("*_profile.json"):
        # Extract username from filename
        username = profile_path.stem.replace('_profile', '')
        profiles.append(username)
    
    return sorted(profiles)


def delete_profile(username: str) -> bool:
    """
    Delete a user profile.
    
    Args:
        username: Username of the profile to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    profile_path = PROFILES_DIR / f"{username}_profile.json"
    
    if not profile_path.exists():
        logger.warning(f"Profile not found for deletion: {username}")
        return False
    
    try:
        profile_path.unlink()
        logger.info(f"Deleted profile for {username}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to delete profile for {username}: {e}")
        return False


def validate_profile(profile_data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate a profile data structure.
    
    Args:
        profile_data: Profile dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['username', 'watched_ids', 'ratings', 'stats']
    
    for field in required_fields:
        if field not in profile_data:
            return False, f"Missing required field: {field}"
    
    if not isinstance(profile_data['watched_ids'], list):
        return False, "watched_ids must be a list"
    
    if not isinstance(profile_data['ratings'], dict):
        return False, "ratings must be a dictionary"
    
    if not isinstance(profile_data['stats'], dict):
        return False, "stats must be a dictionary"
    
    # Check rating values are in valid range
    for anime_id, rating in profile_data['ratings'].items():
        if not isinstance(rating, (int, float)):
            return False, f"Invalid rating for anime_id {anime_id}: must be numeric"
        
        if rating < 0 or rating > 10:
            return False, f"Invalid rating for anime_id {anime_id}: must be 0-10"
    
    return True, None


def get_profile_summary(username: str) -> Optional[Dict]:
    """
    Get a summary of a profile without loading full data.
    
    Returns quick stats about the profile for display purposes.
    """
    profile = load_profile(username)
    
    if profile is None:
        return None
    
    return {
        'username': profile.get('username', username),
        'mal_username': profile.get('mal_username', username),
        'total_watched': len(profile.get('watched_ids', [])),
        'total_rated': len(profile.get('ratings', {})),
        'avg_rating': profile.get('stats', {}).get('avg_rating', 0),
        'import_date': profile.get('import_date'),
        'status_breakdown': profile.get('stats', {}).get('status_breakdown', {})
    }
