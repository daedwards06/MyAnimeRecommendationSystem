# Implementation Playbook (Multi-Session)

This file is designed to make work resumable across multiple chat sessions.

How to use:
- Keep this file updated after every work session (2–5 minutes).
- Treat the top sections as the source of truth (assumptions, contracts, decisions).
- Use the “Resume Checklist” to restart quickly without re-reading the repo.

---

## 0) Context Capsule (Update Each Session)

**Project:** Anime Recommendation System (Streamlit portfolio app)

**Primary goal right now:** Phase 4

**Current phase:** Phase 4

**Last updated:** 2025-12-30

**Current blockers (if any):**
- None (app now fails loudly if artifacts are missing/invalid).

**What changed last session (short):**
- Iterated on **Phase 4 / Chunk A3**: refined metadata affinity to use graded, thresholded theme similarity with categorical gating, and added eval diagnostics for bonus firing + rank movement.

**Next action (single sentence):**
- Phase 4 / Chunk A3: (optional) add deterministic TF-IDF synopsis rerank (new artifact) if golden diagnostics suggest it will reduce “weird match” cases.

---

## 0.1) Phase Dashboard (Update Each Session)

Set one phase to **IN PROGRESS**. Keep the rest **NOT STARTED** or **DONE**.

- Phase 1 — Truthful Inference (Artifacts, Paths, Cold-Start): DONE
- Phase 2 — Score Semantics + Explanations (Credibility): DONE
- Phase 3 — UX Flow + Progressive Disclosure (Clarity): DONE
- Phase 4 — Refactor + Tests + Performance (Maintainability): IN PROGRESS
- Phase 5 — Portfolio “Wow” + Docs + QA (Hiring Signal): NOT STARTED 

---

## 1) Resume Checklist (5–10 minutes)

- [ ] Open docs/Audit_Improvement_Plan.md and identify the current phase’s items (High)
- [ ] Confirm which Streamlit entrypoint is used: `streamlit run app/main.py` (not app/app.py) (High)
- [ ] Inspect available model artifacts in `models/` and identify the MF artifact used for inference (High)
- [ ] Confirm metadata parquet exists at `data/processed/anime_metadata.parquet` and includes required UI columns (High)
- [ ] Run the app once and record which scoring path is currently active (before changes) (Medium)
- [ ] Update “Context Capsule”, “Phase Dashboard”, and “Next action” before coding (Low)

---

## 2) Artifact Inventory (Source of Truth)

### 2.1 Expected files/dirs

- `data/processed/anime_metadata.parquet`
- `models/*.joblib`
- `reports/**/*explanations*.json` (optional)
- `reports/**/*diversity*.json` (optional)

### 2.2 Loaded bundle contract (from src/app/artifacts_loader.py)

Bundle keys:
- `metadata`: pandas DataFrame
- `models`: dict of loaded joblib objects (key = filename stem)
- `explanations`: dict of JSON artifacts (optional)
- `diversity`: dict of JSON artifacts (optional)

Minimum required metadata columns (see src/app/constants.py -> MIN_METADATA_COLUMNS):
- `anime_id`, title fields, `genres`, `synopsis` / `synopsis_snippet`, `poster_thumb_url`, `mal_score`, `aired_from`, `type`, etc.

### 2.3 MF model contract (for inference + personalization)

The MF model object must provide:
- `Q`: item factors (shape: num_items x n_factors)
- `item_to_index`: mapping anime_id -> item index
- `index_to_item`: mapping item index -> anime_id

If these are not available, the app must fail loudly with an actionable message (no dummy scoring).

**Selected MF artifact for inference (set once, update if changed):**
- Name: `mf_sgd_v2025.11.21_202756`
- Rationale: Latest timestamped MF artifact in repo; selected deterministically by default and overrideable via `APP_MF_MODEL_STEM`.

### 2.4 Synopsis TF-IDF artifact (optional; ranked rerank)

If present, the app may load a synopsis TF-IDF artifact and use it as a **small additive rerank** in ranked modes.

- File pattern: `models/synopsis_tfidf_v*.joblib`
- Selected deterministically by default; override by setting `APP_SYNOPSIS_TFIDF_STEM=<stem>`
- Loaded into bundle at: `bundle["models"]["synopsis_tfidf"]`
- Expected object: `SynopsisTfidfArtifact` (see `src/app/synopsis_tfidf.py`)
  - Must include an `anime_ids` alignment and an `anime_id_to_row` mapping for deterministic lookup
  - Must include the fitted `TfidfVectorizer` and the aligned sparse `tfidf_matrix`
  - Must include `schema` and `vectorizer_params` for traceability

Build command:
- `python scripts/build_synopsis_tfidf_artifact.py`

Artifact metadata tracking:
- Appends build info under `data/processed/artifacts_manifest.json` with key `synopsis_tfidf`

---

## 3) Scoring Path Definitions (Source of Truth)

### 3.1 Modes

- **Browse mode:** filter and sort metadata only; no recommender scoring.
- **Seed-based:** generate recommendations from hybrid scoring using seed(s) and/or default user index.
- **Personalized:** generate recommendations from user embedding computed from profile ratings + MF item factors.
- **Cold-start content-only:** if an item is not in MF training (see below), use content similarity artifacts (if available).

### 3.2 Cold-start definition

Default (recommended for portfolio + robustness):
- An item is **in training** iff `anime_id in mf_model.item_to_index`.
- An item is **cold-start** otherwise.

This is inference-safe and does not require shipping the interactions dataset to the app.

---

## 4) Phased Implementation Plan (1–5)

Each chunk should be doable in ~30–90 minutes. Prefer completing an entire chunk per session.

### Phase 1 — Truthful Inference (Artifacts, Paths, Cold-Start)

**Goal:** No placeholder/dummy scoring; app uses real artifacts or fails loudly with actionable errors; scoring path is visible; cold-start is real.

**Dependencies:** None.

**Phase 1 done when:**
- The app cannot generate recommendations from any dummy/placeholder score arrays.
- Missing/invalid artifacts produce a clear, actionable error message in the UI (not silent fallback).
- The UI shows the correct active scoring path for: Browse, Seed-based, Personalized.
- Cold-start badges reflect real “in training” status (based on MF factor availability).

#### Chunk 1 — Remove placeholder scoring + enforce contracts

- [x] Remove all placeholder/dummy scoring paths so recommendations are always generated from real loaded artifacts; app must raise a clear error if required artifacts are missing (High)
- [x] Add strict artifact contract checks in the artifact loader (required columns, MF factor matrix, mappings) with actionable error messages; verify failures are informative and non-silent (Medium)

**Done when:**
- Running `streamlit run app/main.py` produces recommendations only if real artifacts load successfully.
- If the MF artifact is missing or lacks required attributes (`Q`, `item_to_index`, `index_to_item`), the UI shows an error stating exactly what is missing and where it was expected.
- There is no code path that constructs dummy `mf_scores`, `knn_scores`, or `pop_scores` arrays to power recommendation results.

