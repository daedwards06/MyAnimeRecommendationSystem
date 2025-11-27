Last updated: 2025-11-26 (Phase 5 UX refinement + type filter debugging)

## 19. Multi-Seed Recommendations Bug Fixes & Type Filter Debugging (2025-11-26)
**Critical Bug Fixes**:
- **Genre Parsing Bug**: Multi-seed recommendations returned zero results despite debug script showing they should work
  - Root cause: Code assumed genres stored as pipe-delimited strings but data stored as numpy arrays
  - Solution: Added dual format handling for both string and array genres in multi-seed logic
  - Impact: Tokyo Ghoul + Death Note multi-seed now returns ~50 recommendations

- **Match Percentage Normalization**: Weighted overlap scores >1.0 broke percentage display
  - Root cause: Raw weighted overlap not normalized to 0-1 range
  - Solution: `weighted_overlap = raw_overlap / max_possible_overlap`
  - Impact: Match percentages now display correctly (76% vs incorrect 23%)

- **Quality Filter Issue**: Filter removing all recommendations after genre parsing fix
  - Solution: Removed quality filter entirely (no longer needed with correct genre parsing)
  - Impact: Recommendations now appear consistently

**Type Differentiation Feature**:
- Added `type` field to Jikan fetch script (TV, Movie, OVA, Special, ONA, Music, TV Special, CM, PV)
- Implemented type filter UI (multi-select in sidebar with 9 type options)
- Type filter logic with NaN handling: `pd.notna(item_type) and str(item_type).strip() in type_filter`
- **Type Filter Bug FIXED** (2025-11-26):
  - **Root Cause #1**: Browse mode completely omitted type filter logic (only applied genre + year filters) - FIXED
  - **Root Cause #2**: Recommendation mode genre filter had incorrect numpy array handling (broke filter order) - FIXED
  - **Root Cause #3 (ACTUAL BUG)**: `type` column was missing from `MIN_METADATA_COLUMNS` in artifact loader, so it was being dropped during metadata pruning
  - **Solution**: Added `"type"` to `MIN_METADATA_COLUMNS` in `src/app/constants.py`
  - **Impact**: Type filter now works correctly in both browse and recommendation modes
  - Debug logging removed after successful fix verification

**Image Path Restoration**:
- All 12,923 thumbnail images disappeared from metadata after fetch_jikan.py run
- Root cause: fetch_jikan.py rewrites entire parquet file, losing enriched columns not in FIELDS
- Solution: Ran `enrich_images.py --repair-from-files --repair-only` to restore paths from disk
- Impact: 12,183 thumbnail paths recovered from filesystem scan

**Data Format Discoveries**:
- Type data coverage: 12,182/13,037 anime (93.4%)
- Type distribution: TV (3,752), OVA (3,271), Movie (2,337), Special (1,123), ONA (611), Music (479), TV Special (449), CM (117), PV (43)
- Genre format: Stored as numpy arrays requiring `hasattr(genres, '__iter__')` checks
- Type format: Simple string values, requires NaN handling before filtering

**Verification Complete (2025-11-26)**:
- ✅ Type filter now working correctly in both browse and recommendation modes
- ✅ Tested with Sci-Fi + Movie filter - correctly excludes non-movie types
- ✅ Items with type=None properly excluded when filter active
- ✅ All debug logging removed after successful fix
- ✅ Filter quantity fix: Recommendations now request 5x items when filters active, then trim to top N after filtering (ensures full N results)
- ✅ Type display added to cards: Shows type (TV, Movie, OVA, etc.) in both list and grid views alongside MAL score

## 18. Phase 5 UX Refinement Session (2025-11-26)
Major bug fixes and feature enhancements:

**Card Rendering Architecture Fix**:
- **Problem**: Empty/partially empty boxes appearing above all recommendations in both list and grid views
- **Root Cause**: Manual HTML `<div>` tags created via `st.markdown()` incompatible with Streamlit's native `st.image()` component—images rendered outside the div context, leaving empty boxes
- **Solution**: Replaced all manual `<div>` wrappers with `st.container(border=True)` for proper component wrapping
- **Impact**: Clean card rendering with proper borders, no visual artifacts

