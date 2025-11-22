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

## Phase 4 Evaluation Report

Core evaluation artifacts (curves, ablation, explanations, temporal robustness, diversity/novelty) are consolidated in `reports/phase4_evaluation.md`. Run the Phase 4 scripts to regenerate:

```powershell
python scripts/plot_phase4_metrics.py --metrics-path data/processed/phase4/metrics_by_k.parquet
python scripts/generate_phase4_ablation.py
python scripts/explain_hybrid_examples.py --k 10 --sample-users 500 --max-users 3
python scripts/evaluate_temporal_split.py --interactions data/processed/interactions.parquet --train-frac 0.7
```

Additional artifacts (run after generating sample recommendations):

```powershell
python scripts/generate_recommendations_sample.py --k 10 --sample-users 500
python scripts/genre_exposure_scan.py --recommendations data/processed/recommendations_sample.parquet --items data/processed/anime_metadata_normalized.parquet --model hybrid
python scripts/novelty_bias_plot.py --recommendations data/processed/recommendations_sample.parquet --popularity data/processed/popularity.parquet
python scripts/explain_hybrid_examples.py --k 10 --sample-users 500 --max-users 3 --out-suffix alt --w-mf 0.7 --w-knn 0.2 --w-pop 0.1
```

Artifacts overview:
- Metric & diversity plots: `reports/figures/phase4/ndcg_vs_k.png`, `map_vs_k.png`, `coverage_vs_k.png`, `gini_vs_k.png`
- Genre exposure: `reports/figures/phase4/genre_exposure_ratio.png` + JSON `reports/artifacts/genre_exposure.json`
- Novelty/popularity bias: `reports/figures/phase4/novelty_bias.png` + JSON `reports/artifacts/novelty_bias.json`
- Hybrid explanations (default + alt weights): `experiments/metrics/hybrid_explanations.json`, `experiments/metrics/hybrid_explanations_alt.json`
- Temporal split comparison: `reports/artifacts/temporal_split_comparison.json`
- Ablation summary: `reports/phase4_ablation.md` + CSV `reports/phase4_ablation.csv`

Phase 4 tag (to be created): `phase4-complete`.

### Looking Ahead (Phase 5 Preview)
Phase 5 will introduce the Streamlit app with:
- Title search & seed similarity
- Hybrid recommendations (alternate weights toggle)
- Explanation panel showing mf/knn/pop contribution shares
- Cold-start badges & novelty/diversity indicators
- Accessible palette + inline metric help

Refer to the expanded Phase 5 plan in `PROJECT_PROPOSAL.md` and structured tasks in `docs/checklist.md`.

Enable pre-commit hooks after dependency install:

```powershell
pre-commit install
```
