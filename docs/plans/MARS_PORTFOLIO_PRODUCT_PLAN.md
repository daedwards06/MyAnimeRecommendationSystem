# MARS Portfolio + Product Plan — From Working Recommender to Credible Portfolio Piece

> Generated: 2026-09-12 | Scope decided with the project owner over a product + portfolio review
> Executor: Claude via Claude Code (protocol in `CLAUDE.md`) | Est. effort: 4 phases, 17 tasks + a deferred list
> Owner: data scientist; this is the single portfolio project, so every task is judged by
> "what does a hiring manager see in the first five minutes?"

---

## Why this plan exists

A review on 2026-09-12 read the app, the evaluation artifacts, the README, and the repo as a
reviewer would. The engineering is well above typical portfolio scope (three-stage pipeline,
hybrid CF + content + neural signals, model card, CI with coverage, 246 green tests, LFS for
artifacts). The problems are in what a visitor actually experiences and in how the results are
told.

| Finding | Evidence |
|---|---|
| ~~The public demo link never renders for an anonymous visitor~~ **Not reproduced (2026-09-16)** | The `303` to `share.streamlit.io/-/auth/app` is the anonymous-session cookie handshake every Community Cloud app performs, not an auth wall. Followed with a cookie jar it completes in three hops and serves the app with `200`; the dashboard was already "public and searchable". The original finding inspected only the first hop |
| The README headline lift is the baseline compared with itself | **Corrected 2026-09-16.** `+43% NDCG / +61% MAP` is popularity@500 (0.043849 / 0.029593) over popularity@300 (0.030722 / 0.018332) — the lift percentages match those rows exactly. The hybrid is absent from the ablation table entirely (see the next row), so **no hybrid lift has ever been published**; hybrid@500 is 0.044411 (+44.6%), a number that appears nowhere. In the 1,000-user cohort: popularity 0.0412, MF 0.0504, hybrid 0.0497 — but see the conflicting-rows note in Task 0.4 |
| The ablation table is mislabeled | `generate_phase4_ablation.py` filters on model names `mf`/`hybrid` that do not exist in the parquet (`mf_sgd`/`hybrid_weighted`), so MF and hybrid are silently dropped and the output is ten rows all labeled `popularity` at three different cohort sizes. `compute_lifts` takes `iloc[0]` as the baseline (popularity@300) and the output drops `users_evaluated`, making the mismatch invisible. **This table is where the README's headline number comes from.** Regenerating it reproduces the committed CSV value-for-value |
| MF alone beats the hybrid on accuracy | 1,000-user cohort: MF NDCG 0.0504 / coverage 0.071 vs. hybrid 0.0497 / 0.066. The honest story is "hybrid ≈ MF, both far above popularity on coverage", and it is not told |
| Item-kNN scores near zero offline | NDCG@10 of 0.0017 at 1,000 users, 30× below MF; either a bug or a result that needs explaining before it carries 7% of the blend |
| The evaluation report is labeled a draft | `reports/phase4_evaluation.md` opens with "Draft artifact – populate after running"; the model card says the ablation CSV is a draft with duplicate rows |
| The primary action is fourth in the sidebar | Order is Mode → Profile → Personalization → Search → Filters; the README screenshot shows the sidebar already scrolled |
| Cards show debug output as the explanation | `CF 0.0% \| Content 94.9% \| Popularity 5.1%` renders on every card; to a user "CF 0.0%" reads as "the model did nothing" |
| Discovery mode still leads with franchise entries | Top result for Steins;Gate under "Discovery (similar vibes)" is a Steins;Gate special; `FRANCHISE_CAP_TOP20 = 6` |
| "98% Match" implies calibration the score does not have | `format_user_friendly_score` maps rank 0 → 98% by construction; `score_semantics.py` itself says scores are uncalibrated |
| Personalization is invisible to reviewers | It requires a MyAnimeList XML export, upload, parse, profile pick, mode switch. `data/samples/personas.json` exists and is unused by the UI |
| Three product names | "MARS" (README), "Anime Recommender" (header), "Anime Explorer" (browser tab, Browse header) |
| Repo weight and privacy | `data/raw/rating.csv` (98.79 MiB committed, one row under GitHub's 100 MiB hard limit, Kaggle redistribution), two personal MAL export XMLs with the owner's username tracked, three byte-identical copies of the 189 MB kNN artifact in LFS (the MF copies are **not** identical — see Task 0.3), **1.1 GB** `.git` on clone |
| Analysis is thin for a data-science portfolio | Two notebooks (8 and 17 code cells) against ~14K lines of app code; no error or segment analysis; no narrative write-up (`docs/index.md` is a placeholder) |

**Decisions taken with the owner (2026-09-12 review):**
- Fix what a visitor sees first (Phase 0), then the product surface (Phase 1), then the
  data-science story (Phase 2). Nothing in Phase 2 starts until the demo link works and the
  README numbers are honest.
- The ranking pipeline is not rewritten. Hand-tuned heuristics stay; a learned reranker is an
  offline experiment first (Task 2.3) and only enters the app if it wins.
- Product name is **MARS** everywhere, expanded once as "My Anime Recommendation System".
- Raw Kaggle data leaves the tree and is fetched by a script. Git history is **not** rewritten
  in this plan (the file stays in history; that is an owner decision recorded in Phase 3).
- Plan files and `CLAUDE.md` are tracked, matching the owner's other project.

---

## Design principles for this plan

1. **First five minutes.** Every task is justified by what a reviewer sees: the link, the
   README, the first screen, the first card.
2. **One cohort, one script, one table.** Every number in the README comes from a single
   reproducible run at one sample size and one seed, produced by a script that is in the repo.
3. **Say what the model is.** Hybrid ≈ MF on accuracy; the value is coverage and explainability.
   Tell that story instead of a lift that does not survive a matched comparison.
4. **Users see words, reviewers see numbers.** Plain-language explanations on the card; raw
   shares, timings, and weights behind an expander.
5. **Additive UI changes.** Session-state keys, modes, and the pipeline contract stay; the
   sidebar is reordered and regrouped, not rebuilt.
6. **Private data never enters git.** The owner's profile and MAL exports stay out; demo
   profiles are fictional and committed.
7. **Green gate every task.** `$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x` green and
   `ruff check src/ tests/` at 0 after every task.

---

# Phase 0 — Unblock the Demo and Make the Numbers Honest

## Task 0.1: Public Demo Link — **Owner action**

**Why:** The README badge is the first click. The premise of this task — that it bounces to a
sign-in page for anyone not logged into Streamlit — was **disproved on 2026-09-16**: the app was
already public, and the `303` that prompted the finding is the cookie handshake every Community
Cloud app performs. What survives is the documentation: a check that actually distinguishes
public from private, so this is not re-diagnosed wrongly later.

**Preflight Files:**
- `README.md` (the "Open in Streamlit" badge URL at the top)
- `docs/DEPLOYMENT.md` (§ "Streamlit Cloud limits": notes 1 private app vs. unlimited public;
  no section on the sharing setting)
- `.streamlit/config.toml` (`headless`, `gatherUsageStats`; nothing here controls sharing)

**Validation Commands:**
```powershell
# Must follow redirects AND store cookies: the first hop is always a 303 to /-/auth/app, and
# without a cookie jar the handshake never completes (curl stops after 50 redirects).
curl.exe -sL -c "$env:TEMP\st.txt" -b "$env:TEMP\st.txt" -o NUL -w "%{http_code} %{url_effective}`n" https://myanimerecommendationsystem-x6rqm6vqjmbr2ij8i8yk3b.streamlit.app/
# Expect: 200 and a final URL back on ...streamlit.app/ (public). A chain ending on
# share.streamlit.io with a sign-in page means the app is private.
```

**Checklist:**
- [x] **Owner:** in the Streamlit Community Cloud dashboard, open the app's Settings → Sharing
      and set it to public ("Anyone can view"); confirm the app is not in the "private app"
      slot — *confirmed 2026-09-16: already set to "This app is public and searchable"; no
      change was needed*
- [x] `docs/DEPLOYMENT.md`: add a "Sharing setting" subsection (where it is, what the symptom
      of a private app looks like: 303 → `/-/auth/app` loop) and a "Verify from outside"
      subsection with the curl line above
- [x] README: keep the badge; add one line under it noting the app sleeps after inactivity and
      takes ~10–20 s to wake (Community Cloud behavior)
- [x] Record a decision in `docs/decisions.md` (create it; dated log) on whether to add a
      Hugging Face Spaces mirror later (Phase 3)

---

## Task 0.2: Raw Data and Personal Exports Out of the Tree

**Why:** `data/raw/rating.csv` is 98.8 MB (GitHub hard limit 100 MB) and redistributes a Kaggle
dataset. Two of the owner's MyAnimeList export XMLs, containing the owner's username, are
tracked. `scripts/download_data.py` is a placeholder. A clone should pull code, processed
parquets, and LFS pointers, and fetch raw data on demand.

**Preflight Files:**
- `.gitignore` (§ data rules around lines 205–230; `data/user_profiles/*.json` is already
  ignored with an `!example_profile.json` exception — copy that pattern)
- `scripts/download_data.py` (placeholder; becomes the real fetcher)
- `docs/DATA_SOURCES.md` (Kaggle dataset URL `hernan4444/anime-recommendation-database-2020`)
- `data/README.md` (three-line placeholder; document the layout here)
- `Makefile` (`discover-new` uses `data/raw/anime.csv` as the baseline — keep that path working)
- `scripts/discover_new_ids.py`, `scripts/build_features.py` (confirm which raw files they read)
- `scripts/fetch_jikan.py` (uses `data/raw/jikan.tar.gz`; that cache stays tracked)

**Validation Commands:**
```powershell
git ls-files data/raw
# Expect: .gitkeep, jikan.tar.gz, anime_ids.txt, new_anime_ids_*.txt, new_since_2019.txt — no *.csv, no *.xml
python scripts/download_data.py --help
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [x] `.gitignore`: add `data/raw/*.csv`, `data/raw/*.xml`, `data/raw/animelist_*`; keep
      `jikan.tar.gz` and the small id lists tracked
- [x] `git rm --cached data/raw/rating.csv data/raw/anime.csv data/raw/animelist_*.xml`
      (files stay on disk); commit message states the files remain in history
- [x] `scripts/download_data.py`: fetch the Kaggle dataset via the `kaggle` CLI (document
      `KAGGLE_USERNAME` / `KAGGLE_KEY`), unzip into `data/raw/`, rename to the file names the
      pipeline expects, verify row counts against a small manifest in the script; `--dry-run`
      prints what it would do; exits non-zero with a clear message when the CLI is missing
- [x] `data/README.md`: layout, which files are tracked vs. fetched, and the one command to
      fetch; `docs/DATA_SOURCES.md` links to it
- [x] README Quick Start: add "optional: fetch raw data for retraining" line; the app itself
      still runs from committed parquets with no download
- [x] Tests: `download_data.py` manifest/rename logic as pure functions (no network)
- [x] Tests + ruff green

---

## Task 0.3: Prune Duplicate LFS Artifacts and Point Scripts at One Stem Set

**Why:** `git lfs ls-files -s` shows the 189 MB kNN artifact three times with the **same LFS
object id** `14808c1048` (`v1.0`, `v2025.11.21`, `v2026.03.14`) — pure waste. The MF artifacts
are a different problem: `v1.0` is `e31310c952` while `v2025.11.21` and `v2026.03.14` share
`1358863976`. Eval scripts hard-code `*_v1.0.joblib` while the app loads `*_v2025.11.21_202756`,
so the published metrics were **definitely** produced by a different MF model than the app
serves (verified 2026-09-16 — not a "may"). One stem per artifact family, referenced from one
constant, ends both problems.

**This task blocks Task 0.4.** Re-running the evaluation before the stems are settled would
republish metrics from the wrong MF model again.

**Preflight Files:**
- `src/app/constants.py` (`DEFAULT_MF_MODEL_STEM`, `DEFAULT_KNN_MODEL_STEM`, lines 57–58)
- `src/models/constants.py` (`MODELS_DIR`, `DEFAULT_HYBRID_WEIGHTS`; add the stem constants here
  so scripts do not import from `src.app`)
- `src/app/artifacts_loader.py` (`_select_model_stem` lines 51–92: with two candidates and no
  `preferred_stem`, selection raises "ambiguous" unless `APP_*_STEM` is set — confirm how the
  synopsis families resolve today with two artifacts each)
- `scripts/evaluate_hybrid.py`, `scripts/evaluate_knn_mf.py`, `scripts/explain_hybrid_examples.py`,
  `scripts/sweep_hybrid_weights.py`, `scripts/generate_recommendations_sample.py`,
  `scripts/evaluate_phase4_golden.py`, `scripts/tune_hybrid_optuna.py` (all hard-code `_v1.0`)
- `scripts/inspect_mf_model.py`, `scripts/test_user_embedding.py` (hard-code `v2025.11.21`)
- `tests/test_artifacts_loader.py` (uses its own temp `mf_sgd_v1.0.joblib` fixtures — unaffected,
  confirm)
- `docs/DEPLOYMENT.md` (§ File Size Summary, § LFS)

**Validation Commands:**
```powershell
git lfs ls-files -s
# Expect exactly 5 entries: one item_knn_sklearn, one mf_sgd, one synopsis_tfidf, one synopsis_embeddings, one synopsis_neural_embeddings
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
streamlit run app/main.py   # visual: app boots; "Scoring details" shows the stems in use; no ArtifactContractError
```

**Checklist:**
- [x] Decide the surviving stems: MF and kNN `v2025.11.21_202756` (identical bytes to the
      2026.03 files; the app already prefers them), synopsis TF-IDF / embeddings `v2026.03.14`
      (latest catalog), neural `v2026.01.31`; write the decision in `docs/decisions.md`
- [x] `git rm` the other six `.joblib` files; keep `models/.gitkeep`
- [x] Add `MF_MODEL_STEM` / `KNN_MODEL_STEM` to `src/models/constants.py`; `src/app/constants.py`
      re-exports them; every script above imports the constant instead of a literal
- [x] `_select_model_stem`: confirm that one candidate per family resolves without env vars;
      if the synopsis families were only loading because of an env override, remove the need
- [x] `docs/DEPLOYMENT.md`: update sizes (~250 MB of LFS instead of ~650 MB) and the artifact list
- [x] Tests: a test that the stem constants match a file in `models/` when the directory is
      present (skips in CI)
- [x] Tests + ruff green

---

## Task 0.4: One Cohort, One Script — Rebuild the Evaluation Table

> **Precondition added 2026-09-16 (after Task 0.3).** The artifacts in `models/` are fit on the
> full interaction table, and `build_validation` carves its holdout out of that same table, so
> every MF / kNN / hybrid metric published so far was scored against rows the model trained on.
> Offline evaluation now uses train-split artifacts: run
> `python scripts/save_artifacts.py --split train` **before** the cohort run below.
>
> This is a methodology fix, not a numbers fix — measured across three seeds on a 120K-row slice,
> the model that saw the validation rows scored no higher than the one that did not (mean NDCG@10
> delta −0.0018, between-seed spread 0.0040). Do not expect the provisional figures quoted in this
> task to move much; do expect to be able to say the split was clean. See `docs/decisions.md`,
> "One CF trainer; offline evaluation gets its own train-split artifacts".


**Why:** *(premise corrected 2026-09-16 — the original was wrong in a way that widens this
task.)* The README's `+43% NDCG / +61% MAP` is not a hybrid run compared against an unmatched
popularity run. The ablation generator's model filter drops `mf_sgd` and `hybrid_weighted`
entirely, so **the table contains no hybrid row at all**: the headline is popularity@500
(0.043849 / 0.029593) over popularity@300 (0.030722 / 0.018332) — the baseline against itself at
a different sample size.

The consequence for scope: this is not a re-framing job. No hybrid lift has ever been published,
so every number in README § Results is regenerated from scratch rather than recompared.

The 1,000-user cohort looks more interesting — MF 0.0504, hybrid 0.0497, popularity 0.0412 on
NDCG@10, coverage 0.071 / 0.066 / 0.006 — but **treat the hybrid figure as provisional**:
`hybrid_weighted@1000` has three conflicting rows in the parquet (0.041348 / 0.041198 /
0.049725) and 0.0497 is one of them, chosen without a tiebreak. See the integrity check below.
This task makes one script produce one table from one run, and the README, model card, and
evaluation report all quote it.

**Preflight Files:**
- `data/processed/phase4/metrics_by_k.parquet` (columns `model, K, ndcg, map, coverage, gini,
  users_evaluated`; only K=10; mixed cohorts 300/500/1000; duplicated rows)
- `scripts/aggregate_phase4_metrics.py` (globs every JSON in `experiments/metrics/`, no
  dedupe, no `generated_at` ordering)
- `scripts/generate_phase4_ablation.py` (`MODELS = ["popularity", "mf", "hybrid", "content_tfidf"]`
  — wrong names; `compute_lifts` in `src/eval/phase4_utils.py` takes `iloc[0]` of the baseline)
- `scripts/evaluate_hybrid.py`, `scripts/evaluate_knn_mf.py`, `scripts/evaluate_content_only.py`,
  `scripts/run_unified_eval.py` (the runs that feed the parquet; `--k`, `--sample-users`)
- `src/models/constants.py` (`DEFAULT_SAMPLE_USERS = 300`, `RANDOM_SEED = 42`)
- `src/eval/splits.py` (`build_validation`, `sample_user_ids`)
- `reports/phase4_evaluation.md` (opens with the draft banner; §4 says "include table")
- `reports/phase4_ablation.md`, `reports/phase4_ablation.csv` (the broken outputs)
- `docs/MODEL_CARD.md` (§ Metrics quotes the synthetic temporal split first and the ablation
  second, and calls the ablation a draft)
- `README.md` (§ Results, lines 24–53)
- `Makefile` (`phase4-artifacts` target)

**Validation Commands:**
```powershell
python scripts/run_unified_eval.py --k 10 --sample-users 1000
python scripts/aggregate_phase4_metrics.py
python scripts/generate_phase4_ablation.py
# Expect: reports/phase4_ablation.md has one row per model (popularity, item_knn_sklearn, mf_sgd, hybrid_weighted, hybrid_rrf, content_tfidf, content_embeddings), a users_evaluated column, and every value in the README Results table appears verbatim
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] `aggregate_phase4_metrics.py`: read `generated_at` (or file mtime) and `users_evaluated`
      from each JSON; keep the **latest** run per `(model, K, users_evaluated)`; `--cohort`
      flag selects one `users_evaluated` for the output parquet
- [ ] **Integrity check before any cohort is chosen.** Timestamp dedupe alone would resolve the
      three conflicting `hybrid_weighted@1000` rows silently and hide a real bug: the middle row
      (ndcg 0.041198, map 0.027851) is **bit-identical to `popularity@1000` on both metrics**,
      i.e. either a popularity run written under a hybrid label or a silent fallback to
      popularity. Make the aggregator fail (or loudly warn) when two different models share an
      identical metric vector, and diagnose this instance before re-running
- [ ] Make the ablation script runnable from the venv: it needs `PYTHONPATH=.` (add a
      `sys.path` bootstrap or run it as `python -m`), and `df.to_markdown()` imports `tabulate`,
      which is declared in no requirements file — the script currently writes the CSV and *then*
      crashes on the Markdown, leaving the two artifacts out of sync
- [ ] `generate_phase4_ablation.py`: use the real model names; add `users_evaluated` and
      `gini` columns; add a "vs. MF" lift column next to "vs. popularity"; sort rows by NDCG
- [ ] `run_unified_eval.py`: pass `--sample-users` through consistently and write the seed and
      artifact stems (Task 0.3 constants) into every JSON
- [ ] Re-run at 1,000 users, seed 42, against the app's stems; commit the regenerated
      `phase4_ablation.{csv,md}` and `metrics_by_k.parquet`
- [ ] README § Results: one table (model, NDCG@10, MAP@10, Coverage@10, Gini@10, lift vs.
      popularity), one sentence that says hybrid ≈ MF on accuracy with ~11× the coverage of
      popularity; **move** the synthetic temporal-split table out of the README into
      `reports/phase4_evaluation.md` §6 with its caveat
- [ ] `docs/MODEL_CARD.md` § Metrics: same table, drop the "treat as draft" note and the
      duplicate-rows note
- [ ] `reports/phase4_evaluation.md`: remove the draft banner; §4 embeds the table; §8 tells
      the MF-vs-hybrid story explicitly
- [ ] Tests: `compute_lifts` with a two-baseline-row frame raises or dedupes (not `iloc[0]`);
      aggregate dedupe keeps latest
- [ ] Tests + ruff green

---

## Task 0.5: Repo Tidy

**Why:** Small things a reviewer trips on: a Makefile target that runs a file that does not
exist, a docs index that says "more pages to be added", seven `scripts/test_*.py` ad-hoc scripts
that look like tests, a tracked `app/assets/archive/` with a PDF and old screenshots, and 1 ruff
error in `app/` that CI never sees.

**Preflight Files:**
- `Makefile` (`app:` target runs `app/app.py` — wrong path; `lint:` covers `src/ tests/` only)
- `docs/index.md` (placeholder)
- `scripts/test_explanations.py`, `scripts/test_mal_parser.py`, `scripts/test_personalized_integration.py`,
  `scripts/test_personalized_quick.py`, `scripts/test_profile_loading.py`, `scripts/test_quality_filter.py`,
  `scripts/test_user_embedding.py` (ad-hoc; `pytest.ini` excludes `scripts/` so they never run)
- `app/assets/archive/` (tracked: `1.png`, `2.png`, `3.png`, `Anime Recommender.pdf`,
  `UX_Suggestions.md`); `.gitignore` line 217 `archive/` ignores `scripts/archive` and
  `docs/archive` but these files were tracked before the rule
- `.github/workflows/ci.yml` (`ruff check src/ tests/`)
- `ruff.toml` (`[lint.per-file-ignores]` has `"app/main.py" = ["E402"]`)

**Validation Commands:**
```powershell
ruff check src/ tests/ app/
# Expect: All checks passed!
git ls-files app/assets scripts | Select-String "archive|scripts/test_"
# Expect: no output
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
```

**Checklist:**
- [ ] `Makefile`: `app:` runs `app/main.py`; `lint:` and `fmt-check:` include `app/`
- [ ] Fix the one ruff error in `app/`; add `app/` to the CI lint line; leave `scripts/` out
      (394 errors, its own item in Phase 3)
- [ ] Move `scripts/test_*.py` to `scripts/archive/` (git-ignored) or delete; any that contain
      real assertions become tests under `tests/`. Five of the seven read personal or
      now-untracked data - `test_explanations.py`, `test_mal_parser.py`,
      `test_personalized_integration.py`, `test_profile_loading.py`, `test_user_embedding.py`
      reference `data/raw/animelist_*.xml` or `data/user_profiles/*.json`, neither of which
      exists in a fresh clone since Task 0.2. Anything promoted to `tests/` must build a
      synthetic fixture instead of reading the owner's export. (`test_mal_parser.py` has no
      assertions at all - it prints a parse of a hardcoded personal XML; archive it.)
- [ ] `git rm -r --cached app/assets/archive`; fold the still-useful ideas from
      `UX_Suggestions.md` into `docs/ui_design.md` § Backlog before removing it
- [ ] `docs/index.md`: replace the placeholder with a one-screen table of contents linking
      every doc and report (it becomes the write-up landing page in Task 2.5)
- [ ] Tests + ruff green

---

# Phase 1 — The Product Surface

## Task 1.1: One Name, Fewer Meta-Panels

**Why:** Three names for one product. Four meta-panels (first-run banner, onboarding expander,
Scoring details expander, Help/FAQ) sit between the header and the first card.

**Preflight Files:**
- `app/main.py` (`st.set_page_config(page_title="Anime Explorer", ...)`; the
  `_default_seed_active` banner block)
- `app/display.py` (`render_header` — three mode-dependent H1s; `render_results` — the
  "Scoring details" expander; `render_footer`)
- `src/app/components/instructions.py` (`render_onboarding`, `_MODE_STEPS`)
- `src/app/components/help.py` (`FAQ_MD_RANKED`, `FAQ_MD_BROWSE`)
- `README.md` (title line)

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: tab title and H1 both say MARS; first card is visible without scrolling at 1440×900
```

**Checklist:**
- [ ] Page title and header: **MARS** with a one-line subtitle per mode ("Find anime like the
      ones you love" / "Ranked from your ratings" / "Browse the catalog"); README H1 unchanged
- [ ] First-run banner and onboarding expander merge into one dismissible line under the
      header: "Showing picks for **Fullmetal Alchemist: Brotherhood** — pick your own titles in
      the sidebar" with a "How it works" link that opens the Help expander
- [ ] "Scoring details" moves into the footer next to Help (it is a reviewer panel, not a
      user panel); shows active scoring path, artifact stems, and last pipeline time
- [ ] Help/FAQ rewritten for users first (three short Q&As), with a "For reviewers" subsection
      that keeps the current technical text
- [ ] Tests: header/subtitle helper is a pure function with a test per mode
- [ ] Tests + ruff green

---

## Task 1.2: Sidebar Information Architecture

**Why:** Picking a title is what every visitor does; it is fourth in the sidebar under two
sections most never use. Hybrid weights, MMR, and seed goal are ML knobs on the front page.

**Preflight Files:**
- `app/sidebar.py` (`render_sidebar` order at lines 75–90; `_render_mode_selector`,
  `_render_profile_section`, `_render_personalization_section`, `_render_search_seeds_section`,
  `_render_filters_display_fragment`, `_render_performance_section`)
- `app/state.py` (`init_session_state` keys: `weight_mode`, `top_n`, `sort_by`, `view_mode`,
  `genre_filter`, `type_filter`; query-param bindings `q`, `wm`, `n`, `sort`)
- `app/pipeline_runner.py` (`run_recommendations` reads `SidebarResult` — the contract that
  must not change)
- `tests/test_app_helpers.py` (what is already covered)

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: Search is the first sidebar control; Advanced is collapsed; Personalize is collapsed unless Personalized mode
```

**Checklist:**
- [ ] New order: **Find** (mode as three plain labels "Similar to a title / For me / Browse",
      then the title multiselect) → **Refine** (genre, type, year, top-N, sort) → **Personalize**
      (expander: profile + import + strength; auto-expanded only in "For me" mode) → **Advanced**
      (expander: hybrid weights, MMR toggle + strength, seed goal, reload artifacts, performance)
- [ ] Mode radio keeps the internal values `Seed-based | Personalized | Browse` so
      `pipeline_runner`, state, and tests are untouched; only labels change
- [ ] `SidebarResult` fields and session-state keys unchanged; query params still round-trip
- [ ] Sample-seed buttons (currently under the seed indicator) move directly under the
      multiselect as "Try: Steins;Gate · Your Name · Cowboy Bebop"
- [ ] Tests: label ↔ internal mode mapping; existing `test_app_helpers` unchanged
- [ ] Tests + ruff green

---

## Task 1.3: Plain-Language Explanations on the Card

**Why:** `CF 0.0% | Content 94.9% | Popularity 5.1%` is the truthful-shares debug line, not an
explanation. The data to write a sentence already exists in the contributions dict
(`overlap_per_seed`, `seed_coverage`, `weighted_overlap`, `synopsis_*_sim`, `metadata_affinity`).

**The line is also factually wrong, so this is a correctness fix and not only a presentation
one** (found 2026-09-16). `_DISPLAY_LABELS` maps `knn → "Content"`, but the blend has exactly
three signals — `mf` 0.931, `knn` 0.066, `pop` 0.003 (`DEFAULT_HYBRID_WEIGHTS`) — and **no
content signal at all**. Item-kNN is collaborative filtering over the user-item matrix, so
"Content 94.9%" is the kNN share under a false name. Moving that line into an expander without
renaming it would preserve the error somewhere less visible.

**Preflight Files:**
- `src/app/explanations.py` (`format_explanation`, `format_seed_explanation`, `_DISPLAY_LABELS`
  — the `knn → "Content"` mislabel lives here, lines 26–30)
- `src/models/constants.py` (`DEFAULT_HYBRID_WEIGHTS` — confirms the blend is mf/knn/pop with no
  content term)
- `src/app/scoring_pipeline.py` (`finalize_explanation_shares` line ~2001; the keys written into
  each rec's contributions dict in `run_seed_based_pipeline` — `weighted_overlap`,
  `metadata_affinity`, `synopsis_neural_sim`, `synopsis_tfidf_sim`, `theme_overlap`,
  `seed_coverage`, `overlap_per_seed`)
- `src/app/components/cards.py` (`render_card` line ~362 renders `rec["explanation"]`;
  `render_card_grid` line ~181; "More details" expander line ~466)
- `src/app/components/explanations.py` (`generate_explanation` — the personalized-mode
  sentence builder; reuse its genre-preference phrasing)
- `tests/test_truthful_shares.py`, `tests/test_explain.py` (existing contracts:
  unused components are hidden)

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: card reads e.g. "Shares Sci-Fi and Suspense with Steins;Gate · very similar synopsis · fans of Steins;Gate also rate it highly"; share line only inside More details
```

**Checklist:**
- [ ] `explain_in_words(contributions, seed_titles, item_genres) -> str` in
      `src/app/explanations.py`: up to three clauses chosen by which signal dominates
      (genre/theme overlap → "Shares X and Y with <seed>"; synopsis sim above the high-sim
      threshold → "very similar story"; MF share > 0.5 → "fans of <seed> also rate it highly";
      popularity band → "a well-known pick" / "a hidden gem"); deterministic; never mentions
      a component with zero share
- [ ] Fix `_DISPLAY_LABELS` first: `knn` is labelled as the collaborative signal it is (e.g.
      "Similar-item CF"), not "Content". Check whether "CF" for `mf` stays unambiguous once
      both are CF — "Matrix factorization" / "Similar-item CF" / "Popularity" reads honestly
- [ ] Card renders the sentence where the share line is now; the share line
      (`format_explanation`) moves into "More details" under a "Signal breakdown" caption
- [ ] Multi-seed: "Matches 2 of 3 seeds" stays, appended to the sentence
- [ ] Tests: one test per clause type, a zero-share test, a multi-seed test.
      `test_truthful_shares` **does** change: `test_format_explanation_hides_unused_components`
      asserts on the literal string `"Content"` and its comment reads "Content (knn)" — both
      move to the new label. The behavioural contract (unused components stay hidden) is what
      must survive, not the wording
- [ ] Tests + ruff green

---

## Task 1.4: Discovery by Default, Franchise Entries Opt-In

**Why:** A user asking for "similar vibes" does not want the same franchise's TV special at #1.
Today the default seed goal is `completion` and Discovery still allows six franchise-like items
in the top 20.

**Preflight Files:**
- `src/app/constants.py` (`SEED_RANKING_MODE` default `completion`; `FRANCHISE_CAP_TOP20 = 6`,
  `FRANCHISE_CAP_TOP50 = 15`, `FRANCHISE_TITLE_OVERLAP_THRESHOLD`, strong-match flags; the
  comment block says "Default must preserve current behavior: completion" — this task changes
  that contract on purpose)
- `src/app/franchise_cap.py` (`apply_franchise_cap`, `_classify_franchise_like`,
  `FranchiseCapDiagnostics`)
- `src/app/scoring_pipeline.py` (lines ~1555–1565 where the cap is applied in discovery mode)
- `app/sidebar.py` (seed goal radio in `_render_search_seeds_section`; moves to Advanced in
  Task 1.2 — coordinate)
- `app/pipeline_runner.py` (line ~435 reads `seed_ranking_mode` from session state)
- `tests/test_scoring_pipeline.py`, `tests/conftest.py` (franchise fixtures)

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: Steins;Gate seed → no Steins;Gate-titled entries in the top 10 unless "Include sequels & spin-offs" is checked
```

**Checklist:**
- [ ] Default `SEED_RANKING_MODE = "discovery"`; new `FRANCHISE_CAP_TOPN` (default 0) applied
      to the displayed top-N in discovery mode, with `FRANCHISE_CAP_TOP20/50` kept for the
      longer prefixes; env overrides preserved
- [ ] Sidebar control becomes a single checkbox "Include sequels & spin-offs" (unchecked =
      discovery); internal values unchanged
- [ ] Diagnostics (`FranchiseCapDiagnostics`) surface in the footer Scoring details as
      "N franchise entries hidden — check the box to show them"
- [ ] Tests: cap 0 removes all franchise-like items from the top-N; completion mode unchanged;
      env override still works; the existing default-behavior test updated deliberately
- [ ] Tests + ruff green

---

## Task 1.5: Match Badge Without a Fake Percentage

**Why:** `format_user_friendly_score` maps rank 0 to "98% Match" by construction. The module
docstring says scores are uncalibrated. A tiered label says the same thing honestly.

**Preflight Files:**
- `src/app/score_semantics.py` (`format_user_friendly_score` returns `(text, tooltip, color)`;
  callers depend on the tuple)
- `src/app/components/cards.py` (badge rendering in `render_card` and `render_card_grid`)
- `src/app/components/tooltips.py` (tooltip registry)
- `tests/test_score_semantics.py`

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
```

**Checklist:**
- [ ] Same function, same tuple: text becomes `Top match` / `Strong match` / `Good match` /
      `Worth a look` by within-run percentile quartile; tooltip keeps "rank N of M in this
      run, raw score X"; colors unchanged
- [ ] Card shows the label plus a subtle rank ("#1") so ordering is still readable
- [ ] Help text (Task 1.1) explains that matches are relative to the current run
- [ ] Tests: tiers at boundaries; single-item run; tooltip contains rank
- [ ] Tests + ruff green

---

## Task 1.6: One-Click Demo Taste Profiles

**Why:** Personalization is the most differentiated feature and no reviewer will export a MAL
XML to see it. Two fictional profiles, one click, and the "For me" mode shows its work.

**Preflight Files:**
- `data/samples/personas.json` (two personas with `favorite_genres` and `liked_example_ids`;
  loaded by `app/main.py` `load_personas` and otherwise unused)
- `data/user_profiles/example_profile.json` (the profile schema: `username`, `watched_ids`,
  `ratings`, `status_map`, `import_date`, `stats`)
- `src/data/user_profiles.py` (`PROFILES_DIR`, `list_profiles` globs `*_profile.json`,
  `validate_profile`, `save_profile`)
- `src/models/user_embedding.py` (`generate_user_embedding` — needs rated ids that exist in the
  MF item index, otherwise personalization is gated off)
- `app/sidebar.py` (`_render_profile_section`, `_render_personalization_section` gate logic,
  `_render_mode_selector`)
- `app/pipeline_runner.py` (`_check_personalization_gate`)
- `.gitignore` (`data/user_profiles/*.json` + `!example_profile.json`)

**Validation Commands:**
```powershell
python scripts/build_demo_profiles.py
# Expect: data/user_profiles/demo_action_adventurer_profile.json and demo_drama_slice_fan_profile.json, each with >= 25 ratings, all ids in the MF index
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: "For me" mode shows two "Try a demo profile" buttons; one click → results with the taste-profile explanation, no gate warning
```

**Checklist:**
- [ ] `scripts/build_demo_profiles.py`: for each persona, pick 25–35 titles deterministically
      (seed 42) from the persona's `liked_example_ids` plus the most popular in-training titles
      in its `favorite_genres`, assign ratings 7–10 with a fixed pattern, write
      `demo_<slug>_profile.json` in the profile schema with `demo: true`
- [ ] `.gitignore`: `!data/user_profiles/demo_*_profile.json`
- [ ] Sidebar: in "For me" mode with no active profile, show the demo buttons above the import
      widget; clicking loads the profile, enables personalization, reruns; a "Demo profile"
      caption stays visible while active
- [ ] Rating buttons on cards are disabled for demo profiles (they are read-only fixtures)
- [ ] `docs/user_guide_personalization.md`: "Try it without an export" section first
- [ ] Tests: generated profiles validate; every rated id is in the MF index (skips if models
      absent); demo flag prevents save
- [ ] Tests + ruff green

---

## Task 1.7: README Rewrite and Demo Media

**Why:** The README leads with a feature list and an architecture diagram, then the catalog
refresh how-to and directory tree. A hiring manager wants: what it is, see it, the result,
what was hard, what is next. Runs after Tasks 0.4 and 1.1–1.6 so the screenshot and numbers
are final.

**Preflight Files:**
- `README.md` (current section order: Key Features, Results, Architecture, Quick Start,
  Updating the Catalog, Project Structure, Tech Stack, Documentation)
- `app/assets/demo_screenshot.png` (replace after the UI tasks)
- `reports/phase4_ablation.md` (source of the one Results table)
- `docs/index.md` (Task 0.5 table of contents; the README links here instead of listing every doc)
- `docs/MODEL_CARD.md` § Limitations (source for the "What I'd do differently" bullets)

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
# Manual: README renders on GitHub; every relative link resolves; the badge opens the app
```

**Checklist:**
- [ ] New order: 2-sentence pitch → demo badge + GIF (10–15 s: pick a seed, read a card's
      explanation, switch to a demo profile) → Results (one table + one sentence, from Task 0.4)
      → How it works (existing Mermaid diagram, trimmed) → What was hard / what I learned
      (5 bullets: MF ≈ hybrid, kNN result, coverage vs. accuracy, synthetic timestamps,
      hand-tuned gates) → Quick Start → Links (docs index, model card, write-up)
- [ ] Catalog refresh, project structure, and tech stack move to `docs/` pages linked from
      the index
- [ ] Record the GIF with the final UI; keep a still PNG as fallback; both under
      `app/assets/`; each under 5 MB
- [ ] Every number in the README is copied from `reports/phase4_ablation.md`
- [ ] Tests + ruff green

---

# Phase 2 — Data-Science Credibility

## Task 2.1: Item-kNN Diagnostic

**Why:** Offline item-kNN NDCG@10 is 0.0017 at 1,000 users, 30× below MF and 25× below
popularity. Either the evaluation path is wrong (`recommend` vs `score_all`, exclude-seen,
user-profile shrinkage, the popularity prior) or kNN genuinely fails on this data. Either answer
must be known before kNN carries 7% of the blend and a line in the README.

**Preflight Files:**
- `src/models/knn_sklearn.py` (`ItemKNNRecommender.fit`, `_user_profile`, `recommend`,
  `score_all`; k=40 cosine, shrinkage, popularity prior)
- `scripts/evaluate_knn_mf.py` (lines 55–100: builds `knn_recs` via `recommend(exclude_seen=True)`)
- `scripts/evaluate_hybrid.py` (uses `score_all` — compare the two paths on the same users)
- `src/eval/metrics.py` (`ndcg_at_k`, `average_precision_at_k`, `evaluate_ranking`)
- `src/eval/splits.py` (`build_validation` — check that val items for a user are not in train)
- `experiments/optuna_studies/hybrid_weights_best.json` (the 0.066 kNN weight came from Optuna
  on validation NDCG — confirm what kNN contributed there)

**Validation Commands:**
```powershell
python scripts/diagnose_knn.py --sample-users 300
# Expect: a table of NDCG@10 for kNN under each hypothesis (as-is, no popularity prior, score_all path, no shrinkage, k in {20,40,100}) and a one-paragraph conclusion
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] `scripts/diagnose_knn.py`: runs the hypotheses above on one user sample and prints a
      table; writes `reports/knn_diagnostic.md`
- [ ] If a bug: fix it in `knn_sklearn.py` or the eval script with a regression test; re-run
      Task 0.4's pipeline and update the table
- [ ] If not a bug: `reports/knn_diagnostic.md` explains why (sparsity, rating-weighted
      profiles, prior), and the model card + README "What I learned" cite it
- [ ] Decide whether the kNN weight in `BALANCED_WEIGHTS` stays; record in `docs/decisions.md`
- [ ] Tests + ruff green

---

## Task 2.2: Full Ablation and the Hero Chart

**Why:** The interesting result is the accuracy-versus-coverage trade-off across model variants
at one cohort. One scatter plot tells it faster than any table and becomes the README hero
image.

**Preflight Files:**
- `data/processed/phase4/metrics_by_k.parquet` (after Task 0.4: one row per model at the cohort)
- `scripts/plot_phase4_metrics.py` (existing NDCG/MAP/coverage/Gini vs K plots — K is only 10
  today, so these are single points; repurpose or retire)
- `reports/figures/phase4/` (existing PNGs)
- `scripts/evaluate_hybrid.py` (`--w-mf/--w-knn/--w-pop` — needed for the "MF + kNN, no pop"
  and "Optuna vs. diversity-emphasized weights" rows)
- `src/app/constants.py` (`BALANCED_WEIGHTS`, `DIVERSITY_EMPHASIZED_WEIGHTS`)
- `README.md` § Results (Task 1.7 layout)

**Validation Commands:**
```powershell
python scripts/run_unified_eval.py --k 10 --sample-users 1000 --variants all
python scripts/aggregate_phase4_metrics.py --cohort 1000
python scripts/generate_phase4_ablation.py
python scripts/plot_ablation_tradeoff.py
# Expect: reports/figures/ablation_accuracy_vs_coverage.png with 9 labeled points; reports/phase4_ablation.md with 9 rows
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] Variants: popularity, item-kNN, MF, MF+kNN (no pop), hybrid balanced (Optuna weights),
      hybrid diversity-emphasized, hybrid RRF, content TF-IDF, content embeddings — all at
      K ∈ {5, 10, 20}, 1,000 users, seed 42, with coverage and Gini for every row
- [ ] `scripts/plot_ablation_tradeoff.py`: NDCG@10 (x) vs Coverage@10 (y), one point per
      variant, labeled, popularity and MF highlighted; also NDCG@K curves now that K varies
- [ ] `reports/phase4_evaluation.md` §2–§4 embed the new figures and table; §8 narrative
      updated
- [ ] README hero image = the trade-off plot; caption states the cohort and seed
- [ ] Tests: plot script runs on a 3-row fixture frame and writes a PNG
- [ ] Tests + ruff green

---

## Task 2.3: Learned Reranker Experiment (Offline)

**Why:** Stage 2 blends ten-plus hand-tuned signals. The natural senior-level question is
"why not learn the weights?" Answer it with an experiment: a gradient-boosted ranker over the
same signals, evaluated on the same cohort. A win, a tie, or a loss are all good interview
material; only a clear win changes the app.

**Preflight Files:**
- `src/app/scoring_pipeline.py` (`run_personalized_pipeline` line ~1643 and the per-item
  signal keys: `mf`/`knn`/`pop` scores, `weighted_overlap`, `metadata_affinity`,
  `synopsis_neural_sim`, `synopsis_tfidf_sim`, `synopsis_embed_sim`, `theme_overlap`,
  `mal_score`, popularity percentile)
- `src/app/recommender.py` (hybrid blend — the baseline the ranker must beat)
- `src/models/user_embedding.py` (`generate_user_embedding`, `compute_personalized_scores` —
  per-user MF scores for held-out users)
- `src/eval/splits.py`, `src/eval/metrics.py`
- `scripts/tune_hybrid_optuna.py` (`_prepare_cache` — reuse its per-user score cache pattern)
- `requirements-dev.txt` (add `lightgbm`)

**Validation Commands:**
```powershell
python scripts/train_learned_reranker.py --sample-users 1000 --k 10
# Expect: reports/learned_reranker.md with NDCG@10 / MAP@10 / Coverage@10 for hand-weighted hybrid vs LightGBM LambdaRank on the same held-out users, plus feature importance
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] `src/models/learned_reranker.py`: build a per-(user, candidate) feature frame from the
      top-200 blended candidates per user (train split), label = held-out interaction, group
      by user; LightGBM `lambdarank`; save with the versioned-stem convention
- [ ] `scripts/train_learned_reranker.py`: user-level train/val split disjoint from the eval
      cohort; reports metrics for hand-weighted vs learned on identical candidates; writes
      `reports/learned_reranker.md` with feature importance and a one-paragraph conclusion
- [ ] If learned NDCG@10 beats hand-weighted by more than the seed-to-seed spread (run 3
      seeds): wire it behind `RERANKER_MODE=learned` in `constants.py` and the personalized
      pipeline only; otherwise the app is untouched and the report says why
- [ ] README "What I learned" gets the one-line result either way
- [ ] Tests: feature frame shape and no label leakage (val items absent from features);
      ranker trains on a tiny fixture
- [ ] Tests + ruff green

---

## Task 2.4: Segment and Error Analysis Notebook

**Why:** The portfolio's owner is a data scientist and the repo has two notebooks with 25 code
cells between them. The questions a DS reviewer asks: who does the model work for, where do
the hits come from, what happens at the cold edges.

**Preflight Files:**
- `notebooks/02_pipeline_walkthrough.ipynb` (style and setup cells to mirror)
- `src/eval/metrics.py`, `src/eval/metrics_extra.py`, `src/eval/splits.py`
- `data/processed/popularity.parquet`, `data/processed/interactions.parquet`,
  `data/processed/user_features.parquet`
- `scripts/evaluate_hybrid.py` (per-user recommendation lists — expose a function that returns
  them instead of only aggregates)
- `Makefile` (`venv-kernel` target for the notebook kernel)

**Validation Commands:**
```powershell
python -m jupyter nbconvert --to notebook --execute notebooks/03_segment_and_error_analysis.ipynb --output 03_segment_and_error_analysis.ipynb --ExecutePreprocessor.timeout=1800
# Expect: executes end-to-end; figures saved under reports/figures/segments/
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] `notebooks/03_segment_and_error_analysis.ipynb`: NDCG@10 and hit rate by user-activity
      quartile (train rating count); share of hits by item-popularity decile for popularity,
      MF, hybrid; cold-start users (< 5 train ratings) vs warm; a "misses" table for five
      sampled users with the held-out title and what was recommended instead
- [ ] Every section ends with a two-sentence takeaway; a final "Implications" cell lists what
      changed or should change in the pipeline because of it
- [ ] Figures saved to `reports/figures/segments/`; the notebook is committed executed
- [ ] `docs/index.md` links it; README "What I learned" cites one finding
- [ ] Tests + ruff green

---

## Task 2.5: The Write-Up

**Why:** A 1,500-word narrative is what a reviewer reads when they want to know how the owner
thinks. The repo has the material scattered across a model card, a draft report, a proposal,
and commit messages.

**Preflight Files:**
- `docs/index.md` (Task 0.5 table of contents — the write-up lives beside it as
  `docs/WRITEUP.md`)
- `docs/PROJECT_PROPOSAL.md` (original goals — useful for "what changed from the plan")
- `docs/MODEL_CARD.md` (limitations and ethics sections)
- `reports/phase4_evaluation.md`, `reports/phase4_ablation.md`, `reports/knn_diagnostic.md`,
  `reports/learned_reranker.md` (Tasks 0.4, 2.1–2.3 outputs)
- `notebooks/03_segment_and_error_analysis.ipynb` (Task 2.4 takeaways)
- `docs/decisions.md` (dated decision log started in Task 0.1)

**Validation Commands:**
```powershell
# Manual: docs/WRITEUP.md renders; every internal link resolves; 1,200–1,800 words
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
```

**Checklist:**
- [ ] `docs/WRITEUP.md` sections: the problem and data → approach (why three stages, why
      hybrid) → results (the hero chart, one paragraph) → what did not work (RRF, kNN,
      embeddings below TF-IDF for cold start, synthetic timestamps) → product decisions
      (explanations, discovery default, demo profiles) → what I would do next
- [ ] Written in first person, past tense, no marketing language; numbers copied from the
      reports, not retyped
- [ ] README links it from the pitch paragraph ("Read the write-up")
- [ ] Tests + ruff green

---

# Phase 3 — Optional and Deferred

Recorded so they are not lost. None block the phases above.

- **Hugging Face Spaces mirror** of the Streamlit app so the demo does not sleep; decision
  recorded in Task 0.1.
- **Git history rewrite** to drop `data/raw/rating.csv` and the MAL XMLs from history
  (`git filter-repo`); shrinks the pack from ~800 MB. **Task 0.2 untracked these files but
  deliberately did not touch history**, so a rewrite is now the only remaining step: the
  98.8 MB blob and the owner's MAL username are still in every clone and on GitHub.
  Untracking stops the repo growing, it does not shrink it. Owner decision: it rewrites every
  commit hash and requires a force-push. Weigh it on the username, not the size - the size is
  merely no longer getting worse, whereas the username is published and stays published.
- **Lint `scripts/`** (394 ruff errors, 352 auto-fixable); add to CI when green.
- **Ruff format** the tree (`ruff format --check src/ tests/` would reformat 50 files) in one
  commit with no logic changes.
- **In-app feedback logging** (thumbs up/down per card to a local table) as the seed of an
  online evaluation story.
- **A second, smaller portfolio project** in a different problem class (forecasting,
  experimentation, or causal inference) so the portfolio shows breadth alongside this depth.

---

## Execution Order

```
Phase 0  0.1 public link (owner) → 0.2 raw data out → 0.3 LFS prune + stems → 0.4 one-cohort eval table → 0.5 tidy
Phase 1  1.1 name + panels → 1.2 sidebar IA → 1.3 explanations → 1.4 discovery default → 1.5 badge
         → 1.6 demo profiles → 1.7 README + GIF
Phase 2  2.1 kNN diagnostic → 2.2 full ablation + hero chart → 2.3 learned reranker → 2.4 segment notebook
         → 2.5 write-up
Phase 3  as decided
```

Task 0.1 is closed (2026-09-16: the app was already public; the finding did not reproduce).
Tasks 0.2 and 0.5 are independent of everything else, but **0.3 blocks 0.4** — re-running the
evaluation before the artifact stems are settled would republish metrics from the wrong MF
model, which is the defect 0.3 exists to fix. Task 1.7 waits for the rest of Phase 1 and for
Task 0.4. Task 2.2 depends on 0.3, 0.4, and 2.1. Task 2.5 is last.

## Success Criteria

1. An anonymous visitor clicks the README badge and sees recommendations within 30 seconds,
   with the first card visible without scrolling and a sentence, not a share line, explaining it.
2. Every number in the README appears verbatim in `reports/phase4_ablation.md`, comes from one
   run at one cohort and seed, and the README says plainly that hybrid ≈ MF on accuracy.
3. A fresh clone pulls no raw Kaggle data, no personal exports, and one artifact per model
   family; `git lfs ls-files` lists five files.
4. The kNN result is explained, the learned-reranker experiment has a written conclusion, and
   a segment-analysis notebook and a write-up exist and are linked from the README.
5. `$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x` green and `ruff check src/ tests/ app/`
   at 0 after every task.
