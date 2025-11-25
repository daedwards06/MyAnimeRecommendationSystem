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
## Phase 5 Streamlit App Usage

Launch the Phase 5 prototype (new entrypoint) with cached artifacts:

```powershell
streamlit run app/main.py --server.headless true
```

Sidebar controls:
- Persona selector: loads sample preference summary.
- Search Title: fuzzy match (RapidFuzz with substring fallback).
- Hybrid Weights: toggle between balanced and diversity-emphasized blend.
- Top N: adjust recommendation list size (default 10).

Displayed per item:
- Badges: cold-start (placeholder until training presence integrated), popularity band (percentile), novelty ratio.
- Explanation: normalized mf / knn / pop contribution shares.

Diversity & Novelty summary panel shows coverage (unique recommended / N), genre exposure ratio vs catalog, and average novelty.

### Reproducibility
- Deterministic seed: set globally in `src/app/constants.py` (RANDOM_SEED=42).
- Pruned metadata columns reduce memory & load latency (<3s target initial load).
- Weight presets centralized for clarity (`BALANCED_WEIGHTS`, `DIVERSITY_EMPHASIZED_WEIGHTS`).

### Deployment (Streamlit Cloud / Hugging Face Spaces)
1. Push repository with `requirements.txt` and `.streamlit/config.toml`.
2. Select Python 3.11 runtime; enable persistent caching.
3. Set entrypoint command:
	```bash
	streamlit run app/main.py --server.headless true
	```
4. Verify memory usage (<512MB) and median inference latency (<250ms) via logs.
5. Capture screenshots (landing, recommendations, diversity summary, help panel) and add to README.

Environment slimming: comment out `sentence-transformers` & `torch` in `requirements.txt` to disable embeddings path if memory constrained.

### Post-Deployment Checklist
- Public URL recorded in README & `docs/running_context.md`.
- Screenshots committed under `reports/figures/phase5/`.
- Latency metrics excerpt added to README.
- Phase 5 completion tag: `phase5-app-prototype`.

### Diversity Metrics & Genre Normalization
The app computes several diversity/novelty indicators:

- Coverage: `unique_recommended_ids / requested_top_n`.
- Genre Exposure Ratio: `unique_genres_in_recs / unique_genres_in_catalog` using a **normalized genres column**.
- Average Novelty: mean of per-item `novelty_ratio` badge (placeholder heuristic until full interaction-based novelty integrated).
- Popularity Band: derived from percentile rank of a popularity score vector (top 10%, top 25%, mid, long tail).

Robust Genre Normalization:
Metadata can contain genre representations as strings, lists, tuples, sets, NumPy arrays, or nested mixtures. The helper `_coerce_genres` (defined in `src/app/diversity.py` and mirrored defensively in `app/main.py`) flattens nested array-like structures and joins tokens with `|` while filtering out `None` and blanks. This prevents the common Python error: `ValueError: The truth value of an array with more than one element is ambiguous` which arises when directly evaluating NumPy arrays in boolean contexts.

Implementation Notes:
- No boolean checks like `if x` are performed on raw ndarray elements; they are converted to strings first.
- The diversity summary normalizes the entire `metadata['genres']` column before ratio calculations.
- Safe normalization ensures future ingestion of embeddings or enriched metadata will not break the summary panel.

If you extend metadata with nested genre hierarchies (e.g., theme -> subtheme), `_coerce_genres` will flatten them; consider adding hierarchical diversity metrics in a subsequent phase.

### Known Limitations (Phase 5 Prototype)

### Upgrading Design & UX (Planned)
Upcoming enhancements will focus on:

### Image Attribution & Usage
Poster images are sourced via the Jikan API (proxying MyAnimeList). Each enrichment run records:
- `poster_url`: Original remote image URL.
- `poster_thumb_url`: Local resized WebP thumbnail (`data/processed/images/posters/`).
- `image_last_fetched`: UTC timestamp for refresh policy.
- `image_attribution`: Static attribution string (Jikan / MyAnimeList).

Refresh Policy: Images refetched only if older than the configured age threshold (default 30 days) unless `--force-refresh` is passed.

Fallbacks: If a thumbnail is missing or fetch fails, the UI shows a textual placeholder; future iterations will include an inline SVG placeholder for accessibility.

Usage Guidelines: Do not redistribute raw images outside this application context. Respect Jikan rate limits — batch enrichment with throttling (default 0.75s) and avoid aggressive parallel fetches.

Command Examples:
```powershell
# Enrich first 100 metadata items with posters (skip recent ones <30 days old)
python scripts/enrich_images.py --limit 100 --age-threshold-days 30

# Force refresh all poster images for specified IDs
python scripts/enrich_images.py --ids 1 5 8 12 --force-refresh
```

Planned Enhancements:
- Placeholder SVG asset for missing images.
- Alt text refinement using synopsis summarization.
- Optional high-resolution modal on card click (lazy load).
- Responsive layout & improved typography.
- Collapsible advanced metrics panel (hide by default).
- Inline tooltips (hover for explanation components & badges).
- Persistent user session state (store last persona & weights).
- Accessibility audit (keyboard navigation, ARIA labels, contrast).

These UX upgrades will be scoped before tagging the Phase 5 design completion.

```
