
## 1. Executive-Level Fixes

- [ ] Remove all placeholder/dummy scoring paths so recommendations are always generated from real loaded artifacts; app must raise a clear error if required artifacts are missing (High)
- [ ] Implement an explicit “active scoring path” status indicator (e.g., MF-only, Hybrid, Personalized, Cold-start content) that reflects the actual code path used for the current results (High)
- [ ] Ensure personalization works end-to-end by wiring the correct MF model key from the loaded `bundle["models"]` and verifying the personalized ranking changes when user ratings change (High)
- [ ] Standardize score semantics across the app (e.g., “relative score”, “predicted rating”, or “match percentile”) and verify that the displayed explanation matches the chosen semantics everywhere (High)
- [ ] Make cold-start detection real by deriving `is_in_training` from training interactions / MF factor availability, and verify cold-start badges appear for truly unseen items only (High)

---

## 2. User Flow & UX Improvements

- [ ] Align onboarding copy to the implemented UX (profiles + seeds + browse mode); remove persona language unless personas are fully implemented and visible in the UI (High)
- [ ] Add a single “Choose your mode” decision at the top (Personalized / Seed-based / Browse) with only relevant controls shown per mode; verify a first-time user can get results in ≤2 actions (High)
- [ ] Ensure the app clearly answers “What is this / Why care / What next” on first load (1–2 sentences + primary CTA); verify via a cold-start screenshot (Medium)
- [ ] In recommendation mode, show an explicit empty-state checklist when results are empty (e.g., “remove filters”, “try fewer seeds”, “disable browse mode”); verify each suggestion is actionable in-app (Medium)
- [ ] Make the seed workflow explicit: show current seeds, count, and clear action; verify seeds persist correctly across reruns and clearing seeds returns to neutral state (Medium)
- [ ] Ensure “Browse by Genre” mode disables or visually de-emphasizes seed-specific copy; verify headings and help text match mode consistently (Medium)
- [ ] Add consistent tooltips/help text for key controls (Hybrid Weights, personalization strength, filters); verify every control has either help text or is self-explanatory (Low)

---

## 3. Data Science & Modeling Rigor

- [ ] Add an in-app “Model Card / Evaluation” expander that reports dataset snapshot date, split strategy (user-aware + temporal check), and 3–5 headline metrics (NDCG@K, MAP@K, coverage, Gini); verify it matches the Phase 4 artifacts (High)
- [ ] Calibrate or reframe personalized scores so the explanation cannot exceed valid bounds (e.g., if showing “/10”, enforce 0–10); verify with unit tests and a manual profile run (High)
- [ ] Make hybrid explanations truthful by showing per-item source contributions computed from the actual score components used for that item; verify contributions sum to ~100% and reflect the active model path (High)
- [ ] Implement and display a cold-start “content-only” pathway when MF factors are unavailable; verify with a known cold-start item that recommendations still render with a “content-only” explanation (Medium)
- [ ] Add a small “Known limitations & failure modes” section in-app (sparsity, popularity bias, metadata noise); verify it’s visible and consistent with docs (Medium)
- [ ] Validate that diversity metrics shown in-app (coverage, genre exposure ratio, novelty) are computed from correct inputs (user history + catalog genres); verify with a controlled test set and sanity checks (Medium)

---

## 4. Technical & Code Quality Improvements

- [ ] Refactor main.py into smaller modules (sidebar/state, scoring, filtering, rendering) while preserving identical UX; verify by running the app and confirming all features still work (High)
- [ ] Centralize genre/type/year parsing and filtering into reusable functions to eliminate duplicated logic; verify only one implementation exists for each filter type (High)
- [ ] Replace repeated `metadata.iterrows()` loops and repeated `metadata.loc[...]` lookups with cached indexes (e.g., `anime_id -> row`, `anime_id -> genre set`); verify a measurable latency improvement in the performance panel (Medium)
- [ ] Add strict artifact contract checks in the artifact loader (required columns, MF factor matrix, mappings) with actionable error messages; verify failures are informative and non-silent (Medium)
- [ ] Remove `print()` debug logging from the recommendation path and replace with structured logging (or Streamlit-friendly debug toggle); verify no console noise in normal runs (Low)
- [ ] Add a lightweight smoke test that imports the app in “light mode” and confirms key modules load without heavy artifacts; verify it runs in CI (Medium)
- [ ] Add unit tests for: genre coercion, badge payload correctness, explanation formatting, and personalized embedding generation; verify tests pass locally and in CI (Medium)

---

## 5. Portfolio Differentiators

- [ ] Add an interactive “Accuracy vs Diversity” explanation tied to offline metrics (e.g., show metric deltas when toggling weights); verify numbers match Phase 4 evaluation artifacts (High)
- [ ] Add per-recommendation drill-down for “Why this anime?” that shows: matched genres, similar rated titles (if personalized), and source contributions; verify drill-down is consistent with active mode (Medium)
- [ ] Add a visible “Reproducibility & Lineage” section that lists artifact versions/timestamps and whether data is stale; verify it reads from real artifact metadata (Medium)
- [ ] Add a small “Tradeoffs & Decisions” panel describing why MF+hybrid was chosen and what was deferred (ALS/LightFM) with justification; verify it references concrete results (Low)

---

## 6. Reviewer & Hiring Manager Signal

- [ ] Ensure the app demonstrates real ML inference (not a UI demo) by proving recommendations change when: seed changes, weights toggle changes, and user ratings change; verify with a scripted “demo checklist” run (High)
- [ ] Add a transparent “What’s happening under the hood” summary (1 short paragraph) that is accurate and non-technical; verify it matches implemented pipeline steps (Medium)
- [ ] Add a visible “Robustness” note showing temporal validation outcome and leakage safeguards; verify it is consistent with Phase 4 writeups (Medium)
- [ ] Ensure codebase clearly separates concerns (data loading, scoring, UI rendering) and is easy to navigate; verify by file structure and module boundaries (Medium)

---

## 7. Documentation & Presentation

- [ ] Update README with: live demo instructions, screenshots (browse, seed, personalized), and a 60-second “how to use” flow; verify links and images render on GitHub (High)
- [ ] Add a short architecture diagram (data → features → models → artifacts → Streamlit) and confirm it matches repo structure; verify it is included in README or docs index (Medium)
- [ ] Add a “Model & Data Cards” doc page summarizing dataset provenance/licensing, preprocessing, evaluation protocol, and limitations; verify it references actual files/artifacts (Medium)
- [ ] Add a “Demo Script” doc for interviews (3 scenarios: cold start, seed-based, personalized) with expected outcomes; verify it can be followed step-by-step (Low)

---

## 8. Final Polish & Validation

- [ ] Run and document a full “portfolio QA” pass: cold start, seed recommendations, browse mode, MAL import, exclusions, ratings updates, personalization strength slider, and filters; verify no crashes and clear UX throughout (High)
- [ ] Validate that badges/metrics displayed never contradict the underlying data (e.g., cold-start badge correctness, novelty not computed from item genres alone); verify with spot checks and tests (High)
- [ ] Confirm performance targets are met on a typical machine (e.g., <500ms interactive updates, reasonable memory footprint) and reflect real measurements in the performance panel (Medium)
- [ ] Remove or gate any experimental UI remnants (e.g., persona references, unused imports/components) so reviewers see a coherent product; verify no dead UI paths remain (Low)
- [ ] Ensure all dependencies required to run the app are pinned and minimal for deployment; verify `pip install -r requirements.txt` followed by app launch works cleanly (Medium)