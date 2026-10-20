# UX Plan (Task 0.3)

> Audit of the flow from landing to a useful recommendation, 2026-10-19, commit `c527b47b`.
> Sources: the Task 0.2 baseline (`docs/redesign/baseline/*.png`, `timing.json`), the code at the
> file:line cited in each row, and the UI UX Pro Max skill's UX domain
> (`search.py "<topic>" --domain ux` for loading states, empty states, error messages, forms,
> focus, touch targets, responsive). Contrast ratios are WCAG 2.x relative-luminance ratios
> computed from the hex values in the code, measured against the page background `#FAFBFC`.
>
> **Status: approved by the owner, 2026-10-19.** Phase 3 may start.

## Steps to the first useful result, per mode

| Mode | Desktop interactions | Phone extra | What the visitor sees | Evidence |
| ---- | -------------------- | ----------- | --------------------- | -------- |
| Similar to a title (default) | **0**: the default seed (Fullmetal Alchemist: Brotherhood) is preloaded | 0 | First card at about y = 437 px; warm time to first card has a median of 8.9 s (range 5.3–14.0 s) | `app/state.py` `setup_first_run`; `seed_1440x900.png`; `timing.json` |
| For me | **2**: pick "For me", then a demo profile. The Personalize expander opens itself and shows the demo buttons. | +2 (open and close the sidebar) | Cards rank with the profile, but the header still says "Similar to Fullmetal Alchemist: Brotherhood" and the intro still says "Load a rated profile…" (F2) | `app/sidebar.py:84, 238-239`; `personalized_1440x900.png` |
| Browse | **3**: pick "Browse", open the genre multiselect, pick a genre | +2 | An empty page with a blue info box until a genre is picked | `app/main.py:171-173`; `app/sidebar.py:744-758` |

## Findings, ranked by impact on the first five minutes

Each finding is marked **fix in Phase 3** (with the task), **defer** (to a named task or
later), or **won't fix**, with the reason.