#### Chunk 2 — Add “active scoring path” indicator

- [x] Implement an explicit “active scoring path” status indicator (e.g., MF-only, Hybrid, Personalized, Cold-start content) that reflects the actual code path used for the current results (High)

**Done when:**
- The UI displays a single “Active scoring path” label for every run.
- Toggling Browse mode switches the label to Browse.
- Enabling personalization (with a rated profile) switches the label to Personalized when active.
- Seed selection (1+ seeds) switches the label to Seed-based / Multi-seed (as appropriate).

#### Chunk 3 — Wire personalization end-to-end

- [x] Ensure personalization works end-to-end by wiring the correct MF model key from the loaded `bundle["models"]` and verifying the personalized ranking changes when user ratings change (High)

**Done when:**
- With a loaded profile that has ratings, enabling personalization produces a different top-N list than seed-only at the same filters.
- Changing at least one rating (via in-app rating or profile edit) changes the personalized ranking on the next run.
- The personalization path uses the selected MF artifact from the bundle (no hard-coded model key assumptions).

#### Chunk 4 — Make cold-start detection real

- [x] Make cold-start detection real by deriving `is_in_training` from training interactions / MF factor availability, and verify cold-start badges appear for truly unseen items only (High)

**Done when:**
- For any recommended item `anime_id`:
  - If `anime_id` is in `mf_model.item_to_index`, it is labeled Trained.
  - If not, it is labeled Cold-start.
- Spot-check at least 5 items: 3 trained + 2 cold-start, and the badge matches MF factor availability.

---

### Phase 2 — Score Semantics + Explanations (Credibility)

**Goal:** Every displayed score/explanation/badge is numerically defensible and consistent with the underlying scoring path.

**Dependencies:** Phase 1 (must be running real inference paths).

**Phase 2 done when:**
- One score meaning is documented and consistently displayed across UI + explanations.
- Personalized explanations never show impossible bounds (e.g., >10/10) and match score semantics.
- Hybrid contribution shares are truthful and sum to ~100% when shown.
- Diversity/novelty metrics are computed from correct inputs (user history, catalog genres) and pass sanity checks.

#### Chunk 1 — Standardize score semantics (single source of truth)

- [x] Standardize score semantics across the app (e.g., “relative score”, “predicted rating”, or “match percentile”) and verify that the displayed explanation matches the chosen semantics everywhere (High)

**Done when:**
- The app uses one named score semantic everywhere (e.g., “Match score (relative)”, “Predicted rating”, or “Percentile”).
- The Help/FAQ and any inline labels match the chosen semantics.
- There is no mix of “/10” and raw dot-product scores in the same mode.

#### Chunk 2 — Fix personalization score bounds

- [~] Calibrate or reframe personalized scores so the explanation cannot exceed valid bounds (e.g., if showing “/10”, enforce 0–10); verify with unit tests and a manual profile run (High)
  - **Note (2025-12-24):** Not applicable while we display **Match score (relative)** (unitless/uncalibrated). Only needed if we switch back to a bounded rating display (e.g., “Predicted rating /10”).

**Done when:**
- Manual run: at least 10 personalized recommendations show scores within the defined bounds.
- Unit test (or deterministic check) prevents regressions for out-of-range formatting.

#### Chunk 3 — Truthful hybrid explanation shares

- [x] Make hybrid explanations truthful by showing per-item source contributions computed from the actual score components used for that item; verify contributions sum to ~100% and reflect the active model path (High)

**Done when:**
- For at least 5 items, the displayed MF/kNN/Pop shares sum to ~100%.
- Switching weight preset changes at least one item’s shares in a visible way.

**Notes (UI):** In Seed-based mode, the popularity share is often present but tiny (e.g., ~0.02%–0.05%) and can round to `0.0%` because the UI formats shares to 1 decimal percent.

#### Chunk 4 — Diversity metrics computed from correct inputs

- [x] Validate that diversity metrics shown in-app (coverage, genre exposure ratio, novelty) are computed from correct inputs (user history + catalog genres); verify with a controlled test set and sanity checks (Medium)

**Done when:**
- With a rated profile, novelty uses the user’s genre history (not item genres as a proxy).
- With no profile, novelty is either hidden/NA or clearly labeled as non-personalized.

---

### Phase 3 — UX Flow + Progressive Disclosure (Clarity)

**Goal:** Reduce cognitive load; make first-time usage obvious; ensure copy matches the real UI and scoring paths.

**Dependencies:** Phase 1–2 (needs truthful behavior + stable semantics).

**Phase 3 done when:**
- First-time user can get results in ≤2 actions in each mode (Personalized / Seed / Browse).
- Onboarding/help text matches the implemented controls and scoring paths.
- Empty states provide actionable recovery steps and users can recover without leaving the app.

#### Chunk 1 — Align onboarding and remove persona mismatch

- [x] Align onboarding copy to the implemented UX (profiles + seeds + browse mode); remove persona language unless personas are fully implemented and visible in the UI (High)

**Done when:**
- On first load, onboarding references only controls that actually exist.
- Any mention of personas is removed unless persona selection is present and functional.

#### Chunk 2 — Choose-a-mode gating (progressive disclosure)

- [x] Add a single “Choose your mode” decision at the top (Personalized / Seed-based / Browse) with only relevant controls shown per mode; verify a first-time user can get results in ≤2 actions (High)

**Done when:**
- Only relevant controls are shown for the selected mode.
- Each mode produces visible results within ≤2 user actions from a cold start.

#### Chunk 3 — First-load clarity and empty-state recovery

- [x] Ensure the app clearly answers “What is this / Why care / What next” on first load (1–2 sentences + primary CTA); verify via a cold-start screenshot (Medium)
- [x] In recommendation mode, show an explicit empty-state checklist when results are empty (e.g., “remove filters”, “try fewer seeds”, “disable browse mode”); verify each suggestion is actionable in-app (Medium)

**Done when:**
- A cold-start screenshot includes: what this is, why it matters, and what to do next.
- Empty-state checklist contains only actions available in-app and leads to recovery.

#### Chunk 4 — Consistent mode-specific copy + tooltips

- [x] Ensure “Browse by Genre” mode disables or visually de-emphasizes seed-specific copy; verify headings and help text match mode consistently (Medium)
- [x] Add consistent tooltips/help text for key controls (Hybrid Weights, personalization strength, filters); verify every control has either help text or is self-explanatory (Low)

**Done when:**
- Mode headings match the mode (Browse vs Recommendations) at all times.
- Every non-obvious control has help text (hover) or an adjacent hint.

---

### Phase 4 — Refactor + Tests + Performance (Maintainability)

