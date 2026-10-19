# Style Inventory (Task 0.3)

> Snapshot of where styling is set before the redesign, taken 2026-10-19 at commit `c527b47b`.
> Task 2.1 moves all of it to `app/styles/` (CSS) and `src/app/theme_tokens.py` (values).

## Count

The plan's validation command (Windows PowerShell 5.1):

```
Select-String -Path app/*.py, src/app/**/*.py -Pattern "unsafe_allow_html|<style|style=" | Measure-Object
Count    : 96
```

PowerShell 5.1 treats `**` as a single `*`, so `src/app/**/*.py` matches `src/app/components/*.py`
only. Re-running with `src/app/*.py` added also gives **96**: no top-level `src/app/*.py` module
emits HTML. Per file:

| File | Matching lines |
| ---- | -------------- |
| `src/app/components/cards.py` | 44 |
| `app/display.py` | 30 |
| `app/sidebar.py` | 8 |
| `src/app/components/taste_profile.py` | 6 |
| `src/app/components/diversity.py` | 5 |
| `src/app/components/skeletons.py` | 3 |
| **Total** | **96** |

Task 2.1 target: the matches left are the single CSS injection point in `app/styles/` and HTML
fragments that carry class names but no `style=`.

## 1. Streamlit theme: `.streamlit/config.toml`

| Line | Key | Value | Duplicated in `src/app/theme.py` as |
| ---- | --- | ----- | ----------------------------------- |
| 8 | `primaryColor` | `#6C63FF` | `primary` |
| 9 | `backgroundColor` | `#FAFBFC` | `bg` |
| 10 | `secondaryBackgroundColor` | `#F0F2F6` | `surface_alt` |
| 11 | `textColor` | `#1A1A2E` | `text_primary` |
| 12 | `font` | `"sans serif"` | none |

The two files are kept in step by hand; nothing checks they agree.

## 2. Token module: `src/app/theme.py`

`COLORS` (lines 8–51, 33 keys), `SPACING` (53–62), `TYPE_SCALE` (64–71) and `ELEVATION`
(73–77), both read only by `tests/test_theme.py`, and `get_theme()` (80–88). In the app, only
`app/display.py` and `app/main.py` read it. `cards.py`, `sidebar.py`, `diversity.py`,
`taste_profile.py`, `skeletons.py` and `score_semantics.py` hard-code hex values, several of
which match a token value without referencing it.

## 3. `<style>` blocks

| File:line | What | Notes |
| --------- | ---- | ----- |
| `app/display.py:44-182` (`inject_css`, called from `app/main.py:121`) | Global stylesheet built in an f-string from `theme.py` tokens: block-container width/padding, h1–h3, `.stMarkdown`, sidebar background and headings, `.stButton`, **all** `button[kind="secondary"]` as genre pills, bordered containers (cards) with hover lift, expander header, `stMetric`, `hr`, captions, radio gap, selectbox, hides `#MainMenu`/`footer`/`header` | Literal `rgba(108, 99, 255, …)` at 93 and 118 (primary color, not via token). `transition` / `transform` at 88, 92, 117, 126, 130 with no `prefers-reduced-motion` guard. Uses `.streamlit-expanderHeader` (134), a pre-1.30 class name, and `[data-testid]` hooks elsewhere. No `st-emotion-cache-*` selectors. |
| `src/app/components/skeletons.py:8-12` | `.skel-box` shimmer, `background: #2A2F36` (dark on a light theme), infinite `animation` | Module is **not imported anywhere** in `app/`, `src/` or `tests/`. |

## 4. Inline `style=` attributes in HTML f-strings

### `app/display.py`

