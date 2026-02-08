# MARS Improvement Plan

> Generated: 2026-02-07 | Based on comprehensive codebase audit  
> Target executor: Claude Sonnet 4.5 via Copilot agent mode  
> Estimated total effort: 5 phases, ~15-20 focused sessions

---

## Table of Contents

1. [Phase 1: Architecture & Testability (P0)](#phase-1-architecture--testability-p0)
2. [Phase 2: Recommendation Quality & Honesty (P1)](#phase-2-recommendation-quality--honesty-p1)
3. [Phase 3: Portfolio Presentation (P1)](#phase-3-portfolio-presentation-p1)
4. [Phase 4: UX & App Polish (P2)](#phase-4-ux--app-polish-p2)
5. [Phase 5: Code Hygiene & Hardening (P3)](#phase-5-code-hygiene--hardening-p3)

---

## Phase 1: Architecture & Testability (P0)

**Goal:** Extract the scoring pipeline from the 3,067-line `app/main.py` monolith into testable pure-Python modules, and add CI.

### Task 1.1: Extract Scoring Pipeline into `src/app/scoring_pipeline.py`

**Why:** The entire Stage 0 → Stage 1 → Stage 2 → post-processing pipeline currently lives inline inside `app/main.py` (approximately lines 1574–2530), interleaved with `st.session_state` reads and Streamlit widget calls. This makes the core ranking logic impossible to unit-test without mocking Streamlit, and signals poor decomposition to portfolio reviewers.

**Checklist:**
- [x] Create `src/app/scoring_pipeline.py` with a pure-data `ScoringContext` dataclass and a `run_seed_based_pipeline()` function
- [x] Create `src/app/scoring_pipeline.py` with a `run_personalized_pipeline()` function
- [x] Move Stage 0 orchestration call (candidate pool construction) into the pipeline module
- [x] Move Stage 1 shortlist loop (genre overlap, semantic similarity, type gates, pool assignment) into the pipeline module
- [x] Move Stage 1 confidence gating and `build_stage1_shortlist()` call into the pipeline module
- [x] Move Stage 2 reranking loop (hybrid CF, popularity boost, semantic bonuses/penalties, obscurity penalty, final score formula) into the pipeline module
- [x] Move post-score processing (franchise cap, personalization blend, post-filters) into the pipeline module
- [x] Create a `PipelineResult` dataclass returned by the pipeline (ranked items, diagnostics, diversity stats, timing)
- [x] Update `app/main.py` to call the pipeline module instead of inline logic
- [x] Verify the app produces identical output before/after refactor by manual comparison on 3+ seed queries
- [x] Ensure no `import streamlit` appears in `src/app/scoring_pipeline.py`

**Prompt for Claude Sonnet 4.5:**

```
I need to extract the scoring pipeline from app/main.py into a pure-Python module src/app/scoring_pipeline.py. This is the most important refactoring task for my project.

CONTEXT:
- app/main.py is 3,067 lines and contains the entire recommendation pipeline inline
- The scoring pipeline spans approximately lines 1574-2530 of app/main.py
- It has 3 stages: Stage 0 (candidate generation), Stage 1 (shortlist construction with semantic admission), Stage 2 (reranking with final score formula)
- Post-processing includes franchise cap, personalization blending, and display filters
- Currently the pipeline reads from st.session_state and calls Streamlit widgets inline

REQUIREMENTS:
1. Create src/app/scoring_pipeline.py with:
   - A @dataclass ScoringContext that holds ALL inputs the pipeline needs (seed_ids, metadata DataFrame, model artifacts, weights, user_embedding, personalization_strength, watched_ids, filters, etc.) — replacing all st.session_state reads
   - A @dataclass PipelineResult that holds ALL outputs (ranked_items list[dict], stage0_diagnostics, stage1_diagnostics, diversity_stats, timing_dict, any warnings/messages)
   - A function run_seed_based_pipeline(ctx: ScoringContext) -> PipelineResult that contains the full Stage 0 → 1 → 2 → post-processing flow
   - A function run_personalized_pipeline(ctx: ScoringContext) -> PipelineResult for the personalized-mode path
   - A function run_browse_pipeline(ctx: ScoringContext) -> PipelineResult for the browse/filter path

2. CRITICAL CONSTRAINT: src/app/scoring_pipeline.py must NOT import streamlit. All Streamlit interaction stays in app/main.py. The pipeline module must be pure computation.

3. Update app/main.py to:
   - Build a ScoringContext from session state and sidebar widget values
   - Call the appropriate pipeline function
   - Unpack PipelineResult for rendering

4. The refactored code must produce IDENTICAL recommendations for the same inputs. Do not change any scoring logic, weights, thresholds, or formulas — only move them.

5. Add a module docstring to scoring_pipeline.py explaining the 3-stage architecture.

Start by reading app/main.py lines 1500-2600 to understand the full pipeline, then read the existing helper modules it calls (stage0_candidates.py, stage1_shortlist.py, stage2_overrides.py, metadata_features.py, synopsis_tfidf.py, synopsis_embeddings.py, synopsis_neural_embeddings.py) to understand the interface contracts. Then implement the extraction.
```

---

### Task 1.2: Add Integration Tests for the Extracted Pipeline

**Why:** The extracted pipeline can now be tested with pure data fixtures — no Streamlit mocking required. This is the highest-value test coverage we can add.

**Checklist:**
- [x] Create `tests/test_scoring_pipeline.py`
- [x] Add a `mock_scoring_context()` fixture that builds a minimal ScoringContext with tiny synthetic data (5-10 anime, 2-3 users, small factor matrices)
- [x] Test: `run_seed_based_pipeline` returns non-empty results for valid seed
- [x] Test: `run_seed_based_pipeline` returns empty results for seed not in metadata
- [x] Test: results are sorted by score descending
- [x] Test: seed anime IDs are excluded from results
- [x] Test: watched IDs are excluded from results
- [x] Test: genre filter restricts output genres
- [x] Test: type filter restricts output types
- [x] Test: year range filter restricts output years
- [x] Test: `run_personalized_pipeline` returns results when user_embedding is valid
- [x] Test: `run_personalized_pipeline` raises/returns empty when user_embedding is None
- [x] Test: franchise cap limits same-franchise entries in top-20
- [x] Test: `PipelineResult.timing` contains expected keys
- [x] Test: deterministic — same inputs produce same outputs across 3 runs

**Prompt for Claude Sonnet 4.5:**

```
I just extracted the scoring pipeline into src/app/scoring_pipeline.py (Task 1.1). Now I need comprehensive integration tests.

CONTEXT:
- src/app/scoring_pipeline.py exports: ScoringContext, PipelineResult, run_seed_based_pipeline(), run_personalized_pipeline(), run_browse_pipeline()
- The pipeline depends on: metadata DataFrame, MF model (with P, Q, item_to_index, index_to_item), kNN model, synopsis artifacts, neural artifacts
- Tests should use SMALL synthetic data (5-10 anime, tiny factor matrices) — not real model files

REQUIREMENTS:
1. Create tests/test_scoring_pipeline.py

2. Build a comprehensive mock_scoring_context() pytest fixture that:
   - Creates a small metadata DataFrame (8-10 anime with realistic columns: anime_id, title_display, genres, type, episodes, aired_from, mal_score, members_count, themes, demographics, studios, synopsis_snippet)
   - Creates a MockMFModel with 3 users × 10 items, n_factors=8, with P, Q, item_to_index, index_to_item, global_mean attributes
   - Creates a MockKNNModel or sets knn=None (kNN is 7% weight so can be None for most tests)
   - Sets synopsis/neural artifacts to None (content signals will be zero — that's fine for integration)
   - Returns a ScoringContext with sensible defaults

3. Write these specific tests:
   a. test_seed_pipeline_returns_results — seed=[anime_id 1], expect non-empty results
   b. test_seed_excluded_from_results — seed anime_id must not appear in output
   c. test_watched_excluded — watched_ids={2,3} must not appear in output
   d. test_results_sorted_by_score — score[i] >= score[i+1] for all i
   e. test_genre_filter — genre_filter=["Action"], all results must contain "Action"
   f. test_type_filter — type_filter=["TV"], all results must have type="TV"
   g. test_year_range_filter — year_min=2010, year_max=2020, all results in range
   h. test_personalized_with_valid_embedding — generate a user_embedding, expect results
   i. test_personalized_without_embedding — user_embedding=None, expect empty or error
   j. test_deterministic — run 3 times with same input, assert identical output
   k. test_pipeline_result_has_timing — check timing dict has expected keys
   l. test_top_n_respected — top_n=3, assert len(results) <= 3

4. Each test should be self-contained and fast (<100ms).

5. Add clear docstrings explaining what each test verifies.
```

---

### Task 1.3: Add GitHub Actions CI

**Why:** A green CI badge is instant portfolio credibility. It proves tests pass, and prevents regressions.

**Checklist:**
- [x] Create `.github/workflows/ci.yml`
- [x] Configure: Python 3.11, pip install from requirements.txt, run `pytest -x -q`
- [x] Set `APP_IMPORT_LIGHT=1` environment variable (avoids loading real model artifacts in CI)
- [x] Add pytest badge to README.md
- [x] Verify all 64+ existing tests pass in CI
- [x] Add a `make ci` target to Makefile that mirrors the CI steps locally

**Prompt for Claude Sonnet 4.5:**

```
I need to add GitHub Actions CI to my anime recommendation project.

CONTEXT:
- Python 3.11 project with requirements.txt
- 18 test files, 64+ tests under tests/
- pytest.ini is configured: testpaths = ["tests"], norecursedirs for data/models/reports
- Environment variable APP_IMPORT_LIGHT=1 must be set to avoid loading real model artifacts (which aren't in the repo)
- Models (.joblib files) and large data files are .gitignored — CI cannot depend on them
- The project uses: pandas, numpy, scikit-learn, joblib, rapidfuzz, streamlit (but tests don't need streamlit running)

REQUIREMENTS:
1. Create .github/workflows/ci.yml that:
   - Triggers on push to main and on pull requests
   - Uses Python 3.11
   - Caches pip dependencies
   - Installs requirements.txt
   - Sets APP_IMPORT_LIGHT=1
   - Runs: pytest -x -q --tb=short
   - Has a meaningful job name like "test"

2. Add a Makefile target `ci` that runs the same steps locally:
   ```
   ci:
       APP_IMPORT_LIGHT=1 pytest -x -q --tb=short
   ```

3. Add a pytest/CI status badge to the top of README.md, right after the title line. Use the standard GitHub Actions badge format:
   ![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)
   Use a placeholder for <owner>/<repo> that I can replace.

4. Verify there are no test files that would fail without real model artifacts by checking for any tests that import from artifacts_loader or load .joblib files directly — list them so I can review.
```

---

### Task 1.4: Extract Constants from Inline Scoring Formula

**Why:** The final scoring formula at ~L2200 of main.py mixes hardcoded numbers (`0.3`, `0.1`, `0.15`, `0.05`, `1.5`, `-0.25`, etc.) with imported constants. A reviewer will ask "how were these tuned?" Moving them to named constants with comments makes the formula auditable.

**Checklist:**
- [x] Add all scoring formula weights to `src/app/constants.py` with descriptive names and docstring comments
- [x] Add all penalty thresholds (obscurity penalty, quality factor bounds) to constants
- [x] Replace all inline magic numbers in the scoring formula with constant references
- [x] Add a block comment above each constant group explaining the rationale (e.g., "Tuned via Optuna Phase 4 ablation study — see reports/phase4_ablation.md")
- [x] Verify recommendations are identical after the swap

**Prompt for Claude Sonnet 4.5:**

```
I need to extract all magic numbers from the scoring formula in my recommendation pipeline into named constants.

CONTEXT:
- The scoring formula is in the scoring pipeline (previously in app/main.py ~L2200, now extracted to src/app/scoring_pipeline.py if Task 1.1 is done, otherwise still in app/main.py)
- Constants should go in src/app/constants.py which already exists and has similar constants
- The final score formula currently looks approximately like:
  score = 0.3 * genre_overlap + 0.1 * seed_coverage + 0.15 * hybrid_cf + 0.05 * pop_boost + 0.10 * stage1_score + 1.5 * neural_sim * quality_factor + bonuses - penalties
- Additional magic numbers in the obscurity penalty: members_count < 50000 → -0.25, missing MAL → -0.15, MAL < 7.0 → scaled -0.20
- Quality factor: clamp((mal_score - 5) / 4, 0.15, 1.0)

REQUIREMENTS:
1. Add these named constants to src/app/constants.py with descriptive names:

   # Stage 2 Final Score Weights (tuned via Phase 4 ablation — see reports/phase4_ablation.md)
   STAGE2_GENRE_OVERLAP_WEIGHT = 0.3
   STAGE2_SEED_COVERAGE_WEIGHT = 0.1
   STAGE2_HYBRID_CF_WEIGHT = 0.15
   STAGE2_POPULARITY_BOOST_WEIGHT = 0.05
   STAGE2_STAGE1_SCORE_WEIGHT = 0.10
   STAGE2_NEURAL_SIM_WEIGHT = 1.5

   # Quality Factor (scales neural similarity by MAL consensus)
   QUALITY_FACTOR_MAL_FLOOR = 5.0
   QUALITY_FACTOR_MAL_RANGE = 4.0
   QUALITY_FACTOR_MIN = 0.15
   QUALITY_FACTOR_MAX = 1.0

   # Obscurity Penalty
   OBSCURITY_MEMBERS_THRESHOLD = 50000
   OBSCURITY_LOW_MEMBERS_PENALTY = 0.25
   OBSCURITY_MISSING_MAL_PENALTY = 0.15
   OBSCURITY_LOW_MAL_THRESHOLD = 7.0
   OBSCURITY_LOW_MAL_PENALTY_SCALE = 0.20

2. Replace all corresponding inline numbers in the scoring formula with these constants.

3. Add a block docstring at the top of the constants section explaining the rationale:
   "Stage 2 weights were tuned via grid search during Phase 4 ablation (reports/phase4_ablation.md).
    Obscurity penalties prevent low-quality/obscure items from ranking above genre-relevant alternatives.
    Quality factor biases neural similarity toward community-validated titles."

4. Do NOT change any values — only move them from inline to named constants. Verify the formula computes identically.
```

---

## Phase 2: Recommendation Quality & Honesty (P1)

**Goal:** Fix the two biggest recommendation quality issues — the fake CF baseline and the quality factor bias.

### Task 2.1: Replace Demo User CF Baseline with Mean-User Vector

**Why:** When no personalization is active, the system uses `P[0]` (the first user in the MF training set) as the collaborative filtering signal. This means "collaborative filtering contribution" in seed-based mode is actually one random stranger's preferences. A reviewer who understands CF will immediately question this.

**Checklist:**
- [x] Compute `mean_user_vector = P.mean(axis=0)` during artifact loading in `src/app/artifacts_loader.py`
- [x] Store as `bundle["models"]["mf_mean_user"]`
- [x] In the scoring pipeline, use the mean-user vector when `personalization_enabled=False`
- [x] Add a constant `USE_MEAN_USER_CF = True` to constants.py (allows toggling back)
- [ ] Compare seed-based recommendations before/after on 5 golden queries — document any changes in a brief note
- [x] Update the `HybridRecommender._blend()` docstring to note the mean-user approach
- [x] Verify MF share percentages in explanation badges still sum to 100% and make sense

**Prompt for Claude Sonnet 4.5:**

```
I need to fix a recommendation quality issue: replace the "demo user" CF baseline with a mean-user vector.

CONTEXT:
- Currently, when no personalization is active, the system uses user_index=0 (the first user in the MF training set's P matrix) for collaborative filtering scores.
- This means the "MF 93%" share shown in explanations is actually one arbitrary user's preferences, not a meaningful signal.
- The MF model is a FunkSVD with P (users × factors) and Q (items × factors) matrices, stored as a joblib artifact.
- The model is loaded in src/app/artifacts_loader.py and stored in bundle["models"]["mf"].
- The hybrid recommender (src/app/recommender.py) calls self.c.mf[user_index] to get MF scores.

REQUIREMENTS:
1. In src/app/artifacts_loader.py, after loading the MF model:
   - Compute mean_user_P = mf_model.P.mean(axis=0) (shape: [n_factors])
   - Compute mean_user_scores = mf_model.global_mean + mean_user_P @ mf_model.Q.T (shape: [n_items])  
   - Store both in the bundle: bundle["models"]["mf_mean_user_vector"] = mean_user_P
     and bundle["models"]["mf_mean_user_scores"] = mean_user_scores

2. In the scoring pipeline (src/app/scoring_pipeline.py or app/main.py), when computing hybrid CF scores for seed-based (non-personalized) mode:
   - Instead of using recommender._blend(user_index=0, ...), use the precomputed mean_user_scores
   - This replaces the MF component only; kNN and popularity remain unchanged

3. Add USE_MEAN_USER_CF = True to src/app/constants.py with docstring:
   "When True, seed-based mode uses the mean of all training user vectors for CF contribution,
    rather than a single demo user (index 0). This makes the CF signal represent average community
    preferences instead of one arbitrary user's taste."

4. Update the HybridRecommender class or the pipeline to respect this toggle.

5. Do NOT change the personalized mode path — that correctly uses the user's own embedding.

Read src/app/artifacts_loader.py, src/app/recommender.py, and the scoring pipeline to understand the current flow before making changes.
```

---

### Task 2.2: Add Configurable Quality Factor with Niche-Friendly Option

**Why:** The current `quality_factor = clamp((MAL_score - 5) / 4, 0.15, 1.0)` scales neural similarity by MAL rating, which penalizes niche anime with MAL 6-7 that may be highly relevant. This conflates community consensus with personal relevance.

**Checklist:**
- [x] Add `QUALITY_FACTOR_MODE` constant with options: `"mal_scaled"` (current), `"binary"` (1.0 if MAL >= 6.0 else 0.5), `"disabled"` (always 1.0)
- [x] Implement all three modes in the scoring formula
- [x] Default to `"mal_scaled"` (preserve current behavior)
- [x] Run golden queries with all 3 modes and document which niche anime emerge/disappear
- [x] Add a brief comment in constants.py explaining the tradeoff

**Prompt for Claude Sonnet 4.5:**

```
I need to make the quality factor in my recommendation scoring formula configurable to reduce bias against niche anime.

CONTEXT:
- The current quality factor formula: quality_factor = max(0.15, min(1.0, (mal_score - 5) / 4))
- This scales neural similarity contribution: 1.5 * neural_sim * quality_factor
- Problem: A highly relevant niche anime with MAL 6.5 gets quality_factor=0.375, cutting its neural similarity contribution by 62%
- This biases the system toward popular consensus favorites and away from niche gems that might be more relevant to a specific seed query

REQUIREMENTS:
1. Add to src/app/constants.py:
   # Quality Factor Mode for neural similarity scaling
   # "mal_scaled" (default): quality = clamp((MAL - 5) / 4, 0.15, 1.0) — favors high-MAL titles
   # "binary": quality = 1.0 if MAL >= 6.0 else 0.5 — mild penalty only for very low-rated titles
   # "disabled": quality = 1.0 always — pure relevance, no quality gating
   QUALITY_FACTOR_MODE = _env_str("QUALITY_FACTOR_MODE", "mal_scaled")

2. Create a function compute_quality_factor(mal_score: float | None, mode: str) -> float in the scoring pipeline (or constants module) that implements all three modes.

3. Replace the inline quality_factor computation in the scoring formula with a call to this function.

4. Add a brief docstring explaining the tradeoff:
   "mal_scaled favors community-validated titles but penalizes niche; 
    binary is a gentler gate; disabled trusts semantic similarity fully."

5. Default must remain "mal_scaled" to preserve current behavior. The other modes are opt-in via environment variable.
```

---

### Task 2.3: Implement Graded Relevance for NDCG

**Why:** The eval module uses binary relevance (0/1) for NDCG, but the data has 1-10 ratings. Graded relevance is the standard in RecSys literature and makes the metric more informative.

**Checklist:**
- [ ] Add `ndcg_at_k_graded()` to `src/eval/metrics.py` that accepts a `ratings: dict[int, float]` instead of a `relevant: set[int]`
- [ ] Use gain = `2^rating - 1` (standard) or `rating` (linear) — make it configurable
- [ ] Update `evaluate_ranking()` to compute both binary and graded NDCG
- [ ] Add tests for the graded NDCG function in `tests/test_eval_metrics.py`
- [ ] Re-run evaluation scripts and update reported NDCG numbers

**Prompt for Claude Sonnet 4.5:**

```
I need to add graded relevance NDCG to my evaluation metrics module.

CONTEXT:
- src/eval/metrics.py currently has ndcg_at_k(ranked_list, relevant_set, k) with binary relevance (1 if item in relevant_set else 0)
- My data has 1-10 ratings, so graded relevance is more informative
- The standard in RecSys literature is to use gain = 2^rating - 1 for NDCG

REQUIREMENTS:
1. Add to src/eval/metrics.py:
   def ndcg_at_k_graded(
       ranked_list: list[int],
       item_ratings: dict[int, float],
       k: int,
       gain_fn: str = "exponential",  # "exponential" = 2^r - 1, "linear" = r
   ) -> float:
       """NDCG@K with graded relevance from explicit ratings.
       
       Args:
           ranked_list: Ordered list of recommended item IDs
           item_ratings: Dict mapping item_id -> rating (e.g., 1-10 scale)
           k: Cutoff position
           gain_fn: "exponential" for 2^rating - 1, "linear" for raw rating
       
       Returns:
           NDCG@K score in [0, 1]
       """

2. Update evaluate_ranking() to include ndcg_graded_at_k alongside existing ndcg_at_k for each K value.

3. Create tests/test_eval_metrics.py with:
   - test_ndcg_graded_perfect_ranking: items ordered by rating → NDCG = 1.0
   - test_ndcg_graded_reversed_ranking: items in reverse order → NDCG < 1.0
   - test_ndcg_graded_no_relevant: all items unrated → NDCG = 0.0
   - test_ndcg_graded_at_k_1: only top-1 matters
   - test_ndcg_graded_linear_vs_exponential: verify different gain functions produce different values
   - test_ndcg_graded_matches_binary_for_uniform_ratings: when all ratings are equal, graded NDCG should equal binary NDCG

4. Export the new function in __all__.
```

---

## Phase 3: Portfolio Presentation (P1)

**Goal:** Make the project sell itself to recruiters and hiring managers in 30 seconds.

### Task 3.1: Add Results Section to README with Concrete Metrics

**Why:** The README has extensive feature descriptions but zero numbers. A hiring manager scanning the README wants to see "NDCG@10 = 0.XX" immediately. This is the single highest-ROI change for portfolio impact.

**Checklist:**
- [ ] Run the full evaluation pipeline (`make phase4-artifacts` or equivalent)
- [ ] Collect key metrics: NDCG@10, MAP@10, Precision@10, Recall@10, Coverage, Gini Index
- [ ] Add a "## Results" section after "Key Features" in README.md
- [ ] Include a results table with metrics
- [ ] Add 1-2 sentences of interpretation (what the numbers mean)
- [ ] Include the hybrid weight breakdown (MF 93%, kNN 7%, Pop 0.3%)
- [ ] Reference the reports directory for detailed evaluation

**Prompt for Claude Sonnet 4.5:**

```
I need to add a Results section to my README.md to showcase evaluation metrics for portfolio reviewers.

CONTEXT:
- README.md is in the project root. The "Key Features" section is at the top.
- Evaluation reports exist in reports/ (phase4_evaluation.md, phase4_ablation.md, phase4_ablation.csv)
- The eval module computes: Precision@K, Recall@K, F1@K, NDCG@K, MAP@K, Coverage, Gini Index
- Hybrid weights: MF 93.08%, kNN 6.63%, Popularity 0.30% (from constants.py BALANCED_WEIGHTS)
- Training data: 73,515 users, 13,000+ anime (from the README and model docs)
- Models: FunkSVD (64 factors), Item-kNN (cosine), TF-IDF + SVD + Neural sentence embeddings

REQUIREMENTS:
1. Read the existing evaluation reports in reports/phase4_evaluation.md and reports/phase4_ablation.csv to extract real metric numbers. If they aren't available, read any metric output files in experiments/metrics/ or reports/.

2. Add a "## 📈 Results" section to README.md, positioned AFTER "Key Features" and BEFORE "Project structure". Include:

   ### Offline Evaluation
   | Metric | @5 | @10 | @20 |
   |--------|-----|------|------|
   | NDCG | X.XXX | X.XXX | X.XXX |
   | MAP | X.XXX | X.XXX | X.XXX |
   | Precision | X.XXX | X.XXX | X.XXX |
   | Recall | X.XXX | X.XXX | X.XXX |

   ### Beyond-Accuracy Metrics
   | Metric | Value |
   |--------|-------|
   | Catalog Coverage | XX.X% |
   | Gini Index | X.XXX |
   | Genre Exposure Ratio | X.XX |

   ### Model Architecture
   A brief 3-4 sentence summary: hybrid model, training data size, key architectural choices.

3. If exact metric values can't be found in reports, add placeholder values with a TODO comment and instructions to run the eval pipeline.

4. Add a sentence linking to detailed reports: "See [reports/](reports/) for detailed evaluation including ablation studies and golden query assessments."

5. Keep it concise — aim for 30-40 lines max. Recruiters scan, they don't read.
```

---

### Task 3.2: Add Architecture Diagram to README

**Why:** A visual diagram of the multi-stage pipeline is worth 1000 words for communicating system design.

**Checklist:**
- [ ] Create a Mermaid diagram showing: Data → Models → Stage 0 → Stage 1 → Stage 2 → UI
- [ ] Add it to README.md in the Results or Architecture section
- [ ] Include the key signal flows (MF, kNN, content-based, metadata)

**Prompt for Claude Sonnet 4.5:**

```
I need to add a Mermaid architecture diagram to my README.md showing the recommendation pipeline.

CONTEXT:
The pipeline has these stages:
1. Data Layer: anime_metadata.parquet (13K+ anime), user ratings (73K users), synopsis text
2. Model Training (offline): FunkSVD MF (64 factors), Item-kNN (cosine), TF-IDF vectorizer, SVD embeddings, Neural sentence embeddings (all-MiniLM-L6-v2)
3. Stage 0 - Candidate Generation: Neural top-K neighbors (primary), Metadata-strict overlap (confirmer), Popularity backfill (safety) → Pool of ~500 candidates
4. Stage 1 - Shortlist: Semantic admission (sim thresholds), Type/episode gates, Confidence gating → 600-item shortlist split into semantic pool A and metadata pool B
5. Stage 2 - Reranking: Hybrid CF score (0.93 MF + 0.07 kNN), Genre/theme/studio overlap, Synopsis similarity (3 modalities), Obscurity penalty, Quality-scaled neural → Final score
6. Post-Processing: Franchise cap, Personalization blend, Display filters (genre/type/year), Top-N selection
7. UI: Streamlit app with cards, badges, explanations, diversity panel

REQUIREMENTS:
1. Create a Mermaid flowchart (top-to-bottom) showing the pipeline with clear stage labels
2. Use subgraphs to group related components
3. Show the key signal flows (which signals feed into which stages)
4. Add it to README.md in a new "## 🏗️ Architecture" section after Results
5. Keep it readable — not every constant, just the high-level flow
6. Use ```mermaid code blocks (GitHub renders these natively)
```

---

### Task 3.3: Create a Compelling Project Screenshot / Demo GIF Note

**Why:** A screenshot or GIF of the app in action makes the README visually engaging.

**Checklist:**
- [ ] Add instructions in README for how to take a demo screenshot
- [ ] Add an `app/assets/` placeholder for a screenshot
- [ ] Add image reference in README: `![MARS Demo](app/assets/demo_screenshot.png)`
- [ ] Note: actual screenshot must be taken manually when app is running

**Prompt for Claude Sonnet 4.5:**

```
I need to add a demo screenshot section to my README.md.

REQUIREMENTS:
1. Add a "## 🖼️ Demo" section to README.md right after the title/description and before Key Features
2. Add an image reference: ![MARS Demo](app/assets/demo_screenshot.png)
3. Add a caption: "Seed-based recommendations for Steins;Gate showing match scores, explanations, and metadata"
4. Add a small HTML comment near the image tag: <!-- To update: run the app (streamlit run app/main.py), search for a popular title, take a screenshot, save to app/assets/demo_screenshot.png -->
5. Create an empty placeholder file app/assets/.gitkeep if the assets directory doesn't exist
6. Keep this section brief — 3-4 lines max.
```

---

## Phase 4: UX & App Polish (P2)

**Goal:** Make the app demo-friendly and fix user-facing rough edges.

### Task 4.1: Simplify First-Run Experience

**Why:** A portfolio reviewer will launch the app and have 60 seconds of patience. The first screen should show recommendations immediately, not an empty state requiring them to figure out seeds.

**Checklist:**
- [ ] Auto-populate a default seed (e.g., "Fullmetal Alchemist: Brotherhood") on first load
- [ ] Show recommendations immediately without requiring any user action
- [ ] Add a prominent "Try These" section with 4-6 popular anime as one-click seed buttons
- [ ] Ensure the onboarding text explains what they're seeing in one sentence
- [ ] Test: fresh session load should show recommendations within 3 seconds

**Prompt for Claude Sonnet 4.5:**

```
I need to improve the first-run experience of my Streamlit anime recommendation app so reviewers see results immediately.

CONTEXT:
- The app is in app/main.py (with scoring logic either inline or in src/app/scoring_pipeline.py)
- Currently, a fresh load shows an empty main area with instructions to select a seed
- The sidebar has "Try these popular titles" sample buttons, but they require two actions (click sample + wait)
- The app has 3 modes: Personalized, Seed-based, Browse
- Default mode on fresh load is "Seed-based"

REQUIREMENTS:
1. On very first load (no seeds selected, no query params, no profile), auto-set a default seed:
   - Default seed: "Fullmetal Alchemist: Brotherhood" (anime_id 5114, universally known)
   - Set it in session_state["selected_seed_ids"] and session_state["selected_seed_titles"] 
   - Only on FIRST load — check a flag like session_state.get("_first_load_done", False)
   - After setting the initial seed, set session_state["_first_load_done"] = True

2. Add a visible banner above the results: 
   "🎬 Showing recommendations based on **Fullmetal Alchemist: Brotherhood** — change the seed in the sidebar to explore!"
   Only show this banner when the default seed is active and user hasn't changed it.

3. Keep the existing sample buttons but make them more prominent — move them from the sidebar into the main area as a horizontal row of styled buttons when no results are showing (empty/cleared state).

4. The first-load experience should be: open app → see 10 recommendations immediately → understand what to do next.

5. Do NOT remove any existing functionality — this is purely additive UX improvement.
```

---

### Task 4.2: Convert Score Display to User-Friendly Format

**Why:** "Match score: 0.847" is meaningless to end users. A 5-star or percentage representation communicates quality instantly.

**Checklist:**
- [ ] Add a `format_user_score(raw_score: float, all_scores: list[float]) -> str` function that converts to percentile within the current result set
- [ ] Display as "95% Match" or "★★★★☆" instead of raw decimal
- [ ] Keep the raw score available in an expander/tooltip for technical users
- [ ] Update both list and grid card views
- [ ] Update `src/app/score_semantics.py` with the new display logic

**Prompt for Claude Sonnet 4.5:**

```
I need to convert the recommendation score display from raw decimals to a user-friendly format.

CONTEXT:
- Currently, scores are displayed as "Match score: 0.847" — raw, uncalibrated, unitless
- Score semantics are defined in src/app/score_semantics.py: explicitly labeled as relative and uncalibrated
- Cards are rendered in src/app/components/cards.py via render_card() and render_card_grid()
- The score is passed to cards as part of the recommendation dict (key: "score")
- Scores vary per query — they're relative within a result set, not absolute

REQUIREMENTS:
1. Add a function to src/app/score_semantics.py:
   def format_user_friendly_score(raw_score: float, all_raw_scores: list[float]) -> tuple[str, str]:
       """Convert raw score to user-friendly display.
       
       Returns:
           (display_text, tooltip_text)
           display_text: e.g., "95% Match" or "★★★★½"
           tooltip_text: e.g., "Raw score: 0.847 (relative to this result set)"
       """
   
   Implementation: compute percentile rank within the result set.
   - Top item always gets "98% Match" (not 100% — feels more honest)
   - Scale linearly: percentile_rank * 0.98 → display as "XX% Match"
   - Minimum display: "50% Match" (don't show low numbers for recommended items)

2. Update render_card() and render_card_grid() in src/app/components/cards.py to:
   - Show the user-friendly format prominently
   - Show the raw score in a smaller caption or tooltip below
   - Use color coding: ≥90% green, ≥75% blue, ≥60% orange, else grey

3. Pass all_raw_scores into the card rendering pipeline so percentile can be computed.

4. Keep the existing format_match_score() function for backward compatibility and technical display in expanders.

5. Update score_semantics.py docstring to explain the dual display approach.
```

---

### Task 4.3: Remove Debug Print Statements

**Why:** `print(f"[TYPE FILTER]...")` in production code is unprofessional.

**Checklist:**
- [ ] Search for all `print(` statements in `app/main.py` and `src/`
- [ ] Replace debug prints with `logger.debug()` calls
- [ ] Verify logging is configured at INFO level by default (DEBUG only when env var set)

**Prompt for Claude Sonnet 4.5:**

```
Find and fix all debug print statements in the codebase.

REQUIREMENTS:
1. Search all .py files in app/ and src/ for print() calls
2. For each print() found:
   - If it's clearly debug output (e.g., print(f"[TYPE FILTER]...")), replace with logger.debug()
   - If it's legitimate user output, leave it
   - If unsure, replace with logger.debug()
3. Ensure each file that gets logger.debug() calls has: import logging; logger = logging.getLogger(__name__)
4. Do NOT add any new logging configuration — just replace prints with logger calls
5. List all changes made so I can review
```

---

## Phase 5: Code Hygiene & Hardening (P3)

**Goal:** Clean up code smells, add missing test coverage, and eliminate duplication.

### Task 5.1: De-duplicate Utility Functions

**Why:** `_coerce_genres` / `_parse_str_set` / `_parse_pipe_set` are implemented 3+ times across different files. This violates DRY and creates divergence risk.

**Checklist:**
- [ ] Create `src/utils/parsing.py` with canonical implementations of: `parse_pipe_delimited_set()`, `coerce_genres()`, `parse_str_set()`
- [ ] Replace all duplicates in `app/main.py`, `src/app/components/cards.py`, `src/app/diversity.py`, `src/app/stage0_candidates.py`
- [ ] Add unit tests for the canonical implementations
- [ ] Verify all existing tests still pass

**Prompt for Claude Sonnet 4.5:**

```
I need to de-duplicate utility functions that are copy-pasted across multiple files.

CONTEXT:
These parsing functions exist in multiple places:
1. _parse_str_set() in app/main.py (~L155) — parses pipe-delimited strings into sets
2. _parse_pipe_set() in src/app/stage0_candidates.py (~L65) — same logic, different name
3. _coerce_genres() in src/app/components/cards.py — coerces genre values to list
4. _coerce_genres() in src/app/diversity.py — same logic
5. Related: _seed_union_set() in stage0_candidates.py uses _parse_pipe_set internally

REQUIREMENTS:
1. Create src/utils/__init__.py (empty) and src/utils/parsing.py

2. In src/utils/parsing.py, implement canonical versions:
   def parse_pipe_set(val: object) -> set[str]:
       """Parse a value that might be a pipe-delimited string, list, set, or None into a set of strings."""
   
   def coerce_genres(val: object) -> list[str]:
       """Coerce a genres value (string, list, ndarray, None) into a sorted list of genre strings."""

3. Replace ALL duplicates:
   - app/main.py: replace _parse_str_set with from src.utils.parsing import parse_pipe_set
   - src/app/stage0_candidates.py: replace _parse_pipe_set with import
   - src/app/components/cards.py: replace _coerce_genres with import
   - src/app/diversity.py: replace _coerce_genres with import

4. Add tests/test_parsing_utils.py:
   - test_parse_pipe_set_none → empty set
   - test_parse_pipe_set_empty_string → empty set
   - test_parse_pipe_set_single → {"Action"}
   - test_parse_pipe_set_multiple → {"Action", "Drama", "Comedy"}
   - test_parse_pipe_set_list_input → handles list
   - test_parse_pipe_set_nan → empty set
   - test_coerce_genres_string → sorted list
   - test_coerce_genres_none → empty list
   - test_coerce_genres_numpy_array → sorted list

5. Run all existing tests to verify nothing breaks.
```

---

### Task 5.2: Remove `locals().get()` Anti-pattern

**Why:** `locals().get("personalization_applied", False)` is fragile — if variable scoping changes, it silently returns the default instead of failing. Direct variable access with proper initialization is safer.

**Checklist:**
- [ ] Search for all `locals().get(` calls in app/main.py
- [ ] Replace each with explicit variable initialization at the top of the relevant scope
- [ ] Verify logic is preserved

**Prompt for Claude Sonnet 4.5:**

```
Find and fix all locals().get() anti-patterns in app/main.py.

CONTEXT:
- app/main.py uses locals().get("personalization_applied", False) and locals().get("personalized_gate_reason") around line 2800
- This is fragile because if the variable is defined in a different scope (e.g., inside an if-block), locals().get() may not find it depending on Python's scoping rules
- The fix is to initialize the variables explicitly at the top of the relevant code block

REQUIREMENTS:
1. Search app/main.py for all occurrences of locals().get(
2. For each occurrence:
   - Find where the variable SHOULD be defined
   - Add an explicit initialization (e.g., personalization_applied = False) at the start of the relevant code block
   - Replace locals().get("var", default) with just the variable name
3. Ensure the initialization happens before any conditional branches that might set the variable
4. Verify the logic is identical — the defaults in locals().get() should match the initial values
```

---

### Task 5.3: Fix Performance Issue in Post-Scoring Metadata Lookups

**Why:** The post-scoring filter loop does `metadata.loc[metadata["anime_id"] == anime_id].head(1)` per recommendation — O(N) per item. With 13K metadata rows and 30 results, that's 390K comparisons instead of 30 hashtable lookups.

**Checklist:**
- [ ] Build a `metadata_by_id: dict[int, pd.Series]` lookup once before the results loop
- [ ] Or use `metadata.set_index("anime_id")` and `.loc[id]` for O(1) lookups
- [ ] Apply the same fix in browse mode filtering if applicable
- [ ] Verify correctness — same results, faster

**Prompt for Claude Sonnet 4.5:**

```
I need to fix a performance issue in post-scoring metadata lookups.

CONTEXT:
- In app/main.py (or src/app/scoring_pipeline.py), the post-scoring filter loop around line 2610-2700 does:
  metadata.loc[metadata["anime_id"] == anime_id].head(1) 
  for EACH recommended item
- This is O(N) per lookup where N = number of metadata rows (13,000+)
- With 30 results, that's 390,000 comparisons instead of 30 O(1) lookups
- Also check for similar patterns in browse mode filtering

REQUIREMENTS:
1. Before any recommendation result processing loop, build a lookup:
   metadata_by_id = metadata.set_index("anime_id")
   # or: metadata_by_id = {int(row["anime_id"]): row for _, row in metadata.iterrows()}

2. Replace all instances of:
   metadata.loc[metadata["anime_id"] == some_id].head(1)
   with:
   metadata_by_id.loc[some_id] (with try/except KeyError for safety)

3. Apply this fix everywhere in the file where per-item metadata lookups happen in a loop.

4. Also check browse mode (~L1340-1400) for row-level Python genre matching that could use vectorized pandas:
   - If genre filtering uses a Python loop with string parsing, replace with:
     metadata[metadata["genres"].str.contains("Action", na=False)]

5. Verify results are identical before and after.
```

---

### Task 5.4: Add Missing Test Coverage for Eval Metrics

**Why:** `src/eval/metrics.py` and `metrics_extra.py` have no dedicated tests. These are critical functions that need correctness validation.

**Checklist:**
- [ ] Create `tests/test_eval_metrics.py`
- [ ] Test each metric function with known-answer inputs
- [ ] Test edge cases: empty lists, k=0, k > len(ranked_list), no relevant items
- [ ] Test consistency: P@K, R@K, F1@K relationship (F1 = harmonic mean of P and R)

**Prompt for Claude Sonnet 4.5:**

```
I need to add unit tests for src/eval/metrics.py and src/eval/metrics_extra.py.

CONTEXT:
- src/eval/metrics.py contains: precision_at_k, recall_at_k, f1_at_k, ndcg_at_k, average_precision_at_k, evaluate_ranking
- src/eval/metrics_extra.py contains: item_coverage, gini_index
- These have NO existing tests
- All functions take ranked lists (list[int]) and relevant sets (set[int])

REQUIREMENTS:
1. Create tests/test_eval_metrics.py with comprehensive tests:

   # Precision@K
   - test_precision_perfect: ranked=[1,2,3], relevant={1,2,3}, k=3 → 1.0
   - test_precision_half: ranked=[1,2,3,4], relevant={1,3}, k=4 → 0.5
   - test_precision_none_relevant: ranked=[1,2,3], relevant={4,5}, k=3 → 0.0
   - test_precision_k_larger_than_list: ranked=[1], relevant={1}, k=5 → 1.0

   # Recall@K
   - test_recall_perfect: ranked=[1,2,3], relevant={1,2,3}, k=3 → 1.0
   - test_recall_partial: ranked=[1,2], relevant={1,2,3}, k=2 → 2/3
   - test_recall_empty_relevant: ranked=[1,2,3], relevant=set(), k=3 → 0.0

   # F1@K
   - test_f1_consistency: verify f1 = 2*p*r/(p+r) for several inputs
   - test_f1_zero_precision_and_recall: → 0.0

   # NDCG@K
   - test_ndcg_perfect: ideal ordering → 1.0
   - test_ndcg_reversed: worst ordering → < 1.0 but > 0.0
   - test_ndcg_no_relevant: → 0.0

   # MAP@K  
   - test_map_perfect: → 1.0
   - test_map_single_relevant: verify formula manually

   # evaluate_ranking
   - test_evaluate_ranking_returns_all_metrics: check dict keys
   - test_evaluate_ranking_multiple_k: check multiple K values present

   # Coverage & Gini
   - test_coverage_full: all catalog items recommended → 1.0
   - test_coverage_partial: half recommended → 0.5
   - test_gini_uniform: all items recommended equally → 0.0
   - test_gini_concentrated: one item dominates → close to 1.0

2. Each test should have a clear docstring.
3. Use pytest.approx() for floating-point comparisons.
```

---

### Task 5.5: Add Tests for Artifact Loading

**Why:** `src/app/artifacts_loader.py` (~380 lines) handles model selection, validation, and the fail-loud contract — and has zero tests. A bad artifact load silently breaks the entire app.

**Checklist:**
- [ ] Create `tests/test_artifacts_loader.py`
- [ ] Test: missing metadata file → raises `ArtifactContractError`
- [ ] Test: missing MF model → raises `ArtifactContractError`
- [ ] Test: MF model without required attributes → raises with details
- [ ] Test: valid artifacts → returns expected bundle structure
- [ ] Use tmp_path fixture with minimal files (no real models needed)

**Prompt for Claude Sonnet 4.5:**

```
I need to add tests for src/app/artifacts_loader.py which currently has zero test coverage.

CONTEXT:
- artifacts_loader.py (~380 lines) loads and validates: metadata parquet, MF model, kNN model, synopsis artifacts, neural artifacts
- It raises ArtifactContractError (custom exception) when required artifacts are missing or malformed
- The build_artifacts() function returns a bundle dict with keys: "metadata", "models", "explanations", "diversity"
- Models are .joblib files in models/ directory
- Metadata is a .parquet file in data/processed/
- The module uses env vars (APP_MF_MODEL_STEM, APP_KNN_MODEL_STEM) for model selection

REQUIREMENTS:
1. Read src/app/artifacts_loader.py fully to understand the validation logic and ArtifactContractError.

2. Create tests/test_artifacts_loader.py with tests using pytest's tmp_path fixture:

   a. test_missing_metadata_raises:
      - Create a tmp dir with no parquet file
      - Monkeypatch the data path constant
      - Assert build_artifacts() raises ArtifactContractError

   b. test_missing_mf_model_raises:
      - Create metadata parquet but no .joblib files
      - Assert raises ArtifactContractError with "MF" in message

   c. test_mf_missing_required_attributes:
      - Create a mock joblib file that loads to an object without Q/item_to_index
      - Assert raises ArtifactContractError with details listing missing attributes

   d. test_valid_minimal_bundle:
      - Create valid metadata parquet (5 rows with required columns)
      - Create valid mock MF model with P, Q, item_to_index, index_to_item, global_mean
      - Serialize with joblib to tmp_path/models/
      - Assert build_artifacts() returns dict with expected keys
      - Assert bundle["metadata"] is a DataFrame with correct columns

   e. test_artifact_contract_error_has_details:
      - Verify the ArtifactContractError stores details list

3. Use monkeypatch to override file paths rather than modifying real data. This means the tests should work in CI with APP_IMPORT_LIGHT=0 as long as the tmp_path fixtures are correct.

4. Each test should be independent and clean up after itself via tmp_path (automatic).
```

---

## Execution Order & Dependencies

```
Phase 1 (Architecture):
  1.1 Extract Pipeline ──→ 1.2 Pipeline Tests
  1.3 CI (independent)
  1.4 Constants (depends on 1.1)

Phase 2 (Quality):
  2.1 Mean-User CF (depends on 1.1)
  2.2 Quality Factor (depends on 1.1 + 1.4)
  2.3 Graded NDCG (independent)

Phase 3 (Portfolio):
  3.1 Results README (depends on 2.3 for updated metrics)
  3.2 Architecture Diagram (depends on 1.1 for clear architecture)
  3.3 Screenshot (independent, but best after Phase 4)

Phase 4 (UX):
  4.1 First-Run (independent)
  4.2 Score Display (depends on 1.1)
  4.3 Debug Prints (independent)

Phase 5 (Hygiene):
  All tasks independent — can be done in any order
```

---

## Quick Reference: Session Prompts

| Session | Tasks | Est. Time |
|---------|-------|-----------|
| Session 1 | 1.1 (Extract Pipeline) | 60-90 min |
| Session 2 | 1.2 (Pipeline Tests) + 1.4 (Constants) | 45-60 min |
| Session 3 | 1.3 (CI) | 20-30 min |
| Session 4 | 2.1 (Mean-User CF) + 2.2 (Quality Factor) | 45-60 min |
| Session 5 | 2.3 (Graded NDCG) + 5.4 (Eval Tests) | 30-45 min |
| Session 6 | 3.1 (Results README) + 3.2 (Architecture Diagram) | 30-45 min |
| Session 7 | 4.1 (First-Run UX) + 4.2 (Score Display) | 45-60 min |
| Session 8 | 4.3 (Debug Prints) + 5.1 (Dedup) + 5.2 (locals fix) | 30-45 min |
| Session 9 | 5.3 (Perf fix) + 5.5 (Artifact Tests) | 30-45 min |
| Session 10 | 3.3 (Screenshot) + Final review | 20-30 min |

---

## Success Criteria

After all phases, the project should:

1. **Architecture**: Scoring pipeline is a standalone testable module; main.py is under 1,500 lines
2. **Tests**: 90+ tests passing in CI with green badge
3. **Metrics**: README shows concrete NDCG/MAP/Precision numbers
4. **Recommendations**: CF baseline uses mean-user (honest signal); quality factor is configurable
5. **UX**: First-time visitor sees recommendations in <3 seconds without any action
6. **Code**: Zero duplicate utilities, zero print statements, zero `locals().get()` calls
7. **Portfolio impact**: A hiring manager can understand the project's value in 30 seconds from the README