**Goal:** Improve recommendation quality safely (repeatable evaluation + better signals) while reducing `app/main.py` complexity, removing duplicated logic, improving responsiveness, and strengthening test coverage.

**Dependencies:** Phase 1–3 (avoid refactoring unstable behavior).

**Phase 4 done when:**
- Recommendation quality improvements are measurable and reproducible (offline eval + “golden queries”), and new/updated artifacts are versioned and load safely in-app.
- App behavior is unchanged from the user perspective unless explicitly called out by a specific chunk.
- Duplicated parsing/filtering logic is removed (single implementation per concern).
- Basic smoke + unit tests run cleanly.
- Performance improves measurably or remains stable while complexity drops.

**Track A — Model Quality / Re-evaluation**

Goal: reduce “obviously wrong” recommendations (e.g., recap/special artifacts) and improve relevance + novelty + cold-start quality by iterating on candidate hygiene, content features, collaborative models, and hybrid tuning.

Notes:
- Keep the app’s inference contracts stable (see Section 2: Artifact Inventory). If new artifacts are introduced (e.g., embeddings), define their contract here before wiring them into the UI.
- Prefer changes that are measurable offline first, then validated in the Streamlit app.

#### Chunk A1 — Golden queries + offline evaluation harness

- [x] Create a small “golden queries / failure cases” set (10–30 titles) with expected good/bad behaviors (e.g., “Tokyo Ghoul should not surface recaps/specials in top-N”).
- [x] Add a repeatable offline evaluation entrypoint that outputs: headline ranking metrics (e.g., NDCG@K/MAP@K), coverage/novelty summaries, and a human-readable report for the golden queries.

**Done when:**
- A single command generates an evaluation report artifact under `reports/` (metrics + golden query examples).
- The report is stable/reproducible for a fixed artifact snapshot (seeded randomness, pinned inputs).

#### Chunk A2 — Candidate hygiene (format/type guardrails)

- [x] Add explicit candidate filtering/penalties for low-signal or non-standard formats (recaps/summaries/specials/shorts) using metadata fields (e.g., `type`) and conservative title heuristics as a fallback.
- [x] Verify the guardrails apply only to ranked modes (Seed-based / Personalized), not Browse.

**Done when:**
- Golden queries no longer surface obvious recap/special entries in top-N for representative seeds.
- Any exclusions/penalties are recorded in the Decision Log (so they don’t get re-litigated).

#### Chunk A3 — Content features (parquet + new data)

- [x] Use additional metadata columns from `data/processed/anime_metadata.parquet` as features for similarity/ranking (studios, themes, year proximity).
- [x] Optionally add new data/features for stronger semantic similarity and better cold-start behavior.

**Expanded next steps (keep deterministic + measurable):**
- [x] Add more sensitive offline reporting (rank movement, top-20 overlap, mean rank delta) so improvements show up even when top-10 membership doesn’t change.
- [x] Replace binary overlap with graded overlap (e.g., Jaccard on themes/studios) + thresholding so we can increase coefficients without “year-only” false positives.
- [x] Add a lightweight “new data” feature: TF-IDF synopsis similarity rerank (artifact + deterministic inference).
- [ ] If adding embeddings later: define the artifact contract in Section 2 (format, dims, dtype, ID alignment), add versioning, and wire via the same ranked scoring choke points + golden harness.

**Done when:**
- Cold-start quality improves vs baseline and is detectable in offline outputs (even if top-10 membership is unchanged).
- Golden query safety is preserved (no increases in `violation_count`).
- Any new feature artifact(s) are versioned and their load contract is documented.

#### Chunk A4 — Collaborative retrain / alternative CF model

- [ ] Retrain MF with improved training setup (regularization/objective/data filtering) and/or evaluate alternative CF (e.g., implicit ALS/BPR) against the current MF artifact.
- [ ] Ensure the selected model artifact still satisfies the MF contract required by the app (or update the app contract explicitly if changing model type).

**Done when:**
- Offline ranking metrics improve vs the current baseline artifact (with documented deltas).
- The chosen artifact is versioned (timestamped) and can be swapped via `APP_MF_MODEL_STEM` without app changes.

#### Chunk A5 — Hybrid tuning + novelty/popularity controls

- [ ] Tune hybrid weights (MF / content / popularity components) using a repeatable search procedure (e.g., Optuna) and evaluate the relevance vs novelty tradeoff.
- [ ] Add/verify simple debiasing controls (e.g., cap popularity contribution, or rerank for diversity) only if they improve golden queries without harming relevance.

**Done when:**
- A tuned preset exists with documented tradeoffs and reproducible evaluation outputs.
- Golden queries improve for both “relevance” and “no obvious junk” cases.

**Track B — Maintainability (Refactor + Tests + Performance)**

#### Chunk 1 — Modularize the app entrypoint

- [ ] Refactor main.py into smaller modules (sidebar/state, scoring, filtering, rendering) while preserving identical UX; verify by running the app and confirming all features still work (High)

**Done when:**
- `app/main.py` primarily composes UI and calls functions from `src/app/` modules.
- No single file contains the full browse + recommend + personalization + filtering logic end-to-end.

#### Chunk 2 — Centralize parsing/filtering + cache indexes

- [ ] Centralize genre/type/year parsing and filtering into reusable functions to eliminate duplicated logic; verify only one implementation exists for each filter type (High)
- [ ] Replace repeated `metadata.iterrows()` loops and repeated `metadata.loc[...]` lookups with cached indexes (e.g., `anime_id -> row`, `anime_id -> genre set`); verify a measurable latency improvement in the performance panel (Medium)

**Done when:**
- Genre/type/year parsing exists in one shared utility location.
- Recommendation-mode and browse-mode reuse the same filter functions.
- Performance panel shows reduced or stable latency with fewer repeated DataFrame scans.

#### Chunk 3 — Tests + logging hygiene

- [ ] Remove `print()` debug logging from the recommendation path and replace with structured logging (or Streamlit-friendly debug toggle); verify no console noise in normal runs (Low)
- [ ] Add a lightweight smoke test that imports the app in “light mode” and confirms key modules load without heavy artifacts; verify it runs in CI (Medium)
- [ ] Add unit tests for: genre coercion, badge payload correctness, explanation formatting, and personalized embedding generation; verify tests pass locally and in CI (Medium)

**Done when:**
- Default runs produce no noisy debug `print()` output.
- Smoke test validates imports with `APP_IMPORT_LIGHT=1`.
- Unit tests cover: genre coercion, badge payload, explanation formatting, user embedding.

---

### Phase 5 — Portfolio “Wow” + Docs + QA (Hiring Signal)

**Goal:** Surface evaluation rigor, tradeoffs, lineage, and a coherent demo narrative; finalize stability and presentation.

**Dependencies:** Phase 1–4.

