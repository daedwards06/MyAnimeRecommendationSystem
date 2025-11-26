# Anime Recommendation System — Professional Project Proposal

## 1. Executive Summary

Build an end-to-end, production-lean anime recommendation system that demonstrates practical data science, model engineering, and full‑stack delivery. The audience includes hiring managers, applied data scientists, and ML engineers.

What this project showcases:
- Technical breadth: data acquisition, feature engineering, recommender algorithms (collaborative, content‑based, hybrid), evaluation, and deployment.
- Data storytelling: clear EDA, interpretable recommendation logic, and performance narratives supported by metrics and visuals.
- Reproducibility and polish: structured repo, tests, pinned dependencies, and a live Streamlit app.

Technologies and final deliverables:
- Core: Python (Pandas, NumPy, scikit‑learn), Streamlit
- Recommenders: Surprise/LightFM/implicit; sentence‑transformers for NLP content features
- Tooling: Optuna for tuning, PyTest for tests, pre‑commit/ruff or flake8 for linting, MkDocs/Markdown for docs
- Deliverables: Organized GitHub repo, Jupyter notebooks, modular src code, Streamlit app, evaluation report, and optional CI/CD

## 2. Project Roadmap

### Phase 1 — Data Discovery & Acquisition
- Objectives
  - Identify reliable anime datasets with user interactions (ratings, watchlists) plus metadata (genres, studios, synopsis, tags).
  - Establish data governance: licensing, attribution, versioning, and storage.
- Core tasks
  - Source data from public datasets (e.g., MyAnimeList/Kaggle exports) and metadata APIs if allowed by TOS.
  - Define schemas, keys, and ID mappings (anime_id, user_id).
  - Create data catalog (dataset summary, field descriptions, provenance).
  - Implement Jikan metadata fetch script with caching, throttling, retries, and checkpointing.
  - Establish metadata snapshot versioning policy (e.g., `anime_metadata_<YYYYMM_or_tag>.parquet`) and refresh cadence.
- Deliverables
  - Raw data snapshot in `data/raw/` with README on licensing and fields.
  - Data catalog markdown (`docs/data_catalog.md`).
  - `DATA_SOURCES.md` documenting attribution, terms of use, update policy, and enrichment approach.
- Recommended tools/libraries
  - Requests/httpx (if API used), Pandas, PyYAML for data catalog.

### Phase 2 — Data Cleaning & Feature Engineering
- Objectives
  - Produce consistent, analysis‑ready tables for users, items, and interactions.
  - Engineer features to enable both collaborative and content‑based approaches.
- Core tasks
  - Clean nulls, deduplicate items/users, resolve conflicting ratings, standardize categorical fields.
  - Build item features:
    - Genres/tags: multi‑hot and TF‑IDF vectors
    - Synopsis text: sentence embeddings via `sentence-transformers`
    - Popularity/recency features
  - Identify titles introduced after the frozen Kaggle snapshot (post‑snapshot/new MAL IDs) and flag for content‑only recommendations.
  - Implement a content‑only recommendation path for new items (no ratings), leveraging content features and popularity priors.
  - Create train/validation/test splits (user‑aware, optionally time‑based). Persist as `parquet`.
- Deliverables
  - `data/processed/` parquet files (users, items, interactions, feature matrices).
  - Feature documentation with shapes and value ranges.
  - Vectorizer artifact persisted for inference: `data/processed/features/tfidf_vectorizer.joblib`.
  - User features, user/item index mappings, feature scaling snapshot (JSON), quality slices, and artifacts manifest for Phase 3 readiness.
- Recommended tools/libraries
  - Pandas, NumPy, scikit‑learn, `sentence-transformers`, scikit‑learn’s TfidfVectorizer.

### Phase 3 — Model Development
- Objectives
  - Establish strong baselines and develop a hybrid recommender.
