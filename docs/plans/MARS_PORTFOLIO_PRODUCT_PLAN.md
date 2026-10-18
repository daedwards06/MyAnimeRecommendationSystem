# MARS Portfolio + Product Plan — From Working Recommender to Credible Portfolio Piece

> Generated: 2026-09-12 | Scope decided with the project owner over a product + portfolio review
> Revised: 2026-10-17 after Task 0.4's corrected evaluation reordered the models (Task 0.6 added,
> Task 2.1 retargeted from kNN to MF, Tasks 1.3 / 2.2 / 2.3 / 2.5 and the success criteria updated);
> then Tasks 0.7, 0.8, 1.8 and a Cut Line added; then Task 0.9 added after Task 0.6 found the app
> never serves kNN
> Executor: Claude via Claude Code (protocol in `CLAUDE.md`) | Est. effort: 4 phases, 22 tasks + a deferred list
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
| ~~MF alone beats the hybrid on accuracy~~ **Superseded by Task 0.4 (2026-09-17)** | Original: MF NDCG 0.0504 vs. hybrid 0.0497. On the corrected protocol hybrid ≈ MF still holds (0.0324 vs. 0.0326), but **both sit below popularity** (0.0347) and MF fell 35% from the figure quoted here — see Task 2.1 |
| ~~Item-kNN scores near zero offline~~ **Resolved by Task 0.4 — it was the evaluation** | Original: NDCG@10 0.0017. `recommend(exclude_seen=True)` masked items using the model's own matrix, so a full-fit artifact removed the held-out item before scoring. On train-split artifacts item-kNN is the **best** model: 0.0628, +81% vs. popularity |
| The shipped blend is mistuned *(added 2026-10-17; re-tuned offline by Task 0.6, served by Task 0.9)* | `BALANCED_WEIGHTS` (mf 0.931 / knn 0.066 / pop 0.003) came from an Optuna sweep run while kNN could not score, so it weights the weakest CF model highest. RRF over the same three sources reaches 0.0586 vs. the shipped blend's 0.0324. `reports/phase4_evaluation.md` §8 names re-tuning the top open item; Task 0.6 does it |
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
3. **Say what the model is.** Tell the result the matched comparison actually gives, including
   the parts that are unflattering. As of Task 0.4 that is: item-kNN wins, the shipped blend ≈ MF
   ≈ popularity on accuracy with ~11× popularity's coverage, and the blend was tuned under a
   broken protocol. Every "≈" or "beats" claim carries an interval (Task 0.6).
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
>
> **Outcome (2026-10-17): that prediction was wrong.** The figures moved a lot. Item-kNN went
> from 0.0017 to 0.0628: the train split stopped `recommend(exclude_seen=True)` from masking the
> held-out item. MF went from 0.0504 to 0.0326, and the interaction snapshot changed between the
> two runs (refreshed 2026-03-14), so this is not a clean before/after. The provisional figures
> below are kept as history. The current table is `reports/phase4_ablation.md`. Task 0.6 and
> Task 2.1 follow up.


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
- [x] `aggregate_phase4_metrics.py`: read `generated_at` (or file mtime) and `users_evaluated`
      from each JSON; keep the **latest** run per `(model, K, users_evaluated)`; `--cohort`
      flag selects one `users_evaluated` for the output parquet
- [x] **Integrity check before any cohort is chosen.** Timestamp dedupe alone would resolve the
      three conflicting `hybrid_weighted@1000` rows silently and hide a real bug: the middle row
      (ndcg 0.041198, map 0.027851) is **bit-identical to `popularity@1000` on both metrics**,
      i.e. either a popularity run written under a hybrid label or a silent fallback to
      popularity. Make the aggregator fail (or loudly warn) when two different models share an
      identical metric vector, and diagnose this instance before re-running
- [x] Make the ablation script runnable from the venv: it needs `PYTHONPATH=.` (add a
      `sys.path` bootstrap or run it as `python -m`), and `df.to_markdown()` imports `tabulate`,
      which is declared in no requirements file — the script currently writes the CSV and *then*
      crashes on the Markdown, leaving the two artifacts out of sync
- [x] `generate_phase4_ablation.py`: use the real model names; add `users_evaluated` and
      `gini` columns; add a "vs. MF" lift column next to "vs. popularity"; sort rows by NDCG
- [x] `run_unified_eval.py`: pass `--sample-users` through consistently and write the seed and
      artifact stems (Task 0.3 constants) into every JSON
