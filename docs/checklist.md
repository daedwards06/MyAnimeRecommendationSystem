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

### Core (Completed 2025-11-22)
- [x] Plot metric curves (NDCG@K, MAP@K vs K) for Popularity, MF, Hybrid, Content TF-IDF
- [x] Plot coverage & Gini vs K (diversity trade-offs)
- [x] Ablation table (Popularity vs MF vs Hybrid vs Content) with relative lifts
- [x] Integrated hybrid explanation examples (per-source score shares for top 3 recommendations)

### Rigor & Validation
- [x] Temporal split sanity check (earlier vs later) -> stability confirmed
- [x] Cold-start recap integrated (content-only path documented)

### Infrastructure
- [x] CI + lint (GitHub Actions: tests + ruff/black)
- [x] Pre-commit hooks (ruff, black) configured
- [x] Phase 4 doc updates (proposal, running_context, evaluation report)
- [x] Targeted tests (lift edge cases, JSON sanitization)
- [x] Accessibility palette (colorblind-safe plots)

### Stretch (Executed / Deferred)
- [x] Genre exposure quick check (ratio plot + JSON)
- [x] Novelty / popularity bias plot
- [x] Alternate hybrid explanations (diversity-emphasized weights)
- [ ] Implicit ALS prototype (deferred)
- [ ] LightFM deeper tuning & comparison plot (deferred)

### Exit Criteria (Phase 4 Completion) — Achieved 2025-11-22
- Curves & ablations published in `reports/phase4_evaluation.md`
- Balanced hybrid justified vs MF & Popularity (near-parity accuracy + improved coverage)
- Temporal robustness documented (synthetic timestamp sanity hold)
- CI green; explanation examples integrated
- Diversity & novelty artifacts (genre exposure, popularity percentile) included
- Accessibility improvements and alternate weights explanations added

Phase 4 Tag Target: `phase4-complete` (to be created)

## Phase 5 — App Development & Deployment
### Core Implementation
- [ ] Integrate artifact loader (`src/app/artifacts_loader.py`) for metrics & explanations
- [ ] Title search + fuzzy normalization utility
- [ ] Hybrid recommendation function (balanced weights)
- [ ] Alternate weight toggle (diversity-emphasized blend)
- [ ] Seed anime similarity (TF-IDF or embeddings) path
- [ ] User simulation selector (sample personas)
- [ ] Cold-start detection & badge tooltip

### UI & Explainability
- [ ] Recommendation results panel (title, genres, badges)
- [ ] Explanation breakdown (mf/knn/pop shares) top 5 items
- [ ] Diversity / novelty indicators (coverage/genre ratio, popularity percentile)
- [ ] Accessible palette + alt text for embedded charts
- [ ] Inline help / FAQ accordion (metrics & model rationale)

### Performance & Ops
- [ ] Artifact pruning (minimal metadata columns)
- [ ] Caching strategy (`st.cache_data` / `st.cache_resource`)
- [ ] Latency profiling (<250ms inference target)
- [ ] Memory usage audit (<512MB target)
- [ ] Fallback to TF-IDF when embeddings unavailable

### Testing & Quality
- [ ] Unit tests: search normalization, badge logic, explanation formatting
- [ ] Smoke test: app imports & minimal render
- [ ] CI extension: include app tests & lint of `app/` code

### Deployment
- [ ] Minimal `requirements.txt` (pruned for app)
- [ ] Streamlit config (headless, page layout)
- [ ] Deploy to Streamlit Cloud / HF Spaces
- [ ] Capture screenshots & public URL
- [ ] README usage section update

### Stretch / Optional
- [ ] ANN index (FAISS/Annoy) for embedding similarity
- [ ] Favorites/watchlist emulation UI
- [ ] Dark mode toggle & contrast audit
- [ ] Feedback logging (click events) local JSON
- [ ] Session persistence via query params

### Exit Criteria (Phase 5 Completion)
- Deployed app URL accessible
- Hybrid + similarity + cold-start flows functional
- Explanations & diversity/novelty indicators visible
- Alternate weights toggle works without reload
- Tests & CI green for app utilities
- README updated with screenshots & instructions

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

**Last Updated:** 2025-11-22
**This Section Updated:** 2025-11-22 (Phase 5 plan expanded)
