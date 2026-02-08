"""
User Embedding Generation from Ratings

Generates personalized user embeddings from rating history using the MF model's item factors.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def generate_user_embedding(
    ratings_dict: dict[int, float],
    mf_model,
    method: str = "weighted_average",
    default_rating: float | None = None,
    normalize: bool = True
) -> np.ndarray:
    """
    Generate a user embedding vector from their rating history.

    Args:
        ratings_dict: Dictionary mapping anime_id -> rating (1-10 scale)
        mf_model: Trained MF model with Q (item factors) and item_to_index mapping
        method: Embedding generation method:
            - "weighted_average": Average item factors weighted by normalized ratings
            - "simple_average": Unweighted average of item factors
        default_rating: If provided, use this rating for items without explicit ratings
        normalize: Whether to L2-normalize the final embedding

    Returns:
        User embedding vector (same dimensions as item factors)
    """
    if not hasattr(mf_model, 'Q') or not hasattr(mf_model, 'item_to_index'):
        raise ValueError("MF model must have 'Q' (item factors) and 'item_to_index' attributes")

    Q = mf_model.Q  # Item factors matrix (num_items, n_factors)
    item_to_index = mf_model.item_to_index
    n_factors = Q.shape[1]

    # Filter ratings to only include items in the training set
    valid_ratings = {}
    missing_count = 0

    for anime_id, rating in ratings_dict.items():
        if anime_id in item_to_index:
            valid_ratings[anime_id] = rating
        else:
            missing_count += 1

    if missing_count > 0:
        logger.info(f"Skipped {missing_count} items not in MF training set")

    if not valid_ratings:
        logger.warning("No valid ratings found in training set - returning zero embedding")
        return np.zeros(n_factors, dtype=np.float32)

    # Generate embedding based on method
    if method == "weighted_average":
        # Use mean-centered ratings as weights, with a positive floor.
        # This avoids the min-max normalization pitfall where a user who
        # rates everything 8-10 would have their 8/10 anime mapped to
        # weight 0.0 (losing their positive signal entirely).
        #
        # Formula: weight = max(rating - user_mean + 1.0, 0.1)
        # The +1.0 shift ensures items at the user's mean still contribute
        # positively. The 0.1 floor prevents any rated item from being
        # completely ignored.
        ratings_array = np.array(list(valid_ratings.values()), dtype=np.float32)
        user_mean = float(np.mean(ratings_array))
        weights_array = np.maximum(ratings_array - user_mean + 1.0, 0.1)

        # Weighted sum of item factors
        embedding = np.zeros(n_factors, dtype=np.float32)
        weight_sum = 0.0

        for (anime_id, _), weight in zip(valid_ratings.items(), weights_array):
            item_idx = item_to_index[anime_id]
            embedding += weight * Q[item_idx]
            weight_sum += weight

        if weight_sum > 0:
            embedding /= weight_sum

    elif method == "simple_average":
        # Unweighted average of item factors
        embedding = np.zeros(n_factors, dtype=np.float32)

        for anime_id in valid_ratings:
            item_idx = item_to_index[anime_id]
            embedding += Q[item_idx]

        embedding /= len(valid_ratings)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'weighted_average' or 'simple_average'")

    # Optional L2 normalization
    if normalize:
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding /= norm

    logger.info(f"Generated user embedding from {len(valid_ratings)} ratings using {method}")

    return embedding


def compute_personalized_scores(
    user_embedding: np.ndarray,
    mf_model,
    exclude_anime_ids: set | None = None
) -> dict[int, float]:
    """
    Compute personalized recommendation scores for all items using user embedding.

    Args:
        user_embedding: User factor vector (n_factors,)
        mf_model: Trained MF model with Q (item factors) and index_to_item mapping
        exclude_anime_ids: Set of anime_ids to exclude from scoring

    Returns:
        Dictionary mapping anime_id -> predicted score
    """
    if not hasattr(mf_model, 'Q') or not hasattr(mf_model, 'index_to_item'):
        raise ValueError("MF model must have 'Q' (item factors) and 'index_to_item' attributes")

    Q = mf_model.Q  # Item factors matrix (num_items, n_factors)
    index_to_item = mf_model.index_to_item

    # Compute scores: dot product of user embedding with all item factors
    scores = user_embedding @ Q.T  # (n_factors,) @ (num_items, n_factors).T -> (num_items,)

    # Build result dictionary
    result = {}
    for idx, anime_id in index_to_item.items():
        if exclude_anime_ids and anime_id in exclude_anime_ids:
            continue
        result[anime_id] = float(scores[idx])

    return result


def get_user_taste_profile(
    ratings_dict: dict[int, float],
    metadata_df,
    top_n_genres: int = 5
) -> dict:
    """
    Analyze user's taste profile from their ratings.

    Args:
        ratings_dict: Dictionary mapping anime_id -> rating
        metadata_df: DataFrame with anime metadata (must have anime_id, genres columns)
        top_n_genres: Number of top genres to return

    Returns:
        Dictionary with taste statistics:
        - avg_rating: Overall average rating
        - genre_ratings: Average rating per genre
        - top_genres: List of (genre, avg_rating) tuples
        - rating_distribution: Count of ratings by score range
    """
    if ratings_dict is None or not ratings_dict:
        return {
            'avg_rating': 0.0,
            'genre_ratings': {},
            'top_genres': [],
            'rating_distribution': {}
        }

    # Overall average
    avg_rating = np.mean(list(ratings_dict.values()))

    # Genre-based analysis
    genre_ratings = {}
    genre_counts = {}

    for anime_id, rating in ratings_dict.items():
        # Find metadata row
        row = metadata_df[metadata_df['anime_id'] == anime_id]
        if row.empty:
            continue

        # Parse genres
        genres_val = row.iloc[0].get('genres')
        if isinstance(genres_val, str):
            genres = [g.strip() for g in genres_val.split('|') if g.strip()]
        elif hasattr(genres_val, '__iter__') and not isinstance(genres_val, str):
            genres = [str(g).strip() for g in genres_val if g]
        else:
            genres = []

        # Accumulate ratings per genre
        for genre in genres:
            if genre not in genre_ratings:
                genre_ratings[genre] = 0.0
                genre_counts[genre] = 0
            genre_ratings[genre] += rating
            genre_counts[genre] += 1

    # Average ratings per genre
    for genre in genre_ratings:
        genre_ratings[genre] /= genre_counts[genre]

    # Sort by average rating
    top_genres = sorted(genre_ratings.items(), key=lambda x: x[1], reverse=True)[:top_n_genres]

    # Rating distribution
    rating_distribution = {
        '9-10': sum(1 for r in ratings_dict.values() if r >= 9),
        '7-8': sum(1 for r in ratings_dict.values() if 7 <= r < 9),
        '5-6': sum(1 for r in ratings_dict.values() if 5 <= r < 7),
        '1-4': sum(1 for r in ratings_dict.values() if r < 5),
    }

    return {
        'avg_rating': round(avg_rating, 2),
        'genre_ratings': {k: round(v, 2) for k, v in genre_ratings.items()},
        'top_genres': [(g, round(r, 2)) for g, r in top_genres],
        'rating_distribution': rating_distribution
    }


__all__ = [
    'compute_personalized_scores',
    'generate_user_embedding',
    'get_user_taste_profile',
]
