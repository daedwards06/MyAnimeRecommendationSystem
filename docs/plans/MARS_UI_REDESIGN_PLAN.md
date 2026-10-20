# MARS UI Redesign Plan — 90s Anime Aesthetic and a Better First Five Minutes

> Generated: 2026-10-19 | Scope: visual redesign and UX improvements of the existing Streamlit app
> Executor: Claude via Claude Code (protocol in `CLAUDE.md`), design decisions sourced from the
> UI UX Pro Max skill | Est. effort: 5 phases, 19 tasks + a deferred list
> Owner: data scientist; follows `docs/plans/MARS_PORTFOLIO_PRODUCT_PLAN.md`, so every task is
> still judged by "what does a hiring manager see in the first five minutes?"
> Depends on: Portfolio plan Phase 1 (IA, explanations, badges, demo profiles) being merged. This
> plan restyles that surface; it does not reopen its decisions.

---

## Why this plan exists

The portfolio plan fixed what the app *says* (honest numbers, plain-language explanations,
one-click demo profiles, a sidebar that leads with the primary action). It did not touch what
the app *looks like*: the default Streamlit theme reads as a prototype, and a recommender for
anime is a natural place to show product taste. The goal is a distinct 90s anime look (cel
shading, title cards, a sunset / night-sky palette, a light CRT texture) that makes the demo
memorable, without costing load time, readability, or any of the contracts the portfolio plan
put under test.

The findings table is filled by Task 0.3 rather than written from memory, so every row has
evidence the same way the portfolio plan's review did.

Ranked by impact on the first five minutes. Full rows, with decisions, are in
`docs/redesign/UX_PLAN.md`; where styling lives is in `docs/redesign/STYLE_INVENTORY.md`.

| Finding | Evidence |
| ------- | -------- |
| F1 Mix bar above the first card miscounts (Top-10% counted as Mid, Hidden gems always 0); badge explanations fall back to generic text for the same reason | `src/app/badges.py:14-20` vs `app/display.py:361, 373`, `src/app/components/tooltips.py:47-60`; `baseline/seed_1440x900.png` "Popular 1 · Mid 9 · Hidden gems 0" over mostly "Top 10%" cards |
| F2 For me mode header says "Similar to Fullmetal Alchemist: Brotherhood" and the intro says "Load a rated profile…" with a demo profile loaded | `baseline/personalized_1440x900.png`; `app/main.py:175-207`; `src/app/components/instructions.py:9-31` |
| F3 Secondary text fails 4.5:1: muted `#A0AEC0` 2.18, tier badges 2.47–3.04, card meta colors 1.56–2.37, primary 4.17 | `src/app/theme.py:31, 35-50`; `src/app/score_semantics.py:47-50`; ratios computed vs `#FAFBFC` |
| F4 Warm first card at a median of 8.9 s (5.3–14.0 s), with one spinner line as feedback; cold load shows none; skeleton component unused | `baseline/timing.json`; `app/pipeline_runner.py:377`; `app/main.py:69`; `src/app/components/skeletons.py` (no importers) |
| F5 Phone: sidebar collapsed, so the mode switch is hidden; first card title at y ≈ 875 on an 844 px screen; cards ≈ 1,200 px tall; page 12,120 px | `baseline/seed_390x844.png`; `src/app/components/cards.py:85, 327, 416, 440` |
| F6 Every non-primary button gets the 30 px genre-pill style; sample-seed labels wrap mid-word ("Steins;G / ate") | `app/display.py:101-119`; `baseline/seed_1440x900.png` sidebar |
| F7 Card title announced twice (poster caption + h3); tier badge inside the heading; "Trained / Novelty NA" jargon on every card | `src/app/components/cards.py:85, 97, 356-359, 440-453` |
| F8 Popularity band has four names: Long Tail, Hidden gems, a hidden gem, Long-tail | `src/app/badges.py:20`; `app/display.py:398, 413`; `src/app/explanations.py:135`; `src/app/components/tooltips.py:55` |
| F9 Empty states print one generic "Try:" list instead of naming the active filter; two panels use hard-coded colors | `app/main.py:220-233`; `app/display.py:527-576` |
| F10 Personalized gate shown in both sidebar and main area; visitor error mentions `APP_IMPORT_LIGHT` | `app/sidebar.py:483-494`; `app/main.py:175-188, 234-238` |
| F11 No focus styles; `!important` button overrides may hide the focus ring; hover transforms without a reduced-motion guard | `app/display.py:85-131` |
| F12 Grid-view add-seed button is icon only ("🔄") | `src/app/components/cards.py:237-242` |
| F13 Three palettes in use plus dark one-offs on a light page | `docs/redesign/STYLE_INVENTORY.md` §§4–5 |
| F14 Browse starts empty: three interactions before any title | `app/main.py:171-173` |
| F15 Explanation repeats the seed title twice | `baseline/seed_1440x900.png`; `src/app/explanations.py` |
| F16 Six Refine controls always shown before Personalize | `app/sidebar.py:717-853` |
| F17 Last pipeline time appears in two panels | `app/sidebar.py:990-992`; `app/display.py:662-663` |
| Styling sites: 96 lines match `unsafe_allow_html\|<style\|style=` across 6 files | Task 0.3 validation command; per-file table in `STYLE_INVENTORY.md` |