| Lines | Element | Values |
| ----- | ------- | ------ |
| 218-220 | Header `<h1>` + subtitle `<p>` | `font-weight:800`; subtitle color `text_muted` token, `1.05rem` |
| 314-319 | Result count ("10 recommendations of 13,062") | flex row; `text_primary`, `text_muted` tokens; `1.15rem`, `0.82rem` |
| 387-401 | Mix bar segments | `popular` / `midrange` / `longtail` / `text_muted` tokens, `height:6px` |
| 407-419 | Mix bar label + legend + track | `0.75rem` / `0.72rem`, `text_muted`, `border_light` tokens, `border-radius:3px` |
| 527-534 | Personalized "isn't running yet" panel | **Hard-coded** `#FFF3CD`, `#FCF8E3`, `#F0AD4E`, `#8A6D3B` (Bootstrap warning palette, not in `theme.py`) |
| 569-575 | Cold-start "Get Started" panel | **Hard-coded** `#F0EFFF`, `#1A1A2E`, `#4A5568` (same values as tokens, not referenced) |

### `app/sidebar.py`

| Lines | Element | Values |
| ----- | ------- | ------ |
| 114-119 (`_section_label`) | FIND / REFINE / PROFILE / PERSONALIZATION / PERFORMANCE labels | Hard-coded `#4A5568`, `0.8rem`, uppercase |
| 926-935 | Quick Guide body | Hard-coded `#4A5568`, `0.88rem`, `line-height:1.9` |
| 974-981 | Performance "Inference" tile | Hard-coded `#48BB78` / `#ECC94B` / `#FC8181` status, `#F7FAFC`, `#E2E8F0`, `#A0AEC0` |

### `src/app/components/cards.py`

| Lines | Element | Values |
| ----- | ------- | ------ |
| 31-34 (`_render_placeholder_box`) | No-image placeholder | `180×260`, `#F0F2F6`, `#E2E8F0`, `#A0AEC0` |
| 165-175 | Grid card tier badge + rank | tier color from `MATCH_TIERS` with `15` alpha suffix; `#A0AEC0`; fallback `#6C63FF` |
| 177-179 | Grid card title | `#1A1A2E`, `0.95rem` |
| 182 | Grid card badge wrapper `<p>` | margin only |
| 187 | Grid card explanation | `#4A5568`, `0.72rem`, italic |
| 191-203 | Grid card meta (★ score, type, year) | `#48BB78` / `#6C63FF` / `#A0AEC0` by MAL score, `#B794F4` type |
| 342-354 | List card tier badge + rank | as grid, `0.82rem` pill |
| 356-359 | List card title `<h3>` (badge HTML inside the heading) | `#1A1A2E`, `1.15rem` |
| 362-364 | Alt (Japanese) title | `#A0AEC0`, italic, `0.85rem` |
| 370-374 | Explanation callout | `#F0EFFF` background, `#6C63FF` left border, `#4A5568` text |
| 378-394 | Meta row (★, type, eps, year, status) | `#48BB78` / `#6C63FF` / `#A0AEC0` / `#B794F4` / `#ECC94B` / `#63B3ED` |
| 403-410 | Studio / source line | `#A0AEC0`, `0.82rem` |
| 434-436 | Synopsis | `#4A5568`, `0.88rem`, `line-height:1.6` |
| 444-453 | Badge row (Trained/Cold-start, popularity band, novelty) | `#ECC94B` / `#48BB78` / `#63B3ED` / `#A0AEC0` / `#B794F4` / `#6C63FF`, `0.75rem` |
| 459, 461 | "In seeds" / "Max 5 seeds" | `#48BB78`, `#A0AEC0` |
| 487 | "Watch on" streaming links | `#6C63FF` background, `white`, pill |

### `src/app/components/diversity.py`

| Lines | Element | Values |
| ----- | ------- | ------ |
| 35-42 | "MMR Diversification Active" banner | Dark `#1A1A2E` panel with `#4ECDC4`, `#B0B0B0`, `#888` on a light page |

### `src/app/components/taste_profile.py`

