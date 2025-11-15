# Running Context (Live Project Snapshot)

Last updated: 2025-11-14

> Purpose: This document is a concise, living summary of the project state so any new chat/session can quickly regain context without rereading long-form artifacts or scrolling history.

---
## 1. Project Identity
- Name: MyAnimeRecommendationSystem (MARS)
- Goal: Portfolio-grade hybrid anime recommender (collaborative + content + popularity + recency) with explainability and Streamlit UI.
- Guiding Principle: Reproducible historical ratings + fresh enriched metadata for relevance.

## 2. Scope & Phases (Condensed)
| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Data acquisition & enrichment (Kaggle + Jikan) | COMPLETE |
| 2 | Cleaning & feature engineering | COMPLETE (wrap-up enhancements added) |
| 3 | Baseline recommenders (CF/content) | Pending |
| 4 | Hybrid + optimization (weights, Optuna) | Pending |
| 5 | Evaluation & explainability | Pending |
| 6 | Deployment (Streamlit + optional API) | Pending |

Reference: Full strategic detail lives in `PROJECT_PROPOSAL.md` (authoritative roadmap). This context file distills the active snapshot.

## 3. Data Assets & Versions
| Asset | Path | Source | Versioning Strategy |
|-------|------|--------|---------------------|
| Raw ratings | `data/raw/rating.csv` | Kaggle snapshot | Immutable baseline |
| Raw anime metadata (legacy) | `data/raw/anime.csv` | Kaggle snapshot | Immutable baseline |
| Extracted IDs | `data/raw/anime_ids.txt` | Derived from Kaggle | Regenerate if base changes |
| Jikan raw JSON cache | `data/raw/jikan/<id>.json` | Jikan API | Cached per MAL ID (UTF-8) |
| Enriched metadata parquet (latest) | `data/processed/anime_metadata.parquet` | Consolidated | Overwritten on updates |
| Enriched metadata snapshot | `data/processed/anime_metadata_<suffix>.parquet` | Consolidated | Versioned via `--snapshot-suffix` |
| Normalized metadata (genres/themes lists) | `data/processed/anime_metadata_normalized.parquet` | Derived from enriched | Auxiliary for Phase 2 |

Latest enrichment snapshot suffix: `202511_full` (completed). Additional discovery/fetch runs added new titles with snapshots like `202511_new`, `202511_range`; base metadata updated accordingly.
Current enriched metadata (base): 13,037 rows, ~26 columns (includes `title_display`, English/Japanese variants). Checkpoint interval: 300 IDs. Throttle: 0.70s + jitter.

## 4. Key Decisions & Rationale
| Decision | Rationale | Date |
|----------|-----------|------|
| Keep Kaggle ratings static | Ensures reproducibility for benchmarks & comparisons | 2025-11-08 |
| Enrich with current Jikan metadata | Adds freshness (updated genres, scores, status) | 2025-11-08 |
| Use cached JSON + periodic checkpoints | Avoid refetch & survive long-run interruption | 2025-11-09 |
| Switch to UTC aware datetimes | Future-proof against deprecation & ambiguous timezones | 2025-11-09 |
| Force UTF-8 for cache files | Prevent Windows cp1252 encode errors on synopsis text | 2025-11-09 |

(Add new rows as decisions occur.)

## 5. Current Phase Deep Dive (Phase 2)
- Status: Phase 2 complete; features and splits generated. Wrap-up enhancements included for Phase 3 readiness.
- Achieved (latest build 2025-11-14):
	- Clean interactions: 7,813,730 rows; user-aware splits train/val/test: 5,470,724 / 1,171,503 / 1,171,503
	- Multi-hot features: 13,037 x 74 (includes `anime_id`; 21 genre + 52 theme columns)
	- TF-IDF features: 13,037 x 1,171 (1,170 tfidf_* + `anime_id`); vectorizer saved to `data/processed/features/tfidf_vectorizer.joblib`
	- Embeddings: 13,037 x 385 (384 dims + `anime_id`) via all-MiniLM-L6-v2
	- Items table with popularity, recency, cold-start flags (+ optional `data_version`)
	- User features: `data/processed/user_features.parquet` (counts, mean rating, recency, genre diversity)
	- ID indices: `data/processed/user_index.parquet`, `data/processed/item_index.parquet`
	- Feature scaling snapshot: `data/processed/feature_stats.json` (mean/std/min/max for numeric signals)
	- Quality slices: `data/processed/slices/items_slices.parquet` + summary JSON
	- Artifacts manifest: `data/processed/artifacts_manifest.json` (sizes, paths, `data_version`)
- Residual Risks: TF-IDF stored dense for parquet compatibility; may switch to sparse NPZ if size grows.
- Next: Begin Phase 3 baselines and CF modeling.