**Decisions taken up front:**

- Streamlit stays. No framework migration in this plan (recorded in Phase 4 as deferred).
- The ranking pipeline, models, evaluation, and every published number are out of scope. No file
  under `src/models/`, `src/eval/`, or `reports/` changes in this plan.
- The aesthetic evokes the era; it does not copy any series. No real logos, characters, or
  recreated title cards in the app chrome. Catalog posters are the only franchise imagery.
- Design tokens live in one Python module and are generated into `config.toml` and CSS, so the
  palette cannot drift between files (same idea as the README-numbers test).
- The UI UX Pro Max skill is used for design decisions only (palette, typography, UX rules,
  anti-patterns, checklist). Its stack-specific code guidance is ignored.

---

## Design principles for this plan

1. **First five minutes, still.** The redesign may not slow the first card. Budget: warm time to
   first card no more than 1 s slower than the Task 0.2 baseline; no image assets for texture
   (CSS only); web fonts load with `display=swap` and real fallback stacks.
2. **Era, not IP.** Cel-style flat color, hard shadows, outlined display type, title-card
   framing, katakana as decoration. Nothing that reproduces a specific show's logo or art.
3. **Readability beats texture.** Text contrast ≥ 4.5:1 on every token pair, enforced by a test.
   Scanlines and noise never sit behind body text. All motion respects
   `prefers-reduced-motion`.
4. **Additive and contract-preserving.** Session-state keys, the mode values
   `Seed-based | Personalized | Browse`, `SidebarResult`, and the pipeline contract stay
   exactly as the portfolio plan left them. Tests that assert on visible strings change only on
   purpose, with the reason in the commit message.
5. **One token source, one stylesheet entry point.** Tokens in `src/app/theme_tokens.py`; CSS in
   `app/styles/`, injected once from `app/main.py`. No inline style strings in components.
6. **Selectors that survive upgrades.** Style the app's own classes and `data-testid` hooks, never
   Streamlit's generated `st-emotion-cache-*` class names.
7. **The live check stays green.** `scripts/check_live_app.py` detects the first card by the
   "N recommendations" header plus a poster image outside `stSidebar`. Both survive every task.
8. **Green gate every task.** `$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x` green and
   `ruff check src/ tests/ app/` at 0 after every task.

---

# Phase 0 — Setup, Baseline, and Audit

## Task 0.1: Install the Skill and Extend the Protocol

**Why:** The skill has to be available to Claude Code in this repo, and `CLAUDE.md` has to say
how to use it here, or it will default to HTML + Tailwind output and start writing React.

**Preflight Files:**

- `CLAUDE.md` (existing executor protocol; add a section, do not rewrite)
- `.gitignore` (decide whether `.claude/skills/` is tracked)
- `requirements.txt` (confirm the pinned Streamlit version; the portfolio plan notes 1.38
  locally, which matters for theming options in Task 2.2)

**Validation Commands:**

```
node -v                                   # v20 or newer
npx ui-ux-pro-max-cli init --ai claude
Test-Path .claude/skills/ui-ux-pro-max/SKILL.md   # True
python .claude/skills/ui-ux-pro-max/scripts/search.py "dashboard" --domain chart
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
```

**Checklist:**

- [x] **Owner:** install the skill project-locally (command above) and start a new Claude Code
      session
- [x] `CLAUDE.md` § "UI redesign rules": Streamlit only (no React/Vue/Tailwind/standalone HTML);
      skill used for design decisions only; tokens in `src/app/theme_tokens.py`; CSS only in
      `app/styles/`; no `st-emotion-cache-*` selectors; the eight principles above by reference
      to this plan
- [x] `.gitignore`: ignore `.claude/skills/ui-ux-pro-max/` (third-party, reinstallable) and track
      `design-system/` (project decisions); record the choice in `docs/decisions.md`
