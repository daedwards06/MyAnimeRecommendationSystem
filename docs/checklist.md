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

## Phase 3 — Model Development (Closed 2025-11-21)
- [x] Popularity baseline recommender
- [x] Genre similarity baseline (cosine TF-IDF/multi-hot)
- [x] Item kNN (sklearn profile-cosine; replaced Surprise KNNBasic)
- [x] Matrix factorization (FunkSVD via NumPy SGD; replaced Surprise SVD)
- [ ] Implicit ALS model (`implicit` library)  
- [x] LightFM WARP baseline trainer script (`scripts/train_lightfm_baseline.py`)
- [x] Content embedding similarity (synopsis embeddings)
- [x] Hybrid blending logic (weighted / rank fusion)
- [x] Hyperparameter tuning (Optuna studies: MF params + hybrid weights with diversity/coverage objective)
- [x] Model serialization to `models/` (versioned artifacts)
- [x] Experiment tracking (CSV/JSON or MLflow)

Final status (2025-11-21):
- Shared split/sampler utility (`src/eval/splits.py`) in use across all evaluators.
- Diversity & coverage metrics (item coverage, Gini) integrated (`src/eval/metrics_extra.py`).
- Hybrid tuning completed: initial popularity-heavy blend replaced by diversity-aware Optuna run with coverage reward & popularity cap; balanced weights frozen in `src/models/constants.py` as mf=0.93078, knn=0.06625, pop=0.00297.
- MF (FunkSVD) remains strongest single model on NDCG; balanced hybrid nearly matches MF while improving coverage vs popularity baseline.
- Artifact versioning script (`scripts/save_artifacts.py`) updated to use timezone-aware UTC timestamps.
- Report (`reports/phase3_summary.md`) now shows final unified slice metrics (users=1000) including coverage & Gini.
- All Phase 3 core objectives achieved; remaining experimental models (Implicit ALS) deferred to optional backlog.

Phase 3 next actions (rolled into Phase 4):
- Comparative plots (NDCG/MAP vs K, coverage, diversity trends).
- Ablation table (MF vs Hybrid vs Popularity vs Content).
- Temporal/recency split sanity check.
- Optional: introduce ALS or LightFM only if it adds portfolio narrative (defer if marginal).

## Phase 4 — Evaluation & Analysis (Kickoff 2025-11-22)
Goal: Turn raw metric tables into persuasive evaluation artifacts (plots, ablations, explanations) that set up Phase 5 app narrative.

### Core Kickoff (High ROI)
- [ ] Plot metric curves (NDCG@K, MAP@K vs K) for Popularity, MF, Hybrid, Content TF-IDF
- [ ] Plot coverage & Gini vs K (diversity trade-offs)
- [ ] Ablation table (Popularity vs MF vs Hybrid vs Content) with relative lifts
- [ ] Integrated hybrid explanation examples (per-source score shares for top 3 recommendations)

### Rigor & Validation
- [ ] Temporal split sanity check (train on earlier, validate on later) -> confirm stability
- [ ] Cold-start recap (already implemented) summarize in Phase 4 report section

### Infrastructure
- [ ] CI + lint (GitHub Actions: tests + ruff/black)
- [ ] Pre-commit hooks (ruff, black) configured
- [ ] Phase 4 doc updates (proposal, running_context, summary report Phase 4 section)

### Stretch (Optional, Defer if Time-Constrained)
- [ ] Fairness / genre exposure quick check
- [ ] Implicit ALS prototype (only if adds clear narrative boost)
- [ ] LightFM deeper tuning & comparison plot
- [ ] Novelty / popularity bias plot

### Exit Criteria (Phase 4 Completion)
- Curves & ablations published in `reports/phase4_evaluation.md`
- Balanced hybrid justified vs MF & Popularity with lift metrics
- Temporal robustness confirmed or documented
- CI green (tests + lint) and explanation examples integrated

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

**Last Updated:** 2025-11-21
**This Section Updated:** 2025-11-21
