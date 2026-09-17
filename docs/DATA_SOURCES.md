# Data Sources & Attribution

This document records all external data and APIs used in the project for transparency, licensing, and reproducibility.

## 0. Fetching the Raw Data
The raw Kaggle CSVs are **not tracked in this repository** (size and redistribution). The app
runs from the committed parquets in `data/processed/`; raw data is only needed to rebuild
features or retrain models. Fetch it with `python scripts/download_data.py` - see
[`data/README.md`](../data/README.md) for credentials, layout, and which files are tracked
versus fetched.

## 1. Core Interaction Dataset
- **Name:** (Kaggle) MyAnimeList Ratings Dataset (2017 snapshot)
- **URL:** https://www.kaggle.com/datasets/CooperUnion/anime-recommendations-database
- **Note:** earlier revisions of this document named `hernan4444/anime-recommendation-database-2020`.
  The files the pipeline actually reads are CooperUnion's (`anime_id` schema; `rating.csv` with
  `-1` sentinels for watched-but-unrated). The 2020 dataset uses `MAL_ID` and
  `rating_complete.csv`, and is not a drop-in replacement.
- **Contents:** User–anime explicit ratings (user_id, anime_id, rating, timestamp if available).
- **License / Terms:** Refer to Kaggle dataset page; ensure compliance with uploader licensing.
- **Usage:** Primary collaborative filtering training matrix. Provides historical interaction scale.
- **Limitations:** Snapshot is static and does not include post-2020 titles or recent popularity shifts.

## 2. Metadata / Enrichment (Jikan API)
- **API:** Jikan (Unofficial MyAnimeList API)
- **Base URL:** https://api.jikan.moe/v4/
- **Endpoints Used:** `/anime/{id}/full` (plus any needed for seasonal or popular listings).
- **Data Fields:** Titles, synopsis, genres, themes, demographics, studios, producers, source, episodes, status, airing dates, MAL score, rank, popularity, members.
- **Usage:** Content-based features (genres/themes embeddings), synopsis text embeddings, popularity signal, cold-start handling for new titles absent in ratings dataset.
- **Caching Strategy:** Raw JSON snapshots stored under `data/raw/jikan/` (git-ignored; the
  cache is committed in compact form as `data/raw/jikan.tar.gz`) with retrieval timestamp. Monthly refresh suggested; old snapshots retained for reproducibility.
- **Rate Limiting & Etiquette:** Throttle requests (~2–3 req/sec, adjust if 429 responses). Implement exponential backoff and reuse cached data where available.
- **Limitations:** Unofficial service; occasional downtime or structural changes. Popularity/score values drift over time—version with timestamps.

## 3. Derived Artifacts
- **Processed Interaction Splits:** `data/processed/interactions_train.parquet`, `interactions_val.parquet`, `interactions_test.parquet` (user-aware or time-based split).
- **Metadata Normalization:** `data/processed/anime_metadata.parquet` (canonical schema).
- **Embeddings:** `data/processed/synopsis_embeddings.parquet` (or separate binary matrix).
- **Feature Matrices:** Genre/theme multi-hot, TF-IDF vectors saved under `data/processed/features/`.

## 4. Attribution & Compliance
Add acknowledgements in `README.md` and application footer:
> Data sourced from Kaggle (MyAnimeList snapshot) and enriched via the Jikan API. Licensing and usage governed by original dataset and MyAnimeList terms.

Maintain an `ATTRIBUTION` section if further sources (e.g., seasonal lists, external reviews) are added.

## 5. Update Policy
| Artifact | Update Frequency | Method | Notes |
|----------|------------------|--------|-------|
| Ratings snapshot | Static | Manual replacement | Keep original for reproducibility |
| Jikan metadata | Monthly (optional) | Refresh script | Versioned: `anime_metadata_YYYYMM.parquet` |
| Embeddings | After metadata refresh | Regenerate embeddings for new/changed items |
| Feature matrices | After content changes | Recompute and prune unused features |

## 6. Reproducibility Notes
- Store script versions (commit hash) used to create each artifact.
- Pin dependency versions in `requirements.txt`.
- Record random seeds for splits and model training in experiment logs.

## 7. Potential Future Sources (Optional)
- User reviews (if permissible) for sentiment or topic modeling.
- Seasonal anime lists for highlighting new releases.
- External popularity indices for cross-checking (e.g., AniList, ANN).

---
**Last Updated:** 2026-09-16