- [x] Re-run at 1,000 users, seed 42, against **train-split artifacts** (per the precondition;
      every JSON records the served stems alongside); commit the regenerated
      `phase4_ablation.{csv,md}` and `metrics_by_k.parquet` — *done in `70818e07`. The item
      originally said "against the app's stems", which the train-split precondition supersedes*
- [x] README § Results: one table (model, NDCG@10, MAP@10, Coverage@10, Gini@10, lift vs.
      popularity), one sentence that says hybrid ≈ MF on accuracy with ~11× the coverage of
      popularity; **move** the synthetic temporal-split table out of the README into
      `reports/phase4_evaluation.md` §6 with its caveat
- [x] `docs/MODEL_CARD.md` § Metrics: same table, drop the "treat as draft" note and the
      duplicate-rows note
- [x] `reports/phase4_evaluation.md`: remove the draft banner; §4 embeds the table; §8 tells
      the MF-vs-hybrid story explicitly
- [x] Tests: `compute_lifts` with a two-baseline-row frame raises or dedupes (not `iloc[0]`);
      aggregate dedupe keeps latest
- [x] Tests + ruff green

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
- [x] `Makefile`: `app:` runs `app/main.py`; `lint:` and `fmt-check:` include `app/`
- [x] Fix the one ruff error in `app/`; add `app/` to the CI lint line; leave `scripts/` out
      (394 errors, its own item in Phase 3)
- [x] Move `scripts/test_*.py` to `scripts/archive/` (git-ignored) or delete; any that contain
      real assertions become tests under `tests/`. Five of the seven read personal or
      now-untracked data - `test_explanations.py`, `test_mal_parser.py`,
      `test_personalized_integration.py`, `test_profile_loading.py`, `test_user_embedding.py`
      reference `data/raw/animelist_*.xml` or `data/user_profiles/*.json`, neither of which
      exists in a fresh clone since Task 0.2. Anything promoted to `tests/` must build a
      synthetic fixture instead of reading the owner's export. (`test_mal_parser.py` has no
      assertions at all - it prints a parse of a hardcoded personal XML; archive it.)
- [x] `git rm -r --cached app/assets/archive`; fold the still-useful ideas from
      `UX_Suggestions.md` into `docs/ui_design.md` § Backlog before removing it
- [x] `docs/index.md`: replace the placeholder with a one-screen table of contents linking
      every doc and report (it becomes the write-up landing page in Task 2.5)
- [x] Stale test counts: README (pitch paragraph and project tree) and `CLAUDE.md` say 246
      tests; use the count from this task's own green run. Prefer wording that does not go stale
      (e.g. "~290 tests") over an exact number
- [x] Tests + ruff green

---

## Task 0.6: Re-tune the Blend Under the Corrected Protocol, With Intervals

*(Added 2026-10-17.)*

**Why:** Task 0.4 showed that the app serves a blend weighted toward its weakest CF model.
`BALANCED_WEIGHTS` (mf 0.931 / knn 0.066 / pop 0.003) came from an Optuna sweep run while
item-kNN could not score at all. On the corrected protocol, kNN alone gets NDCG@10 0.0628, RRF
over the same three sources gets 0.0586, and the shipped weighted blend gets 0.0324, which is
below popularity. `reports/phase4_evaluation.md` §8 calls this the highest-value open item.

This task runs before Phase 1 because three later tasks depend on which signal dominates: the
card wording in 1.3, the variants in 2.2, and the baseline the learned reranker has to beat in
2.3.

Two problems with how the old sweep was set up:
- **It tuned on the test users.** `tune_hybrid_optuna.py` and the eval scripts both call
  `sample_user_ids(val_df users, n)` with `RANDOM_SEED = 42` on the same population, so the
  sweep users almost certainly overlap the 1,000-user reporting cohort. Weights tuned on the
  reporting cohort make the next headline number optimistic by construction.
- **No published comparison has an interval.** A −0.6% "hybrid ≈ MF" gap and a −6% "MF vs.
  popularity" gap come from one seed with no spread.

**Preflight Files:**
- `scripts/tune_hybrid_optuna.py` (`_prepare_cache` lines 21–30: the user sample; `tune_hybrid`
  writes `experiments/optuna_studies/hybrid_weights_best.json`)
- `src/eval/splits.py` (`build_validation`, `sample_user_ids`)
- `src/eval/eval_artifacts.py` (`load_eval_models`, `run_metadata`)
- `scripts/evaluate_hybrid.py` (weighted and RRF paths; `--w-mf/--w-knn/--w-pop`)
- `scripts/run_unified_eval.py`, `scripts/aggregate_phase4_metrics.py`,
  `scripts/generate_phase4_ablation.py`