**Phase 5 done when:**
- In-app evaluation transparency exists (metrics + split + robustness) and matches reports.
- Differentiators are tied to offline evidence (accuracy vs diversity tradeoff).
- README/docs support a clean 5–10 minute interview demo.
- Final QA checklist passes; app is stable and coherent.

#### Chunk 1 — In-app evaluation transparency

- [ ] Add an in-app “Model Card / Evaluation” expander that reports dataset snapshot date, split strategy (user-aware + temporal check), and 3–5 headline metrics (NDCG@K, MAP@K, coverage, Gini); verify it matches the Phase 4 artifacts (High)
- [ ] Add a visible “Robustness” note showing temporal validation outcome and leakage safeguards; verify it is consistent with Phase 4 writeups (Medium)

**Done when:**
- In-app metrics match Phase 4 artifacts (numbers, labels, and dataset snapshot).
- A reviewer can understand evaluation setup without opening notebooks.

#### Chunk 2 — Differentiators and decision tradeoffs

- [ ] Add an interactive “Accuracy vs Diversity” explanation tied to offline metrics (e.g., show metric deltas when toggling weights); verify numbers match Phase 4 evaluation artifacts (High)
- [ ] Add per-recommendation drill-down for “Why this anime?” that shows: matched genres, similar rated titles (if personalized), and source contributions; verify drill-down is consistent with active mode (Medium)
- [ ] Add a visible “Reproducibility & Lineage” section that lists artifact versions/timestamps and whether data is stale; verify it reads from real artifact metadata (Medium)
- [ ] Add a small “Tradeoffs & Decisions” panel describing why MF+hybrid was chosen and what was deferred (ALS/LightFM) with justification; verify it references concrete results (Low)

**Done when:**
- Accuracy vs Diversity explanation shows numbers consistent with offline evaluation.
- Drill-down explanations reflect the actual active scoring path.

#### Chunk 3 — Docs + interview-ready demo

- [ ] Update README with: live demo instructions, screenshots (browse, seed, personalized), and a 60-second “how to use” flow; verify links and images render on GitHub (High)
- [ ] Add a short architecture diagram (data → features → models → artifacts → Streamlit) and confirm it matches repo structure; verify it is included in README or docs index (Medium)
- [ ] Add a “Model & Data Cards” doc page summarizing dataset provenance/licensing, preprocessing, evaluation protocol, and limitations; verify it references actual files/artifacts (Medium)
- [ ] Add a “Demo Script” doc for interviews (3 scenarios: cold start, seed-based, personalized) with expected outcomes; verify it can be followed step-by-step (Low)

**Done when:**
- README renders correctly with screenshots and a 60-second usage flow.
- Architecture diagram matches repo structure and terminology.
- Demo script can be followed verbatim by someone unfamiliar with the repo.

#### Chunk 4 — Final QA + correctness checks

- [ ] Ensure the app demonstrates real ML inference (not a UI demo) by proving recommendations change when: seed changes, weights toggle changes, and user ratings change; verify with a scripted “demo checklist” run (High)
- [ ] Ensure codebase clearly separates concerns (data loading, scoring, UI rendering) and is easy to navigate; verify by file structure and module boundaries (Medium)
- [ ] Run and document a full “portfolio QA” pass: cold start, seed recommendations, browse mode, MAL import, exclusions, ratings updates, personalization strength slider, and filters; verify no crashes and clear UX throughout (High)
- [ ] Validate that badges/metrics displayed never contradict the underlying data (e.g., cold-start badge correctness, novelty not computed from item genres alone); verify with spot checks and tests (High)
- [ ] Confirm performance targets are met on a typical machine (e.g., <500ms interactive updates, reasonable memory footprint) and reflect real measurements in the performance panel (Medium)
- [ ] Remove or gate any experimental UI remnants (e.g., persona references, unused imports/components) so reviewers see a coherent product; verify no dead UI paths remain (Low)
- [ ] Ensure all dependencies required to run the app are pinned and minimal for deployment; verify `pip install -r requirements.txt` followed by app launch works cleanly (Medium)

**Done when:**
- Scripted demo checklist proves recommendations change with seeds, weights, and ratings.
- Badges/metrics never contradict the underlying data.
- App meets stated performance targets (or documents observed values and constraints).

---

## 5) Validation Checklist (What to Run After Changes)

### 5.1 Manual checks (fast)

- [ ] Browse mode still works with genre/type/year filters (Medium)
- [ ] Seed-based recommendations generate without placeholder scoring (High)
- [ ] “Active scoring path” indicator matches observed behavior (High)
- [ ] Personalization changes ranking when ratings change (High)

### 5.2 Developer checks

- [ ] `APP_IMPORT_LIGHT=1` import path still works for tests (Medium)
- [ ] No silent fallback to dummy arrays remains (High)
- [ ] `python -m pytest -q` passes (pytest should only collect `tests/` via `pytest.ini`) (High)
- [ ] Manual negative test: set `APP_MF_MODEL_STEM=__bad__` and confirm UI fails loudly + disables recommendations (High)

---

## 6) Decision Log (Keep This Short)
### 2025-12-29 — Phase 4 / Chunk A2: Ranked candidate hygiene

- **Decision:** In ranked modes only, exclude candidates when:
  - `type` is in {`Special`, `Music`}
  - `title_display` matches the conservative recap/summary regex: `(?i)\b(recap|recaps|summary|digest|compilation|episode\s*0)\b`
- **Where implemented:** `src/app/quality_filters.py` (`build_ranked_candidate_hygiene_exclude_ids`) and applied in ranked choke points in `app/main.py` and `scripts/evaluate_phase4_golden.py`.
- **Rationale:** Directly targets Phase 4 golden failures (e.g., Tokyo Ghoul showing specials/recaps) while minimizing over-filtering; rules match the golden expectations defaults.
- **Tradeoffs:** Legitimate specials (or music entries) may be suppressed in ranked recommendations; Browse mode remains unchanged and can still surface them via metadata filters.

### 2025-12-29 — Phase 4 / Chunk A3: Lightweight metadata affinity (ranked rerank)

- **Decision:** Add a conservative, deterministic “metadata affinity” bonus term for ranked seed-based scoring using only existing parquet columns:
  - `studios` (binary overlap)
  - `themes` (graded overlap ratio with minimum overlap + minimum similarity threshold)
  - `aired_from` year proximity (weak tie-breaker)
- **Guardrail:** Require at least one categorical overlap (`studios` or `themes`) before year proximity can contribute (prevents year-only false positives).
- **Where implemented:**
  - Feature logic + weights/constants in `src/app/metadata_features.py`
  - Wired into ranked choke points in `app/main.py` (multi-seed ranked) and `scripts/evaluate_phase4_golden.py` (seed-based golden scorer)
  - Ensured `themes` is retained in pruned app metadata via `src/app/constants.py` (`MIN_METADATA_COLUMNS`)
