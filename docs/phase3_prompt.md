# === TASK SPECIFICATION FOR COPILOT GPT-5 ===
You are operating inside VS Code as an autonomous machine-learning assistant.
Follow this structured project specification and produce actionable outputs directly usable in this repository.
Prefer concise reasoning and modular code snippets over narrative text.

---

# === CONTEXT ===
We are now entering **Phase 3 — Model Development** of the professional data-science portfolio project:  
**Anime Recommendation System** (Python + Streamlit).

Phase 2 has produced cleaned and feature-engineered data:
- `users.parquet`, `items.parquet`, `interactions.parquet`
- TF-IDF features, multi-hot genres, and embeddings
- Train/val/test splits and feature documentation  
All artifacts exist in `data/processed/`.

Phase 3 focuses on building **baseline**, **collaborative**, **content-based**, and **hybrid** recommenders and evaluating them.

---

# === PHASE 3 OBJECTIVES ===
- Establish strong **baseline recommenders**
- Implement multiple **collaborative filtering models**
- Build **content-based recommenders** using Phase 2 features
- Develop **hybrid strategies** (weighted blending, rank fusion, optional stacking)
- Conduct **hyperparameter optimization** (Optuna)
- Produce **versioned, reproducible model artifacts**

---

# === CORE TASKS ===

## 1. Baseline Models
- **Popularity baseline**
  - Recommend top-N items ranked by: `log(1 + num_ratings) * mean_rating`
- **Genre similarity baseline**
  - Cosine similarity using TF-IDF or multi-hot genre vectors

## 2. Collaborative Filtering Models
- **User/Item k-NN (Surprise KNNBasic)**  
  - Default similarity: cosine; grid-search k via Optuna or manual tuning
- **Matrix Factorization (Surprise SVD)**  
  - Tune `n_factors`, `reg_all`, `lr_all`
- **Implicit ALS (`implicit` library)**  
  - Use confidence-weighted interaction matrix
  - Evaluate using ranking metrics
- **LightFM WARP baseline**  
  - Implement script `scripts/train_lightfm_baseline.py`

## 3. Content-Based Models
- **Cosine similarity on TF-IDF (genres/tags)**
- **Cosine similarity on sentence embeddings (synopsis)**
- Expose functions: `recommend_by_tfidf()`, `recommend_by_embedding()`

## 4. Hybrid Recommenders
- **Weighted blending**
  - Learn weights on validation using Optuna  
- **Rank aggregation**
  - Borda Count, Reciprocal Rank Fusion (RRF)  
- **Optional stacking meta-model**
  - Use linear/logistic model or gradient boosting on stacked scores

## 5. Hyperparameter Optimization (Optuna)
- Define objective metric: `NDCG@K` (primary) + `MAP@K`
- Use consistent validation split from Phase 2
- Store studies: `experiments/optuna_studies/`

## 6. Model Serialization & Experiment Tracking
- Save artifacts to `models/` using versioned filenames  
  (`model_name_v{major}.{minor}.joblib`)
- Track metrics via CSV, JSON, or MLflow-lite  
  (`experiments/metrics/`)

---

# === DELIVERABLES ===
- Training scripts in `src/models/`
- Experiment notebooks in `notebooks/`
- Versioned model artifacts in `models/`
- Baseline CF trainer scripts:
  - `scripts/train_lightfm_baseline.py`
  - `scripts/train_svd.py`
  - `scripts/train_knn.py`
  - `scripts/train_als_implicit.py`
- Evaluation utilities: Precision@K, Recall@K, F1@K, NDCG@K, MAP@K
- Optuna study results for each model family

---

# === RECOMMENDED LIBRARIES ===
`Surprise`, `LightFM`, `implicit`, `scikit-learn`, `Optuna`, `pandas`, `numpy`, `joblib`, `pyarrow`

---

# === PHASE 3 TASK CHECKLIST ===
Use this as the authoritative implementation to-do list.

- [ ] Popularity baseline recommender  
- [ ] Genre similarity baseline (TF-IDF / multi-hot)  
- [ ] User–Item kNN (Surprise KNNBasic)  
- [ ] Matrix Factorization SVD (Surprise)  
- [ ] Implicit ALS model (`implicit` library)  
- [ ] LightFM WARP baseline (`scripts/train_lightfm_baseline.py`)  
- [ ] Content embedding similarity (synopsis embeddings)  
- [ ] Hybrid blending logic (weighted / rank fusion)  
- [ ] Hyperparameter tuning (Optuna study optimizing NDCG@K / MAP@K)  
- [ ] Model serialization to `models/` (versioned)  
- [ ] Experiment tracking (CSV/JSON or MLflow-lite)  

---

# === REQUEST ===
Generate a **structured Markdown implementation plan** covering:

1. **Phase 3 Implementation Plan** – step-by-step actions and rationale  
2. **Code Snippets** – production-ready examples (baselines, CF, content-based, hybrid, Optuna) with docstrings + type hints  
3. **File / Module Layout** for `src/models/` and training scripts  
4. **Milestone Checklist** – criteria for marking Phase 3 complete  
5. **Phase 4 Preview** – how trained models integrate into the Streamlit front-end for real-time recommendations  

---

# === STYLE GUIDELINES ===
- Use concise Markdown formatting and fenced code blocks  
- Include type hints, docstrings, reproducible randomness (`RANDOM_SEED`)  
- Scripts must load Phase 2 artifacts directly  
- Avoid long explanations; focus on immediately usable code and structure  
- Ensure file paths match the repo structure