| # | Finding | Evidence | Decision |
| - | ------- | -------- | -------- |
| F1 | **The mix bar above the first card miscounts.** It counts "Popular" by the substring `"Top 25%"` and "Hidden gems" by `"Long-tail"`. `popularity_band` returns `"Top 10%"`, `"Top 25%"`, `"Mid"` and `"Long Tail"`, so Top-10% titles count as Mid and Hidden gems is always 0. The badge explanations under "More details" have the same mismatch: they key on `"Mid 50%"` and `"Long-tail"`, so Top 10%, Mid and Long Tail titles all get the generic fallback text. | `src/app/badges.py:14-20` vs `app/display.py:361, 373` and `src/app/components/tooltips.py:47-60`. In `seed_1440x900.png`, most cards show "Top 10%" while the bar reads "Popular 1 · Mid 9 · Hidden gems 0". In `personalized_1440x900.png`, card #1 shows "Long Tail" and the bar still reads "Hidden gems 0". | **Fix in Phase 3 (3.4).** It is the first data graphic a visitor sees and it is wrong. Count from `popularity_band` values, not substrings. Add a unit test. Display code only, so no ranking change. **Closed in `44ddc076` (with F8).** |
| F2 | **For me mode doesn't say what it is ranking.** With a demo profile loaded, the section header reads "Similar to Fullmetal Alchemist: Brotherhood" and the intro reads "Load a rated profile, or try a demo profile…". The header branch never names the profile when seeds are present, and `intro_line` doesn't know a profile is loaded. | `personalized_1440x900.png` (top); `app/main.py:175-207`; `src/app/components/instructions.py:9-31` | **Fix in Phase 3 (3.4).** The header should name both inputs ("For demo_action_adventurer · anchored on …") and the intro should drop the load-a-profile hint once a profile is active. Copy and branching only. The mode values and `SidebarResult` are unchanged. **Closed in `84c169e8`.** |
| F3 | **Most secondary text fails 4.5:1.** The muted text `#A0AEC0` (subtitle, alt title, studio line, rank, "of 13,062", mix legend) is 2.18:1. Match-tier badges are 2.47–3.04:1 before their 8 % tint (`#27AE60` 2.77, `#3498DB` 3.04, `#E67E22` 2.75, `#95A5A6` 2.47). Card meta and badge colors: `#48BB78` 2.34, `#63B3ED` 2.20, `#B794F4` 2.37, `#ECC94B` 1.56. Primary `#6C63FF` is 4.17. | `src/app/theme.py:31, 35-50`; `src/app/score_semantics.py:47-50`; `src/app/components/cards.py:343-453`. Body text `#4A5568` passes at 7.26. | **Defer to Task 1.2** (the token contrast test) **and Phase 2** (components move onto tokens). **Phase 3.3** re-checks the rendered pairs. |
| F4 | **The wait for the first card has little feedback.** The warm first-card median is 8.9 s (5.3–14.0 s). The only feedback is a one-line spinner around the ranking call. The artifact load on a cold start uses `show_spinner=False`. A skeleton component exists but nothing imports it. The skill rates "Loading States" and "Loading Indicators" High: use a skeleton or progress with a busy status, and never leave a long wait unexplained. | `timing.json`; `app/pipeline_runner.py:377`; `app/main.py:69`; `src/app/components/skeletons.py` (no importers) | **Fix in Phase 3 (3.1).** Show card skeletons in the results area while the pipeline runs, and give the cold load a status line naming the step. Restyle the skeleton onto tokens with a reduced-motion guard. |
| F5 | **On a phone, the first card's title is below the fold and changing modes takes extra steps.** The sidebar starts collapsed, so the mode switch is behind a chevron. The first viewport ends inside the first poster, and its title starts at about y = 875 on an 844 px screen. Each card is about 1,200 px tall: genre pills, badges and the intro's ✕ each stack onto their own full-width row. Ten cards make a 12,120 px page. | `seed_390x844.png` (crops of the first two viewports); `src/app/components/cards.py:85, 327, 416, 440`; `src/app/components/instructions.py:43` | **Fix in Phase 3 (3.2).** Put the poster beside the title at narrow widths, cap its height, keep pills and badges inline, and add a visible mode hint in the main area on phones. |
| F6 | **Every non-primary button looks like a genre pill.** `button[kind="secondary"]` gets a fixed 30 px height and pill styling, and Streamlit gives every default button that kind. The result: sample-seed buttons wrap mid-word ("Steins;G / ate", "Your / Name") and overflow their 30 px. "Add to Seeds", "Clear Seeds", "How it works" and ✕ look like genre tags. | `app/display.py:101-119`; `seed_1440x900.png` (sidebar "Try:" row, card action row) | **Fix in Phase 3 (3.4).** Scope the pill rule to genre chips through a container class. Task 2.1 must keep current behavior (no visual change), so the fix lands after it. Tasks 2.4 and 2.5 may already resolve it; 3.4 verifies. **Closed in `c4a179ac`.** |
| F7 | **The card's reading order and labels work against a first-time visitor.** The title is announced twice: once as the poster caption, then in the `<h3>`. The tier badge sits inside the `<h3>`, so the heading reads "Black Butler IITop match #1". Every card has a row of model-internal labels ("Trained", "Cold-start", "Novelty NA"). In Similar-to-a-title mode, "Novelty NA" is on all ten cards. | `src/app/components/cards.py:85, 97, 356-359, 440-453`; `seed_1440x900.png` card row | **Fix in Phase 3 (3.3** for order and semantics: no caption, badge outside the heading**; 3.4** for wording: hide Novelty when it is NA, plain-language Trained/Cold-start**).** The badge payload and its contract stay the same. **Wording closed in `ae5e0a98`; order and semantics were Task 3.3.** |
| F8 | **Four names for the popularity band.** It is "Long Tail" on the badge, "Hidden gems" in the mix bar, "a hidden gem" in the explanation, and "Long-tail" in the badge explanation. | `src/app/badges.py:20`; `app/display.py:398, 413`; `src/app/explanations.py:135`; `src/app/components/tooltips.py:55` | **Fix in Phase 3 (3.4)** together with F1: one visitor-facing name, mapped in one place. **Closed in `44ddc076` (with F1).** |
| F9 | **Empty states list every filter instead of naming the one to relax.** Browse-zero, seed-zero and personalized-zero each print the same generic four-item "Try:" list. Two panels use hard-coded colors outside the theme. The skill's "Empty States" rule: give a helpful message and action. The `docs/ui_design.md` backlog asks for this too. | `app/main.py:220-233`; `app/display.py:527-534, 538-564, 567-576` | **Fix in Phase 3 (3.1).** Name the active filters, put the reset action first, and put both panels on tokens. |
| F10 | **Gate and error messages are duplicated or written for developers.** In For me mode without a profile, the same problem shows in the sidebar (warning plus caption) and in the main area (warning plus info). The engine-unavailable error tells a visitor to "Disable APP_IMPORT_LIGHT". The skill's "Error Messages" rule: one clear message, announced. | `app/sidebar.py:483-494`; `app/main.py:175-188, 234-238` | **Fix in Phase 3 (3.1).** One main-area message with the fix; the sidebar keeps a short caption. Visitor wording for the unavailable error, with the developer hint moved under Scoring details. The no-silent-fallback text stays. |
| F11 | **Keyboard focus is untested, and the custom CSS puts it at risk.** `inject_css` sets no focus styles. The secondary-button rule overrides border and background with `!important`, so it may hide Streamlit's focus ring. Hover uses `transform` with `transition: all` and no `prefers-reduced-motion` guard. Not keyboard-tested in this task. | `app/display.py:85-131` | **Fix in Phase 3 (3.3).** Add a visible focus ring on every interactive element through tokens and a reduced-motion guard. Task 2.6 adds motion and must add the guard with it. |
| F12 | **The grid view's add-seed button is icon only.** "🔄" carries its meaning only in a hover tooltip, which touch and screen-reader users don't get. | `src/app/components/cards.py:237-242` | **Fix in Phase 3 (3.3).** Use a text label ("+ Seed"). **Closed in `b33ba639` (Task 3.4; it was still open after 3.3).** |
| F13 | **Three palettes, plus dark one-offs on a light page.** The flat-UI tier colors and taste-profile charts are separate from `theme.py`. The MMR banner is a dark `#1A1A2E` panel. The skeleton is `#2A2F36`. | `docs/redesign/STYLE_INVENTORY.md` §§4–5 | **Defer to Task 2.1** (consolidation) **and Task 1.2** (tokens). This is structure, not a Phase 3 UX fix. |
| F14 | **Browse starts empty.** It takes three interactions before any title shows. | `app/main.py:171-173`; steps table above | **Defer.** Browse is filters-only by design (mode help at `app/sidebar.py:153-157`; `FAQ_MD_BROWSE`). A preselected genre is a product decision for the owner, not a restyle. Phase 3.1 turns the empty state into an action ("Pick a genre to start") instead. |
| F15 | **The explanation line repeats the seed title.** "Shares Action with Fullmetal Alchemist: Brotherhood · fans of Fullmetal Alchemist: Brotherhood also rate it highly". | `seed_1440x900.png` cards; text built in `src/app/explanations.py` | **Defer.** The explanation text is a portfolio-plan contract with tests on its wording. Changing it belongs in a follow-up to that plan, not a restyle. |
| F16 | **The sidebar is long before Personalize.** The Refine section always shows six controls (genre, type, year, Top N, sort, view). | `app/sidebar.py:717-853`; `seed_1440x900.png` sidebar | **Won't fix.** The portfolio plan set this IA, with Find, then Refine, then Personalize, then Advanced. Phase 2.5 makes it scan faster without moving controls. |
| F17 | **The last pipeline time appears twice.** It shows in Advanced → Performance and again in Scoring details. | `app/sidebar.py:990-992`; `app/display.py:662-663` | **Won't fix.** Both panels are collapsed by default, are reviewer-facing, and cost the visitor nothing. |
| F18 | **Switching to Grid does nothing until something else reruns the app.** The List/Grid radio is inside `_render_filters_display_fragment`, an `@st.fragment`. Changing it reruns only the fragment: the radio shows Grid and `view_mode` is set to `"grid"`, but the main area still shows list cards. The grid appears only after a full rerun, such as clicking "How it works". Found during Task 2.4, 2026-10-19; it was already there before that task. | `app/sidebar.py:716, 834-842`; `app/display.py:261-267`. Reproduced in a headless browser: after Grid was selected and the app was left for 180 s, it still showed 10 list cards and 0 grid cards. | **Fix in Phase 3 (3.4).** On a change, call `st.rerun()` (full scope), or move the radio out of the fragment. Keep the `view_mode` key and its values as they are. Add a test that a view change reaches `_render_cards`. **Closed in `5d0f3495`.** |