- [x] Tests + ruff green

---

## Task 0.2: Baseline Capture

**Why:** A redesign without a before-state cannot show it improved anything, and the GIF and
write-up will want a before/after. The timing baseline sets the performance budget in
principle 1.

**Preflight Files:**

- `scripts/check_live_app.py` (Playwright pattern, first-card detector; reuse, do not fork)
- `app/main.py`, `app/display.py`, `app/sidebar.py` (the three surfaces to capture)
- `docs/DEPLOYMENT.md` § Performance (warm median 10.9 s on the deployed app)

**Validation Commands:**

```
streamlit run app/main.py                 # separate terminal
python scripts/capture_ui_baseline.py --url http://localhost:8501
# Expect: docs/redesign/baseline/{seed,personalized,browse}_{1440x900,390x844}.png and
# docs/redesign/baseline/timing.json (3 runs, median and range, local warm)
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
```

**Checklist:**

- [x] `scripts/capture_ui_baseline.py`: reuses the `check_live_app.py` detector (import it, or
      factor the detector into a shared helper), drives each mode (Seed-based with the default
      seed, Personalized with a demo profile, Browse) at desktop and phone widths, saves
      full-page screenshots, records local warm time to first card over three runs
- [x] If `check_live_app.py` has no `--url` option, add one (default stays the deployed URL)
- [x] Commit the baseline images and `timing.json`; keep each PNG under 1 MB
- [x] Tests: the shared detector helper has a unit test on a fixture HTML page (fires with header
      + poster, times out without)
- [x] Tests + ruff green

---

## Task 0.3: Style Inventory and UX Audit

**Why:** Fills the findings table. Two questions: where does styling live today (so Task 2.1 can
consolidate it), and what in the flow from landing to a useful recommendation is still costing
the visitor time or clarity after the portfolio plan's Phase 1.

**Preflight Files:**

- `app/main.py`, `app/display.py`, `app/sidebar.py`, `app/pipeline_runner.py`
- `src/app/components/cards.py` (`render_card`, `render_card_grid`, "More details" expander)
- `src/app/components/instructions.py`, `src/app/components/help.py`,
  `src/app/components/tooltips.py`
- `src/app/score_semantics.py` (badge tiers and colors)
- `.streamlit/config.toml`
- `docs/ui_design.md` (§ Backlog holds the ideas folded in from `UX_Suggestions.md`)
- `docs/redesign/baseline/` (Task 0.2 screenshots)

**Validation Commands:**

```
Select-String -Path app/*.py, src/app/**/*.py -Pattern "unsafe_allow_html|<style|style=" | Measure-Object
# Record the count; Task 2.1 drives it to the single injection point
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
```

**Checklist:**

- [x] `docs/redesign/STYLE_INVENTORY.md`: every place styling is set (config.toml keys, `<style>`
      blocks, inline `style=` attributes, HTML built in f-strings), with file and line
- [x] Audit using the skill's UX domain (`search.py "<topic>" --domain ux` for loading states,
      empty states, error messages, forms, focus, touch targets, responsive) against the
      baseline screenshots; cover: steps to first useful result per mode, loading feedback while
      the pipeline runs, empty state when filters remove everything, error and gate messages,
      phone width, keyboard focus, reading order of a card
- [x] Fill this plan's findings table (evidence column mandatory) and write
      `docs/redesign/UX_PLAN.md`: findings ranked by impact on the first five minutes, each
      marked **fix in Phase 3**, **defer**, or **won't fix** with a reason
- [x] **Owner:** approve UX_PLAN.md before Phase 3 starts
- [x] No code changes in this task

---

# Phase 1 — The Design System

## Task 1.1: Explore the Skill's Catalog and Generate the Design System

**Why:** The skill's reasoning engine works from product type and industry, so left alone it
returns a clean, modern "entertainment" system. Searching the style and typography domains for
era terms first gives it something to lean toward, and persisting the result gives every later
session the same source of truth.

**Preflight Files:**

- `.claude/skills/ui-ux-pro-max/SKILL.md`
- `docs/redesign/UX_PLAN.md` (Task 0.3)
- `docs/redesign/STYLE_INVENTORY.md` (the components the system must cover)

**Validation Commands:**