- `src/app/constants.py` (`BALANCED_WEIGHTS`, `DIVERSITY_EMPHASIZED_WEIGHTS`)
- `src/app/recommender.py` (`choose_weights` line ~318)
- `src/models/constants.py` (`DEFAULT_HYBRID_WEIGHTS`)
- `src/app/recommender.py`, `src/app/scoring_pipeline.py` (where the weights are consumed —
  confirm whether RRF could be served without changing the pipeline contract)
- `reports/phase4_evaluation.md` §8–§9, `docs/MODEL_CARD.md` § Metrics, `README.md` § Results

**Validation Commands:**
```powershell
python scripts/tune_hybrid_optuna.py --trials 100 --sample-users 1000
# Expect: the printed tuning-user set has zero overlap with the reporting cohort
python scripts/run_unified_eval.py --k 10 --sample-users 1000
python scripts/aggregate_phase4_metrics.py --cohort 1000
python scripts/generate_phase4_ablation.py
# Expect: phase4_ablation.md has ndcg@10 95% CI columns and rows for hybrid_weighted (old),
# hybrid_weighted (re-tuned), hybrid_rrf, item_knn_sklearn
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [x] Tuning users come from the validation users **minus** the reporting cohort (one helper in
      `src/eval/splits.py`, used by both scripts). Record the tuning-set size and seed in the
      Optuna output JSON
- [x] Per-user metric vectors are kept, and the ablation reports a 95% bootstrap CI on NDCG@10
      and MAP@10 (users resampled, 1,000 resamples, fixed seed), plus a paired bootstrap CI on
      the NDCG difference vs. popularity and vs. MF. Paired, because every model is scored on
      the same users
- [x] Re-tune the weighted blend; evaluate on the reporting cohort: old weights, re-tuned
      weights, RRF, kNN alone
- [x] Decide what the app serves, using the paired intervals: re-tuned weights, RRF, or kNN
      alone. Record it in `docs/decisions.md` with the numbers. If the winner is RRF and serving
      it would change the pipeline contract, stop: ship the best *weighted* blend now and record
      RRF as a follow-up — *done 2026-10-17: the served weights stay. The app has no kNN
      component (`knn=None`), so neither the re-tuned blend (mf 0.048 / knn 0.952) nor kNN alone
      can be served by changing constants. The stop rule applied to the weighted blend itself;
      the follow-up is Task 0.9*
- [x] ~~Update `BALANCED_WEIGHTS` / `DEFAULT_HYBRID_WEIGHTS` (and `DIVERSITY_EMPHASIZED_WEIGHTS`
      if a diversity-aware re-tune changes it); confirm the README Key Features and the
      architecture diagram's "93% MF + 7% kNN" are updated to match~~ — *superseded 2026-10-17
      by the decision above (owner-approved): the app has no kNN component, so the weights can't
      be served by changing constants. Carried by Task 0.9. README Key Features and the diagram
      were corrected here to describe what the app does serve: MF plus a popularity prior*
- [x] Regenerate the ablation, then update README § Results, model card § Metrics and
      `reports/phase4_evaluation.md` §8 (the "re-tune is the top open item" text becomes the
      result). No claim of "≈" or "beats" whose paired CI says otherwise
- [x] ~~Visual check: the app boots in all three modes with the new weights; Steins;Gate seed
      still gives sensible results (seed mode reranks with these CF scores too)~~ — *superseded
      2026-10-17 (owner-approved): no served weights or app code changed in this task, so the
      check was not run. Carried by Task 0.9*
- [x] Tests: tuning and reporting user sets are disjoint; bootstrap CI is deterministic with a
      seed and brackets the point estimate; existing weight-selection tests updated on purpose —
      *weight-selection tests unchanged because the weights are unchanged*
- [x] Tests + ruff green

---

## Task 0.7: A Test That the README Numbers Match the Ablation Table

*(Added 2026-10-17.)*

**Why:** Success criterion 2 (every README number appears verbatim in the ablation) has been
enforced by hand, and by-hand is how the original headline lift came about. A test that reads
both files makes the criterion something CI checks. It needs no model artifacts, so it runs in
CI as-is.

**Preflight Files:**
- `README.md` § Results (the ablation table and the lift sentence after it)
- `reports/phase4_ablation.csv`, `reports/phase4_ablation.md`
- `scripts/generate_phase4_ablation.py` (column names and rounding, which the README copies)
- `docs/MODEL_CARD.md` § Metrics (quotes the same table)
- `tests/test_phase4_aggregate.py` (style of the existing evaluation tests)

**Validation Commands:**
```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q tests/test_published_numbers.py
# Then change one README value by 0.0001 and confirm the test fails, then revert
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] `tests/test_published_numbers.py`: parse the README Results table (model label → NDCG,
      MAP, coverage, Gini, lift) and assert each value equals the CSV value rounded the way the
      README shows it; same for the model card's table
