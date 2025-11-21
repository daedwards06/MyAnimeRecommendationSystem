from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List
from sklearn.metrics.pairwise import cosine_similarity


def recommend_by_tfidf(
    item_features: pd.DataFrame, seed_item_id: int, top_k: int = 10, exclude_seed: bool = True
) -> List[int]:
    """Recommend items by cosine similarity on TF-IDF (or multi-hot) features.

    item_features: DataFrame indexed by anime_id with feature columns.
    """
    if seed_item_id not in item_features.index:
        raise ValueError("Seed item not found in feature index")
    seed = item_features.loc[[seed_item_id]].values
    sims = cosine_similarity(seed, item_features.values)[0]
    order = np.argsort(-sims)
    ids = item_features.index[order].tolist()
    if exclude_seed:
        ids = [i for i in ids if i != seed_item_id]
    return ids[:top_k]