- **Rationale:** Provide a small, interpretable cold-start and “weird match” reduction signal without adding new heavy artifacts/dependencies.
- **Tradeoffs:** Signal is intentionally weak and may not change top-N often; thresholding means sparse/underspecified themes will not contribute.

### 2025-12-30 — Phase 4 / Chunk A3: Graded themes + observability

- **Decision:** Replace binary theme overlap with a graded similarity (overlap ratio) with conservative guardrails:
  - require minimum overlap count
  - require minimum overlap ratio
  - keep studios as a strong binary gate
  - allow year proximity only if a categorical gate passes
- **Decision:** Add eval-only diagnostics to make metadata bonus firing and rank movement observable per golden query.
- **Where implemented:** `src/app/metadata_features.py` (graded/thresholded themes; categorical gate) and `scripts/evaluate_phase4_golden.py` (per-query diagnostics; rank-movement summaries).
- **Rationale:** Increase sensitivity of the signal without reintroducing “single generic theme” false positives; make changes measurable even when top-10 membership is unchanged.
- **Tradeoffs:** Diagnostics focus on set overlap + rank delta; they don’t directly measure semantic relevance and should be paired with human review of golden reports.

### 2025-12-30 — Phase 4 / Chunk A3: Synopsis TF-IDF rerank (new artifact)

- **Decision:** Add an optional synopsis TF-IDF semantic similarity signal as a small additive rerank term in ranked modes.
- **Guardrails:**
  - Deterministic artifact build (stable sort by `anime_id`, fixed TF-IDF params).
  - Conservative gate: pass if same `type` OR `episodes >= MIN_EPISODES`.
  - Off-gate short-form penalty bounded to never become positive.
- **Where implemented:**
  - Artifact contract + build + similarity utilities: `src/app/synopsis_tfidf.py`
  - Artifact build script + manifest append: `scripts/build_synopsis_tfidf_artifact.py`
  - Optional loader alias + env override: `src/app/artifacts_loader.py` (`APP_SYNOPSIS_TFIDF_STEM`)
  - Ranked scoring wiring + explanation fields: `app/main.py`
  - Golden harness wiring + TF-IDF diagnostics: `scripts/evaluate_phase4_golden.py`
- **Rationale:** Metadata-only affinity did not reliably suppress “weird match” content for narrative-heavy seeds; synopsis text provides a cheap semantic signal without embeddings.
- **Tradeoffs:**
  - TF-IDF often matches franchise-adjacent text strongly (sequels/movies/specials) and may not generalize to “similar vibe” titles.
  - Signal can be sparse if synopses are short/missing; bonus magnitudes remain intentionally small.
  - Seed resolution can still be wrong (e.g., golden `my_hero_academia` resolves to Demon Slayer), which limits interpretation of some golden rows.


Record decisions that future sessions must not re-litigate.

- **2025-12-20:** Created this playbook to persist Phase 1 assumptions + contracts.
- **2025-12-22:** Enforced MF artifact contract (must have `Q`, `item_to_index`, `index_to_item`) and removed all placeholder scoring. Default MF selection is `mf_sgd_v2025.11.21_202756` unless overridden by `APP_MF_MODEL_STEM`.
- **2025-12-22:** Popularity percentiles are treated as neutral (0.5) unless a real popularity signal is loaded (Phase 1 / Chunk 2). Percentiles are on a 0..1 scale where lower means more popular.
- **2025-12-23:** Pytest collection is restricted to `tests/` via `pytest.ini` to avoid collecting runnable scripts under `scripts/test_*.py`.
- **2025-12-24:** Standardized recommendation score display to **Match score (relative)** (unitless/uncalibrated). As a result, Phase 2 / Chunk 2 (bounded score enforcement) is only applicable if we later switch to a bounded “/10” semantics.

---

## 7) Session Log (Tiny, but consistent)

### Session 2025-12-30 (Phase 4 / Chunk A3)

- What I did:
  - Refined metadata affinity by using graded theme overlap (ratio) with conservative thresholds and a categorical gate (studios/themes) before year proximity can contribute.
  - Added eval diagnostics to make `metadata_bonus` firing and rank movement observable per golden query.

- What I changed:
  - Refined `themes` affinity to be graded + thresholded in [src/app/metadata_features.py](src/app/metadata_features.py)
  - Added/extended per-query diagnostics + rank-movement reporting in [scripts/evaluate_phase4_golden.py](scripts/evaluate_phase4_golden.py)

- Observed effects (golden run 20251230175115):
  - Tokyo Ghoul: `bonus_fired=0`, `top20_moved=0`, `violation_count=0`
  - One Piece: `bonus_fired=1`, `top20_moved=2` (e.g., `anime_id=30028` received `metadata_bonus=0.00846` and moved ahead of `anime_id=31201`)
  - Haikyuu!!: `bonus_fired=5`, `top20_moved=6`, `top50_moved=20` (same set; mild within-top reordering)

- Validation run:
  - `python -m pytest -q` (57 passed, 3 warnings)
  - `python scripts/evaluate_phase4_golden.py --k 10 --sample-users 50`
    - Wrote: `experiments/metrics/phase4_eval_20251230175115.json`
    - Wrote: `reports/phase4_golden_queries_20251230175115.md`
    - Wrote: `reports/artifacts/phase4_golden_queries_20251230175115.json`

- Next session start here:
  - Proceeded with the Phase 4 / Chunk A3 “new data” experiment (synopsis TF-IDF rerank) and validated it through the golden harness.

### Session 2025-12-30 (Phase 4 / Chunk A3 — Synopsis TF-IDF)

- What I did:
  - Built a versioned synopsis TF-IDF artifact.
  - Wired it into ranked seed-based scoring (and personalized-with-seeds) as an additive bonus + bounded penalty.
  - Extended golden reporting to include TF-IDF firing counts and rank movement vs “without TF-IDF”.

- Observed effects (baseline `20251230193641` → latest `20251230214709`):
  - `violation_count` remained 0 across golden queries.
  - TF-IDF causes measurable within-top movement (e.g., Tokyo Ghoul `top20_overlap_tfidf=0.250`, `top20_moved_tfidf=5`).
  - Qualitatively, results are still dominated by non-franchise short-form/catalog quirks for some seeds; TF-IDF did not reliably surface “similar long shounen” for One Piece.

- Validation run:
  - `python scripts/evaluate_phase4_golden.py --golden-weight-mode Balanced`
    - Wrote: `reports/phase4_golden_queries_20251230214709.md`

### Session 2025-12-29

- What I did:
  - Implemented Phase 3 / Chunk 3: first-load clarity + empty-state recovery.
  - Verified mode-aware prompts for Browse / Seed-based / Personalized and ensured no silent fallback.
  - Implemented Phase 3 / Chunk 4: consistent mode-specific copy + lightweight tooltips (no scoring/model changes).