- [ ] A small explicit label map (README display name → ablation model id) in the test, and
      the test fails on any README row the map doesn't cover. A renamed row can't silently
      drop out of the check
- [ ] Prose numbers in the Results paragraph (e.g. "10.9× popularity's coverage", "within
      0.6%") are recomputed from the CSV and checked too; keep the list short and explicit
- [ ] Mutation check from the Validation Commands done and reverted
- [ ] Tests + ruff green

---

## Task 0.8: Smoke Check Against the Real Artifacts; Optional Models Fail Loudly

*(Added 2026-10-17.)*

**Why:** CI runs with `APP_IMPORT_LIGHT=1` and checks out no LFS objects, so no automated check
has ever loaded the real models. That is how synopsis TF-IDF and synopsis embeddings went
unloaded in the deployed app with nobody noticing (found in Task 0.3). `build_artifacts` still
catches `ArtifactContractError` for kNN, TF-IDF, embeddings and neural embeddings and carries on
(`src/app/artifacts_loader.py` lines ~360–412), which works against the convention that the
app never silently falls back. Pulling ~250 MB of LFS on every CI run would use up GitHub's
free LFS bandwidth, so the smoke check runs locally or on a schedule, not on every push.

**Preflight Files:**
- `src/app/artifacts_loader.py` (`build_artifacts`, `_load_models`, the optional-family
  `except ArtifactContractError` blocks)
- `app/main.py` (`@st.cache_resource` around `build_artifacts()` line ~63)
- `app/display.py` (Scoring details expander, which moves to the footer in Task 1.1)
- `src/app/scoring_pipeline.py` (`run_seed_based_pipeline`, `run_personalized_pipeline`: the
  smoke run calls these, not Streamlit)
- `Makefile` (`test`, `ci` targets: pattern for a new `smoke` target)
- `.github/workflows/ci.yml` (no LFS checkout, light import mode)
- `docs/DEPLOYMENT.md`

**Validation Commands:**
```powershell
python scripts/smoke_artifacts.py
# Expect: one line per model family (loaded / stem / size), a seed-mode top-10 for Steins;Gate and a
# personalized top-10 for the example profile, exit 0
# Then rename one synopsis artifact, re-run: expect non-zero exit naming that family; restore it
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] `build_artifacts` records which families loaded and why any did not (e.g. a
      `bundle["load_report"]` dict); the optional-family blocks log at warning level with the
      reason, instead of passing silently
- [ ] The app shows a visible notice when a family that is expected for deployment fails to load
      (one line under the header, details in Scoring details). It keeps running, but says what
      is off. Which families count as "expected" is one constant in `src/app/constants.py`
- [ ] `scripts/smoke_artifacts.py` + `make smoke`: loads the real bundle, prints the load
      report, runs one seed query and one personalized query through the pipeline functions,
      exits non-zero if an expected family is missing or either query returns fewer than 10
      results
- [ ] Optional: a `workflow_dispatch` + weekly `schedule` GitHub workflow with `lfs: true` that
      runs `make smoke`. Note the LFS bandwidth cost in `docs/DEPLOYMENT.md`; owner decides
      whether to enable it
- [ ] Tests: the load report marks a family missing when its artifact is absent (temp-dir
      fixtures, like `tests/test_artifacts_loader.py`); the expected-family notice fires
- [ ] Tests + ruff green

---

## Task 0.9: Serve Item-kNN in the App

*(Added 2026-10-17, from Task 0.6.)*

**Why:** Task 0.6 found that the app has never served kNN. `app/pipeline_runner.py` builds
`HybridComponents(mf=..., knn=None, ...)` and reads the kNN artifact only for its popularity
vector, so the served CF signal is `w_mf·MF + w_pop·pop`. Offline, item-kNN alone (0.0628) and
the re-tuned kNN-led blend (0.0658) are tied with each other (paired CI [−0.0033, +0.0097]),
and both beat MF and popularity. MF and popularity are tied with each other. The app serves the
weaker side of that table. Changing the weights alone cannot fix it (see `docs/decisions.md`,
2026-10-17), so this task wires kNN in and then serves it.

**Preflight Files:**
- `app/pipeline_runner.py` (`HybridComponents` construction line ~203; mean-user MF scores)
- `src/app/recommender.py` (`HybridRecommender._blend`, `get_personalized_recommendations`, which
  has no kNN term)
- `src/app/scoring_pipeline.py` (blended scores ~1166–1201; hard-coded `0.93 * mf_base + 0.07 *
  knn_base` in `hybrid_cf_score` ~1247; `STAGE2_HYBRID_CF_WEIGHT` use ~1416)
- `src/models/knn_sklearn.py` (`score_all`, `_user_profile`: needs a profile built from seeds or
  profile ratings, not a training-user id)
- `src/app/constants.py` (`BALANCED_WEIGHTS`, `DIVERSITY_EMPHASIZED_WEIGHTS`, Stage-2 coefficients)
- `docs/decisions.md` 2026-10-17, `reports/phase4_ablation.md`

**Checklist:**
- [ ] kNN scores in the app from a profile vector: seeds in seed mode, profile ratings when
      personalized; `components.knn` populated (or an equivalent per-request vector)
- [ ] Serve item-kNN alone or the re-tuned blend; they are tied offline, so prefer the simpler
      one unless the visual check says otherwise. Record the choice in `docs/decisions.md`
- [ ] Replace the hard-coded 0.93 / 0.07 in `hybrid_cf_score` with the served weights; re-check
      the Stage-2 coefficients against the new CF magnitude
- [ ] Update `BALANCED_WEIGHTS` / `DEFAULT_HYBRID_WEIGHTS` (and the diversity preset); README
      Key Features and architecture diagram describe what is served
- [ ] Visual check: all three modes boot; Steins;Gate seed still gives sensible results
- [ ] Tests: kNN component present in seed and personalized paths; weight-selection tests
      updated on purpose
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
three signals — `mf` 0.931, `knn` 0.066, `pop` 0.003 (`DEFAULT_HYBRID_WEIGHTS` before Task
0.6) — and **no content signal at all**. Item-kNN is collaborative filtering over the user-item
matrix, so "Content 94.9%" is the kNN share under a false name. Moving that line into an expander
without renaming it would preserve the error somewhere less visible.

**Runs after Task 0.6** *(added 2026-10-17)*. The sentence clauses are chosen by which signal
dominates, and Task 0.6 decides that. Under the old weights an "MF share > 0.5" rule would fire
on almost every card.

**Premise partly corrected by Task 0.6 (2026-10-17).** The app never loads a kNN component
(`HybridComponents(..., knn=None)`). In seed mode the card's `knn` raw share is assembled in
`scoring_pipeline.py` (~1457) from genre overlap, seed coverage, Stage-1 score and synopsis
adjustments, which *are* content signals. So "Content" is closer to the truth than the paragraph
above says. The real defect is that the key is named `knn`. Re-read the share assembly before
relabelling, and run this after Task 0.9, which changes what the CF share contains.

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
      threshold → "very similar story"; **kNN** share is the largest CF share → "fans of <seed>
      also rate it highly" (that sentence is literally what item-item CF measures; MF gets its
      own phrasing, e.g. "matches the taste of people who liked <seed>", and neither fires on a
      fixed share threshold tuned to the old 93/7 weights); popularity band → "a well-known
      pick" / "a hidden gem"); deterministic; never mentions a component with zero share
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
      (5 bullets: the evaluation bug that hid kNN and the re-tune it forced, MF vs. popularity
      (Task 2.1), coverage vs. accuracy, synthetic timestamps, hand-tuned gates) → Quick Start → Links (docs index, model card, write-up)
- [ ] Catalog refresh, project structure, and tech stack move to `docs/` pages linked from
      the index
- [ ] Record the GIF with the final UI; keep a still PNG as fallback; both under
      `app/assets/`; each under 5 MB
- [ ] Every number in the README is copied from `reports/phase4_ablation.md` (the Task 0.7
      test enforces this; extend its prose-number list for any new number the rewrite adds)
- [ ] Tests + ruff green

---

## Task 1.8: Measure the First Load

*(Added 2026-10-17.)*

**Why:** Success criterion 1 says a visitor sees recommendations within 30 seconds, but that has
never been measured. Wake-up alone is 10–20 s, then the app loads ~250 MB of models on Community
Cloud's 1 GB RAM tier. `docs/DEPLOYMENT.md` estimates memory at "~600–800 MB", and nobody has
measured that either. Task 0.6 can change what loads at startup, and if the measurements don't
fit, that is a reason to bring the Phase 3 Hugging Face mirror forward. Do this after Task 0.6
and before Task 1.7 records the GIF.

**Preflight Files:**
- `docs/DEPLOYMENT.md` (§ Streamlit Cloud limits, § Memory Limits, the RAM estimate)
- `app/main.py` (`st.set_page_config`, cached `build_artifacts()`, first render path)
- `src/app/artifacts_loader.py` (`build_artifacts`: what loads eagerly)
- `.python-version` (3.11.9, what Cloud runs) vs. the local 3.12 venv
- `requirements.txt` (pinned versions; confirm the eval-time library versions match)

**Validation Commands:**
```powershell
# After the app has slept: time to first card, three runs, by stopwatch or browser devtools
# Warm: reload, time to first card
python scripts/smoke_artifacts.py --profile-memory   # local peak RSS during load + one query
```

**Checklist:**
- [ ] Cold start (after sleep) and warm load timed on the deployed app, three runs each;
      record the median and the range in `docs/DEPLOYMENT.md` § Performance with the date
- [ ] Peak memory during load + first query measured locally (`--profile-memory` on the Task
      0.8 smoke script, using `tracemalloc` or `psutil` RSS); replace the "~600–800 MB" estimate
      with the measured number
- [ ] If cold start > 30 s or peak memory > 800 MB: record options in `docs/decisions.md`
      (lazy-load the neural model, memory-map artifacts, Hugging Face mirror) and decide with
      the owner; do not implement here
- [ ] Python version: confirm the Task 0.6 ablation reproduces under 3.11 (CI's and Cloud's
      version) to the published rounding, or record that it was checked and differs
- [ ] README demo note under the badge uses the measured cold-start figure
- [ ] Tests + ruff green

---

# Phase 2 — Data-Science Credibility

## Task 2.1: MF Diagnostic — Why Matrix Factorization Sits Below Popularity

*(Retargeted 2026-10-17. This was the item-kNN diagnostic. Task 0.4 answered that question:
kNN's 0.0017 came from `recommend(exclude_seen=True)` masking the held-out item in a full-fit
artifact, and on train-split artifacts kNN is the best model. One piece of that work carries
over, a regression test. The open question is now MF.)*

**Why:** On the corrected protocol, FunkSVD scores NDCG@10 0.0326, below the popularity
baseline's 0.0347. It also fell 35% from the 0.0504 the plan first quoted, and two things changed
between those runs: the protocol and the interaction snapshot (refreshed 2026-03-14). There is a
well-known candidate explanation. FunkSVD is fit to minimize rating error (RMSE) on observed
ratings, and that objective is often weak at top-N ranking over the full catalog. Sparse items
can get high predicted ratings, and the model has no signal for which items a user *chose to
watch*. If that is the cause, it is a good finding to explain, not a bug. It still has to be
shown rather than assumed, because MF drives the personalized mode, and still dominates the
blend unless Task 0.6 changes that.

**Preflight Files:**
- `src/models/mf_sgd.py` (`FunkSVDRecommender.fit`, `recommend(exclude=...)`; the training loss)
- `src/models/knn_sklearn.py` (`recommend(exclude_seen=True)`: which matrix the seen-mask comes
  from; this is the Task 0.4 finding the regression test pins)
- `src/eval/eval_artifacts.py` (`load_eval_models`, the fingerprint cache)
- `scripts/evaluate_knn_mf.py`, `scripts/evaluate_hybrid.py` (MF eval path; exclusion set built
  from train history)
- `src/eval/splits.py` (`build_validation`: the held-out item is one random rating per user, not
  necessarily a *liked* item, so check what "relevant" means for a 3/10 rating)
- `experiments/optuna_studies/mf_sgd_best.json`, `mf_sgd_trials.csv` (what the MF sweep
  optimized; `docs/decisions.md` notes the "tuned" values equal the class defaults)
- `reports/phase4_evaluation.md` §8, `reports/phase3_summary.md` (superseded MF figures and the
  snapshot note)

**Validation Commands:**
```powershell
python scripts/diagnose_mf.py --sample-users 1000
# Expect: a table of NDCG@10 / coverage@10 with paired CIs vs. popularity for: MF as-is; MF on the
# pre-2026-03-14 snapshot (if recoverable) vs. current; MF with a popularity-debiased score; MF
# scored on liked holdouts only (rating >= 8); an implicit-feedback MF (BPR or ALS on watched/not
# watched); and a short conclusion
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] **Carry-over regression test (from the kNN finding):** a kNN model fit on data that
      contains a user's held-out item, evaluated with that user's *train* history, must not mask
      the held-out item. Whichever exclusion source the eval path uses, the test fails if it
      goes back to the model's own matrix
