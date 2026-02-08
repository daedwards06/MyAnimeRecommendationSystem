from __future__ import annotations

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def flag_cold_start(
    enriched_meta: pd.DataFrame,
    kaggle_anime: pd.DataFrame,
    interactions: pd.DataFrame,
    snapshot_cutoff_date: str | None = None,
    low_interaction_threshold: int = 5,
) -> pd.DataFrame:
    """Mark items as cold-start and provide reasons.

    Rules:
    - is_post_snapshot: True if not present in Kaggle baseline OR (if cutoff provided) aired_from >= cutoff.
    - is_low_interaction: True if total interactions for the item <= threshold.
    - is_cold_start: True if either of the above is True.
    - cold_reason: 'post_snapshot' > 'low_interaction' > 'none'.
    """
    df = enriched_meta[["anime_id", "aired_from"]].copy()
    baseline_ids = set(kaggle_anime["anime_id"].unique()) if not kaggle_anime.empty else set()

    # Interactions per item
    if interactions.empty:
        inter_counts = pd.Series(dtype="int64")
    else:
        inter_counts = interactions.groupby("anime_id").size()
    df["interaction_count"] = df["anime_id"].map(inter_counts).fillna(0).astype(int)

    # In Kaggle baseline
    df["is_in_kaggle"] = df["anime_id"].isin(baseline_ids)

    # Post-snapshot detection
    is_post_snapshot = ~df["is_in_kaggle"]
    if snapshot_cutoff_date:
        try:
            cutoff_dt = pd.to_datetime(snapshot_cutoff_date, utc=False, errors="coerce")
            aired = pd.to_datetime(df["aired_from"], utc=False, errors="coerce")
            is_post_snapshot = is_post_snapshot | (aired >= cutoff_dt)
        except Exception:
            # Fallback silently to Kaggle-based detection if parsing fails
            pass
    df["is_post_snapshot"] = is_post_snapshot.fillna(False)

    # Low interaction
    df["is_low_interaction"] = (df["interaction_count"] <= int(low_interaction_threshold))

    # Final cold start and reason
    df["is_cold_start"] = df["is_post_snapshot"] | df["is_low_interaction"]
    def reason_row(row) -> str:
        if row["is_post_snapshot"]:
            return "post_snapshot"
        if row["is_low_interaction"]:
            return "low_interaction"
        return "none"

    df["cold_reason"] = df.apply(reason_row, axis=1)
    return df[[
        "anime_id",
        "is_post_snapshot",
        "is_low_interaction",
        "is_cold_start",
        "cold_reason",
    ]]


def content_only_score(
    query_item_id: int,
    item_tfidf: pd.DataFrame,
    item_embeddings: pd.DataFrame | None,
    popularity: pd.DataFrame | None,
    w_tfidf: float = 0.6,
    w_emb: float = 0.3,
    w_pop: float = 0.1,
    top_k: int = 20,
) -> pd.DataFrame:
    """
    Weighted similarity: w_tfidf*cosine(TFIDF) + w_emb*cosine(emb) + w_pop*pop_norm.
    Returns top-k similar items (excluding the query).
    """
    id_col = "anime_id"
    tfidf = item_tfidf.set_index(id_col).sort_index()
    if query_item_id not in tfidf.index:
        raise KeyError(f"{query_item_id} not found in TF-IDF matrix")
    q_vec_tfidf = tfidf.loc[[query_item_id]].values
    sims_tfidf = cosine_similarity(q_vec_tfidf, tfidf.values).ravel()
    score = w_tfidf * sims_tfidf
    idx = tfidf.index

    if item_embeddings is not None and len(item_embeddings) > 0:
        emb = item_embeddings.set_index(id_col).sort_index()
        common_idx = idx.intersection(emb.index)
        tfidf = tfidf.loc[common_idx]
        sims_tfidf = cosine_similarity(q_vec_tfidf, tfidf.values).ravel()
        q_vec_emb = emb.loc[[query_item_id]].values
        sims_emb = cosine_similarity(q_vec_emb, emb.loc[common_idx].values).ravel()
        score = w_tfidf * sims_tfidf + w_emb * sims_emb
        idx = common_idx

    if popularity is not None and len(popularity) > 0:
        pop = popularity.set_index(id_col).reindex(idx)["popularity"].fillna(0.0)
        pop_norm = (pop - pop.min()) / (pop.max() - pop.min() + 1e-8)
        score = score + w_pop * pop_norm.values

    result = pd.DataFrame({"anime_id": idx.values, "score": score})
    result = result[result["anime_id"] != query_item_id].sort_values(
        "score", ascending=False
    ).head(top_k)
    return result.reset_index(drop=True)