```
python .claude/skills/ui-ux-pro-max/scripts/search.py "retro 90s" --domain style
python .claude/skills/ui-ux-pro-max/scripts/search.py "vaporwave VHS cel animation" --domain style
python .claude/skills/ui-ux-pro-max/scripts/search.py "bold display playful rounded" --domain typography
python .claude/skills/ui-ux-pro-max/scripts/search.py "entertainment streaming night" --domain color
python .claude/skills/ui-ux-pro-max/scripts/search.py "recommendation results" --domain chart
python .claude/skills/ui-ux-pro-max/scripts/search.py "anime recommendation entertainment retro" --design-system --persist -p "MARS"
# Expect: design-system/mars/MASTER.md
```

**Checklist:**

- [x] Shortlist the top style, palette, and typography matches with one line each in
      `docs/redesign/SKILL_SEARCH.md`; **owner** picks the direction
- [x] Generate and persist the design system with the chosen direction in the query
- [x] Page overrides for the three modes only if the audit found mode-specific needs:
      `--page "seed"`, `--page "personalized"`, `--page "browse"`
- [x] Note in MASTER.md which skill rules do not apply to Streamlit (e.g. `cursor-pointer` on
      native widgets, SVG icon rules for widgets Streamlit renders) so later audits skip them
      instead of hacking around the framework

---

## Task 1.2: Lock the 90s Anime Tokens, With a Contrast Test

**Why:** This is where the era actually comes through, and it is the one place a palette can
quietly fail accessibility. Putting tokens in Python makes them testable: contrast pairs and the
sync with `config.toml` become something CI checks, not something remembered.

**Preflight Files:**

- `design-system/mars/MASTER.md` (Task 1.1)
- `.streamlit/config.toml`
- `src/app/score_semantics.py` (badge colors; tier colors become tokens here)
- `tests/test_score_semantics.py` (asserts on colors; update on purpose)

**Validation Commands:**

```
python scripts/build_theme.py
# Expect: .streamlit/config.toml [theme] and app/styles/tokens.css regenerated from src/app/theme_tokens.py
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q tests/test_theme_tokens.py
# Then set one text token to a low-contrast value, confirm the test fails, revert
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
```

**Checklist:**

- [x] MASTER.md § "90s Anime Overrides": palette (starting point, owner adjusts: night navy
      `#1B1F3B` background, deep panel `#262B52`, sunset orange `#FF7A45`, magenta `#E8417A`,
      sakura `#FFC2D4`, cel cream `#FFF4E0` text, VHS teal `#3FB8AF`), display face Dela Gothic
      One (outlined, hard offset shadow), body face M PLUS Rounded 1c, both with Japanese glyph
      coverage for katakana accents; card rules (3 px border, hard shadow, no blur); texture
      rules (scanlines ≤ 6% opacity, background only)
- [x] `src/app/theme_tokens.py`: one `TOKENS` dict (colors, font stacks with fallbacks, radii,
      border widths, shadow offsets) and a `TEXT_PAIRS` list of (foreground, background) pairs
      actually used for text, including badge tiers
- [x] `scripts/build_theme.py`: writes the `[theme]` section of `.streamlit/config.toml`
      (leaving other sections untouched) and `app/styles/tokens.css` as CSS custom properties
- [x] `tests/test_theme_tokens.py`: every `TEXT_PAIRS` entry ≥ 4.5:1 (WCAG relative luminance);
      generated `config.toml` theme and `tokens.css` match `TOKENS` (fails if someone edits a
      generated file by hand); badge tier colors come from tokens
- [x] Tests + ruff green

---

## Task 1.3: Static Mockups Before Code

**Why:** The aesthetic is a taste decision, and taste decisions are cheaper to make on a static
page than across six Streamlit files. Three mockups let the owner pick a direction for the
header, card, and sidebar before any component changes.

**Preflight Files:**

- `design-system/mars/MASTER.md`, `app/styles/tokens.css`
- `docs/redesign/baseline/seed_1440x900.png` (layout to keep)
- `src/app/components/cards.py` (the real card's content: poster, title, badge, rank,
  explanation sentence, "More details")

**Validation Commands:**

```
start docs/redesign/mockups/index.html    # visual: three directions side by side, desktop and phone width
```

**Checklist:**

- [x] `docs/redesign/mockups/index.html`: one static page using `tokens.css`, showing the header,
      one result card, and the sidebar top in three intensities: **Subtle** (palette + type
      only), **Title card** (adds outlined display type, episode-style section headers, hard
      shadows), **Full broadcast** (adds scanlines, a VHS-style hover, katakana accents)
- [x] Real content from the app (Steins;Gate seed, one real explanation sentence) with a
      placeholder poster block, not a real poster file
- [x] **Owner:** pick one direction (or a mix) and record it in `docs/decisions.md`; MASTER.md
      updated to match