- What I changed:
  - Mode-aware first-load + empty-state recovery prompts in [app/main.py](app/main.py)
  - Mode-switch sync: force rerun on mode change so main area updates immediately in [app/main.py](app/main.py)
  - Aligned Browse onboarding wording in [src/app/components/instructions.py](src/app/components/instructions.py)
  - Removed Browse-visible “recommendations”/“match score” helper text and standardized mode headers/tooltips in [app/main.py](app/main.py)
  - Made Help / FAQ mode-aware so Browse stays metadata-only in [src/app/components/help.py](src/app/components/help.py)
  - Clarified seed-action tooltips without changing behavior in [src/app/components/cards.py](src/app/components/cards.py)
  - Fixed Streamlit warning about widget key `ui_mode` by avoiding pre-setting `st.session_state["ui_mode"]` before creating the radio in [app/main.py](app/main.py)

- Decisions made:
  - In **Browse**, avoid “Match score” wording entirely; use “metadata-only” / “no ranking” language.
  - Use “Ranked modes disabled” (instead of “Recommendations disabled”) for artifact failure UI copy to keep Browse wording clean.

- Validation run:
  - Manual: completed Streamlit manual checks (mode copy/tooltips + empty-state behavior; confirmed `ui_mode` warning is gone)
  - `python -m pytest -q` (52 passed, 3 warnings)

- Next session start here:
  - Phase 4: (candidate) centralize genre/type/year filtering utilities to reduce duplication (no UX change).

### Session 2025-12-29 (Phase 4 / Chunk A1)

- What I did:
  - Created a small “golden queries / failure cases” set (includes Tokyo Ghoul) with lightweight expectations.
  - Added a single offline evaluation entrypoint that produces:
    - Headline ranking metrics (NDCG@K, MAP@K; plus coverage/Gini)
    - A human-readable golden-queries report showing top-N outputs per query

- What I changed:
  - Added golden query config in [data/samples/golden_queries_phase4.json](data/samples/golden_queries_phase4.json)
  - Added evaluation script in [scripts/evaluate_phase4_golden.py](scripts/evaluate_phase4_golden.py)

- Decisions made:
  - Store headline metrics under `experiments/metrics/` (consistent with existing eval scripts).
  - Store golden queries JSON under `reports/artifacts/` and a readable Markdown report under `reports/`.
  - Keep evaluation deterministic where possible (fixed seed; stable sorting / tie-breaking in the harness).

- Validation run:
  - `python -m pytest -q` (52 passed, 3 warnings)
  - `python scripts/evaluate_phase4_golden.py --k 10 --sample-users 50`
    - Wrote: `experiments/metrics/phase4_eval_20251229165531.json`
    - Wrote: `reports/phase4_golden_queries_20251229165531.md`
    - Wrote: `reports/artifacts/phase4_golden_queries_20251229165531.json`
  - Manual: completed A1 sanity checks on golden artifacts and determinism

- Next session start here:
  - Phase 4 / Chunk A2: implement candidate hygiene (type/title guardrails) and validate improvements against the golden queries report.

### Session 2025-12-29 (Phase 4 / Chunk A2)

- **Goal:** Reduce ranked-mode junk (recaps/specials/shorts) with conservative, deterministic guardrails.
- **Changes:**
  - Added ranked hygiene exclusion helper in `src/app/quality_filters.py`.
  - Applied hygiene exclusions in ranked app paths (`app/main.py`) and the golden harness (`scripts/evaluate_phase4_golden.py`).
  - Added unit test for hygiene exclusion logic.
- **Validation (run locally):**
  - `python -m pytest -q` (pass)
  - `python scripts/evaluate_phase4_golden.py --k 10 --sample-users 50`
    - Wrote: `experiments/metrics/phase4_eval_20251229175855.json`
    - Wrote: `reports/phase4_golden_queries_20251229175855.md`
    - Wrote: `reports/artifacts/phase4_golden_queries_20251229175855.json`
  - Golden delta (baseline `20251229165531` → `20251229175855`): Tokyo Ghoul violations `3 → 0`.
- **Next:** If future golden updates include OVA/ONA as “bad formats”, prefer a *penalty* (downrank) over exclusion and re-validate.

### Session 2025-12-29 (Phase 4 / Chunk A3)

- **Goal:** Add a minimal, deterministic metadata-based rerank signal using the processed parquet (no new heavy artifacts).
- **Changes:**
  - Added `src/app/metadata_features.py` with a conservative metadata affinity score and centralized coefficients.
  - Wired the bonus into ranked seed-based scoring in `app/main.py` and `scripts/evaluate_phase4_golden.py`.
  - Updated the metadata pruning contract to keep `themes` (`src/app/constants.py`) so the affinity signal uses the intended columns.
  - Tightened affinity gating to require a `studios` or `themes` overlap (prevents year-only false positives).
- **Validation (run locally):**
  - `python -m pytest -q` (pass)
  - `python scripts/evaluate_phase4_golden.py --k 10 --sample-users 50`
    - Wrote: `experiments/metrics/phase4_eval_20251229210520.json`
    - Wrote: `reports/phase4_golden_queries_20251229210520.md`
    - Wrote: `reports/artifacts/phase4_golden_queries_20251229210520.json`
  - Golden delta (baseline `20251229175855` → `20251229210520`): no `violation_count` increases; top-10 stable across queries.
- **Next:** If we want measurable top-N gains, consider adding a stronger content signal (e.g., synopsis embeddings) with an explicit artifact contract and offline eval.

### Session 2025-12-26

- What I validated:
  - Confirmed Seed-based (Active Profile = none) top-30 can legitimately show only ~2/30 items with `pop > 0.0%` due to 1-decimal rounding (most pop shares are non-zero but < 0.05%).
  - Confirmed earlier ranking mismatch was caused by using the wrong title column in an ad-hoc reproduction (`title` vs `title_display`). The UI seed “Steins;Gate” resolves via `title_display`.

- What I did (additional):
  - Implemented Phase 2 / Chunk 4: diversity metrics computed from correct inputs (coverage/genre exposure from displayed list; novelty from user history when available).
  - Ensured novelty never displays a misleading numeric value when no rated profile history exists (shows **NA**).

- Decisions made (additional):
  - Treat novelty as **not available** without rated user history; do not compute novelty from item genres or catalog proxies.

- What I changed (additional):
  - Updated novelty + diversity helpers in [src/app/diversity.py](src/app/diversity.py)
  - Updated novelty badge semantics in [src/app/badges.py](src/app/badges.py)
  - Wired profile genre history into UI badges in [src/app/components/cards.py](src/app/components/cards.py)
  - Made diversity panel show novelty as NA when not personalized in [src/app/components/diversity.py](src/app/components/diversity.py)
  - Stored computed user genre history in session state in [app/main.py](app/main.py)
  - Added deterministic wiring test in [tests/test_diversity.py](tests/test_diversity.py)

