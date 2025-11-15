# Project Execution Checklist

> Living checklist derived from `PROJECT_PROPOSAL.md`. Mark items as you progress. Suggested notation: `[x]` done, `[~]` in progress, `[!]` blocked.

## Phase 1 — Data Discovery & Acquisition
- [x] Source datasets (Kaggle/MAL export, metadata API)
- [x] Verify licensing & attribution (update `data/README.md`)
- [x] Define canonical data schema (anime_id, user_id, rating, genres, synopsis, timestamps?)
- [x] Implement ingestion script (`scripts/download_data.py`)
- [x] Create data catalog (`docs/data_catalog.md`)
- [x] Data quality / EDA notebook (missingness, duplicates, sparsity, rating dist.)
 - [x] Jikan metadata fetch script (`scripts/fetch_jikan.py`)
 - [x] Jikan raw JSON snapshot & versioning policy (`data/raw/jikan/`, monthly snapshots)

## Phase 2 — Data Cleaning & Feature Engineering
- [x] Cleaning pipeline (`src/data/cleaning.py`)
- [x] Genre/tag parsing & normalization
- [x] Multi-hot encoding (genres/tags)
- [x] TF-IDF vectors (tags/keywords)
- [x] Synopsis embeddings (`sentence-transformers`)
- [x] Popularity & recency features
- [x] Train/val/test split (user-aware + optional time split)
- [x] Feature documentation (`docs/features.md`)
 - [x] Normalize Jikan metadata → parquet (`data/processed/anime_metadata.parquet`)
 - [x] Identify and flag new titles (post-snapshot) for content-only recommendations
 - [x] Metadata feature extraction (genres/themes/demographics/studios)

## Phase 3 — Model Development
- [ ] Popularity baseline recommender
- [ ] Genre similarity baseline (cosine TF-IDF/multi-hot)
- [ ] User-Item kNN (Surprise KNNBasic)
- [ ] Matrix factorization SVD (Surprise)
- [ ] Implicit ALS model (`implicit` library)
- [x] LightFM WARP baseline trainer script (`scripts/train_lightfm_baseline.py`)
- [ ] Content embedding similarity (synopsis embeddings)
- [ ] Hybrid blending logic (weighted / rank fusion)
- [ ] Hyperparameter tuning (Optuna study optimizing NDCG/MAP@K)
- [ ] Model serialization to `models/` (versioned artifacts)
- [ ] Experiment tracking (CSV/JSON or MLflow)

## Phase 4 — Evaluation & Optimization
- [ ] Metrics module (`src/eval/metrics.py`: RMSE, MAE, Precision@K, Recall@K, MAP, NDCG)
- [ ] Evaluation script/notebook (compare all models)
- [ ] Ablation studies (CF vs content vs hybrid)
- [ ] Cold-start analysis (new users/items)
- [ ] Coverage & diversity metrics
- [ ] Reporting visuals saved to `reports/` (curves, bars, heatmaps)

## Phase 5 — App Development & Deployment
- [ ] Data/model loading utilities (caching artifacts)
- [ ] Recommendation pipeline (top-N + explanations)
- [ ] Streamlit UI layout (search, filters, results pane)
- [ ] Filter controls (genre/year/maturity)
- [ ] Explanation component (similar items, feature contributions, blend weights)
- [ ] Caching/performance optimization (`st.cache_*` or manual)
- [ ] Deployment config (minimal requirements, optional Dockerfile)
- [ ] Deploy app (capture URL, screenshots)
 - [ ] UI badges for cold-start/content-only recommendations

## Phase 6 — Documentation & Portfolio Presentation
- [ ] Enhanced `README.md` (diagram, screenshots, live demo link)
- [ ] Expand `docs/` pages (data catalog, modeling decisions, evaluation, setup)
- [ ] Unit tests (data transforms, metrics, recommenders)
- [ ] Coverage reporting (badge optional)
- [ ] Lint & format hooks (pre-commit: ruff, black)
- [ ] CI workflow (GitHub Actions: tests + lint)

## Cross-Cutting Tasks
- [ ] Central config (YAML/py for paths & params)
- [ ] Logging setup (structured logging)
- [ ] Reproducibility seeds (document determinism caveats)
- [ ] Dependency refinement (core vs extras requirements)
- [ ] Makefile / task runner (setup, test, train, run-app)
 - [ ] Document Jikan rate limiting & caching strategy

## Optional Enhancements
- [ ] ANN index (FAISS/Annoy) for embedding similarity
- [ ] Network visualization (similarity graph)
- [ ] Docker image & local build instructions
- [ ] Blog post draft (Medium)
- [ ] Video demo (5–8 min walkthrough)
- [ ] Real-time updater job (scheduled refresh)
- [ ] CI/CD deploy pipeline (auto deploy on main)

## Risks & Mitigation Actions
- [ ] Cold-start fallback logic (content/popularity)
- [ ] Performance profiling & caching strategy
- [ ] Explainability UI (feature/model contributions displayed)
- [ ] License compliance (LICENSE/ATTRIBUTION file)
 - [ ] Jikan downtime fallback (use last saved snapshot; indicate staleness)

---
**Usage Tips**
1. Tackle Phase 1–2 sequentially; avoid premature modeling before stable schema/features.
2. Keep artifacts lightweight for Streamlit: prune unused features before deployment.
3. Update this checklist weekly; remove or defer optional items if timeline tight.
4. Record metric improvements with date stamps in `reports/` for portfolio narrative.

**Last Updated:** 2025-11-14
**This Section Updated:** 2025-11-14
