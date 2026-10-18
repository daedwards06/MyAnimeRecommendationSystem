# Project Structure and Tech Stack

## Layout

```
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── sidebar.py, display.py   # Sidebar controls and result rendering
│   ├── pipeline_runner.py       # Runs the scoring pipeline for the current session
│   └── state.py                 # Session-state keys
├── src/
│   ├── app/
│   │   ├── scoring_pipeline.py  # Pure-Python 3-stage pipeline
│   │   ├── artifacts_loader.py  # Model loading + validation
│   │   ├── constants.py         # All scoring weights & thresholds
│   │   ├── recommender.py       # Hybrid CF blending
│   │   ├── stage0_candidates.py # Candidate generation
│   │   ├── stage1_shortlist.py  # Shortlist construction
│   │   └── components/          # Card rendering, explanations, diversity panel
│   ├── models/                  # FunkSVD, kNN, content similarity, user embeddings
│   ├── eval/                    # Metrics (NDCG, MAP, coverage, Gini, graded relevance)
│   ├── features/                # Feature engineering, embeddings, scaling
│   └── data/                    # Data loading, MAL parser, user profiles
├── scripts/
│   ├── refresh_catalog.py       # End-to-end catalog refresh (discover → retrain)
│   ├── fetch_jikan.py           # Fetch metadata from Jikan API
│   ├── discover_new_ids.py      # Find new MAL IDs missing from catalog
│   ├── build_features.py        # Feature engineering orchestrator
│   ├── save_artifacts.py        # Retrain CF models (--split full serves, --split train evaluates)
│   └── run_unified_eval.py      # Offline evaluation of every model on one cohort
├── tests/                       # ~290 tests
├── reports/                     # Evaluation reports, ablation studies
├── models/                      # Trained model artifacts (.joblib, Git LFS)
└── data/                        # Processed parquets + samples tracked; image & Jikan caches gitignored
```

## Tech Stack

| Area | Tools |
|------|-------|
| ML / data | NumPy, pandas, scikit-learn, Optuna |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2; optional, offline build only) |
| App | Streamlit |
| Search | RapidFuzz |
| CI | GitHub Actions, pytest, ruff |
