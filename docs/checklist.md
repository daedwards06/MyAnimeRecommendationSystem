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
- [x] Integrate artifact loader (`src/app/artifacts_loader.py`) for metrics & explanations
- [x] Searchable title dropdown (replaced free text input; 13K+ sorted titles)
- [x] Hybrid recommendation function (balanced weights)
- [x] Alternate weight toggle (diversity-emphasized blend)
- [x] Seed anime similarity path (genre overlap + hybrid + popularity prior)
- [x] Seed selection indicator (green banner "🎯 Active Seed" + clear button)
- [x] Sample search suggestions (4 popular titles in empty state)
- [~] User simulation selector (sample personas; basic persona dropdown, profiles TBD)
- [x] Cold-start detection (flag present) & badge tooltip (tooltip component implemented)
- [x] Multi-seed recommendation bug fixes (genre parsing, match % normalization)
- [x] Type field added to Jikan fetch script (TV, Movie, OVA, etc.)
- [x] Type filter UI implemented (multi-select with 9 type options)
- [~] Type filter debugging (comprehensive debug logging added, awaiting user test)

### UI & Explainability
- [x] Recommendation results panel (title, genres, badges)
- [x] Visual card redesign (colored borders: blue=trained, orange=cold-start; inline badge pills with icons; spacing)
- [x] Badge tooltips component (`src/app/components/tooltips.py`: cold-start, popularity, novelty)
- [x] Explanation panel component (`src/app/components/explanation_panel.py`: top-5 MF/kNN/Pop breakdown)
- [x] Simplified inline explanations (human-friendly summaries like "📊 Collaborative 96%")
- [x] Diversity summary bar (horizontal colored bar: Popular 🔥, Balanced 📊, Exploratory 🌟 with counts/proportions)
- [x] Confidence star ratings (⭐ 1-5 stars per card based on score magnitude)
- [x] Progress spinner ("🔍 Finding recommendations..." during computation)
- [x] Result count heading ("Showing X recommendations")
- [x] Full synopsis display (removed expander, showing complete text directly on cards)
- [x] Accessible palette + alt text (leveraging Phase 4 palette + per-poster alt text)
- [x] Inline help / FAQ accordion (help panel implemented)
- [x] Sort controls (5 options: Confidence, MAL Score, Year Newest/Oldest, Popularity)
- [x] Genre filter (multi-select from all available genres; fixed array format handling)
- [x] Year range filter (1960-2025 slider)
- [x] Type filter (multi-select: TV, Movie, OVA, Special, ONA, Music, TV Special, CM, PV)
- [x] View mode toggle (List/Grid with native st.container borders)
- [x] Browse by Genre mode (explore catalog without seed, genre-based filtering)
- [x] Grid layout cards (3-column responsive design with compact metadata)
- [x] "More Like This" quick pivot buttons (on both list and grid cards)
- [x] Total anime count badge (13,037 displayed in header)
- [x] Filter info display (shows active filters in results heading)
- [x] Card rendering fixes (removed empty div boxes, proper Streamlit containers)
- [x] Image path restoration (12,183 thumbnails recovered via repair-from-files)
- [~] Type filter debugging (comprehensive debug logging, awaiting verification)

### Performance & Ops
- [x] Artifact pruning (minimal metadata columns + restored display fields including poster_thumb_url)
- [x] Caching strategy (`st.cache_data` / `st.cache_resource` in place)
- [x] Image rendering optimized (switched to native st.image() for reliability)
- [~] Latency profiling (<250ms inference target; instrumentation present, surface display pending)
- [~] Memory usage audit (<512MB target; profiling pending)
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

**Last Updated:** 2025-11-24
**This Section Updated:** 2025-11-24 (Phase 5 progress logged)

#### Phase 5 Progress Notes (2025-11-26)
- Onboarding panel + Quick Steps sidebar complete.
- **Image Quality**: Upgraded to large Jikan images (425x600px) for 12,919 anime; sharper thumbnails.
- **English Title Priority**: Dropdown shows English titles first; original/Japanese as subtitle.
- Searchable title dropdown (13K+ titles) with title-to-ID mapping.
- Seed selection with green banner indicator ("🎯 Active Seed") + clear button.
- Sample search suggestions (4 popular titles) in empty state.
- **Rich Metadata Display**:
  - ⭐ Color-coded MAL scores (green ≥8.0, blue ≥7.0, gray <7.0)
  - 📺 Episode count, 📅 year, ✅ status (Finished/Airing)
  - 🎬 Studios (up to 2) and source material
  - 🎬 **Streaming platforms** (Crunchyroll, Netflix) as clickable badges
- Visual card redesign: colored borders (blue/orange), inline badge pills with icons, proper spacing.
- Badge tooltips component (`tooltips.py`) implemented for cold-start, popularity, novelty.
- Explanation panel component (`explanation_panel.py`) showing top-5 MF/kNN/Pop breakdowns.
- Simplified inline explanations with human-friendly summaries + technical expanders.
- Progress spinner, result count heading, visual diversity bar (Popular/Balanced/Exploratory).
- Confidence star ratings (1-5 ⭐) per card based on score magnitude.
- Image rendering fixed: switched from HTML markdown to native `st.image()` component.
- Synopsis truncation fixed: added expandable "📖 Read full synopsis" section for full text.
- Fixed seed similarity indentation bug causing NameError.
- Remaining near-term: latency/memory profiling display, unit tests, deployment + screenshots.

#### Phase 5 UX Enhancement Session (2025-11-26)
- **Card Rendering Fix**: Resolved empty/partially empty boxes above recommendations in both list and grid views
  - Root cause: Manual HTML `<div>` tags via `st.markdown()` incompatible with native `st.image()` component
  - Solution: Replaced manual divs with `st.container(border=True)` for proper component wrapping
- **Genre Filter Fix**: Fixed "No options to select" issue in genre filter dropdown
  - Root cause: Genres stored as numpy arrays, not pipe-delimited strings
  - Solution: Added array format handling to genre extraction logic (`hasattr(genres_val, '__iter__')`)
- **Browse by Genre Mode**: Implemented standalone catalog browsing without seed requirement
  - Checkbox toggle "🗂️ Browse by Genre" in sidebar
  - Filters metadata directly by selected genres + year range
  - Shows "📚 Browsing X anime" vs "✨ Showing X Recommendations"
  - Works with all existing sort options (MAL Score, Year, Popularity)
  - Limit to Top N for performance
- **Synopsis Display Enhancement**: Fixed truncated synopsis issue and simplified display
  - Removed expander complexity, now shows full synopsis directly via `st.caption()`
  - Added proper pandas NaN handling (`pd.notna()` checks)
  - Confirmed metadata has single `synopsis` column with full text (~700 chars)
- **Data Format Discoveries**:
  - Genres: numpy array format (not pipe-delimited strings)
  - Synopsis: Single `synopsis` column only (no `synopsis_snippet` or `synopsis_full`)
  - Images: 12,923/13,037 anime have `poster_thumb_url` (99.1% coverage)
- **Filter & Sort Enhancements**:
  - Genre filter now shows 40+ unique genres (Action, Adventure, Comedy, etc.)
  - Year range slider functional (1960-2025)
  - Sort by MAL Score, Year, Popularity in both recommendation and browse modes
  - Reset filters button clears all selections
- **Next Actions**: Performance profiling display, unit tests for new features, deployment prep