**Genre Filter Implementation**:
- **Problem**: Genre filter dropdown showing "No options to select" despite 13K+ anime with genre data
- **Root Cause**: Metadata stores genres as numpy arrays (e.g., `['Action' 'Adventure']`), not pipe-delimited strings; code only checked `isinstance(genres_val, str)`
- **Solution**: Added array format handling: `elif hasattr(genres_val, '__iter__') and not isinstance(genres_val, str): all_genres.update([str(g).strip() for g in genres_val if g])`
- **Impact**: Genre filter now shows 40+ unique genres (Action, Adventure, Comedy, Drama, etc.)

**Browse by Genre Mode**:
- **Feature**: New standalone catalog browsing mode independent of recommendation engine
- **Implementation**:
  - Checkbox toggle "📂 Browse by Genre" in sidebar Sort & Filter section
  - When enabled + genres selected: filters `metadata` DataFrame directly by genre + year range
  - Bypasses recommendation computation entirely for faster performance
  - Results sorted by selected criteria (MAL Score, Year, Popularity)
  - Limited to Top N slider value for UI performance
- **UI Changes**: Shows "📚 Browsing X anime" vs "✨ Showing X Recommendations"
- **Use Case**: Explore catalog without needing seed anime; discover titles by genre/year filters

**Synopsis Display Enhancement**:
- **Problem**: Synopsis not displaying on cards after multiple fix attempts
- **Investigation**: Created diagnostic script to inspect metadata columns—found only single `synopsis` column (no `synopsis_snippet` or `synopsis_full`)
- **Solution Chain**:
  1. Confirmed `synopsis` column contains full text (~700 chars average)
  2. Added proper pandas NaN handling: `if synopsis_val is not None and pd.notna(synopsis_val)`
  3. Removed expander complexity—now displays full synopsis directly via `st.caption()`
- **Impact**: Full anime descriptions visible immediately on all cards

**Data Format Discoveries** (important for future development):
- **Genres**: Stored as numpy arrays, not strings (requires `hasattr` checks + iteration)
- **Synopsis**: Single `synopsis` column only (~700 char full text)
- **Images**: `poster_thumb_url` column, 12,923/13,037 coverage (99.1%)
- **Aired From**: String format "YYYY-MM-DD", extract year via `[:4]`

**Filter & Sort Infrastructure**:
- Genre multi-select: 40+ options, properly extracted from array format
- Year range slider: 1960-2025, filters in both recommendation and browse modes
- Sort options: Confidence, MAL Score, Year (Newest/Oldest), Popularity
- Reset filters button: Clears all selections, resets to defaults
- Filter info display: Shows active filters in results heading (e.g., "3 genres, 2000-2020")

Next priorities: Performance profiling display, unit tests for new features, deployment preparation.

## 17. Phase 5 Progress Snapshot (2025-11-25)
Implemented:
- Artifact loader integrated with pruned metadata and restored thumbnail column.
- Query param API migration (deprecated experimental functions removed).
- **Image Quality Upgrade**: Large Jikan images (425x600px vs 225x318px) for sharper thumbnails; 12,919 images refreshed.
- **English Title Priority**: Dropdown and cards now prefer English titles (e.g., "Blood Blockade Battlefront" over "Kekkai Sensen"); shows original/Japanese as subtitle.
- Searchable title dropdown (13K+ titles) replacing free text input with title-to-ID mapping.
- Seed selection with green banner indicator + clear button.
- Sample search suggestions (4 popular titles) in empty state.
- **Comprehensive Metadata Cards**:
  - ⭐ Color-coded MAL score (green/blue/gray by rating)
  - 📺 Episode count for watch planning
  - 📅 Release year from aired_from
  - ✅/🟢/🔵 Status indicators (Finished/Airing/Not Yet)
  - 🎬 Studio names (up to 2, with "+X more")
  - Source material type
  - 🎬 **Streaming platform badges** (Crunchyroll, Netflix, etc.) with clickable URLs