- [x] Mockups are reference only; nothing under `docs/redesign/mockups/` is loaded by the app

---

# Phase 2 — Apply the Look

## Task 2.1: Consolidate Styling (No Visual Change)

**Why:** Styling scattered across f-strings and inline attributes is how a redesign turns into
half-old, half-new. This task moves every style into one place first, with the app looking the
same afterwards, so the look itself changes in a contained diff.

**Preflight Files:**

- `docs/redesign/STYLE_INVENTORY.md` (Task 0.3, the list to work through)
- `app/main.py` (where `inject_styles()` is called once, after `st.set_page_config`)
- `src/app/components/cards.py`, `app/display.py`, `app/sidebar.py`,
  `src/app/components/instructions.py`, `src/app/components/help.py`
- `tests/test_app_helpers.py`, `tests/test_header_intro.py`

**Validation Commands:**

```
Select-String -Path app/*.py, src/app/**/*.py -Pattern "<style|style=" | Measure-Object
# Expect: only app/styles loader matches
python scripts/capture_ui_baseline.py --url http://localhost:8501 --out docs/redesign/after_2_1
# Visual diff against docs/redesign/baseline: no intended differences
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
```

**Checklist:**

- [x] `app/styles/`: `tokens.css` (generated), `base.css`, `components.css`; `app/styles/__init__.py`
      or a helper in `app/display.py` with `inject_styles()` that reads and injects them once
      per run
- [x] Inline `style=` attributes in component HTML become classes (`mars-card`, `mars-badge`,
      `mars-title-card`, ...) defined in `components.css`
- [x] Any selector on `st-emotion-cache-*` is replaced with a `data-testid` hook or an own class
- [x] Screenshot comparison shows no intended change; any unintended one is fixed or listed
- [x] Tests: `inject_styles()` is idempotent within a run; component HTML helpers emit classes,
      not inline styles
- [x] Tests + ruff green

---

## Task 2.2: Theme and Typography

**Why:** Palette and type carry most of the aesthetic at almost no performance cost. On
Streamlit 1.38, `config.toml` controls colors but only the built-in font families, so web fonts
load through the stylesheet.

**Preflight Files:**

- `src/app/theme_tokens.py`, `scripts/build_theme.py` (Task 1.2)
- `app/styles/base.css`
- `requirements.txt` (if Streamlit has been upgraded past 1.38, check whether config-based
  custom fonts are available and prefer them)

**Validation Commands:**

```
python scripts/build_theme.py
streamlit run app/main.py   # visual: dark plum-black theme, rounded body font, Mincho display font on headings, Japanese alt titles render
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
```

**Checklist:**

- [x] `config.toml` `[theme]`: `base = "dark"`, primary, background, secondary background, text
      from tokens (generated, not hand-edited)
- [x] `base.css`: Google Fonts `@import` for Shippori Mincho B1 (800) and M PLUS Rounded 1c (400, 700)
      with `display=swap`; body and widget text use the body stack; headings use the display
      stack; every stack ends in a system fallback
- [x] Code blocks and the reviewer panels (Scoring details) keep a monospace stack
- [x] Visual check at 1440×900 and 390×844 in all three modes
- [x] Tests + ruff green

---

## Task 2.3: Header and Title-Card Section Headers

**Why:** The header is the first thing a visitor reads and the cheapest place to establish the
era. Title-card framing for result sections ("EPISODE 01 · Top picks") gives the page rhythm
without touching the recommendation logic.

**Preflight Files:**

- `app/display.py` (`render_header`, mode subtitles from portfolio Task 1.1; `render_results`)
- `tests/test_header_intro.py` (pure header/subtitle helpers)
- `scripts/check_live_app.py` (the "N recommendations" header text the detector reads)

**Validation Commands:**

```
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
python scripts/check_live_app.py --url http://localhost:8501   # exit 0
```

**Checklist:**

- [x] MARS wordmark in the display face, plain (no outline, no offset shadow, no katakana:
      Task 1.3 decision); subtitle per mode unchanged in wording
- [x] `title_card(label, text)` helper in `app/display.py` (pure, returns HTML) used for result
      section headers, set in the display face without episode-style framing (Task 1.3); the
      "N recommendations" string stays present and readable as text, not baked into decoration
- [x] The dismissible intro line from portfolio Task 1.1 restyled, behavior unchanged
- [x] Tests: `title_card` output contains the plain text and no inline styles; header helper
      tests updated only where markup (not wording) changed
