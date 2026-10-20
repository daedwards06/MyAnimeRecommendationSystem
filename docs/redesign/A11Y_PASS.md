# Accessibility Pass (UI Redesign Task 3.3)

**Date:** 2026-10-20 · **Build:** local `streamlit run app/main.py`, Streamlit 1.38.0, Chromium
(Playwright 1.64), 1440 × 900, `prefers-reduced-motion: reduce` so no ring was measured
mid-transition.

The audit list is the pre-delivery checklist in `design-system/mars/MASTER.md`, with the rules
that page marks as not applying to Streamlit left out.

## Keyboard pass

Method: load the app, drive it into the mode (the same steps as `scripts/capture_ui_baseline.py`),
wait until it is idle, then press Tab from the top of the document until focus comes back to an
element it has already visited. At each stop, record the focused element and its computed
`outline`, and pass the stop only if the ring is the focus token (`2px solid #FFD84A`).

| Mode | Tab stops | With the focus ring | Reaches every card control |
| ---- | --------- | ------------------- | -------------------------- |
| Seed-based (default seed) | 75 | 75 | Yes: genre pills, Add to Seeds, More details on all 10 cards, then the three panels |
| Personalized (demo profile "Action Adventurer") | 83 | 83 | Yes: all 10 cards, the panels, then round to the sidebar seed controls |
| Browse (genre Action) | 68 | 68 | Yes: all 10 cards and the panels |

The order is sidebar first (Find → Refine → Personalize → Advanced → Quick Guide), then the main
area: the scroll container, How it works, ✕, each card's genre pills → Add to Seeds → More
details in rank order, and last Diversity & Novelty, Help / FAQ, Scoring details. It follows the
visual order. Focus is never trapped and never lands on a hidden element.

**Found and fixed:** before this task only the sidebar had the focus-token ring (Task 2.5). Every
main-area control (genre pills, Add to Seeds, rating buttons, expanders) fell back to Streamlit's
own ring, a 3 px signal red at 50 % alpha that fades in. On the panel it was barely visible, and
the main scroll container, which takes focus, showed nothing. The ring rule in
`app/styles/base.css` now covers the whole app, and the scroll container gets an inset ring.

**One-off in the first Personalized run:** a late rerun after the profile loaded moved focus back
to the sidebar partway through. A rerun with a longer settle wait went straight through. This is
Streamlit resetting focus on a rerun, not a tab-order bug, and it only happens while the app is
still running.

## Reading order (title, badge, explanation)

The accessibility tree of the first list card, from Playwright's `aria_snapshot()`:

```
- figure "Black Butler II":
  - img "Black Butler II"
  - text: Black Butler II
- heading "Black Butler II #1 Top match" [level=3]
- paragraph: "Shares Action with Fullmetal Alchemist: Brotherhood · fans of … · a well-known pick"
- paragraph: 黒執事II
- text: ★ 7.12 · TV · 12.0 eps · 2010 · Finished Airing
- button "Action" … button "Supernatural"
```

Title, badge, and explanation come in that order. The badge sits inside the title heading, so a
screen reader moving by heading hears the rank and tier with the title. The grid card has the
same order as separate paragraphs. Browse cards carry no match score, so they have no badge or
explanation, by design.

This was checked through the browser's accessibility tree, not with a screen reader. An NVDA or
VoiceOver listen is still worth doing before Task 4.2's demo media.

## Checklist items

| Item | Result |
| ---- | ------ |
| Every text color in the shipped CSS is a tested pair | `tests/test_theme_tokens.py::test_every_shipped_text_color_is_a_listed_pair` parses `base.css` and `components.css`. It resolves each `color` and its rule's own background (or the page and panel surfaces when the rule has none) and fails on any pair missing from `TEXT_PAIRS`. It found the streaming links: white on the old `#6C63FF` primary, **4.32:1, below AA**. They now use `bg` on `cyan` (10.8:1, the hovered-pill pair), and `primary` and `text_inverse` are gone from `LIVE`. The other `LIVE` accents were already used as text without being listed. They all pass (lowest: `chart.bad` on panel, 4.54:1) and are now in `TEXT_PAIRS`. |
| Decorative katakana and texture `aria-hidden` | The direction ships no katakana or texture (MASTER.md, "Texture and decoration"). Japanese text appears only as the real alternate title. The decorative pieces that do exist are hidden: card and grid markers, the loading skeletons and spinner, and the mix bar SVG. The mix legend's colored `●` dots, which were read as "black circle", are now hidden too. |
| Badge meaning does not rely on color alone | The tier label text is always in the badge (`Top match` … `Worth a look`, or `Match: n` with no run to rank in). `tests/test_cards.py::test_badge_meaning_is_in_text_not_only_color` covers every rank in a 20-item run, at both sizes. The rank and label had no space between them in the DOM (`#1Top match`), so they could be read as one word; they now have one. |
| Contrast ≥ 4.5:1 | All `TEXT_PAIRS` are tested (Task 1.2), now including every color the CSS paints as text. |
| Focus states visible | Every stop in all three modes; see the table above. |
| `prefers-reduced-motion` | Covered by Task 2.6 and unchanged. |

## Left for Task 3.4 (not fixed here; all three closed in Task 3.4)

These are outside this task's checklist and are recorded so they are not lost:

1. **Emoji in widget labels are read aloud by name.** Examples: `📥 Import from MAL`,
   `🎨 View Taste Profile`, `🔄 Reset Filters`, the `📊` before View Mode. The grid card's add-seed
   button is labelled only `🔄`, so its accessible name is "anticlockwise arrows button". The
   tooltip is not the name. This is F12 in `UX_PLAN.md`. **Closed in `b33ba639`.**
2. **The poster title is read twice before the heading:** once as the image alt and once as the
   figcaption. The caption could be `aria-hidden`, since the alt already names the image. **Closed in `a9160d41`** (the figure also needed `role='none'`).
3. **The `★` before the MAL score** is read as "black star" with no "MAL score" label. **Closed in `a9160d41`.**
