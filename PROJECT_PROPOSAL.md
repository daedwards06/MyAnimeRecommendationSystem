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

### Phase 4 — Evaluation & Optimization
- Objectives
  - Quantify recommendation quality and justify design decisions.
- Core tasks
  - Metrics: RMSE/MAE for explicit rating prediction; Precision@K, Recall@K, MAP, NDCG for top‑N.
  - Split strategies: user‑based holdout; consider temporal splits to avoid leakage.
  - Ablations: CF only vs content only vs hybrid; impact of synopsis embeddings; cold‑start analysis.
  - Trend‑shift analysis: evaluate changes in genre/theme popularity over time and assess impact on recommendation quality.
  - Calibration and fairness checks (e.g., avoid over‑promoting only popular titles).
- Deliverables
  - `reports/` with metric tables/plots and decision rationale.
  - Reusable evaluation module in `src/eval/`.
- Recommended tools/libraries
  - scikit‑learn, pandas, matplotlib/seaborn, mlflow or a simple CSV log for experiments.

### Phase 5 — App Development & Deployment
- Objectives
  - Deliver an interactive, portfolio‑ready Streamlit app with fast responses and clear explanations.
- Core tasks
  - UI: search by title, choose seed anime/user, filters (genre, year, maturity), “Why recommended?” explainer.
  - UI badges/indicators for cold‑start or content‑only items to set expectations and explain limited personalization.
  - Backend: load precomputed factors/indices; cosine similarity search; top‑N generation; caching layer.
  - Data layer: small, optimized artifacts (sparse matrices, FAISS/Annoy index for embeddings if needed).
  - Deployment: Streamlit Community Cloud or Hugging Face Spaces; optional Docker image.
- Deliverables
  - `app/` Streamlit app with components and `requirements.txt`.
  - Deployed URL and app README section with screenshots.
- Recommended tools/libraries
  - Streamlit, numpy/pandas, `sentence-transformers`, optional FAISS/Annoy, joblib.

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

Next steps
- Phase 2 complete: artifacts and helper utilities are in place for modeling (TF‑IDF vectorizer saved; user/item indices; scaling stats; manifest).
- Begin Phase 3: run CF baselines (e.g., LightFM WARP via `scripts/train_lightfm_baseline.py`), add Surprise KNN/SVD and implicit ALS, then iterate toward hybrid.