- Visual card redesign: colored borders, inline badge pills with icons, proper spacing.
- Badge tooltips component explaining cold-start, popularity, novelty.
- Explanation panel component showing top-5 MF/kNN/Pop breakdowns.
- Simplified inline explanations (human-friendly summaries) with technical expanders.
- Progress spinner, result count heading, visual diversity summary bar (Popular/Balanced/Exploratory).
- Confidence star ratings (1-5 ⭐) per recommendation card.
- Smart synopsis truncation with expandable full text section.
- Fixed seed similarity indentation bug.

Pending (near-term):
- Latency/memory profiling display (<250ms / <512MB targets).
- Unit tests (search, badges, explanations).
- Deployment to Streamlit Cloud/HF Spaces + screenshots + README update.
- Optional: Genre filters, sort options (by score/year/popularity), year range slider.

Stretch (deferred): ANN index; favorites/watchlist; dark mode; feedback logging; multi-select seeds.

Risks addressed: Blurry images (large image URLs), missing English titles (prioritization logic), image codec issues (st.image()), synopsis truncation (expandable section), seed logic error (indentation fix).

### Quick Session Summary (Rolling — last 5 entries)
- 2025-11-23: Phase 5 scaffold started (query params migration, image diagnostics, onboarding design).
- 2025-11-24 (morning): Seed similarity refinement, sidebar Quick Steps, title fallback, synopsis truncation.
- 2025-11-24 (afternoon): Visual card redesign, searchable dropdown, badge tooltips, explanation panel, progress indicators, diversity bar, confidence stars.
- 2025-11-25: Image quality upgrade (large URLs), English title priority, comprehensive metadata display (MAL score, episodes, year, status, studios, streaming platforms).
- 2025-11-26: Card rendering fix (st.container), genre filter fix (array handling), Browse by Genre mode, synopsis display fix, filter/sort infrastructure complete.
Ready for git tag `phase5-ux-refined`; performance profiling and deployment prep next.

### 2025-11-25 Update (Phase 5 Feature-Complete)
- Metadata richness dramatically improved: score, episodes, year, status, studios, streaming links.
- Image quality significantly enhanced (2x resolution source).
- English title discovery vastly improved.
- Next: performance audit (surface latency/memory) → tests → deploy.
# Running Context (Live Project Snapshot)

Last updated: 2025-11-22 (Phase 4 completion)

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
| 4 | Evaluation & analysis (plots, ablations, explanations, temporal check, CI) | COMPLETE (2025-11-22) |
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
## 16. Phase 4 Summary & Transition
Completed artifacts:
- Metric curves (NDCG@K, MAP@K) + diversity curves (Coverage@K, Gini@K)
- Ablation table (Popularity vs MF vs Hybrid vs Content TF-IDF) w/ relative lifts
- Hybrid explanation examples (default + alternate diversity-emphasized weights)
- Temporal split validation (synthetic ordering; stability confirmed)
- Genre exposure ratio JSON + bar plot; novelty/popularity bias plot
- Accessibility upgrades (colorblind-safe palette, alt text references)
- CI workflow + pre-commit hooks; targeted tests (lift edge case & JSON sanitization)

Artifacts locations:
- `reports/figures/phase4/` (curves, genre_exposure_ratio.png, novelty_bias.png)
- `reports/artifacts/genre_exposure.json`, `reports/artifacts/novelty_bias.json`
- `experiments/metrics/hybrid_explanations.json`, `experiments/metrics/hybrid_explanations_alt.json`
- `reports/phase4_evaluation.md` (central narrative)

Phase 5 Focus (up next): Streamlit UI (recommendations + explanations), diversity/novelty badges, cold-start labeling, artifact loader integration, deployment.

---
End of running context.
---
### 2025-11-22 Update (Phase 4 Completion)
- Generated metric & diversity plots, ablation table, explanations (default + alt weights).
- Added genre exposure & novelty bias artifacts (fairness/diversity narrative).
- Temporal split robustness confirmed; synthetic timestamp strategy documented.
- CI + pre-commit operational; tests added for JSON and lift logic.
- Evaluation report enriched with methodology, accessibility notes, and diversity section.
- Ready for git tag `phase4-complete` and Phase 5 app scaffolding.