- Core tasks
  - Baselines: popularity, genre‑based similarity.
  - Collaborative filtering
    - User/Item k‑NN (Surprise KNNBasic)
    - Matrix factorization (Surprise SVD) and/or implicit feedback ALS (`implicit`)
  - Content‑based
    - Cosine similarity on TF‑IDF (genres/tags) and on synopsis embeddings
  - Hybridization strategies
    - Weighted score blending (learn weights via validation)
    - Rank aggregation (Borda/Reciprocal Rank Fusion)
    - Stacking meta‑model (optional)
  - Hyperparameter optimization with Optuna (objective: NDCG@K / MAP@K on validation).
- Deliverables
  - Reproducible training scripts in `src/` and experiment notebooks in `notebooks/`.
  - Serialized models/artifacts in `models/` with versioning.
  - Baseline CF trainer scripts (e.g., `scripts/train_lightfm_baseline.py`) with standard metrics (Precision@K, Recall@K).
- Recommended tools/libraries
  - Surprise, LightFM, implicit, scikit‑learn, Optuna, joblib.

#### Phase 3 — Final status (2025-11-21)

- Baselines complete: Popularity, genre/tag TF-IDF similarity, content embeddings (synopsis), cold-start content-only path.
- Collaborative filtering: MF (FunkSVD via NumPy SGD) stable (lr=0.005, reg=0.05, 64 factors); Item kNN (centered rating-weighted user profiles with shrinkage + popularity prior) implemented (low standalone ranking quality but contributes diversity).
- Hybrid: Weighted blend + Reciprocal Rank Fusion implemented; initial popularity-heavy tuned weights replaced by diversity-aware Optuna tuning (coverage reward + popularity cap) yielding balanced weights frozen in `src/models/constants.py`:
  - mf=0.93078, knn=0.06625, pop=0.00297 (normalized)
- Metrics instrumentation: NDCG@K, MAP@K, item coverage, Gini index integrated across evaluators; explanations (per-source score contributions) available for hybrid examples.
- Artifact management: Versioned model saver uses UTC-aware timestamps; manifest updated with latest serialized kNN & MF artifacts.
- Libraries: Replaced Surprise/implicit with lightweight sklearn/numpy due to environment constraints while preserving core CF capabilities.

Final unified evaluation (K=10, users=1000):
| Model | NDCG@10 | MAP@10 | Coverage@10 | Gini@10 |
|-------|---------|--------|-------------|---------|
| MF (FunkSVD) | 0.05036 | 0.03900 | 0.071 | 0.784 |
| Hybrid (Balanced) | 0.04973 | 0.03844 | 0.066 | 0.791 |
| Popularity | 0.04120 | 0.02785 | 0.006 | 0.726 |
| Item kNN | 0.00169 | 0.00131 | 0.118 | 0.728 |

Interpretation: Balanced hybrid preserves ~99% of MF NDCG while widening item exposure compared to popularity baseline and retaining acceptable diversity. Item kNN underperforms on accuracy but boosts hybrid coverage slightly; popularity alone is strong but narrow.

Phase 3 completion criteria met: baselines, CF models, hybrid strategies, tuning (accuracy & diversity), artifacts, and reporting. Remaining experimental models (implicit ALS, LightFM WARP deep tuning) deferred unless needed for portfolio narrative.

Transition to Phase 4: Focus shifts to evaluation storytelling—plotting metric curves vs K, ablations (CF vs content vs hybrid), diversity trade-offs, temporal validation, and preparation for app integration.

### Phase 4 — Evaluation & Analysis (Kickoff 2025-11-22)
Objectives
  - Transform raw metric logs into persuasive, portfolio-ready evaluation artifacts (plots, ablations, explanations) that justify design choices and hybrid trade‑offs.
  - Validate robustness (temporal split), quantify diversity exposure, and establish CI/lint quality gates before app integration.

Core Kickoff Tasks (High ROI)
  - Plot metric curves: NDCG@K and MAP@K vs K for Popularity, MF, Hybrid (balanced weights), Content TF‑IDF.
  - Plot diversity curves: Coverage@K and Gini@K vs K to illustrate concentration vs exposure.
  - Ablation table: Popularity vs MF vs Hybrid vs Content (TF‑IDF) with relative lift % (e.g., Hybrid vs Popularity NDCG improvement).
  - Hybrid explanation examples: per‑source contribution breakdown for top 3 recommended items (attach to report).