- [ ] Separate the 0.0504 → 0.0326 drop into a protocol part and a snapshot part. Run old protocol
      on new data, and new protocol on new data. Run on old data too if that snapshot can be
      rebuilt; if not, say so
- [ ] Relevance definition: re-score all models with the holdout restricted to liked items
      (rating ≥ 8) as a sensitivity check. Report whether the model ordering changes
- [ ] Objective: add an implicit-feedback MF variant (BPR or ALS; prefer a small numpy
      implementation or the `implicit` package in `requirements-dev.txt`, not the app's
      requirements) and evaluate it on the same cohort with the Task 0.6 intervals
- [ ] `scripts/diagnose_mf.py` writes `reports/mf_diagnostic.md`: table, conclusion, and what
      it means for the served personalized mode
- [ ] If implicit MF clearly beats FunkSVD (paired CI excludes 0): record it in
      `docs/decisions.md` as a candidate for serving. Swapping the served MF is a separate task
      (it touches `user_embedding.py` and the personalized gate). Not done here
- [ ] Model card § Limitations and README "What I learned" cite the result
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
# Expect: reports/figures/ablation_accuracy_vs_coverage.png with one labeled point per variant (10, or 11 with implicit MF); reports/phase4_ablation.md with the same rows
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
```

**Checklist:**
- [ ] Variants: popularity, item-kNN, MF, MF+kNN (no pop), hybrid balanced (**Task 0.6
      re-tuned weights**), hybrid with the pre-0.6 weights (labelled as such, so the re-tune is
      visible on the chart), hybrid diversity-emphasized, hybrid RRF, content TF-IDF, content
      embeddings, plus implicit MF if Task 2.1 added it. All at K ∈ {5, 10, 20}, 1,000 users,
      seed 42, with coverage, Gini and the Task 0.6 bootstrap CIs for every row
- [ ] The trade-off plot draws the NDCG CI as a horizontal error bar on each point
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
- `src/app/recommender.py` (hybrid blend — the baseline the ranker must beat, **with the Task 0.6
  re-tuned weights**. Beating the pre-0.6 weights is not a result: RRF already beats them by 80%
  with no learning. Report the RRF row too)
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
- [ ] If learned NDCG@10 beats the re-tuned hand-weighted blend by more than the seed-to-seed
      spread (run 3 seeds) and the paired bootstrap CI on the difference excludes 0: wire it behind `RERANKER_MODE=learned` in `constants.py` and the personalized
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

**Short form first** *(added 2026-10-17; see Cut Line)*: a ~600-word version (problem, approach,
corrected result, what went wrong and how it was caught) is written right after Task 1.7 and
linked from the README. It does not wait for 2.1–2.4. This task then extends that same file to
full length.

**Why:** A 1,500-word narrative is what a reviewer reads when they want to know how the owner
thinks. The repo has the material scattered across a model card, a draft report, a proposal,
and commit messages.

**Preflight Files:**
- `docs/index.md` (Task 0.5 table of contents — the write-up lives beside it as
  `docs/WRITEUP.md`)
- `docs/PROJECT_PROPOSAL.md` (original goals — useful for "what changed from the plan")
- `docs/MODEL_CARD.md` (limitations and ethics sections)
- `reports/phase4_evaluation.md`, `reports/phase4_ablation.md`, `reports/mf_diagnostic.md`,
  `reports/learned_reranker.md` (Tasks 0.4, 0.6, 2.1–2.3 outputs)
- `notebooks/03_segment_and_error_analysis.ipynb` (Task 2.4 takeaways)
- `docs/decisions.md` (dated decision log started in Task 0.1)

**Validation Commands:**
```powershell
# Manual: docs/WRITEUP.md renders; every internal link resolves; 1,200–1,800 words
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
```

**Checklist:**
- [ ] `docs/WRITEUP.md` sections: the problem and data → approach (why three stages, why
      hybrid) → results (the hero chart, one paragraph) → what went wrong and how it was caught
      (the self-compared headline lift, the exclude-seen masking that hid kNN, weights tuned
      under that protocol and on the reporting cohort) → what did not work (rating-trained MF for
      top-N, embeddings below TF-IDF for cold start, synthetic timestamps) → product decisions
      (explanations, discovery default, demo profiles) → what I would do next
- [ ] Written in first person, past tense, no marketing language; numbers copied from the
      reports, not retyped
- [ ] README links it from the pitch paragraph ("Read the write-up")
- [ ] Tests + ruff green

---

# Phase 3 — Optional and Deferred

Recorded so they are not lost. None block the phases above.

- **Hugging Face Spaces mirror** of the Streamlit app so the demo does not sleep; decision
  recorded in Task 0.1. Bring it forward if Task 1.8's measured cold start or memory doesn't fit.
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
- **Offline evaluation of seed-based mode** *(added 2026-10-17)*. The ablation measures
  recommendations from a user's rating history, which is the personalized path. The mode most
  visitors see, "similar to a title", reranks with ten-plus hand-tuned signals and only has
  golden-query regression checks (`scripts/evaluate_phase4_golden.py`). A simple protocol: for
  each sampled user, seed with one liked title (rating ≥ 8) and score whether their other
  held-out liked titles appear in the top 10, against popularity and pure-CF baselines. This
  would also give Task 1.4's discovery default a number.
- **In-app feedback logging** (thumbs up/down per card to a local table) as the seed of an
  online evaluation story.
- **A second, smaller portfolio project** in a different problem class (forecasting,
  experimentation, or causal inference) so the portfolio shows breadth alongside this depth.

---

## Execution Order

```
Phase 0  0.1 public link (owner) → 0.2 raw data out → 0.3 LFS prune + stems → 0.4 one-cohort eval table → 0.5 tidy
         → 0.6 re-tune blend + intervals → 0.7 README-numbers test → 0.8 artifact smoke check