## 6. Near-Term Tasks (High Priority Queue)
1. Implement popularity baseline evaluation script and run (DONE — see `scripts/evaluate_baselines.py`).
2. Train LightFM WARP baseline (NEW — see `scripts/train_lightfm_baseline.py`) and record val/test Precision@10/Recall@10.
3. Add CF baselines: Surprise KNNBasic and SVD on `train.parquet`; evaluate on `val/test`.
4. Content-only recommender from embeddings/TF-IDF; simple user profiles.
5. Prepare hybrid blending and Optuna setup.
6. Update `docs/features.md` as artifacts evolve; keep counts in sync.
7. Integrate negative sampling into training data prep using `src/eval/neg_sampling.py`.

## 7. Pending / Backlog (Selected)
- LightFM implicit matrix factorization prototype.
- Sentence-transformers embedding generation & caching.
- Hybrid score assembler + Optuna weight tuning.
- Explainability components (reason strings, feature contribution summary).
- Streamlit UI scaffolding & deployment script.

## 8. Tech Stack Snapshot
| Category | Choice |
|----------|--------|
| Language | Python 3.x |
| Data | pandas, parquet (pyarrow) |
| Modeling | scikit-learn, Surprise, LightFM, implicit, sentence-transformers |
| Optimization | Optuna |
| API Fetch | httpx (sync) |
| UI | Streamlit |
| Testing | pytest |
| Visualization | matplotlib, seaborn, plotly |

## 9. Architectural Notes
- Modular source under `src/` (`data`, `features`, `models`, `eval`).
- Separation of raw vs processed vs interim directories for clear lineage.
- Metadata enrichment independent from rating ingestion; join by `anime_id` planned.
- Future: persistent feature store (parquet) for embeddings & precomputed user-item scores.

## 10. Quality & Data Health Plans
- Data catalog updated after each major snapshot.
- Validation scripts (to add) will check: missing critical fields (`title_primary`, `episodes`, `mal_score`).
- Null handling strategy: impute or sentinel for modeling; preserve raw nulls for catalog.

## 11. Risk Log (Active)
| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| API quota exhaustion | Incomplete metadata | Throttle + backoff + cache | Monitoring |
| Metadata schema drift | Inconsistent fields | Version snapshots + catalog updates | Ongoing |
| Long-run interruption | Wasted hours | Checkpoints + resumes | Mitigated |
| Unicode issues on Windows | Script crashes | UTF-8 enforced | Resolved |

## 12. Metrics To Track (Upcoming)
- Coverage: % of anime IDs enriched.
- Freshness: Average age of `retrieved_at` timestamps.
- Modeling: Baseline RMSE / MAP@K / NDCG@K.
- Engagement: Distinct users, rating sparsity metrics.

## 13. Environment Rehydration Cheatsheet
After cloning/fresh session:
1. Install dependencies: `pip install -r requirements.txt`
2. Verify raw data presence under `data/raw/`.
3. If enrichment incomplete, re-run `fetch_jikan.py` with same suffix to resume.
4. Run tests: `pytest -q`.

## 14. Glossary (Quick)
| Term | Meaning |
|------|---------|
| MAL | MyAnimeList (source of Jikan data) |
| Enrichment | Adding current metadata to static rating snapshot |
| Snapshot suffix | Version marker for parquet file (`anime_metadata_<suffix>.parquet`) |
| Hybrid model | Combines CF, content embeddings, popularity signals |

## 15. Update Protocol
When a significant event occurs (decision, phase change, major artifact creation):
1. Append to relevant table (Decisions, Risk, Data Assets).
2. Update last updated date at top.
3. Keep entries succinct (1–2 lines per row).

---
### Quick Session Summary (Rolling)
- 2025-11-09: Enrichment running; encoding + datetime fix applied.
- 2025-11-10: Full enrichment completed; catalog updated; Phase 1 marked COMPLETE.
- 2025-11-13: EDA fixed for genres/themes (stored as numpy arrays); saved `anime_metadata_normalized.parquet`.
- 2025-11-14: Phase 2 pipeline completed; artifacts saved; TF-IDF vectorizer persisted. Wrap-up: user features, indices, scaling stats, quality slices, versions manifest; discovery/fetch enhancements; title variants stored. Tag parsing fix applied for list-like metadata; TF-IDF now 1,170 features on 13,037 items. LightFM baseline trainer added.

(Replace or append daily summaries; keep last 5 only.)

---
## 16. Next Trigger
Begin Phase 3: implement baselines (popularity, TF-IDF/embeddings similarity) and CF models (Surprise KNN/SVD), then hybridization.

---
End of running context.
