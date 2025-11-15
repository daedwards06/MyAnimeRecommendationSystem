# MyAnimeRecommendationSystem
Anime Recommender 

## Project structure

```
MyAnimeRecommendationSystem/
├─ app/
│  └─ app.py
├─ data/
│  ├─ raw/ (.gitkeep)
│  ├─ interim/ (.gitkeep)
│  ├─ processed/ (.gitkeep)
│  └─ README.md
├─ docs/
│  └─ index.md
├─ models/ (.gitkeep)
├─ notebooks/
├─ reports/
├─ scripts/
│  └─ download_data.py
├─ src/
│  ├─ __init__.py
│  ├─ data/__init__.py
│  ├─ features/__init__.py
│  ├─ models/__init__.py
│  └─ eval/__init__.py
├─ tests/
│  └─ test_smoke.py
├─ PROJECT_PROPOSAL.md
├─ requirements.txt
└─ README.md
```

## Getting started

Set up a virtual environment, install dependencies, and run the Streamlit app.

```powershell
# From the repository root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# Run the app
streamlit run app/app.py
```

### Windows PowerShell tips

- Use the backtick ` character for line continuations (not caret ^).
- Paths can be forward slashes or escaped backslashes.

Example: run the Jikan enrichment script with checkpoints and logging:

```powershell
python scripts/fetch_jikan.py `
	--ids-file data/raw/anime_ids.txt `
	--throttle 0.70 `
	--checkpoint-interval 300 `
	--log-interval 50 `
	--snapshot-suffix 202511_full
```

See also: `docs/running_context.md` for a live snapshot of project status and key paths.

## Build Phase 2 artifacts

Generate features, signals, and splits (auto-detects latest metadata):

```powershell
python scripts/build_features.py --data-version "2025-11-14-tagfix"
```

Artifacts are written under `data/processed/` (items, TF-IDF + vectorizer, embeddings, user features, indices, feature_stats.json, slices, train/val/test, artifacts_manifest.json).

## Train a quick CF baseline (LightFM)

Train and evaluate a LightFM WARP model on the splits:

```powershell
python scripts/train_lightfm_baseline.py `
	--epochs 5 `
	--loss warp `
	--no-components 64 `
	--k 10 `
	--num-threads 8 `
	--save-model data/processed/models/lightfm_warp_e5_c64.pkl
```

This reports Precision@K and Recall@K on validation and test.

## Proposal

See `PROJECT_PROPOSAL.md` for the full professional plan, roadmap, timeline, and deliverables.