- Validation run (additional):
  - `python -m pytest -q` (52 passed, 3 warnings)

- What I did (additional):
  - Implemented **Phase 3 / Chunk 1**: aligned onboarding + help + first-load empty-state copy to the implemented UX (Seeds / Browse by Genre / optional Personalization).
  - Removed persona references from user-facing copy and avoided implying personalization when no rated history exists (novelty remains **NA** without ratings).

- Decisions made (additional):
  - Personas are treated as **not implemented** for UX copy until a visible, functional persona selector exists in the UI.

- What I changed (additional):
  - Updated onboarding instructions in [src/app/components/instructions.py](src/app/components/instructions.py)
  - Updated Help / FAQ wording in [src/app/components/help.py](src/app/components/help.py)
  - Updated sidebar Quick Guide + first-load empty-state copy in [app/main.py](app/main.py)
  - Updated this playbook in [docs/IMPLEMENTATION_PLAYBOOK.md](docs/IMPLEMENTATION_PLAYBOOK.md)

- Validation run (additional):
  - `python -m pytest -q` (52 passed, 3 warnings)

- Next session start here (additional):
  - Phase 3 / Chunk 2: choose-a-mode gating (progressive disclosure).

- What I did (Phase 3 / Chunk 2):
  - Added a single top-level **Choose your mode** control: **Personalized / Seed-based / Browse**.
  - Implemented progressive disclosure so only mode-relevant controls and copy are shown.
  - Ensured Personalized mode does **not** silently fall back: when unavailable, the UI states why and how to fix it.
  - Kept score semantics unchanged (**Match score (relative)**) and preserved novelty behavior (novelty stays **NA** without rated history).

- Decisions made (Phase 3 / Chunk 2):
  - The mode selector is the single source of truth for `browse_mode` (legacy flag remains for compatibility).
  - Personalized mode is **gated**: if rated history / embedding is unavailable (or personalization disabled), the app shows an explicit reason instead of showing non-personalized results.
  - To meet the ≤2-action requirement, personalization auto-enables once when entering Personalized mode with a rated profile (user can still disable it).

- What I changed (Phase 3 / Chunk 2):
  - Mode selector + progressive disclosure + personalized gating in [app/main.py](app/main.py)
  - Mode-aware onboarding steps in [src/app/components/instructions.py](src/app/components/instructions.py)
  - Updated Help/FAQ mode definitions in [src/app/components/help.py](src/app/components/help.py)
  - Genre badge clicks now switch the top-level mode to Browse in [src/app/components/cards.py](src/app/components/cards.py)
  - Diversity panel copy is Browse-safe (no “recommendations” wording) in [src/app/components/diversity.py](src/app/components/diversity.py)

- Validation run (Phase 3 / Chunk 2):
  - `python -m pytest -q` (52 passed, 3 warnings)

- Next session start here:
  - Phase 3 / Chunk 3: first-load clarity + empty-state recovery.

### Session 2025-12-22

- What I did:
  - Removed all placeholder/dummy scoring so the app never recommends from fabricated arrays.
  - Added runtime artifact contract validation (MF + metadata) and made failures show clearly in Streamlit.
- What I changed:
  - Enforced MF selection + contract validation in [src/app/artifacts_loader.py](src/app/artifacts_loader.py)
  - Removed dummy scoring init and guarded recommendation paths in [app/main.py](app/main.py)
  - Tightened personalization behavior to avoid all-zero rankings in [src/app/recommender.py](src/app/recommender.py)
  - Added default artifact stems in [src/app/constants.py](src/app/constants.py)
- What I learned:
  - The previous app path depended on dummy mf/knn/pop arrays; real MF artifacts exist but were not wired as `models['mf']`.
- Next session start here:
  - Implement real popularity + (optional) kNN/seed scoring inputs and compute `pop_percentiles` from real data (see [app/main.py](app/main.py)).

### Session 2025-12-23

- What I did:
  - Validated Phase 1 / Chunk 1 end-to-end (tests + UI failure mode).
  - Confirmed the app fails loudly when an invalid MF artifact stem is requested.
- What I changed:
  - Added [pytest.ini](pytest.ini) so `python -m pytest -q` only collects `tests/` (not runnable scripts under `scripts/`).
- What I did (additional):
  - Implemented a single “Active scoring path” label that is computed from the same flags/branches that actually execute.
- What I changed (additional):
  - Added the indicator + safe “Recommendations disabled” labeling in [app/main.py](app/main.py).
- Decisions made:
  - Label priority is: Browse → Recommendations disabled → Personalized (only when personalization is applied) → Multi-seed/Seed-based → Seedless.
- Decisions made (additional):
  - Personalization is considered **unavailable** (and must be stated explicitly) if: no ratings, embedding is missing/near-zero, MF model is missing, MF stem changed since embedding generation, or personalized scoring returns no results. In these cases the app does not silently fall back.
- Validation run:
  - `python -m pytest -q` (40 passed)
  - Manual: set `APP_MF_MODEL_STEM=__bad__` and verified the app shows an actionable error + disables recommendations.
  - Manual (personalization): with the same seeds/filters, Personalization OFF vs ON (Strength 100%) produced a different top-N; editing at least one profile rating changed the top-N again after rerun; the “Active scoring path” label reflected the executed branch.
- What I changed (additional):
  - Wired personalization to the bundle-selected MF artifact and added cache invalidation on ratings/profile/MF stem changes in [app/main.py](app/main.py).
  - Added a small integration test proving rating changes change personalized top-1 in [tests/test_personalization.py](tests/test_personalization.py).
- What I did (additional):
  - Implemented real cold-start detection: `is_in_training = (anime_id in mf_model.item_to_index)` and removed hard-coded `is_in_training=True`.
- What I changed (additional):
  - Wired badge inputs through the UI card renderers in [src/app/components/cards.py](src/app/components/cards.py).
  - Added MF-backed `_is_in_training(...)` helper and used it for displayed items in [app/main.py](app/main.py).
- Validation run (additional):
  - `python -m pytest -q` (41 passed)
  - Spot-check (artifact-backed): 3 trained IDs `[1, 5, 6]`, 2 cold-start IDs `[34591, 34599]` (trained_count=11200, cold_count=1837)
- Next session start here:
  - Manual: toggled Browse / seeds / personalization and verified the “Active scoring path” label changes as expected.
  - (Optional) Verified Browse mode shows Browse and does not claim recommendation scoring.
- Next session start here:
  - Phase 2 / Chunk 1: standardize score semantics (single source of truth) across UI + explanations.

### Session 2025-12-24

