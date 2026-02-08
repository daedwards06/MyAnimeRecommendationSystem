from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def recommend_by_embedding(embeddings: pd.DataFrame, seed_item_id: int, top_k: int = 10) -> list[int]:
    """Cosine similarity over sentence embeddings; embeddings indexed by anime_id."""
    if seed_item_id not in embeddings.index:
        raise ValueError("Seed item not found in embeddings index")
    vec = embeddings.loc[[seed_item_id]].values
    sims = cosine_similarity(vec, embeddings.values)[0]
    order = np.argsort(-sims)
    ids = embeddings.index[order].tolist()
    return [i for i in ids if i != seed_item_id][:top_k]