| Lines | Element | Values |
| ----- | ------- | ------ |
| 73-74 | Plotly radar line / fill | `#3498DB`, `rgba(52,152,219,0.3)` |
| 99-105, 108-112 | Genre rating rows | `#27AE60` / `#3498DB` / `#F39C12` / `#95A5A6` |
| 132, 137 | Plotly bar colors | `#27AE60`, `#3498DB`, `#F39C12`, `#E74C3C` |
| 161-165 | Distribution rows | same palette |

## 5. Colors defined in Python outside any HTML

| File:line | What |
| --------- | ---- |
| `src/app/score_semantics.py:47-50` | `MATCH_TIERS`: `#27AE60` / `#3498DB` / `#E67E22` / `#95A5A6` (flat-UI palette, separate from `theme.py`) |
| `src/app/score_semantics.py:77` | Fallback tier color `#95A5A6` |

## 6. Widget-level styling that is not CSS

| File:line | What |
| --------- | ---- |
| `app/main.py:113` | `st.set_page_config(page_title="MARS", layout="wide", page_icon="🎬")` |
| `src/app/components/cards.py:85, 97` | `st.image(..., width=180, caption=title_display)`: fixed poster width; caption repeats the title |
| `src/app/components/cards.py:327, 416, 440` | Column ratios that set card layout (`[1, 3]`, genre pills up to 5, badge row `[1, 1, 1, 2]`) |
| `src/app/components/instructions.py:43` | Intro row columns `[8, 1.6, 0.6]` |
| `button(type="primary"/"secondary")` throughout | Picks which of the two global button rules applies (see `display.py:85-119`) |

## Summary for Task 2.1

- Three palettes are in use: `theme.py` tokens, the flat-UI set in `score_semantics.py` and
  `taste_profile.py`, and one-off Bootstrap / dark values in `display.py:527`,
  `diversity.py:35` and `skeletons.py:9`.
- One stylesheet (`inject_css`), around 60 inline-styled HTML fragments, and one dead stylesheet
  (`skeletons.py`).
- `button[kind="secondary"]` (`display.py:101-119`) styles **every** non-primary button as a
  30 px genre pill, not just genre chips. See finding F6 in `UX_PLAN.md`.

## After Task 2.1

All styling now lives in `app/styles/`: `tokens.css` (generated), `base.css` (the former
`inject_css` stylesheet) and `components.css` (one `mars-*` class per former inline style),
injected once per run by `app.styles.inject_styles()` from `app/main.py`. The light palette the
app still paints with is `LIVE["color"]`, `LIVE["chart"]` and `LIVE["shadow"]` in
`src/app/theme_tokens.py`, generated as `--mars-live-*` variables; Task 2.2 points the
stylesheets at the night tokens instead. `tests/test_styles.py` fails on any `style=` or
`<style` outside the loader and on any hex literal in the CSS.

- The mix bar segments are SVG `<rect>`s sized by `x`/`width` attributes, so per-run widths need
  no inline style.
- `.streamlit-expanderHeader` was dropped: the class does not exist in Streamlit 1.38, so the rule
  matched nothing. No `st-emotion-cache-*` selectors existed to replace.
- `skeletons.py`'s `<style>` block moved to `components.css`; the module is still unused.
- `src/app/theme.py` is no longer read by the app (only `tests/test_theme.py` imports it).

Screenshot comparison (`docs/redesign/after_2_1` against `docs/redesign/baseline`, pixel diff at
a per-channel threshold of 24): Seed, Personalized and Browse at 1440×900 and Personalized and
Seed at 390×844 are identical; Browse at 390×844 differs in 32 isolated pixels (anti-aliasing).
States the baseline does not cover were captured on the old and new code side by side: grid
view, Personalized-without-profile notice and the taste profile are identical; an expanded card
("Watch on" links), the MMR banner, the Quick Guide and the inference tile differ only in the
timing numbers. Not compared: the "Get Started" panel (clearing seeds shows default results, so
the UI does not reach it) and the unused skeleton. No intended or unintended visual change found.