Rigor & Validation
  - Temporal split sanity check: train on earlier partition, validate on later; compare deltas to current unified slice to detect leakage or drift.
  - Cold‑start recap: integrate existing content‑only evaluation into Phase 4 report section (new item exposure & qualitative examples).
  - (Optional) Fairness / genre exposure quick scan: distribution of genre tags across recommendations vs catalog.

Infrastructure & Quality
  - CI setup: GitHub Actions workflow (install deps, run pytest, run ruff/black checks).
  - Pre‑commit hooks: ruff (lint), black (format), end‑of‑file and trailing whitespace filters.
  - Evaluation plotting script (`scripts/plot_phase4_metrics.py`) and ablation generator (`scripts/generate_phase4_ablation.py`).
  - Report artifact: `reports/phase4_evaluation.md` consolidating curves, tables, explanation snippets, temporal comparison.

Stretch (Optional / Defer)
  - Implicit ALS prototype & comparative curves (only if adds narrative value beyond MF).
  - LightFM deeper tuning (display WARP vs MF/Hybrid performance; diversity impact).
  - Novelty/popularity bias plot (long‑tail exposure metric vs baseline).

Exit Criteria (Phase 4 Completion)
  - Curves (NDCG/MAP, Coverage/Gini) committed. ✅
  - Ablation table with relative lifts published. ✅
  - Explanation examples integrated in evaluation report. ✅
  - Temporal robustness documented (synthetic timestamp sanity + unified comparison). ✅
  - CI pipeline green (tests + ruff/black); pre-commit hooks active. ✅
  - Genre exposure ratio + novelty/popularity bias artifacts generated (added to diversity narrative). ✅
  - Alternate hybrid explanations (diversity-emphasized weights) produced. ✅
  - Accessibility improvements (colorblind-safe palette, alt text references) applied. ✅
  - Phase 4 report (`reports/phase4_evaluation.md`) enriched & referenced in main `README.md`. ✅

Phase 4 Outcome Summary (2025-11-22):
- Artifacts: metric & diversity curves (`reports/figures/phase4/*.png`), ablation CSV/MD, hybrid explanations (default + `hybrid_explanations_alt.json`), temporal split metrics, genre exposure ratio, novelty bias plot.
- Robustness: Temporal split shows negligible degradation; hybrid retains MF accuracy within ~1% while improving coverage vs popularity baseline.
- Diversity: Genre exposure & novelty bias plots illustrate balanced hybrid avoids over-concentration on top genres and high-popularity tail.
- Engineering: CI workflow + pre-commit enforce quality; JSON safety utility and artifact loader prepared for app integration.
- Explainability: Per-item contribution breakdown clarifies blended source influence (mf vs knn vs popularity).

Recommended tools/libraries
  - pandas, numpy, matplotlib/seaborn/plotly for plotting; scikit‑learn metrics (existing); ruff, black, pytest, GitHub Actions for CI; optional implicit/LightFM for stretch.

### Phase 5 — App Development & 
Objectives
  - Deliver an interactive, portfolio‑ready Streamlit app showcasing recommendations, explanations, diversity/novelty indicators, and cold‑start handling.
  - Provide a crisp UX: fast initial load (<3s), clear “Why this anime?” context, accessible color palette, mobile-friendly layout.
  - Ensure reproducibility: controlled artifact loading, deterministic sample recommendations, and clear environment bootstrap.

Core Implementation Tasks
  - Data/Artifact Loader Integration: finalize use of `src/app/artifacts_loader.py` for metrics, explanations, diversity artifacts.
  - Recommendation Endpoint: wrapper functions to fetch top‑N per (user simulation, seed anime similarity, cold‑start content path).
  - User Simulation: simple user persona selection (e.g., sample IDs with stored preference summaries).
  - Title Search & Selection: fuzzy search over normalized titles (English/Japanese) with fallback to substring.
  - Hybrid Recommender Inference: blend MF, kNN, popularity scores with frozen weights; alternate weight toggle.
  - Cold‑Start Labeling: flag items absent from training interactions (new since snapshot) and display badge + tooltip.