- What I did:
  - Proved cold-start badges are correct using the same loaded artifacts the app uses.
- Validation proof:
  - `anime_id=34096` ("Gintama Season 5") => `in_training=False` (not in `mf_model.item_to_index`), so it must display as Cold-start.
  - Observed MF mapping size: 11200 items.
- What I changed:
  - Added [check_in_training_membership.py](check_in_training_membership.py) to quickly validate `anime_id` membership + title lookup.
- Next session start here:
  - Phase 2 / Chunk 1: pick and standardize one score semantic across the app.

- What I did (additional):
  - Implemented Phase 2 / Chunk 1: standardized all recommendation score display to a single semantic: **Match score (relative)**.
  - Removed mixed semantics like “Confidence”, “% Match”, and “/10” for recommendation scores.
- Decisions made (additional):
  - Recommendation scores are displayed as **unitless, uncalibrated match scores** (relative ranking signal). We do not claim bounds or a rating scale.
- What I changed (additional):
  - Added single source of truth for score semantics in [src/app/score_semantics.py](src/app/score_semantics.py)
  - Updated score display in [src/app/components/cards.py](src/app/components/cards.py)
  - Updated sort label + browse-mode score handling in [app/main.py](app/main.py)
  - Updated personalized explanation formatting in [src/app/components/explanations.py](src/app/components/explanations.py)
  - Updated help copy in [src/app/components/help.py](src/app/components/help.py)
  - Added regression tests in [tests/test_score_semantics.py](tests/test_score_semantics.py)
- Validation run (additional):
  - `python -m pytest -q` (47 passed)
- Next session start here (additional):
  - Phase 2 / Chunk 3: compute and display truthful per-item MF/kNN/Pop contribution shares (sum to ~100%).

- What I did (additional):
  - Implemented Phase 2 / Chunk 3: **truthful hybrid explanation shares** computed from actual per-item weighted contributions (not the global weight knobs).
  - Ensured unused components are hidden based on the executed scoring path.
  - Wired a real popularity prior (from the optional kNN artifact’s `item_pop`) into hybrid scoring so MF/Pop shares are meaningful in the UI.
- What I changed (additional):
  - Updated hybrid per-item share computation in [src/app/recommender.py](src/app/recommender.py)
  - Updated formatting to respect `_used` components in [src/app/explanations.py](src/app/explanations.py)
  - Updated multi-seed and blended personalization explanation plumbing in [app/main.py](app/main.py)
  - Added regression tests in [tests/test_truthful_shares.py](tests/test_truthful_shares.py)
- Validation run (additional):
  - `python -m pytest -q` (51 passed)
  - Artifact-backed sanity check: shares sum to 1.0 per item; switching presets changes at least one item’s MF/Pop shares.
  - Manual UI: started Streamlit via `python -m streamlit run app/main.py` and spot-checked that explanations render MF/Pop shares.
- Next session start here (additional):
  - UI spot-check: Multi-seed path should show kNN/content + Pop shares (and sums) for at least 5 items; confirm the displayed shares visibly change when switching weight presets.

---

## 8) 60-Second End-of-Session Update Template

Copy/paste this block at the top of the file (or fill it in-place) at the end of each work session:

**Last updated:** YYYY-MM-DD

**Current phase:** Phase X

**Current blockers (if any):**
- 

**What changed last session (short):**
- 

**Decisions made (only if needed):**
- 

**Next action (single sentence):**
- 

**Next session start here (exact file/function):**
- 

---

## 9) Session Starter Prompt Template (Copy/Paste)

Use this at the start of a new chat to implement exactly one chunk without losing context.

### Template

I’m continuing work on this repo. I want you to implement **Phase {PHASE#} / Chunk {CHUNK#}: {CHUNK_TITLE}**.

Context + source of truth:
- Use the playbook as authoritative context: [docs/IMPLEMENTATION_PLAYBOOK.md](docs/IMPLEMENTATION_PLAYBOOK.md)
- Current date: {YYYY-MM-DD}
- OS: Windows

Scope for this session:
- **Goal:** {1–2 sentences}
- **In-scope tasks:**
  - {Task 1}
  - {Task 2}
  - {Task 3 (optional)}
- **Out of scope:**
  - {Explicit non-goals (e.g., “no refactors”, “no semantics changes”, “no new UI”) }

Constraints (must follow):
- Implement exactly what’s needed for this chunk; avoid “nice-to-haves”.
- Preserve existing design system and UX unless the chunk explicitly requires UX changes.
- Prefer failing loudly with actionable UI errors over silent fallback behavior.
- Keep changes minimal and consistent with the existing style.

Relevant files to inspect first:
- {file 1 path}
- {file 2 path}
- {file 3 path (optional)}

Definition of Done (must satisfy all):
- {DoD 1 — observable/testable}
- {DoD 2 — observable/testable}
- {DoD 3 — observable/testable}
- {DoD 4 (optional)}

What I want you (the assistant) to do:
1) Identify exactly where in the codebase this chunk should be implemented.
2) Implement the smallest set of code changes that meet the Definition of Done.
3) Validate the result (run the narrowest checks available: lint/compile/smoke/tests).
4) Update the playbook Session Log with: decisions made, files changed, validation run, and what’s next.

When you reply, include:
- A short summary of changes (what/where).
- Any remaining risks or follow-ups for the next chunk.

### Optional: “Fast Fill” Checklist (for you, the repo owner)

Fill these before pasting the template:
- {PHASE#}/{CHUNK#}/{CHUNK_TITLE}
- One clear goal sentence
- 2–6 in-scope tasks (verbs)
- 2–6 explicit non-goals
- 3–6 “Done when” bullets that are verifiable
- 2–4 file paths you expect to touch

### Example (Phase 1 / Chunk 1)

I’m continuing work on this repo. I want you to implement **Phase 1 / Chunk 1: Remove placeholder scoring + enforce contracts**.

Context + source of truth:
- Use the playbook as authoritative context: [docs/IMPLEMENTATION_PLAYBOOK.md](docs/IMPLEMENTATION_PLAYBOOK.md)
- Current date: 2025-12-21
- OS: Windows

Scope for this session:
- **Goal:** Prevent any recommendations from being generated using dummy scores; enforce artifact contracts.
- **In-scope tasks:**
  - Remove placeholder MF/kNN/Pop score generation.
  - Add explicit runtime checks for required artifact attributes.
- **Out of scope:**
  - No scoring semantics changes (Phase 2).
  - No large refactors (Phase 4).

Relevant files to inspect first:
- app/main.py
- src/app/artifacts_loader.py
- src/app/recommender.py

Definition of Done (must satisfy all):
- The app never shows recommendations based on placeholder scores.
- Missing MF artifacts/attributes produce a clear UI error and stop execution.
- Real artifacts produce real recommendations.