## Phase 3 work this produces

| Task | Findings |
| ---- | -------- |
| 3.1 Loading, empty, error states | F4, F9, F10 (F14 restyle only) |
| 3.2 Phone width | F5 |
| 3.3 Accessibility pass | F3 (re-check), F7 (order and semantics), F11, F12 |
| 3.4 Audit-driven fixes | F1, F2, F6, F7 (wording), F8, F18 |

## Closed in Task 3.4 (2026-10-20)

One commit per fix, each confirmed by the owner before editing, visually checked on a local run,
and committed with tests and ruff green.

| Commit | Closes |
| ------ | ------ |
| `44ddc076` | F1, F8: mix bar counts from `popularity_band` values; one name per band (`BAND_LABELS`) |
| `84c169e8` | F2: For me header and intro name the active profile |
| `5d0f3495` | F18: a List/Grid change reruns the whole app |
| `c4a179ac` | F6: pill style scoped to genre rows; other secondary buttons are outline buttons |
| `ae5e0a98` | F7 (wording): "Few ratings", band name, genre novelty only with a profile |
| `b33ba639` | F12 and `A11Y_PASS.md` follow-up 1: word labels instead of emoji |
| `a9160d41` | `A11Y_PASS.md` follow-ups 2 and 3: poster title read once; MAL star named |