Phase 1  1.1 name + panels → 1.2 sidebar IA → 1.3 explanations → 1.4 discovery default → 1.5 badge
         → 1.6 demo profiles → 1.8 measure first load → 1.7 README + GIF
Phase 2  2.1 MF diagnostic → 2.2 full ablation + hero chart → 2.3 learned reranker → 2.4 segment notebook
         → 2.5 write-up
Phase 3  as decided
```

**Added 2026-10-17:** 0.6 depends on 0.4 and blocks 1.3 (the clauses depend on the dominant
signal), 1.7 (the README numbers and the "93% MF" text), 2.2 and 2.3. 1.1, 1.2, 1.4, 1.5 and 1.6
do not depend on 0.6 and can go ahead in parallel with it. 0.7 follows 0.6 (it pins the
numbers 0.6 publishes). 0.8 is independent; 1.1's Scoring details move is where its load
report surfaces. 1.8 follows 0.6 and 0.8 (it reuses the smoke script) and precedes 1.7.

## Cut Line

*(Added 2026-10-17.)* This is a portfolio piece, so the plan has to reach "good enough to
send" before it is finished. Tasks in order of how much a reviewer would notice them missing:

| Tier | Tasks | Ships as |
|---|---|---|
| **Must** — portfolio-ready | 0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.3, 1.6, 1.8, 1.7, **2.5 short form** | The first five minutes are clean, the headline result is correct with intervals and enforced by a test, the demo shows personalization in one click, and a ~600-word write-up exists |
| **Strong** — do next | 2.1, 2.2, 1.2, 1.4, 1.5 | Each one is a visible improvement, but missing it won't put a reviewer off |
| **Nice to have** | 2.3, 2.4, Phase 3 | Interview depth more than first-impression value |

The short-form write-up is Task 2.5 cut to the problem, the approach, the corrected result,
and what went wrong and how it was caught. It is written right after 1.7 and later extended
in place as Phase 2 tasks land. It is not a separate document.

Task 0.1 is closed (2026-09-16: the app was already public; the finding did not reproduce).
Tasks 0.2 and 0.5 are independent of everything else, but **0.3 blocks 0.4** — re-running the
evaluation before the artifact stems are settled would republish metrics from the wrong MF
model, which is the defect 0.3 exists to fix. Task 1.7 waits for the rest of Phase 1 and for
Task 0.4. Task 1.3 waits for 0.9, which changes what the CF share contains. Task 2.2 depends
on 0.3, 0.4, 0.6, 0.9, and 2.1. Task 2.5 is last.

## Success Criteria

1. An anonymous visitor clicks the README badge and sees recommendations within 30 seconds,
   with the first card visible without scrolling and a sentence, not a share line, explaining it.
2. Every number in the README appears verbatim in `reports/phase4_ablation.md` and comes from one
   run at one cohort and seed. Every comparative claim ("≈", "beats") is backed by a paired
   bootstrap CI. The README says plainly how the served blend compares with its strongest
   component and with popularity.
3. The served blend weights were tuned on users disjoint from the reporting cohort, under the
   corrected protocol, and the decision is recorded in `docs/decisions.md`.
4. A fresh clone pulls no raw Kaggle data, no personal exports, and one artifact per model
   family; `git lfs ls-files` lists five files.
5. The MF-below-popularity result is explained, the learned-reranker experiment has a written
   conclusion, and a segment-analysis notebook and a write-up exist and are linked from the README.
6. `$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x` green and `ruff check src/ tests/ app/`
   at 0 after every task.
