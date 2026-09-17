# How to Run Plan Tasks

Quick reference for executing tasks from any plan in `docs/plans/` using either
Claude Code or GitHub Copilot.

---

## Where Plans Live

All plan files are in `docs/plans/` and follow the `*_PLAN.md` naming convention.

| Plan | File |
|------|------|
| MARS Portfolio + Product | `docs/plans/MARS_PORTFOLIO_PRODUCT_PLAN.md` |

> To keep plans out of the public repo, add `docs/plans/` (and `CLAUDE.md`,
> `.github/copilot-instructions.md`, this file) to `.gitignore`. They are tracked by default
> so the plan history travels with the repo.

---

## Using Claude Code

Claude Code auto-loads `CLAUDE.md` at session start, so the full protocol
(preflight → implement → validate → update checkboxes) runs automatically.

**One plan in docs/plans/:**
```
Implement Task 0.2 from the plan.
```

**Multiple plans — name it:**
```
Implement Task 1.3 from the Portfolio Product plan.
```

That's all you need to type. Claude Code finds the plan, reads the preflight files,
confirms understanding, implements, runs the validation commands, and updates the
checkboxes — without further prompting.

---

## Using GitHub Copilot (Agent Mode in VS Code)

`.github/copilot-instructions.md` loads the protocol automatically in Agent mode.
You still need to attach the plan file manually with `#file:`.

> **Note:** Each new Copilot chat window loses context. You need the `#file:` reference
> again at the start of every new chat — it does not carry over between sessions.

```
#file:docs/plans/MARS_PORTFOLIO_PRODUCT_PLAN.md

Implement Task 0.2 from the plan.
```

---

## What the Protocol Does (Both Tools)

1. **Preflight** — reads every file listed in the task's `Preflight Files` section
   before touching any code.
2. **Confirm** — writes a 2–4 sentence summary of current state and what will change.
   No code is written until this step is done.
3. **Implement** — follows the task's Checklist as the specification.
4. **Validate** — runs the task's `Validation Commands` and shows the full output.
5. **Update** — checks off completed items in the plan file (`- [ ]` → `- [x]`).

Tasks marked **Owner action** have one step only you can do (for example a Streamlit
Cloud sharing setting). The AI does the rest and tells you what is left.

---

## If the AI Skips a Step

```
Stop — you skipped the preflight. Read the Preflight Files listed in the task first,
then tell me what the current state is before writing any code.
```

The confirmation step should look something like this before any code appears:

> "Current state: `format_explanation` in `src/app/explanations.py` renders
> `CF 0.0% | Content 94.9% | Popularity 5.1%` straight into the card. The gap: no
> plain-language sentence exists. I'm about to add `explain_in_words()` next to it, render
> that on the card, and move the share line into the More details expander."

If you don't see something like that before the code, the preflight was skipped.

---

## Writing New Plan Tasks

Every task needs these two sections in addition to Why / Checklist:

```markdown
**Preflight Files:**
- `path/to/file1.py`   (one-line note on why this file matters)

**Validation Commands:**
\```powershell
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/
\```
(Note what to look for in the output — e.g. "246 passed", "All checks passed!")
```

Without `Preflight Files`, the AI has no anchor for the preflight step and may skip it.
Without `Validation Commands`, there is no exit condition — "done" becomes subjective.

---

## Adding a New Plan

1. Create the file in `docs/plans/` with a `_PLAN.md` suffix.
2. Add a row to the Plan Files table in:
   - `CLAUDE.md`
   - `.github/copilot-instructions.md`
   - The table above in this file.
3. Each task in the plan should have **Preflight Files** and **Validation Commands**.
