from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

RANDOM_SEED = 42
MODEL_NAME = "all-MiniLM-L6-v2"


def load_existing_embeddings(path: Path) -> pd.DataFrame | None:
    return pd.read_parquet(path) if path.exists() else None


def batched_embeddings(
    texts: list[str],
    model: SentenceTransformer,
    batch_size: int = 256,
    device: str | None = None,
) -> np.ndarray:
    """Encode texts using sentence-transformers with no_grad and batching."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    outs: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            emb = model.encode(
                texts[i : i + batch_size],
                convert_to_numpy=True,
                device=device,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            outs.append(emb)
    return (
        np.vstack(outs)
        if outs
        else np.zeros((0, model.get_sentence_embedding_dimension()), dtype=np.float32)
    )


def generate_or_update_item_embeddings(
    meta: pd.DataFrame,
    id_col: str = "anime_id",
    text_col: str = "synopsis",
    out_path: Path = Path("data/processed/item_features_embeddings.parquet"),
    batch_size: int = 256,
) -> pd.DataFrame:
    """
    Generate sentence embeddings for synopsis; cache and only compute missing ids.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing_embeddings(out_path)
    have_ids = set(existing[id_col].tolist()) if existing is not None else set()

    todo = meta[~meta[id_col].isin(have_ids)][[id_col, text_col]].copy()
    todo[text_col] = todo[text_col].fillna("").astype(str)
    if len(todo) > 0:
        model = SentenceTransformer(MODEL_NAME)
        vecs = batched_embeddings(
            todo[text_col].tolist(), model=model, batch_size=batch_size
        )
        new_df = pd.DataFrame(vecs, columns=[f"emb_{i}" for i in range(vecs.shape[1])])
        new_df.insert(0, id_col, todo[id_col].values)
        combined = (
            pd.concat([existing, new_df], ignore_index=True)
            if existing is not None
            else new_df
        )
    else:
        combined = existing if existing is not None else pd.DataFrame(columns=[id_col])
    combined = combined.drop_duplicates(subset=[id_col], keep="last")
    combined.to_parquet(out_path, index=False)
    return combined
