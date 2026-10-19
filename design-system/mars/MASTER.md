# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** MARS
**Generated:** 2026-10-19 01:33:25
**Category:** Video Streaming/OTT

---

## Direction (owner pick, 2026-10-19)

**A: Cel title card at night.** Flat cel fills, 3 px outlines, hard offset shadows, outlined
display type, light scanlines on the background only. The shortlist and the other options are in
`docs/redesign/SKILL_SEARCH.md`.

Generated with
`search.py "anime video streaming personalized recommendation retro" --design-system --persist -p "MARS"`.
The plan's query (`"anime recommendation entertainment retro"`) matches the Gaming row and
returns 3D & Hyperrealism, which breaks the plan's first-card budget. The generator can't reach
the cel look from any query. So this file is the dark base, and the era lives in the
**90s Anime Overrides** section (Task 1.2). Where the two disagree, the overrides win. That
covers the palette, Inter, the soft `--shadow-*` scale, glow, and the 8–12 px radii below.

**Page overrides:** none. The Task 0.3 audit found no mode-specific visual needs. The mode
findings (F2 header copy, F10 gate messages, F14 empty Browse) are copy and flow, handled in
Phase 3. So `pages/` stays empty until a mode needs a visual deviation.

---

## 90s Anime Overrides

These win over every generated section below. Values live in `src/app/theme_tokens.py`
(`TOKENS`), which generates `app/styles/tokens.css` (`--mars-<group>-<key>`) and the
`[theme]` section of `.streamlit/config.toml` with `python scripts/build_theme.py`. Never edit
the generated files or put a hex literal in a component. `tests/test_theme_tokens.py` enforces both.

### Palette

| Token | Hex | Role | Contrast (text on bg / panel) |
| ----- | --- | ---- | ----------------------------- |
| `bg` | `#1B1F3B` | Night navy page background | — |
| `panel` | `#262B52` | Deep panel: cards, sidebar | — |
| `ink` | `#0D0F22` | Cel outlines and hard shadows | — |
| `text` | `#FFF4E0` | Cel cream body and title text | 14.8 / 12.4 |
| `text_muted` | `#B8B3D1` | Secondary text, meta lines | 8.0 / 6.7 |
| `sunset` | `#FF7A45` | Primary action, highlights | 6.2 / 5.2 |
| `on_sunset` | `#1B1F3B` | Text on sunset buttons (cream on sunset is 2.4, fails) | 6.2 on sunset |
| `magenta` | `#E8417A` | **Accent only**: borders, offset shadows, decoration | 4.2 / 3.5, never text |
| `sakura` | `#FFC2D4` | Soft highlight text, focus ring | 10.7 / 9.0 |
| `teal` | `#3FB8AF` | VHS teal, links and secondary accent | 6.7 / 5.6 |
| `focus` | `#FFC2D4` | Focus ring (sakura) | — |

Match-tier badge colors (text on panel, tuple contract in `score_semantics.py` unchanged):
Top match `tier_top` teal 5.6, Strong match `tier_strong` sakura 9.0, Good match `tier_good`
sunset 5.2, Worth a look `tier_look` `#A9A6CC` 5.8.

Every pair used for text is listed in `TEXT_PAIRS` and tested at ≥ 4.5:1. A new text color, or
an existing color on a new surface, goes into `TEXT_PAIRS` in the same change.

**Rollout:** the app still renders the pre-redesign light theme and tier colors. They are held in
`LIVE` in the same module, so the generated files already come from it. Task 2.2 points the
Streamlit theme at these tokens (with `base = "dark"`), and Task 2.4 does the same for the tier
colors. `LIVE` is deleted once both are done.

### Typography

- **Display:** Dela Gothic One, used for the wordmark and section title cards only. It is outlined
  (a `-webkit-text-stroke` / `paint-order` outline in `ink`) with a hard offset shadow. It is too
  heavy at card size, so card titles use the body face in bold.
- **Body:** M PLUS Rounded 1c, 400 and 700.
- Both faces cover Japanese, so katakana accents (decorative, `aria-hidden="true"`) render
  in the same face.
- Load from Google Fonts with `display=swap`. Every stack ends in a system fallback
  (`--mars-font-display`, `--mars-font-body`). Code and the Scoring details panels keep
  `--mars-font-mono`.

### Cards and shape

- 3 px `ink` border (`--mars-border-cel`), flat `panel` fill, no gradients.
- Hard offset shadow, no blur: `var(--mars-shadow-offset-md) var(--mars-shadow-offset-md) 0 0`
  in `ink` (or `magenta` for emphasis). The generated soft `--shadow-*` scale and glow below are
  not used.
- Radii are small (`sm` 4 px, `md` 8 px; `pill` for tags only), replacing the 8–12 px radii below.
- Press feedback may be an instant shadow-offset change. Any transition sits behind
  `prefers-reduced-motion`.

### Texture

- Scanlines are CSS only, never an image, at no more than 6% opacity
  (`--mars-texture-scanline-opacity`).