- [x] Live-check detector fires on the local app
- [x] Tests + ruff green

---

## Task 2.4: Cel-Shaded Recommendation Cards

**Why:** The card is where the visitor spends their attention, and it now carries the
plain-language explanation from portfolio Task 1.3. The redesign should make that sentence the
most readable thing on the card, not compete with it.

**Preflight Files:**

- `src/app/components/cards.py` (`render_card`, `render_card_grid`, "More details" expander,
  rank display from portfolio Task 1.5)
- `src/app/score_semantics.py` (tier labels Top / Strong / Good / Worth a look; tuple contract
  `(text, tooltip, color)` stays)
- `tests/test_score_semantics.py`, `tests/test_truthful_shares.py`,
  `tests/test_personalized_explanation.py`

**Validation Commands:**

```
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: cards at 4/3/2/1 columns by width; explanation sentence is the highest-contrast text after the title
python scripts/check_live_app.py --url http://localhost:8501   # exit 0
```

**Checklist:**

- [ ] Card: 1 px ink border, no shadow, flat panel color (Task 1.3 chose Subtle), poster with a
      thin ink outline; title in the body face bold (display face is for headers only, it is
      too heavy at card size)
- [ ] Match badge restyled as a small "broadcast tag"; tier colors from tokens; rank ("#1") kept;
      tooltip text unchanged
- [ ] Explanation sentence directly under the title in the subtitle style from MASTER.md
      (`subtitle` yellow on panel, in `TEXT_PAIRS`, bold, 1 px ink outline); "More details" and
      the signal breakdown keep their current content
- [ ] Poster `<img>` keeps a meaningful `alt` (the title) and stays a real `img` element (the
      live check depends on it)
- [ ] Rating buttons for demo profiles stay visibly disabled (portfolio Task 1.6)
- [ ] Tests: card HTML contains the explanation sentence, rank, and badge label; no inline styles;
      score_semantics tuple contract unchanged
- [ ] Tests + ruff green

---

## Task 2.5: Sidebar Styling

**Why:** The sidebar order from portfolio Task 1.2 (Find → Refine → Personalize → Advanced) is
right; it just looks like default Streamlit. Group labels styled from tokens make the
structure scannable.

**Preflight Files:**

- `app/sidebar.py` (`render_sidebar` and section renderers; `SidebarResult`)
- `app/state.py` (session keys and query params; must not change)
- `tests/test_app_helpers.py`

**Validation Commands:**

```
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: four labelled groups; Advanced collapsed; sample-seed buttons styled as tags
```

**Checklist:**

- [ ] Group labels for Find / Refine / Personalize / Advanced via one helper, styled from tokens
- [ ] "Try: Steins;Gate · Your Name · Cowboy Bebop" buttons styled as tags; still native buttons
      (keyboard and screen reader behavior unchanged)
- [ ] Widget focus rings visible on the dark theme (token color, ≥ 3:1 against panel)
- [ ] `SidebarResult`, session keys, mode values, and query params untouched (diff check in the
      commit)
- [ ] Tests + ruff green

---

## Task 2.6: Texture and Motion

**Status:** Ruled out by the Task 1.3 decision (Subtle intensity; `docs/decisions.md`,
2026-10-19). Skip unless that decision is revisited.

**Why:** Scanlines and a VHS-style hover are what make it feel like a broadcast rather than a
dark theme. They are also the part most likely to hurt readability and accessibility, so they
come last and come with limits.

**Preflight Files:**

- `app/styles/base.css`, `app/styles/components.css`
- `docs/decisions.md` (Task 1.3 chose the intensity; skip the parts it ruled out)

**Validation Commands:**

```
streamlit run app/main.py
# Visual: scanlines visible on page background only; card hover is a short offset/tracking effect
# With OS "reduce motion" on: no animation or transition anywhere
python scripts/check_live_app.py --url http://localhost:8501   # exit 0, time within budget
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
```

**Checklist:**

- [ ] Scanlines as a fixed `::before` overlay on the app background, `pointer-events: none`,
      ≤ 6% opacity, below card panels in stacking order so no text sits on them
- [ ] Card hover: hard-shadow offset shift plus an optional 150 ms chromatic "tracking" edge;
      no flashing, nothing above 3 flashes per second
- [ ] `@media (prefers-reduced-motion: reduce)` disables all animation and transitions
- [ ] No image files for texture; CSS only
- [ ] Tests + ruff green

---

# Phase 3 — UX Fixes From the Audit