UX & Explainability
  - Explanation Panel: show contributing source scores (mf/knn/pop) for each rec (top 5) + share percentages.
  - Diversity & Novelty Badges: overlay indicators (e.g., genre novelty ratio, popularity percentile band).
  - Accessible Color Scheme: reuse Phase 4 colorblind‑safe palette for charts and badges.
  - Loading Skeletons: placeholder components while artifacts initialize.
  - Inline Help: collapsible FAQ on metrics (NDCG, coverage, Gini, novelty) and hybrid logic.

Performance & Operations
  - Artifact Pruning: reduce item metadata columns to those required by UI (id, title_display, genres, synopsis snippet).
  - Caching Strategy: `st.cache_data` / `st.cache_resource` for models & artifacts; manual TTL for large embeddings.
  - Lightweight Embedding Similarity: optional fallback to TF‑IDF cosine if sentence embeddings omitted for speed.
  - Memory Budget: keep RAM < 512MB for community hosting (monitor sizes of vector/embedding matrices).
  - Latency Targets: recommendation inference <250ms for typical user or seed input.

Testing & Quality
  - Unit tests for UI helper functions (search normalization, badge logic, explanation formatting).
  - Smoke test script (`scripts/run_unified_eval.py` reused) ensures artifacts present before app launch.
  - CI Extension: add app import test (no runtime errors) and simple Streamlit component render test.

Stretch (Optional)
  - ANN Index (FAISS/Annoy) for synopsis embedding similarity; evaluate latency improvement.
  - Favorites / Watchlist Emulation: allow users to select a few liked titles → dynamic re‑ranking.
  - Session Persistence: store last selections in local query params.
  - Dark Mode Toggle & Accessibility audit (ARIA roles, contrast check).
  - Lightweight Feedback Logging (local JSON) for click events.

Exit Criteria (Phase 5 Completion)
  - Deployed Streamlit app (public URL) with: search, hybrid recommendations, explanations, cold‑start badges.
  - Diversity/novelty indicators visible for each recommendation or summary section.
  - Alternate hybrid weight toggle (balanced vs diversity‑emphasized) functioning.
  - App loads within target latency thresholds; caching verified (no repeated heavy load).
  - README updated with screenshots + usage instructions.
  - Minimal test suite for app utilities passing in CI.
  - No PII; reproducible run instructions documented.

Success & UX Metrics (Qualitative)
  - Clarity: user can explain why an item appears after 10s of exploration.
  - Diversity: user notices mix of mainstream and long‑tail items (qualitative check).
  - Responsiveness: interactions feel instantaneous (<500ms) for top‑N updates.

Risks & Mitigations (Phase 5)
  - Large Artifacts Slow Load → prune columns / lazy load explanations.
  - Cold‑Start Confusion → explicit badge + tooltip clarifying content-only path.
  - Embedding Latency → fallback to TF‑IDF similarity when embeddings absent.
  - Memory Constraints → monitor object sizes; optionally compress parquet with snappy.
  - Explainability Overload → limit to top 5 items; drill‑down modal for details.

Transition to Phase 6
  - After deployment and initial manual QA, capture screenshots + architecture diagram.
  - Document inference pipeline and artifact lineage in `README.md` + `docs/`.
  - Prepare optional blog/video assets if time allows.
  
