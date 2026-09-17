# MARS — GitHub Copilot Instructions

## Task Execution Protocol

When told **"Implement Task X.Y"** (with or without a specific plan file named), follow
this protocol exactly:

### Locating the plan
- All plan files live in `docs/plans/` and match the pattern `*_PLAN.md`.
- If the user names a specific plan (e.g. "from the Portfolio Product plan"), find that file.
- If only one plan exists in `docs/plans/`, use it automatically.
- If multiple plans exist and none is specified, list them and ask which one to use.
- In Copilot Chat, attach the identified plan file with `#file:docs/plans/<PLAN_FILE>.md`.

### Step 1 — Preflight (read before writing any code)
1. Open the identified plan file and locate the task by ID (e.g. "Task 1.2").
2. Read every file listed in the task's **Preflight Files** section.
   - In Copilot Chat, attach each file via `#file:<path>` before proceeding.
3. After reading, write a short confirmation (2–4 sentences): what the current state is,
   what the gap is, and what you are about to change. Do not start coding until this is done.

### Step 2 — Implement
- Follow the task's **Checklist** (and **Prompt** section, if present) as the specification.
- Prefer editing existing files over creating new ones.
- Write no comments unless the WHY is non-obvious.
- Do not add features, refactor, or abstract beyond what the task requires.
- Tasks marked **Owner action** contain a step only the repo owner can do. Do everything else
  in the task, then say exactly what is left.

### Step 3 — Validate
- Run every command listed in the task's **Validation Commands** section.
- Show the full terminal output.
- If any command fails, fix the issue before proceeding.

### Step 4 — Update the plan
- For each checklist item you can verify (test passed, file created, command ran green),
  change `- [ ]` to `- [x]` in the plan file.
- Only check off items you can confirm — do not speculatively mark things done.

---

## Plan Files

| File | Description |
|------|-------------|
| `docs/plans/MARS_PORTFOLIO_PRODUCT_PLAN.md` | From the 2026-09-12 product + portfolio review: unblock the demo, repo hygiene, honest evaluation table, UI simplification, data-science credibility (Phases 0–3) |

*(Add new plan files to this table as they are created.)*

---

## Project Context

- **What it is:** A hybrid anime recommender (FunkSVD + item-kNN collaborative filtering,
  synopsis embeddings, metadata overlap) over a 13K-title catalog, with a Streamlit UI.
- **Pipeline:** Stage 0 candidate generation → Stage 1 shortlist → Stage 2 hybrid reranking →
  post-processing. Pipeline in `src/app/scoring_pipeline.py`; Streamlit orchestration in `app/`.
- **Tests:** `$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x` — must stay green.
- **Lint:** `ruff check src/ tests/` — must stay at 0 errors.

## Environment

- Windows 11 / PowerShell. Python 3.12 in `.venv/` — activate with `.\.venv\Scripts\Activate.ps1`
  (bare `python` is Anaconda's interpreter otherwise).
- `ruff` is Anaconda's binary on PATH, not a venv module; do not use `python -m ruff`.
- Model artifacts are Git LFS (`models/*.joblib`). Never commit `experiments/metrics/`,
  `data/raw/jikan/`, `data/processed/images/`, or personal profiles / MAL export XML.