Tasks here come from `docs/redesign/UX_PLAN.md` (Task 0.3). The four below are the likely
candidates; each is confirmed or dropped by the audit, and audit items not listed get their own
task numbered 3.5 onward in the same format.

## Task 3.1: Loading, Empty, and Error States

**Why:** A recommender spends visible time computing, and filters can remove every result. Each
of those moments is a place a visitor decides the demo is broken.

**Preflight Files:**

- `app/pipeline_runner.py` (`run_recommendations`, `_check_personalization_gate`)
- `app/display.py` (`render_results`)
- `src/app/franchise_cap.py` (`FranchiseCapDiagnostics`; hidden-entry count)

**Validation Commands:**

```
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
streamlit run app/main.py   # visual: spinner text while running; filter to an impossible combination → empty state with a one-click reset
```

**Checklist:**

- [ ] Loading: styled spinner with a short "Now loading…" eyecatch line; no fake progress bar
- [ ] Empty state: says which filters removed everything and offers one button that clears
      filters (state keys unchanged; reuses existing defaults)
- [ ] Gate and error messages: plain language first, technical reason in an expander (same rule
      as the portfolio plan: users see words, reviewers see numbers)
- [ ] Tests: empty-state message names active filters; reset restores defaults
- [ ] Tests + ruff green

---

## Task 3.2: Phone Width

**Why:** Hiring managers open portfolio links on phones. Streamlit's columns stack on narrow
screens, but cards, outlined headings, and the sidebar toggle are where layouts usually break.

**Preflight Files:**

- `src/app/components/cards.py` (`render_card_grid` column count)
- `app/styles/components.css`
- `docs/redesign/baseline/*_390x844.png`

**Validation Commands:**

```
python scripts/capture_ui_baseline.py --url http://localhost:8501 --out docs/redesign/after_3_2
# Visual: no horizontal scroll at 390 px; title-card text wraps without clipping; first card visible after the header
```

**Checklist:**

- [ ] No horizontal scroll at 375–390 px in any mode
- [ ] Display-type outline and shadow scale down at narrow widths so headings stay legible
- [ ] Long titles and genre tags wrap; nothing is clipped without an accessible full value
- [ ] Touch targets ≥ 44 px for card actions and sample-seed tags
- [ ] Tests + ruff green

---

## Task 3.3: Accessibility Pass

**Why:** A dark, stylized theme is where focus states and contrast quietly disappear. The
skill's pre-delivery checklist is the audit list.

**Preflight Files:**

- `design-system/mars/MASTER.md` (pre-delivery checklist, with the Streamlit exclusions from
  Task 1.1)
- `src/app/theme_tokens.py` (`TEXT_PAIRS`)

**Validation Commands:**

```
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q tests/test_theme_tokens.py
# Manual: tab through each mode; every interactive element shows focus; screen reader reads card title, badge, explanation in order
```

**Checklist:**

- [ ] Every text color in the shipped CSS appears in `TEXT_PAIRS` (test parses `components.css`
      for color properties and fails on an unlisted pair)
- [ ] Decorative katakana and texture marked `aria-hidden`
- [ ] Badge meaning does not rely on color alone (tier label text is always present)
- [ ] Keyboard pass in all three modes recorded in `docs/redesign/A11Y_PASS.md`
- [ ] Tests + ruff green

---

## Task 3.4: Audit-Driven Fixes

**Why:** Placeholder for the remaining **fix in Phase 3** items in `UX_PLAN.md`, one commit per
fix so any one can be reverted alone.

**Checklist:**

- [ ] For each item: Claude states the change before editing; owner confirms; implement; visual
      check; tests + ruff green; commit referencing the UX_PLAN item number
- [ ] UX_PLAN.md updated with the commit for each closed item

---

# Phase 4 — Ship

## Task 4.1: Performance Check and Deploy

**Why:** Principle 1 is a budget, and the budget is only real if it is measured on the deployed
app.

**Preflight Files:**

- `docs/redesign/baseline/timing.json` (Task 0.2)
- `docs/DEPLOYMENT.md` § Performance
- `.github/workflows/keep-awake.yml` (runs after pushes to `main`)

**Validation Commands:**

```
python scripts/check_live_app.py           # deployed URL, three runs
# Expect: exit 0; warm median within 1 s of the pre-redesign 10.9 s
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x
ruff check src/ tests/ app/
```

**Checklist:**

- [ ] Merge the redesign branch; keep-awake workflow green after the push
- [ ] Three warm runs on the deployed app; median and range in `docs/DEPLOYMENT.md` §
      Performance with the date
