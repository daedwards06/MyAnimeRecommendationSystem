# Phase 2 — Cleaning & Feature Engineering Implementation

Implementation plan with ready-to-use snippets, module layout, milestones, and a brief Phase 3 preview.

This document operationalizes the roadmap from `PROJECT_PROPOSAL.md` and the current status in `docs/running_context.md`. It specifies exactly what to build, where files live, and how artifacts are saved so we can move smoothly into modeling.

## Phase 2 — Cleaning & Feature Engineering Plan

1) Data cleaning and normalization
- Inputs: data/raw/rating.csv, anime_metadata.parquet (Phase 1 output), anime.csv (Kaggle baseline IDs)
- Steps:
  - Coerce types, drop null essentials, deduplicate (user_id, anime_id).
  - Normalize categorical lists: genres/themes/studios/demographics.
  - Persist cleaned interactions and normalized metadata to data/processed/.
- Outputs:
  - data/processed/interactions.parquet
  - anime_metadata.parquet (normalized with list columns)

2) Item feature engineering
- Genres/Themes:
  - Multi-hot matrix with columns: genre_*, theme_* → data/processed/features/genres_multi_hot.parquet
  - TF-IDF over tag strings (genres + themes) with TfidfVectorizer(max_features=10000, ngram_range=(1,2)) → data/processed/item_features_tfidf.parquet
- Synopsis embeddings:
  - SentenceTransformer("all-MiniLM-L6-v2"), batched encode with torch.no_grad(), cache parquet → data/processed/item_features_embeddings.parquet
- Popularity/Recency:
  - popularity = log(1 + num_ratings) * mean_rating
  - released_year, days_since_release from aired_from/release_date

3) Cold-start handling
- Identify titles unseen in Kaggle baseline or with zero interactions → flag is_cold_start
- Provide content_only_score: weighted cosine(TF-IDF, embeddings) + popularity prior

4) Data splitting
- User-aware 70/15/15 split; optional time-based if timestamp exists
- Persist data/processed/train.parquet, val.parquet, test.parquet

5) Feature documentation
- Update features.md with shapes, dtypes, ranges for all processed tables and matrices

Constants and defaults
- RANDOM_SEED = 42
- Model: all-MiniLM-L6-v2
- TF-IDF: max_features=10000, ngram_range=(1,2)
- Embedding batch_size: 256 (adjust per memory)

Assumptions
- Metadata includes synopsis text and date columns (aired_from or release_date). If not, functions are defensive (fillna, safe parsing).


## Code Snippets (production-ready, modular)

Place these under src/ as noted in file/module layout.

### Cleaning, normalization, and splitting (src/data/cleaning.py)

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Iterable

import numpy as np
import pandas as pd

RANDOM_SEED = 42

@dataclass
class SplitConfig:
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    time_col: Optional[str] = None
    user_col: str = "user_id"
    item_col: str = "anime_id"

def load_ratings(path: Path) -> pd.DataFrame:
    """
    Load Kaggle ratings and coerce to expected types.
    Expected columns: user_id, anime_id, rating, [timestamp?].
    """
    df = pd.read_csv(path)
    if "user_id" in df.columns:
        df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce").astype("Int64")
    if "anime_id" in df.columns:
        df["anime_id"] = pd.to_numeric(df["anime_id"], errors="coerce").astype("Int64")
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["user_id", "anime_id", "rating"])
    df[["user_id", "anime_id"]] = df[["user_id", "anime_id"]].astype(int)
    return df

def load_kaggle_items(path: Path) -> pd.DataFrame:
    """
    Load Kaggle baseline anime.csv to anchor cold-start detection.
    """
    df = pd.read_csv(path)
    if "anime_id" in df.columns:
        df["anime_id"] = pd.to_numeric(df["anime_id"], errors="coerce").astype("Int64")
        df = df.dropna(subset=["anime_id"])
        df["anime_id"] = df["anime_id"].astype(int)
    return df

