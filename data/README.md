# Data Directory

## What you need to run the app

Nothing. The Streamlit app runs entirely from the processed parquets committed under
`data/processed/` and the model artifacts in `models/` (Git LFS). Cloning the repo and
running `streamlit run app/main.py` needs no download.

Raw data is only required to **rebuild features or retrain models**
(`scripts/build_features.py`, `scripts/refresh_catalog.py`).

## Fetching the raw data

```bash
pip install kaggle                              # once
export KAGGLE_USERNAME=... KAGGLE_KEY=...       # or ~/.kaggle/kaggle.json
python scripts/download_data.py                 # downloads, extracts, verifies
python scripts/download_data.py --dry-run       # print the plan, change nothing
```

Get an API token at <https://www.kaggle.com/settings/account> under **API → Create New
Token**. The script verifies row counts and column headers against a manifest and exits
non-zero if either does not match, so a wrong dataset fails loudly instead of producing
silently wrong features.

The dataset is [`CooperUnion/anime-recommendations-database`](https://www.kaggle.com/datasets/CooperUnion/anime-recommendations-database)
(the 2017 MyAnimeList snapshot). Note that `docs/DATA_SOURCES.md` historically named the
2020 `hernan4444` dataset; the pipeline's schema (`anime_id`, `rating.csv` with `-1`
sentinels) is CooperUnion's, and the 2020 dataset's `MAL_ID` / `rating_complete.csv`
schema is **not** a drop-in replacement.

## Layout

| Path | Tracked? | Contents |
|------|----------|----------|
| `raw/rating.csv` | fetched | 7,813,737 user–anime ratings (`user_id,anime_id,rating`; `-1` = watched, unrated) |
| `raw/anime.csv` | fetched | 12,294 Kaggle baseline titles (`anime_id,name,genre,type,episodes,rating,members`) |
| `raw/jikan.tar.gz` | tracked | Compact Jikan API response cache; extract to `raw/jikan/` for an offline metadata refresh |
| `raw/jikan/` | ignored | Loose per-id JSON extracted from the tarball |
| `raw/anime_ids.txt`, `raw/new_anime_ids_*.txt`, `raw/new_since_2019.txt` | tracked | Small id lists driving catalog discovery and Jikan fetches |
| `raw/animelist_*.xml` | ignored | Personal MyAnimeList exports — never commit these |
| `interim/` | ignored | Temporary transformation outputs |
| `processed/` | tracked | Cleaned feature tables, splits, metadata, and evaluation parquets the app reads |
| `user_profiles/*.json` | ignored | Personal watchlist profiles; the example and demo profiles are the exceptions |

`raw/rating.csv` and `raw/anime.csv` were tracked until 2026-09-16 and remain in the
repository's Git history; untracking them stops the repo growing further but does not
shrink an existing clone.

## Licensing and attribution

See [`../docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md) for source URLs, licensing terms,
refresh policy, and the Jikan API etiquette this project follows. Raw Kaggle data is not
redistributed by this repository — fetch it from Kaggle under that dataset's own terms.
