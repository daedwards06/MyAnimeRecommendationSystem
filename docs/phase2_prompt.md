# === TASK SPECIFICATION FOR COPILOT GPT-5 ===
You are operating inside VS Code as an autonomous data-science assistant.
Follow this structured project specification and produce actionable outputs directly usable in this repo.
Prefer concise, step-by-step reasoning and modular code snippets over narrative text.

---

# === CONTEXT ===
We are in **Phase 2 — Data Cleaning & Feature Engineering** of a professional data-science portfolio project: **Anime Recommendation System** built with **Python + Streamlit**.
See running_context file `docs/running_context.md` (Phase 1 complete: 12,297 records processed; null distribution captured in catalog; EDA notebook updated to handle ndarray genres/themes; normalized `genres_list`/`themes_list` columns persisted).

Now we are beginning **Phase 2 – Data Cleaning & Feature Engineering**.

---

## Phase 2 Objectives
- Produce consistent, analysis-ready tables for **users**, **items**, and **interactions**
- Engineer features that support **collaborative**, **content-based**, and **hybrid** approaches
- Handle **cold-start** scenarios for new anime titles unseen in the Kaggle snapshot

## Core Tasks
1. **Data Cleaning**
   - Handle nulls, deduplicate items/users, resolve conflicting ratings
   - Standardize categorical fields (genres, studios, type)

2. **Item Feature Engineering**
   - **Genres / Tags:** multi-hot + TF-IDF vectors (using `scikit-learn`’s `TfidfVectorizer`)
     - Output to `data/processed/features/genres_multi_hot.parquet`
     - Column naming: `genre_*` and `theme_*`
     - Suggested defaults: `TfidfVectorizer(max_features=10000, ngram_range=(1,2))`
   - **Synopsis Text:** create sentence embeddings via `sentence-transformers` (default `"all-MiniLM-L6-v2"`)
     - Persist in batches to `data/processed/features/item_embeddings.parquet`
     - Use batching and `torch.no_grad()` for memory efficiency
   - **Popularity / Recency:** derive a numeric popularity score (suggested: `popularity = log(1 + num_ratings) * mean_rating`) and `released_year` or `days_since_release`

3. **Cold-Start Detection and Content-Only Path**
   - Identify titles introduced **after the Kaggle snapshot** (new MAL IDs)
   - Flag these items for **content-only recommendation**
   - Implement a content-only scoring function: weighted similarity (content_features) + popularity prior (tunable)

4. **Data Splitting**
   - Create **train / validation / test** sets (user-aware; optionally time-based)
   - Suggested default splits: `train 70% / val 15% / test 15%` (user-aware); include an optional time-based split method
   - Persist all datasets and feature matrices in `data/processed/` as **Parquet** with index columns (`anime_id`, `user_id`)

5. **Feature Documentation**
   - Record shapes, dtypes, and value ranges for each processed table in `docs/features.md`

## Deliverables
- `data/processed/users.parquet`
- `data/processed/items.parquet`
- `data/processed/interactions.parquet`
- `data/processed/item_features_tfidf.parquet`
- `data/processed/item_features_embeddings.parquet`
- `data/processed/anime_metadata.parquet`
- `docs/features.md` summarizing feature shapes & value ranges
- `requirements.txt` or `pyproject.toml` note (include `sentence-transformers`, `scikit-learn`, `pyarrow`, `pandas`, `numpy`, `torch`)

## Recommended Libraries
`pandas`, `numpy`, `scikit-learn`, `sentence-transformers`, `pyarrow`, `torch`

---

## Phase 2 Task Checklist
Use this as the authoritative to-do list for implementation. Each bullet should map to one or more functions or modules.

- [ ] Cleaning pipeline (`src/data/cleaning.py`)
- [ ] Genre/tag parsing & normalization
- [ ] Multi-hot encoding (genres/tags) -> `data/processed/features/genres_multi_hot.parquet`
- [ ] TF-IDF vectors (tags/keywords) -> `data/processed/item_features_tfidf.parquet`
- [ ] Synopsis embeddings (`sentence-transformers`) -> `data/processed/item_features_embeddings.parquet`
- [ ] Popularity & recency features
- [ ] Train/val/test split (user-aware + optional time split)
- [ ] Feature documentation (`docs/features.md`)
- [ ] Normalize Jikan metadata → Parquet (`data/processed/anime_metadata.parquet`)
- [ ] Identify and flag new titles (post-snapshot) for content-only recommendations
- [ ] Metadata feature extraction (genres/themes/demographics/studios)
- [ ] Basic unit-test stubs (`tests/test_data_cleaning.py`, `tests/test_splitting.py`)

---

## Request
Generate a **structured Markdown implementation plan** covering:

1. **Phase 2 Implementation Plan** – step-by-step rationale and actions  
2. **Code Snippets** – modular, production-ready examples (null cleaning, TF-IDF, embeddings, cold-start detection, splitting). Include docstrings and type hints.  
3. **File / Module Layout** – recommended Python files & notebooks  
4. **Milestone Checklist** – criteria for marking Phase 2 complete  
5. **Phase 3 Preview** – how processed data & features feed into model development (collaborative / content-only / hybrid)

---

# === STYLE GUIDELINES ===
- Clear Markdown headings and fenced code blocks.  
- Concise technical explanations suitable for immediate implementation.  
- Use Python 3.10+ syntax, type hints, and docstrings.  
- Deterministic behavior: set and use a `RANDOM_SEED` constant for splits.  
- Cache expensive artifacts (embeddings) to avoid re-generating.  
- Ensure file paths match repo structure.