#### Phase 5 Progress (2025-11-26)
Status: IN PROGRESS. Feature-rich interactive Streamlit app with polished UX, comprehensive filtering, and dual browsing modes.
Completed so far:
  - Integrated artifact loader (`build_artifacts`) with metadata pruning and required columns restoration.
  - Replaced deprecated Streamlit query param API (migrated to `st.query_params`).
  - **Image Quality Upgrade**: Switched from small (225x318px) to large (425x600px) Jikan images for sharper, crisper thumbnails; rendered via native `st.image()` component.
  - Added onboarding instructions component (dismissible usage steps) and persistent sidebar quick steps.
  - **English Title Prioritization**: Searchable dropdown (13K+ titles) now shows English titles first (e.g., "Blood Blockade Battlefront" vs "Kekkai Sensen") with original/Japanese subtitle when different.
  - Seed selection with auto-population on dropdown change; green success banner "🎯 Active Seed" with clear button.
  - Sample search suggestions (4 popular titles: Steins;Gate, Cowboy Bebop, Death Note, FMA:Brotherhood) in empty state.
  - Added refined seed similarity path (genre overlap + hybrid score + mild popularity boost) with per-item explanation shares.
  - Hybrid recommender with weight toggle (Balanced vs Diversity) wired into UI.
  - **Comprehensive Metadata Display**: Each card now shows:
    - ⭐ MAL score (color-coded: green ≥8.0, blue ≥7.0, gray <7.0)
    - 📺 Episode count
    - 📅 Release year (extracted from aired_from)
    - ✅/🟢/🔵 Airing status (Finished/Currently Airing/Not Yet Aired)
    - 🎬 Studio information (up to 2 studios with "+X more" for additional)
    - Source material (manga, light novel, game, etc.)
    - 🎬 **Streaming platforms** with clickable badges (Crunchyroll, Netflix, Hulu, etc.) linking directly to watch pages
  - Visual card redesign: colored left borders (blue=trained, orange=cold-start), inline badge pills with icons, proper spacing.
  - Simplified inline explanations (human-friendly summaries like "📊 Collaborative 96%") with technical details in expander.
  - Badge tooltips component (`src/app/components/tooltips.py`) explaining cold-start, popularity bands, novelty ratios.
  - Explanation panel component (`src/app/components/explanation_panel.py`) showing top-5 MF/kNN/Pop breakdowns.
  - Smart synopsis truncation with full text available in expandable "📖 Read full synopsis" section.
  - Progress indicators: spinner "🔍 Finding recommendations..." during computation.
  - Result count heading: "Showing X recommendations".
  - Visual diversity summary bar: horizontal colored bar showing Popular (🔥), Balanced (📊), Exploratory (🌟) counts with proportions.
  - Confidence star rating (⭐ 1-5 stars) per card based on recommendation score magnitude.
  - Fixed indentation bug in seed similarity path causing NameError.
  - **Sort & Filter Infrastructure (2025-11-26)**:
    - Sort controls: 5 options (Confidence, MAL Score, Year Newest/Oldest, Popularity)
    - Genre filter: Multi-select dropdown with 40+ genres (Action, Adventure, Comedy, Drama, Fantasy, etc.)
    - Year range filter: Slider (1960-2025) for temporal filtering
    - Reset filters button: Clears all selections and returns to defaults
    - Filter info display: Shows active filters in results heading (e.g., "3 genres, 2000-2020")
  - **Browse by Genre Mode (2025-11-26)**:
    - Checkbox toggle "📂 Browse by Genre" enabling catalog exploration without seed requirement
    - Filters metadata directly by selected genres + year range (bypasses recommendation engine)
    - Shows "📚 Browsing X anime" vs "✨ Showing X Recommendations" in header
    - Works with all sort options (MAL Score, Year, Popularity)
    - Limited to Top N slider for performance
  - **Card Rendering Fix (2025-11-26)**:
    - Resolved empty/partially empty boxes above all recommendations
    - Root cause: Manual HTML `<div>` tags incompatible with native `st.image()` component
    - Solution: Replaced manual divs with `st.container(border=True)` for proper component wrapping
  - **Synopsis Display Enhancement (2025-11-26)**:
    - Confirmed metadata structure: single `synopsis` column with full text (~700 chars average)
    - Removed expander complexity; now displays full synopsis directly via `st.caption()`
    - Added proper pandas NaN handling (`pd.notna()` checks)
  - **Genre Filter Fix (2025-11-26)**:
    - Fixed "No options to select" issue in genre filter dropdown
    - Root cause: Genres stored as numpy arrays, not pipe-delimited strings
    - Solution: Added array format handling to extraction logic

