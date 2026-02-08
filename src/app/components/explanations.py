"""
Personalized Recommendation Explanations

Generates human-readable explanations for why recommendations are being shown
based on user's taste profile and rating history.
"""

import logging

import numpy as np
import pandas as pd

from src.app.score_semantics import SCORE_LABEL_SHORT, format_match_score

logger = logging.getLogger(__name__)


def generate_explanation(
    anime_id: int,
    match_score: float,
    user_profile: dict,
    metadata_df: pd.DataFrame,
    top_n_genres: int = 3
) -> str | None:
    """
    Generate an explanation for why this anime is recommended.

    Args:
        anime_id: ID of recommended anime
        match_score: Recommendation match score (relative, uncalibrated)
        user_profile: User profile with ratings and stats
        metadata_df: DataFrame with anime metadata
        top_n_genres: Number of top genres to mention

    Returns:
        Explanation string or None if unable to generate
    """
    try:
        # Get anime metadata
        anime_row = metadata_df[metadata_df['anime_id'] == anime_id]
        if anime_row.empty:
            return None

        anime_row = anime_row.iloc[0]
        anime_genres = _parse_genres(anime_row.get('genres', ''))

        # Get user's taste profile
        ratings = user_profile.get('ratings', {})
        if not ratings:
            return None

        # Calculate user's genre preferences
        genre_ratings = _calculate_genre_ratings(ratings, metadata_df)

        # Find matching genres between anime and user preferences
        matching_genres = []
        for genre in anime_genres:
            if genre in genre_ratings:
                avg_rating = genre_ratings[genre]['avg']
                count = genre_ratings[genre]['count']
                if count >= 2:  # Only mention genres with at least 2 ratings
                    matching_genres.append((genre, avg_rating, count))

        # Sort by average rating
        matching_genres.sort(key=lambda x: x[1], reverse=True)

        # Build explanation
        parts = []

        # Part 1: Match score (relative, uncalibrated)
        parts.append(f"📈 **{SCORE_LABEL_SHORT}: {format_match_score(match_score)}**")

        # Part 2: Genre match (if any)
        if matching_genres:
            top_genres = matching_genres[:top_n_genres]
            genre_texts = []
            for genre, avg, count in top_genres:
                genre_texts.append(f"{genre} ({avg:.1f}★)")

            if len(genre_texts) == 1:
                parts.append(f"You rate {genre_texts[0]} highly")
            else:
                genre_list = ", ".join(genre_texts[:-1]) + f" & {genre_texts[-1]}"
                parts.append(f"You rate {genre_list}")

        # Part 3: Similar to highly-rated anime (if available)
        similar_anime = _find_similar_rated_anime(
            anime_id,
            anime_genres,
            ratings,
            metadata_df,
            min_rating=8.0,
            max_results=2
        )

        if similar_anime:
            if len(similar_anime) == 1:
                parts.append(f"Similar to: {similar_anime[0]}")
            else:
                parts.append(f"Similar to: {similar_anime[0]}, {similar_anime[1]}")

        # Combine parts
        if len(parts) == 1:
            # Only have match score, add generic message
            return f"{parts[0]} • Based on your taste profile"

        return " • ".join(parts)

    except Exception as e:
        logger.warning(f"Failed to generate explanation for anime {anime_id}: {e}")
        return None


def _parse_genres(genres_str) -> list[str]:
    """Parse genres from string, list, or numpy array format."""
    if isinstance(genres_str, str):
        # Handle pipe-delimited format
        return [g.strip() for g in genres_str.split('|') if g.strip()]
    elif isinstance(genres_str, (list, np.ndarray)):
        # Handle list or numpy array
        return [str(g).strip() for g in genres_str if g]
    return []


def _calculate_genre_ratings(
    ratings: dict[int, float],
    metadata_df: pd.DataFrame
) -> dict[str, dict[str, float]]:
    """
    Calculate average rating per genre from user's rating history.

    Returns:
        Dict mapping genre -> {'avg': float, 'count': int, 'total': float}
    """
    genre_stats = {}

    for anime_id_str, rating in ratings.items():
        # Convert to int (ratings dict has string keys from JSON)
        try:
            anime_id = int(anime_id_str)
        except (ValueError, TypeError):
            continue

        # Find anime in metadata
        anime_row = metadata_df[metadata_df['anime_id'] == anime_id]
        if anime_row.empty:
            continue

        # Parse genres
        genres = _parse_genres(anime_row.iloc[0].get('genres', ''))

        # Update stats for each genre
        for genre in genres:
            if genre not in genre_stats:
                genre_stats[genre] = {'total': 0.0, 'count': 0}

            genre_stats[genre]['total'] += rating
            genre_stats[genre]['count'] += 1

    # Calculate averages
    for genre in genre_stats:
        count = genre_stats[genre]['count']
        total = genre_stats[genre]['total']
        genre_stats[genre]['avg'] = total / count if count > 0 else 0.0

    return genre_stats


def _find_similar_rated_anime(
    target_anime_id: int,
    target_genres: list[str],
    ratings: dict[int, float],
    metadata_df: pd.DataFrame,
    min_rating: float = 8.0,
    max_results: int = 2
) -> list[str]:
    """
    Find highly-rated anime that share genres with the target anime.

    Args:
        target_anime_id: ID of recommended anime
        target_genres: Genres of recommended anime
        ratings: User's rating history
        metadata_df: Anime metadata
        min_rating: Minimum rating to consider (default 8.0)
        max_results: Maximum number of titles to return

    Returns:
        List of anime titles
    """
    similar = []

    for anime_id_str, rating in ratings.items():
        # Convert to int (ratings dict has string keys from JSON)
        try:
            anime_id = int(anime_id_str)
        except (ValueError, TypeError):
            continue

        if anime_id == target_anime_id:
            continue

        if rating < min_rating:
            continue

        # Get anime metadata
        anime_row = metadata_df[metadata_df['anime_id'] == anime_id]
        if anime_row.empty:
            continue

        anime_row = anime_row.iloc[0]
        anime_genres = _parse_genres(anime_row.get('genres', ''))

        # Check for genre overlap
        overlap = set(target_genres) & set(anime_genres)
        if len(overlap) >= 2:  # At least 2 shared genres
            # Prefer English title
            title = anime_row.get('title_english')
            if not title or not isinstance(title, str) or not title.strip():
                title = anime_row.get('title_display', f"Anime {anime_id}")

            similar.append((title, rating, len(overlap)))

    # Sort by rating (desc), then overlap (desc)
    similar.sort(key=lambda x: (x[1], x[2]), reverse=True)

    # Return just titles
    return [title for title, _, _ in similar[:max_results]]


def generate_batch_explanations(
    recommendations: list[dict],
    user_profile: dict,
    metadata_df: pd.DataFrame
) -> list[dict]:
    """
    Generate explanations for a batch of recommendations.

    Args:
        recommendations: List of recommendation dicts with anime_id and score
        user_profile: User profile with ratings
        metadata_df: Anime metadata

    Returns:
        Same recommendations list with 'explanation' field added
    """
    enriched = []

    for rec in recommendations:
        anime_id = rec.get('anime_id')
        score = rec.get('score', 0.0)

        # Generate explanation
        explanation = generate_explanation(
            anime_id=anime_id,
            match_score=score,
            user_profile=user_profile,
            metadata_df=metadata_df
        )

        # Add to recommendation
        rec_copy = rec.copy()
        rec_copy['explanation'] = explanation
        enriched.append(rec_copy)

    return enriched