def clean_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Drop null essentials
    - Deduplicate (user_id, anime_id), keeping last to resolve conflicts
    - Clip ratings to non-negative (adjust upper bound if needed)
    """
    essentials = {"user_id", "anime_id", "rating"}
    if essentials.issubset(df.columns):
        df = df.dropna(subset=list(essentials))
        df = df.drop_duplicates(subset=["user_id", "anime_id"], keep="last")
        df["rating"] = df["rating"].clip(lower=0.0)
    return df

def _split_str_list(x: object, seps: Iterable[str] = (",", "|")) -> list[str]:
    """Split strings by common separators, trimming spaces; [] for null/empty."""
    if not isinstance(x, str) or not x.strip():
        return []
    s = x
    for sep in seps:
        s = s.replace(sep, ",")
    return [t.strip() for t in s.split(",") if t.strip()]

def normalize_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Add *_list columns for genres/themes/studios/demographics when present."""
    out = df.copy()
    if "genres" in out.columns and "genres_list" not in out.columns:
        out["genres_list"] = out["genres"].fillna("").apply(_split_str_list)
    if "themes" in out.columns and "themes_list" not in out.columns:
        out["themes_list"] = out["themes"].fillna("").apply(_split_str_list)
    if "studios" in out.columns and "studios_list" not in out.columns:
        out["studios_list"] = out["studios"].fillna("").apply(_split_str_list)
    if "demographics" in out.columns and "demographics_list" not in out.columns:
        out["demographics_list"] = out["demographics"].fillna("").apply(_split_str_list)
    return out

