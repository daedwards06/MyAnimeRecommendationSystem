# MARS — Claude Code Instructions

## Task Execution Protocol

When told **"Implement Task X.Y"** (with or without a specific plan file named), follow
this protocol exactly:

### Locating the plan
- All plan files live in `docs/plans/` and match the pattern `*_PLAN.md`.
- If the user names a specific plan (e.g. "from the Portfolio Product plan"), find that file.
- If only one plan exists in `docs/plans/`, use it automatically.
- If multiple plans exist and none is specified, list them and ask which one to use.

### Step 1 — Preflight (read before writing any code)
1. Open the identified plan file and locate the task by ID (e.g. "Task 1.2").
2. Read every file listed in the task's **Preflight Files** section.
3. After reading, write a short confirmation (2–4 sentences): what the current state is,
   what the gap is, and what you are about to change. Do not start coding until this is done.

### Step 2 — Implement
- Follow the task's **Checklist** (and **Prompt** section, if present) as the specification.
- Prefer editing existing files over creating new ones.
- Write no comments unless the WHY is non-obvious.
- Do not add features, refactor, or abstract beyond what the task requires.
- Tasks marked **Owner action** contain a step only the repo owner can do (a dashboard
  setting, an account). Do everything else in the task, then say exactly what is left.

### Step 3 — Validate
- Run every command listed in the task's **Validation Commands** section.
- **Always also run the full CI-equivalent check** — the commands under
  **Exact validation commands** below (tests + lint) — even when the task's own Validation
  Commands are narrower (a single script, a visual check). A task's own commands can pass
  while a change silently breaks something CI would catch; the CI-equivalent check is what
  actually gates the task, not a substitute for it.
- Show the full terminal output for every command to the user, not a summary.
- If any command fails — task-specific or CI-equivalent — fix the issue before proceeding.
  Do not mark the task validated on a partial run.

### Step 4 — Update the plan
- For each checklist item you can verify (test passed, file created, command ran green),
  change `- [ ]` to `- [x]` in the plan file.
- Only check off items you can confirm — do not speculatively mark things done.
- Never check off "Tests + ruff green" (or equivalent) on the task's own Validation Commands
  alone — it requires the Step 3 CI-equivalent run to have actually been shown passing.

---

## Plan Files

| File | Description |
|------|-------------|
| `docs/plans/MARS_PORTFOLIO_PRODUCT_PLAN.md` | From the 2026-09-12 product + portfolio review: unblock the demo, repo hygiene, honest evaluation table, UI simplification, data-science credibility (Phases 0–3) |

*(Add new plan files to this table as they are created.)*

---

## Project Context

- **What it is:** A hybrid anime recommender (FunkSVD + item-kNN collaborative filtering,
  TF-IDF / SVD / neural synopsis embeddings, metadata overlap) over a 13K-title catalog, with a
  Streamlit UI. Portfolio project; the owner is a data scientist.
- **Pipeline:** Stage 0 candidate generation → Stage 1 shortlist → Stage 2 hybrid reranking →
  post-processing (franchise cap, personalization blend, display filters). Pure-Python pipeline in
  `src/app/scoring_pipeline.py`; Streamlit orchestration in `app/` (`main.py`, `sidebar.py`,
  `display.py`, `pipeline_runner.py`, `state.py`); card and panel components in
  `src/app/components/`.
- **Scoring weights and thresholds:** all in `src/app/constants.py` (env-overridable).
- **Offline evaluation:** `scripts/evaluate_*.py` write JSON to `experiments/metrics/`
  (git-ignored); `scripts/aggregate_phase4_metrics.py` builds
  `data/processed/phase4/metrics_by_k.parquet`; `scripts/generate_phase4_ablation.py` writes
  `reports/phase4_ablation.{csv,md}`.
- **Tests:** 246 tests in `tests/`, run with `APP_IMPORT_LIGHT=1` so the app entrypoint imports
  without loading model artifacts. Must stay green after every task.
- **Lint:** `ruff check src/ tests/` (the CI scope) must stay at 0 errors. `app/` has 1 error
  and `scripts/` has ~394; widening the scope is a plan task, not a side effect.
- **Deployed app:** Streamlit Community Cloud, link in the README badge. Model artifacts are
  Git LFS (`models/*.joblib`); processed parquets are committed under `data/processed/`.

## Environment

- Windows 11 / PowerShell. Python **3.12.3** in `.venv/` (`.python-version` says 3.11.9 for
  Streamlit Cloud; the local venv is what runs tests).
- `python` on PATH without activation is **Anaconda's** interpreter, not the venv. Activate
  first in PowerShell (`.\.venv\Scripts\Activate.ps1`) or call `.venv\Scripts\python.exe`
  explicitly.
- `ruff` is **not** installed in the venv; the working binary is Anaconda's `ruff` (0.15.x) on
  PATH. Do not use `python -m ruff`.
- `gh` is not authenticated in this shell; use git directly.
- The full test suite takes ~4 minutes; collection alone ~30 s. Use `-x` to fail fast.
- Never commit: `models/*.joblib` outside LFS, `data/raw/jikan/`, `data/processed/images/`,
  `experiments/metrics/`, timestamped reports, personal profiles (`data/user_profiles/*.json`
  except the example and demo profiles), or the owner's MyAnimeList export XML.

### Exact validation commands

```powershell
# Once per shell
.\.venv\Scripts\Activate.ps1

# Tests (lightweight import mode, mirrors CI)
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x

# Lint (CI scope)
ruff check src/ tests/

# Run the app
streamlit run app/main.py
```

Equivalent from the Bash tool (no activation needed):

```bash
APP_IMPORT_LIGHT=1 .venv/Scripts/python.exe -m pytest -q -x
ruff check src/ tests/
```

## Conventions

- Streamlit UI text is built with `st.markdown(..., unsafe_allow_html=True)` and theme tokens
  from `src/app/theme.py`; keep new UI on the same tokens.
- Session-state keys are initialised in `app/state.py`; add new keys there, not inline.
- Recommendation scores are relative and uncalibrated (`src/app/score_semantics.py`); never
  present them as probabilities or /10 ratings.
- The app must not silently fall back between modes; if a mode cannot run, it says why.
- `ruff.toml` carries a list of pre-existing ignores; do not add to it to make a task pass.
