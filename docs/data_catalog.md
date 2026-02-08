# Data Catalog

> Last updated: 2026-02-08

## Overview
This catalog documents all data assets used in the anime recommendation system, their schemas, provenance, and transformation lineage.

## Raw Sources
| Asset | Path | Source | Description | Format | Update Frequency |
|-------|------|--------|-------------|--------|------------------|
| Ratings snapshot | data/raw/ratings.csv | Kaggle (Anime Recommendation Database 2020) | Explicit user ratings | CSV | Static |
| Users snapshot | data/raw/users.csv | Kaggle dataset | User info (if provided) | CSV | Static |
| Anime metadata snapshot | data/raw/anime.csv | Kaggle dataset | Basic item metadata | CSV | Static |
| Jikan raw JSON | data/raw/jikan/*.json | Jikan API | Enriched metadata per anime_id | JSON | Monthly (optional) |

## Processed Artifacts
| Artifact | Path | Derived From | Purpose | Format |
|----------|------|-------------|---------|--------|
| Clean interactions (train/val/test) | data/processed/interactions_*.parquet | ratings.csv | Modeling splits | Parquet |
| Normalized metadata | data/processed/anime_metadata.parquet | Kaggle + Jikan | Unified item features | Parquet |
| Synopsis embeddings | data/processed/synopsis_embeddings.parquet | anime_metadata.parquet | Content similarity | Parquet/NPY |
| Genre/theme multi-hot | data/processed/features/genres_multi_hot.parquet | anime_metadata.parquet | Content features | Parquet |
| TF-IDF matrix (tags/genres) | data/processed/features/tfidf_genres.pkl | anime_metadata.parquet | Vector space sims | Pickle |

## Canonical Schemas

### Interactions
| Field | Type | Description |
|-------|------|-------------|
| user_id | int | Unique user identifier |
| anime_id | int | Unique anime identifier |
| rating | float/int | Explicit rating value |
| timestamp | datetime (optional) | Interaction time for temporal splits |

### Anime Metadata (Unified)
| Field | Type | Source(s) | Notes |
|-------|------|----------|-------|
| anime_id | int | Kaggle/Jikan | Primary key |
| title_primary | string | Jikan/Kaggle | Display title |
| synopsis | string | Jikan/Kaggle | Text description |
| genres | list[str] | Jikan/Kaggle | Categorical features |
| themes | list[str] | Jikan | Additional semantic categories |
| demographics | list[str] | Jikan | Audience category |
| studios | list[str] | Jikan | Production studios |
| producers | list[str] | Jikan | Production companies |
| source_material | string | Jikan | (e.g., Manga, Original) |
| episodes | int | Jikan/Kaggle | Episode count |
| status | string | Jikan | Airing/Finished |
| aired_from | datetime | Jikan | Start date |
| aired_to | datetime | Jikan | End date |
| mal_score | float | Jikan | Community score |
| mal_rank | int | Jikan | Ranking position |
| mal_popularity | int | Jikan | Popularity index |
| members_count | int | Jikan | Member count |
| retrieved_at | datetime | Jikan | Metadata fetch timestamp |

#### Current Snapshot Metrics (202511_full)
- File: `data/processed/anime_metadata.parquet` and `data/processed/anime_metadata_202511_full.parquet`
- Rows: 12,297
- Columns: 18
- Dtypes:
	- anime_id: int64
	- title_primary: object
	- synopsis: object
	- genres: object (list[str] serialized)
	- themes: object (list[str] serialized)
	- demographics: object (list[str] serialized)
	- studios: object (list[str] serialized)
	- producers: object (list[str] serialized)
	- source_material: object
	- episodes: float64
	- status: object
	- aired_from: object (ISO string)
	- aired_to: object (ISO string)
	- mal_score: float64
	- mal_rank: float64
	- mal_popularity: float64
	- members_count: float64
	- retrieved_at: object (ISO UTC string)

- Null counts:
	- title_primary: 114
	- synopsis: 400
	- source_material: 114
	- episodes: 142
	- status: 114
	- aired_from: 135
	- aired_to: 6,088
	- mal_score: 1,301
	- mal_rank: 1,925
	- mal_popularity: 114
	- members_count: 114
	- anime_id, genres, themes, demographics, studios, producers, retrieved_at: 0

### Feature Matrices
| Name | Shape | Key | Description |
|------|-------|-----|-------------|
| genres_multi_hot | (N_items, N_genres) | anime_id | Binary genre indicators |
| tfidf_genres | (N_items, vocab_size) | anime_id | TF-IDF weights for genre/tag tokens |
| synopsis_embeddings | (N_items, emb_dim) | anime_id | Sentence-transformer embeddings |

## Transformation Lineage
1. Raw Kaggle CSVs ingested into `data/raw/`.
2. Cleaning pipeline normalizes interactions → `data/processed/interactions_*.parquet`.
3. Jikan enrichment fetched via `scripts/fetch_jikan.py` → `data/raw/jikan/*.json` → merged into `anime_metadata.parquet`.
4. Feature engineering script builds multi-hot, TF-IDF, and embeddings → saved under `data/processed/features/`.

## Quality & Validation Checks
| Check | Asset | Method | Threshold/Rule |
|-------|-------|--------|----------------|
| Missingness | interactions | Count nulls | <0.1% critical fields |
| Duplicates | interactions | user_id+anime_id grouping | None allowed |
| Rating range | interactions | Min/max verification | Within expected scale |
| Genre integrity | metadata | Validate genres list type | Non-empty for majority (>70%) |
| Embedding coverage | synopsis_embeddings | Count rows vs items | >=95% items |

## Update Policy Notes
- Ratings: Static snapshot for reproducibility.
- Jikan: Refresh monthly; version `anime_metadata_YYYYMM.parquet`.
- Features: Recompute only when metadata changes significantly.

## Open Questions (Fill as project evolves)
- Are there temporal signals strong enough to warrant time-decay in scoring?
- Should we incorporate user watch status beyond ratings?
- Will we add review sentiment as a feature layer?

**Last Updated:** 2025-11-10