def user_based_split(df: pd.DataFrame, cfg: SplitConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Deterministic per-user split (70/15/15 default).
    If cfg.time_col exists, sorts per user by time to reduce leakage.
    """
    assert cfg.user_col in df.columns and cfg.item_col in df.columns
    def split_one(group: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        g = group.sort_values(cfg.time_col) if cfg.time_col and cfg.time_col in group.columns else group.sample(frac=1.0, random_state=RANDOM_SEED)
        n = len(g)
        n_test = int(round(n * cfg.test_ratio))
        n_val = int(round(n * cfg.val_ratio))
        test = g.tail(n_test) if n_test > 0 else g.iloc[0:0]
        val = g.iloc[max(0, n - n_test - n_val):max(0, n - n_test)] if n_val > 0 else g.iloc[0:0]
        train = g.iloc[0:max(0, n - n_val - n_test)]
        return train, val, test
    trains, vals, tests = [], [], []
    for _, grp in df.groupby(cfg.user_col, sort=False):
        tr, va, te = split_one(grp)
        trains.append(tr); vals.append(va); tests.append(te)
    return pd.concat(trains, ignore_index=True), pd.concat(vals, ignore_index=True), pd.concat(tests, ignore_index=True)
```

### Multi-hot and TF-IDF (src/features/tags.py)

```python
from __future__ import annotations
from pathlib import Path
from typing import Iterable
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def build_multi_hot(meta: pd.DataFrame, id_col: str = "anime_id", genres_col: str = "genres_list", themes_col: str = "themes_list") -> pd.DataFrame:
    """Create multi-hot columns for genres and themes; columns named genre_* and theme_*."""
    meta = meta[[id_col, genres_col, themes_col]].copy()
    meta[genres_col] = meta[genres_col].apply(lambda x: x if isinstance(x, list) else [])
    meta[themes_col] = meta[themes_col].apply(lambda x: x if isinstance(x, list) else [])
    genres = sorted({g for lst in meta[genres_col] for g in lst})
    themes = sorted({t for lst in meta[themes_col] for t in lst})
    def to_hot(lst: list[str], vocab: list[str]) -> list[int]:
        s = set(lst); return [1 if v in s else 0 for v in vocab]
    genre_hot = meta[genres_col].apply(lambda lst: pd.Series(to_hot(lst, genres), index=[f"genre_{g}" for g in genres]))
    theme_hot = meta[themes_col].apply(lambda lst: pd.Series(to_hot(lst, themes), index=[f"theme_{t}" for t in themes]))
    return pd.concat([meta[[id_col]], genre_hot, theme_hot], axis=1)

def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

def build_tfidf_from_tags(meta: pd.DataFrame, id_col: str = "anime_id", tag_cols: Iterable[str] = ("genres_list", "themes_list"), max_features: int = 10000, ngram_range: tuple[int, int] = (1, 2)) -> pd.DataFrame:
    """
    Join list-like tag columns into a token string and fit TF-IDF.
    Returns DataFrame with [id_col] + tfidf_* columns.
    """
    def as_str(row: pd.Series) -> str:
        tokens: list[str] = []
        for c in tag_cols:
            val = row.get(c, [])
            if isinstance(val, list): tokens.extend(val)
        return " ".join(sorted(set(tokens)))
    tmp = meta[[id_col, *tag_cols]].copy()
    tmp["tags_str"] = tmp.apply(as_str, axis=1)
    vec = TfidfVectorizer(max_features=max_features, ngram_range=ngram_range, token_pattern=r"(?u)\b\w+\b")
    X = vec.fit_transform(tmp["tags_str"].fillna(""))
    feature_names = [f"tfidf_{t}" for t in vec.get_feature_names_out()]
    X_df = pd.DataFrame.sparse.from_spmatrix(X, index=tmp.index, columns=feature_names)
    return pd.concat([tmp[[id_col]].reset_index(drop=True), X_df.reset_index(drop=True)], axis=1)
```

### Embeddings with caching (src/features/embeddings.py)

```python
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

RANDOM_SEED = 42
MODEL_NAME = "all-MiniLM-L6-v2"

def load_existing_embeddings(path: Path) -> pd.DataFrame | None:
    return pd.read_parquet(path) if path.exists() else None

def batched_embeddings(texts: list[str], model: SentenceTransformer, batch_size: int = 256, device: str | None = None) -> np.ndarray:
    """Encode texts using sentence-transformers with no_grad and batching."""
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    outs: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            emb = model.encode(texts[i:i+batch_size], convert_to_numpy=True, device=device, show_progress_bar=False, normalize_embeddings=True)
            outs.append(emb)
    return np.vstack(outs) if outs else np.zeros((0, model.get_sentence_embedding_dimension()), dtype=np.float32)

def generate_or_update_item_embeddings(meta: pd.DataFrame, id_col: str = "anime_id", text_col: str = "synopsis", out_path: Path = Path("data/processed/item_features_embeddings.parquet"), batch_size: int = 256) -> pd.DataFrame:
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
        vecs = batched_embeddings(todo[text_col].tolist(), model=model, batch_size=batch_size)
        new_df = pd.DataFrame(vecs, columns=[f"emb_{i}" for i in range(vecs.shape[1])])
        new_df.insert(0, id_col, todo[id_col].values)
        combined = pd.concat([existing, new_df], ignore_index=True) if existing is not None else new_df
    else:
        combined = existing if existing is not None else pd.DataFrame(columns=[id_col])
    combined = combined.drop_duplicates(subset=[id_col], keep="last")
    combined.to_parquet(out_path, index=False)
    return combined
```

### Popularity and recency (src/features/signals.py)

```python
from __future__ import annotations
import numpy as np
import pandas as pd

def interaction_signals(interactions: pd.DataFrame) -> pd.DataFrame:
    """num_ratings, mean_rating, popularity = log1p(num_ratings) * mean_rating."""
    grp = interactions.groupby("anime_id").agg(num_ratings=("rating", "size"), mean_rating=("rating", "mean")).reset_index()
    grp["popularity"] = np.log1p(grp["num_ratings"]) * grp["mean_rating"].fillna(0.0)
    return grp

def recency_from_metadata(meta: pd.DataFrame, date_cols: list[str] = ["aired_from", "release_date"]) -> pd.DataFrame:
    """released_year, days_since_release derived from first available date col."""
    out = meta[["anime_id"]].copy()
    date = None
    for c in date_cols:
        if c in meta.columns:
            d = pd.to_datetime(meta[c], errors="coerce", utc=True)
            date = d if date is None else date.fillna(d)
    if date is None:
        out["released_year"] = pd.NA; out["days_since_release"] = pd.NA; return out
    now = pd.Timestamp.utcnow()
    out["released_year"] = date.dt.year
    out["days_since_release"] = (now - date).dt.days.astype("Int64")
    return out
```

### Cold-start flag and content-only scoring (src/features/cold_start.py)

```python
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def flag_cold_start(enriched_meta: pd.DataFrame, kaggle_anime: pd.DataFrame, interactions: pd.DataFrame) -> pd.DataFrame:
    """Mark items as cold-start if absent from Kaggle baseline or have zero interactions."""
    enriched = enriched_meta[["anime_id"]].copy()
    baseline_ids = set(kaggle_anime["anime_id"].unique())
    interacted_ids = set(interactions["anime_id"].unique())
    enriched["is_in_kaggle"] = enriched["anime_id"].isin(baseline_ids)
    enriched["has_interactions"] = enriched["anime_id"].isin(interacted_ids)
    enriched["is_cold_start"] = ~enriched["is_in_kaggle"] | ~enriched["has_interactions"]
    return enriched[["anime_id", "is_cold_start"]]

def content_only_score(query_item_id: int, item_tfidf: pd.DataFrame, item_embeddings: pd.DataFrame | None, popularity: pd.DataFrame | None, w_tfidf: float = 0.6, w_emb: float = 0.3, w_pop: float = 0.1, top_k: int = 20) -> pd.DataFrame:
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
    result = result[result["anime_id"] != query_item_id].sort_values("score", ascending=False).head(top_k)
    return result.reset_index(drop=True)
```

### Persistence helpers (optional) (src/data/persist.py)

```python
from __future__ import annotations
from pathlib import Path
import pandas as pd

def to_parquet(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=index)
```

### Minimal tests (tests/test_data_cleaning.py, tests/test_splitting.py)

```python
# tests/test_data_cleaning.py
import pandas as pd
from src.data.cleaning import clean_interactions

def test_clean_interactions_dedup():
    df = pd.DataFrame({"user_id":[1,1], "anime_id":[10,10], "rating":[7.0, 8.0]})
    out = clean_interactions(df)
    assert len(out) == 1
    assert out.iloc[0]["rating"] == 8.0
```

```python
# tests/test_splitting.py
import pandas as pd
from src.data.cleaning import user_based_split, SplitConfig

def test_user_split_ratios():
    df = pd.DataFrame({"user_id":[1]*10 + [2]*10, "anime_id":list(range(10))*2, "rating":[5.0]*20})
    tr, va, te = user_based_split(df, SplitConfig(val_ratio=0.15, test_ratio=0.15))
    assert len(tr) + len(va) + len(te) == len(df)
    assert len(va) > 0 and len(te) > 0
```

Contract and edge cases
- Inputs:
  - Metadata: anime_id, synopsis (optional), genres_list/themes_list
  - Interactions: user_id, anime_id, rating, optional timestamp
- Outputs:
  - Parquet tables/matrices as specified
- Error modes:
  - Missing columns → safe defaults (empty strings/lists), raise clear KeyError in scorers for missing ids
- Edge cases:
  - No synopsis → zero-length text handled as ""
  - No dates → recency fields NA
  - Empty genres/themes → multi-hot rows of zeros
  - Sparse users/items with <3 interactions → splits may produce small val/test per user; ratios applied deterministically


## File / Module Layout

- cleaning.py
  - Loading/cleaning/splitting + list normalization
- src/data/persist.py
  - Parquet utilities
- src/features/tags.py
  - Multi-hot and TF-IDF builders
- src/features/embeddings.py
  - Batched embeddings with caching
- src/features/signals.py
  - Popularity/recency features
- src/features/cold_start.py
  - Cold-start flagging + content-only scoring
- scripts/build_features.py (optional orchestrator)
  - Reads raw + processed metadata → runs all steps → writes outputs
- notebooks/02_feature_engineering.ipynb (optional QA)
  - Visual checks for distributions and matrix sparsity

Paths to persist
- data/processed/users.parquet
- data/processed/items.parquet
- data/processed/interactions.parquet
- data/processed/features/genres_multi_hot.parquet
- data/processed/item_features_tfidf.parquet
- data/processed/item_features_embeddings.parquet
- anime_metadata.parquet
- data/processed/train.parquet, val.parquet, test.parquet

Dependency note
- Ensure requirements.txt contains:
  - sentence-transformers, scikit-learn, pyarrow, pandas, numpy, torch
- In this repo, add pyarrow and torch if missing.


## Milestone Checklist (Phase 2 completion)

- Cleaning
  - Interactions cleaned, deduped, persisted to data/processed/interactions.parquet
  - Metadata normalized with genres_list/themes_list (plus studios/demographics if present)
- Features
  - genres_multi_hot.parquet created with genre_* and theme_* columns
  - item_features_tfidf.parquet created with tfidf_* columns
  - item_features_embeddings.parquet created (cached, batched)
  - Popularity and recency features computed
  - items.parquet assembled with is_cold_start, popularity, recency
- Splits
  - train/val/test parquet files saved (user-aware; optional time-based)
- Docs
  - features.md updated with shapes, dtypes, value ranges for each artifact
- Tests
  - tests/test_data_cleaning.py and tests/test_splitting.py pass locally
- Quality gates
  - PASS: build/imports; tests green; deterministic outputs with RANDOM_SEED=42


## Phase 3 Preview

- Collaborative filtering
  - Train Surprise SVD/KNNBasic, LightFM, or implicit ALS on train; tune on val; report RMSE/NDCG@K on test
  - Use interactions.parquet and standard user/item id maps
- Content-only recommender
  - Compute user profile from consumed items (average embeddings/TF-IDF) or seed item → rank via content_only_score
  - Default for is_cold_start items
- Hybrid
  - Combine CF score with content similarity and popularity: score = w_cf*CF + w_emb*sim_emb + w_tfidf*sim_tfidf + w_pop*pop
  - Optimize weights with Optuna on val MAP@K/NDCG@K
  - Explainability: show top contributing genres/themes and nearest neighbors in embedding space


