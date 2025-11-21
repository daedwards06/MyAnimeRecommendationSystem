# Running Context (Live Project Snapshot)

Last updated: 2025-11-21

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
| 3 | Baseline recommenders (CF/content + hybrid tuning) | COMPLETE |
| 4 | Evaluation & analysis (plots, ablations, explanations, temporal check, CI) | KICKOFF / IN PROGRESS |
| 5 | App development (Streamlit UI, inference, explainability surfacing) | Pending |
| 6 | Documentation & portfolio polish | Pending |

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

## 5. Phase 3 Summary (Closed) & Transition
- Status: Phase 3 closed (2025-11-21). All baseline CF/content models implemented; hybrid recommender tuned with diversity-aware objective; artifacts versioned.
- Final hybrid weights (balanced accuracy + coverage) frozen in `src/models/constants.py`: mf=0.93078, knn=0.06625, pop=0.00297.
- Item kNN remains low-performing on ranking metrics but contributes to hybrid diversity marginally.
- Diversity-aware Optuna tuning applied (coverage reward + popularity cap) to counter prior popularity-heavy blend.
- Final unified slice metrics (K=10, users=1000):
	- MF (FunkSVD): NDCG≈0.05036, MAP≈0.03900, Coverage≈0.071
	- Hybrid Weighted (balanced): NDCG≈0.04973, MAP≈0.03844, Coverage≈0.066, Gini≈0.791
	- Popularity: NDCG≈0.04120, Coverage≈0.006
	- Item kNN: Coverage leader (≈0.118) but weak NDCG.
- Artifacts saved with UTC-aware timestamps via `scripts/save_artifacts.py`; manifest updated.
- Report updated (`reports/phase3_summary.md`) with final metrics table and historical snapshots retained for provenance.

How to regenerate current metrics (PowerShell):
```powershell
python .\scripts\evaluate_hybrid.py --k 10 --sample-users 1000
python .\scripts\update_phase3_report.py
python .\scripts\save_artifacts.py
```

## 6. Near-Term Tasks (Phase 4 Evaluation & Analysis Kickoff)
1. Plot curves: NDCG/MAP vs K (baseline vs hybrid vs MF vs popularity).
2. Coverage & Gini trend plot vs K.
3. Ablation table (MF vs Hybrid vs Popularity vs Content TF-IDF) with relative lifts.
4. Temporal split experiment (optional leakage check).
5. Add lightweight CI (tests + ruff/black) and lint badges.
6. Integrate explanation examples into report (top 3 items with per-source contributions).

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
- 2025-11-15: Phase 3 started; kNN improved (centering, shrinkage, popularity prior), MF stable; hybrid evaluator created.
- 2025-11-17: Initial hybrid tuning produced popularity-heavy blend (low coverage); diversity metrics integrated.
- 2025-11-21: Diversity-aware Optuna tuning finalized; balanced hybrid weights frozen; artifacts versioned; Phase 3 closed.

(Replace or append daily summaries; keep last 5 only.)

---
## 16. Phase 4 Tracking & Next Trigger
Progress checklist (core):
- [ ] Metric curves (NDCG/MAP vs K)
- [ ] Coverage & Gini curves vs K
- [ ] Ablation table (Popularity vs MF vs Hybrid vs Content TF-IDF) with lifts
- [ ] Explanation examples integrated (top 3 hybrid items per-source shares)
- [ ] Temporal split validation
- [ ] CI + lint (tests + ruff/black) green

Next trigger: Once all core items checked, create Phase 4 evaluation report (`reports/phase4_evaluation.md`) and transition to initial Streamlit scaffolding (Phase 5).

---
End of running context.