Data Format Discoveries (important for maintenance):
  - Genres: numpy array format requiring `hasattr(genres_val, '__iter__')` checks
  - Synopsis: Single `synopsis` column only (no separate snippet/full columns)
  - Images: `poster_thumb_url` column with 99.1% coverage (12,923/13,037)
  - Aired From: String format "YYYY-MM-DD" for year extraction

Remaining (near-term):
  - Latency measurement display + caching audit (ensure <250ms inference path).
  - Memory usage profiling (<512MB target).
  - Unit tests for search normalization, badge logic, explanation formatting.
  - README screenshot & usage section draft; deployment to public hosting.
  - Minimal `requirements.txt` for deployment.

Stretch still open: ANN index, favorites/watchlist, dark mode, feedback logging.

Risks Observed & Mitigated:
  - Metadata pruning inadvertently dropped critical display columns (resolved with expanded `MIN_METADATA_COLUMNS`).
  - Image codec issues avoided via native st.image() instead of HTML markdown.
  - Synopsis truncation cutting mid-sentence (resolved with expandable full text section).
  - Image HTML tags appearing as text (fixed by switching from markdown to st.image()).
  - Seed selection logic indentation error (fixed).
  - Empty card boxes due to HTML div incompatibility (fixed with st.container).
  - Genre filter not populating (fixed with numpy array handling).
  - Synopsis not displaying (fixed with proper NaN handling and metadata column identification).

Next focus: Performance audit (latency/memory surface) → minimal test suite → deploy & document.
Ready for git tag `phase5-ux-refined` once performance profiling display complete.
Deployment
### Phase 6 — Documentation & Portfolio Presentation
- Objectives
  - Communicate impact, rigor, and reproducibility.
- Core tasks
  - Top‑level `README.md` with architecture diagram, screenshots, and live demo link.
  - MkDocs or Markdown docs for: setup, data catalog, modeling decisions, evaluation, and API/app usage.
  - Testing: unit tests for data transforms and recommenders; minimal CI on pull requests.
- Deliverables
  - `README.md`, `docs/` site or markdowns, `tests/` with PyTest suite, coverage badge (optional).
- Recommended tools/libraries
  - MkDocs (optional), PyTest, coverage, pre‑commit hooks.

## 3. Technical Stack & Tools

| Component        | Recommended Tools                                | Purpose                                  |
|------------------|---------------------------------------------------|------------------------------------------|
| Data Processing  | Pandas, NumPy, PyArrow                            | Cleaning, transformation, parquet IO     |
| NLP Features     | sentence-transformers, scikit-learn (TF‑IDF)      | Synopsis embeddings, tag/genre vectors   |
| Modeling         | Surprise, LightFM, implicit, scikit‑learn         | CF, hybrid models, baselines             |
| Experimentation  | Optuna, MLflow (optional), joblib                 | Tuning, tracking, artifact mgmt          |
| Visualization    | Matplotlib, Seaborn, Plotly (optional)            | EDA, metric plots                         |
| Front-End        | Streamlit                                         | Interactive app UI                       |
| Similarity/ANN   | FAISS or Annoy (optional)                         | Fast nearest‑neighbor search             |
| Deployment       | Streamlit Cloud / Hugging Face Spaces / Docker    | Hosting & packaging                      |
| Testing          | PyTest, coverage                                  | Unit tests and quality gate              |
| Lint/Format      | ruff or flake8, black, pre-commit                 | Code quality and consistency             |
| Docs             | Markdown, MkDocs                                  | Reports & documentation                  |

## 4. Timeline & Milestones (4–6 Weeks)