- [ ] If over budget: fonts are the first suspect (check whether `@import` blocks render);
      record options in `docs/decisions.md` before changing anything
- [ ] Tests + ruff green

---

## Task 4.2: New Demo Media and Docs

**Why:** The README GIF and screenshot are the redesign's first impression for anyone who does
not click through.

**Preflight Files:**

- `app/assets/demo.gif`, `app/assets/demo_screenshot.png` (portfolio Task 1.7; same recording
  setup, each under 5 MB)
- `README.md`, `docs/ui_design.md`, `docs/index.md`, `docs/WRITEUP.md`

**Validation Commands:**

```
$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x   # README-numbers tests still green
# Manual: README renders on GitHub; GIF plays; every relative link resolves
```

**Checklist:**

- [ ] Re-record the GIF (10–15 s: pick a seed, read a card's explanation, switch to a demo
      profile) and the still screenshot with the final UI
- [ ] `docs/ui_design.md`: replace the old design notes with a pointer to
      `design-system/mars/MASTER.md`, the token module, and a before/after pair from
      `docs/redesign/`
- [ ] `docs/index.md` links the redesign docs; optional one paragraph in `docs/WRITEUP.md` §
      Product decisions on the aesthetic and the contrast test
- [ ] `docs/decisions.md`: dated entry summarizing the redesign scope and what was deferred
- [ ] Tests + ruff green

---

# Phase 5 — Optional and Deferred

- **Framework migration** (Reflex, or a React front end over a FastAPI wrapper of the pipeline).
  Would let the skill's stack guidance apply directly and remove the CSS-over-Streamlit
  fragility. Only worth it if Streamlit's limits block a UX_PLAN item rated high impact.
- **Light "daytime broadcast" theme** behind the existing Streamlit theme switcher, generated
  from a second token set by the same build script.
- **Sound** (a short eyecatch sting on results). Off by default if ever added; likely never.
- **Visual regression in CI**: screenshot diff of the three modes against committed images on
  pull requests. Needs a pinned browser and font set to avoid noise.

---

## Execution Order

```
Phase 0  0.1 install + protocol → 0.2 baseline → 0.3 inventory + audit (owner approves UX_PLAN)
Phase 1  1.1 skill search + design system → 1.2 tokens + contrast test → 1.3 mockups (owner picks direction)
Phase 2  2.1 consolidate (no visual change) → 2.2 theme + type → 2.3 header + title cards
         → 2.4 cards → 2.5 sidebar → 2.6 texture + motion
Phase 3  3.1 states → 3.2 phone width → 3.3 accessibility → 3.4 audit fixes
Phase 4  4.1 performance + deploy → 4.2 media + docs
Phase 5  as decided
```

2.1 blocks every other Phase 2 task. 1.2 blocks 2.2 onward (tokens are the only color source).
3.1 and 3.2 can run in parallel with 2.5 and 2.6. 3.3 runs after 2.6 so it audits the final
texture. 4.2 waits for everything shipped.

## Cut Line

| Tier | Tasks | Ships as |
| ---- | ----- | -------- |
| **Must** | 0.1, 0.2, 0.3, 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 3.1, 4.1, 4.2 | A distinct, readable 90s look on header and cards, a contrast test in CI, clear loading and empty states, no load-time regression, new demo media |
| **Strong** | 1.3, 2.5, 3.2, 3.3 | Direction chosen deliberately, styled sidebar, solid on phones, accessibility recorded |
| **Nice to have** | 2.6, 3.4, Phase 5 | Texture and motion, remaining audit items |

## Success Criteria

1. A visitor's first screen reads as a 90s anime broadcast, and the first card is still visible
   without scrolling at 1440×900 with a plain-language explanation as its most readable text.
2. Every text color pair in the shipped CSS is ≥ 4.5:1, enforced by `tests/test_theme_tokens.py`;
   all motion is disabled under `prefers-reduced-motion`.
3. Tokens live in `src/app/theme_tokens.py` only; `config.toml` theme and `tokens.css` are
   generated and a test fails if they drift.
4. Warm time to first card on the deployed app is within 1 s of the pre-redesign median, and
   `scripts/check_live_app.py` and the keep-awake workflow stay green.
5. No file under `src/models/`, `src/eval/`, or `reports/` changed; session keys, mode values,
   `SidebarResult`, and the README-numbers tests are untouched.
6. No real series logos or characters appear in the app chrome.
7. `$env:APP_IMPORT_LIGHT = "1"; python -m pytest -q -x` green and `ruff check src/ tests/ app/`
   at 0 after every task.
