# Running Context (Live Project Snapshot)

Last updated: 2025-11-10

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
| 2 | Cleaning & feature engineering | Pending |
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

Latest enrichment snapshot suffix: `202511_full` (completed).
Rows: 12,297 | Columns: 18 | 404 missing IDs: see fetch counters (logged at runtime).
Checkpoint interval used: 300 IDs. Throttle: 0.70s + jitter.

## 4. Key Decisions & Rationale
| Decision | Rationale | Date |
|----------|-----------|------|
| Keep Kaggle ratings static | Ensures reproducibility for benchmarks & comparisons | 2025-11-08 |
| Enrich with current Jikan metadata | Adds freshness (updated genres, scores, status) | 2025-11-08 |
| Use cached JSON + periodic checkpoints | Avoid refetch & survive long-run interruption | 2025-11-09 |
| Switch to UTC aware datetimes | Future-proof against deprecation & ambiguous timezones | 2025-11-09 |
| Force UTF-8 for cache files | Prevent Windows cp1252 encode errors on synopsis text | 2025-11-09 |

(Add new rows as decisions occur.)

## 5. Current Phase Deep Dive (Phase 1)
- Status: Enrichment complete; metadata snapshot finalized.
- Achieved: 12,297 records processed; null distribution captured in catalog.
- Residual Risks: Score/rank nulls for unreleased or unrated titles; large aired_to null count for ongoing shows.
- Next: Transition to Phase 2 (cleaning & feature engineering).

## 6. Near-Term Tasks (High Priority Queue)
1. Finish enrichment run & verify parquet row count matches unique IDs fetched.
2. Update `docs/data_catalog.md` with actual dtypes, null counts, row counts.
3. Add initial EDA notebook: distribution of genres, episodes, MAL score vs popularity.
4. Define feature lists (content embeddings, interaction stats) concretely in `docs/features.md`.
5. Implement preliminary CF baseline (Surprise SVD / KNNBasic) using ratings.

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

(Replace or append daily summaries; keep last 5 only.)

---
## 16. Next Trigger
Begin Phase 2: implement cleaning refinements and generate first feature matrices (genres multi-hot, preliminary embeddings stub).

---
End of running context.