- Background only: never behind body text, cards, or the sidebar's controls.
- No noise or VHS motion under `prefers-reduced-motion`.

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#0F0F23` | `--color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` |
| Secondary | `#1E1B4B` | `--color-secondary` |
| On Secondary | `#FFFFFF` | `--color-on-secondary` |
| Accent/CTA | `#E11D48` | `--color-accent` |
| On Accent/CTA | `#FFFFFF` | `--color-on-accent` |
| Background | `#000000` | `--color-background` |
| Foreground | `#F8FAFC` | `--color-foreground` |
| Card | `#0C0C0D` | `--color-card` |
| Card Foreground | `#F8FAFC` | `--color-card-foreground` |
| Muted | `#181818` | `--color-muted` |
| Muted Foreground | `#94A3B8` | `--color-muted-foreground` |
| Border | `#312E81` | `--color-border` |
| Destructive | `#EF4444` | `--color-destructive` |
| On Destructive | `#000000` | `--color-on-destructive` |
| Ring | `#FFFFFF` | `--color-ring` |

**Color Notes:** Cinema dark + play red

### Typography

- **Heading Font:** Inter
- **Body Font:** Inter
- **Mood:** dark, cinematic, technical, precision, clean, premium, developer, professional, high-end utility
- **Google Fonts:** [Inter + Inter](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap)

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #E11D48;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #0F0F23;
  border: 2px solid #0F0F23;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #000000;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #0F0F23;
  outline: none;
  box-shadow: 0 0 0 3px #0F0F2320;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Dark Mode (OLED)

**Keywords:** Dark theme, low light, high contrast, deep black, midnight blue, eye-friendly, OLED, night mode, power efficient

**Best For:** Night-mode apps, coding platforms, entertainment, eye-strain prevention, OLED devices, low-light

**Key Effects:** Minimal glow (text-shadow: 0 0 10px), dark-to-light transitions, low white emission, high readability, visible focus

### Page Pattern

**Pattern Name:** Hero-Centric Design

- **Conversion Strategy:** One primary CTA. Let the hero dominate the initial viewport without hiding the next content cue. Use a static hero and non-pulsing CTA when reduced motion is requested; provide video controls. Pause hero media offscreen/hidden and keep the final hero message and CTA static under reduced motion.
- **CTA Placement:** Hero dominant (center/bottom) + Sticky nav CTA
- **Section Order:** Full-bleed Hero (headline + visual) > Single value prop strip > Key benefit or proof > Primary CTA

---

## Anti-Patterns (Do NOT Use)

- ❌ Static layout
- ❌ Slow video player

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile

---

## Rules That Do Not Apply to Streamlit

MARS is Streamlit 1.38. Streamlit renders its own widgets, so some rules above only reach the
HTML the app writes itself (`st.markdown` / `st.html` fragments with app classes). Audits skip
the cases below. Don't hack around the framework to satisfy them.

| Rule | Scope in MARS | Why |
| ---- | ------------- | --- |
| **Component Specs** CSS (`.btn-primary`, `.card`, `.input`, `.modal`) | Ignored | Stack-level code output. Buttons, inputs and bordered containers are Streamlit widgets, styled from `app/styles/` through `data-testid` hooks and app classes, using tokens from `src/app/theme_tokens.py`. |
| `cursor-pointer` on all clickable elements | App HTML only | Native buttons, selects, radios, expanders and the sidebar toggle already set their own cursor. |
| No emoji icons / one SVG icon set | App HTML only | Widget labels (`st.button`, `st.expander`, `st.radio`) are text strings Streamlit renders, and `page_icon` is a favicon, so an SVG can't go inside a native label. Where a label needs an icon, use a text label instead (F12). |
| `.input:focus { outline: none }` | **Never** | Removing the focus ring contradicts the focus-visible rule and F11. Streamlit's own focus ring stays, and app CSS may only make it stronger. |
| Hero-Centric pattern, sticky nav CTA, full-bleed hero, "Static layout", "Slow video player" | Not applicable | Landing-page and video-player guidance. The layout (sidebar Find → Refine → Personalize → Advanced, results in main) was set by the portfolio plan and is out of scope. |
| Modals (`backdrop-filter: blur`) | Not applicable | The app has no modals. Details open in `st.expander`. |
| Breakpoints 375 / 768 / 1024 / 1440 | Check at the baseline widths, 390 × 844 and 1440 × 900 | Streamlit decides when columns stack and the sidebar collapses. App CSS can only add media queries for its own classes (Task 3.2). |
| "Instant state changes": always transition 150–300 ms | App classes only, behind `prefers-reduced-motion` | Native widget transitions belong to Streamlit. Hard-shadow press feedback may be instant, as the cel style intends. |
| "No content hidden behind fixed navbars" | Not applicable | Streamlit's header is hidden by the app's CSS. There is no fixed bar of the app's own. |
| Viewport meta, `touch-action`, skip links, focus on route change, deep links | Not applicable | Streamlit owns the document shell and has no routes, only reruns. |
| "Light mode: text contrast 4.5:1" | Applies to the **dark** pairs | Direction A is dark-only. Every text pair in `TEXT_PAIRS` is tested at ≥ 4.5:1 (Task 1.2). |