| Week | Focus Area                               | Key Deliverables                                                |
|------|-------------------------------------------|-----------------------------------------------------------------|
| 1    | Data collection & EDA                     | Datasets sourced, cataloged; initial EDA and data quality notes |
| 2    | Feature engineering & baseline modeling   | Clean processed data; TF‑IDF/embeddings; baseline models        |
| 3    | Model tuning & hybrid system              | Optuna runs; hybridization; evaluation tables/plots             |
| 4    | Streamlit app development                 | Working UI; recommendation endpoints; caching                   |
| 5    | Deployment & testing                      | App deployed; tests passing; repo structure finalized           |
| 6    | Polish & presentation (optional)          | Blog post, CI/CD, Docker image, video demo                      |

## 5. Evaluation Strategy

- Metrics
  - Rating prediction: RMSE, MAE
  - Top‑N ranking: Precision@K, Recall@K, MAP@K, NDCG@K
- Split strategies
  - User‑based split to ensure unseen users in test or, alternatively, leave‑one‑out per user.
  - Time‑aware splits when timestamps exist to minimize leakage.
- Visualization
  - Metric comparison tables by model; lift charts; precision‑recall vs K; recall@K by user activity deciles.
  - Confusion‑style heatmaps for genre coverage; histogram of recommendation diversity/novelty.
- Communication
  - Lead with a simple business framing ("find similar to X" and "what a new user sees").
  - Pair metric gains with qualitative examples and “why” explanations to bridge to non‑technical readers.

## 6. Deliverables Checklist

- 📁 Organized GitHub repo
  - `data/` (raw, interim, processed), `notebooks/`, `src/`, `app/`, `models/`, `tests/`, `docs/`, `reports/`
- 🧾 `README.md` with overview, architecture diagram, visuals, and live demo link
- 📓 Jupyter notebooks: EDA, feature engineering, modeling experiments, final model
- 🧠 Clean, modular source code in `src/` with clear interfaces and docstrings
- 🌐 Deployed Streamlit app + usage examples and screenshots
- 🗒️ Technical documentation or final report in `docs/`/`reports/`
- 🧩 Optional: blog post, short video demo, CI/CD workflow, Dockerfile, environment files (`requirements.txt`/`pyproject.toml`)

## 7. Expected Outcomes & Portfolio Value

- Demonstrates end‑to‑end ownership: data → features → models → evaluation → app → deployment.
- Shows algorithmic maturity: CF vs content tradeoffs, cold‑start handling, and hybridization.
- Communicates clearly through metrics, visuals, and concise documentation suitable for hiring panels.
- Signals engineering hygiene: tests, linting, reproducibility, small performant artifacts for apps.

## 8. Optional Enhancements

- NLP‑based personalization from reviews/synopses; fine‑tune or re‑rank with transformer models.
- Real‑time updates via periodic retraining jobs; simple API integration for fresh metadata.
- Visualize item similarity networks and user taste profiles.
- Containerize with Docker; add GitHub Actions CI/CD and caching for model artifacts.
- Publish a Medium post or 5–8 minute video walkthrough with app demo and lessons learned.

## 9. Risk Mitigation & Next Steps

- Data sparsity and cold‑start
  - Mitigation: robust content features (genres, embeddings), popularity priors, hybrid blending.
- API rate limits or licensing constraints
  - Mitigation: rely primarily on static datasets; cache responses; document attribution.
- Model explainability
  - Mitigation: show top contributing genres/tags and nearest‑neighbor exemplars in the UI.
- Performance and latency in the app
  - Mitigation: precompute factors, use sparse matrices/ANN indices, caching, and lightweight artifacts.
- Reproducibility and environment drift
  - Mitigation: pinned dependencies, Makefile/tasks, deterministic seeds, saved artifacts with versions.

---

Next Steps (Phase 5 Initiation)
- Integrate loader module into Streamlit app (`src/app/artifacts_loader.py`).
- Build interactive recommendation view (user simulation + seed title search) with explanation panel.
- Surface diversity/novelty indicators (badges, ratios) alongside recommendations.
- Implement cold-start item labeling (new since snapshot) and explanatory tooltip.
- Optimize artifact sizes (prune unused columns; optionally compress parquet) for faster app load.
- Deploy initial Streamlit prototype; collect manual UX feedback and iterate.

Tagging: Create git tag `phase4-complete` to freeze evaluation baseline before UI development.
