# Feature Documentation (Template)

## Overview
This document describes engineered features used by recommendation models, covering source data, transformations, storage format, and intended usage.

## Feature Groups
| Group | Purpose | Models Consuming | Storage Path |
|-------|---------|------------------|--------------|
| Multi-hot genres/themes | Categorical content similarity | Content-based, hybrid, cold-start | data/processed/features/genres_multi_hot.parquet |
| TF-IDF genre/tag text | Fine-grained token weighting for similarity | Content-based similarity, hybrid re-rank | data/processed/features/tfidf_genres.pkl |
| Synopsis embeddings | Semantic narrative similarity | Embedding similarity recommender, hybrid | data/processed/synopsis_embeddings.parquet |
| Popularity metrics | Prior and ranking bias | Baselines, hybrid blending | Derived from interactions + Jikan |
| Recency indicators | Time-aware adjustments | Hybrid (optional) | Derived columns in metadata parquet |
| Studio/demographics features | Diversity and niche segmentation | Hybrid filtering/explanations | anime_metadata.parquet |

## Multi-hot Genres/Themes
- Source: `anime_metadata.parquet` fields `genres`, `themes`.
- Transformation: Build unified vocabulary; assign column per token; binary indicator.
- Edge Cases: Items with empty lists → all zeros; rare tokens may be dropped (< min frequency threshold).

## TF-IDF Genre/Tag Matrix
- Source: Concatenated genre + theme tokens per anime.
- Vectorizer: scikit-learn `TfidfVectorizer` with token pattern `[A-Za-z0-9_\-]+`.
- Normalization: L2 by default.
- Persistence: Pickled vectorizer + sparse matrix; consider storing matrix in `.npz` for efficiency.
- Edge Cases: Items with no tokens → zero vector; ensure downstream similarity handles zero norms.

## Synopsis Embeddings
- Model: `sentence-transformers` (e.g., `all-MiniLM-L6-v2` initially, upgrade later if needed).
- Preprocessing: Strip HTML, collapse whitespace, truncate extremely long synopses (>1024 chars) if memory constrained.
- Output: Dense float32 matrix shape `(N_items, emb_dim)`.
- Storage: Parquet (per-row list) or `.npy`/`.npz` for faster load. If parquet, store as list/array field.
- Edge Cases: Missing synopsis → use zero vector or mean embedding placeholder.

## Popularity & Recency
- Popularity: Count interactions (ratings) per anime; optionally combine with MAL popularity rank (scaled).
- Recency: Days since `aired_from` (or last interaction timestamp) bucketed (e.g., <90 days, <180 days, etc.).
- Usage: Weight or adjust blended ranking to avoid only older popular titles.

## Hybrid Blend Weights
- Candidate Inputs: CF score, content similarity score (embeddings), popularity prior.
- Strategy: Validate on validation set; Optuna can optimize weights to maximize NDCG@10.
- Storage: `models/hybrid_config.json` containing weights and thresholds.

## Diversity & Coverage Features (Optional)
- Genre entropy per recommendation list (post-generation metric).
- Novelty: Inverse popularity rank percentile.
- Coverage: Ratio of unique genres represented in top-N.

## Explainability Artifacts
| Artifact | Description | Generation | Storage |
|----------|-------------|------------|---------|
| Top contributing genres | Intersect user’s liked genres vs candidate’s genre set | Post-hoc during recommendation | On the fly |
| Similar exemplar titles | k nearest items by embedding among user’s history | Precomputed FAISS/Annoy (optional) | In-memory index |
| Blend component scores | CF vs content vs popularity scalar contributions | Pipeline output | Included in response JSON |

## Quality Checks
| Check | Feature | Method | Threshold |
|-------|---------|--------|-----------|
| Sparsity | Multi-hot matrix | Non-zero ratio | Monitor; remove ultra-sparse tokens |
| Embedding norm | Synopsis embeddings | Validate non-zero norm | >99% non-zero |
| TF-IDF integrity | TF-IDF | Vocabulary size sanity check | Within expected range |
| Drift (monthly) | Popularity metrics | Compare distributions | Alert if large shift |

## Future Extensions
- Sentiment embeddings from reviews.
- Temporal decay weighting applied to CF latent factors.
- User embedding construction (aggregate liked item embeddings).

**Last Updated:** <!-- timestamp placeholder -->
