# Skill Catalog Search (Task 1.1)

> Searches of the UI UX Pro Max catalog (`.claude/skills/ui-ux-pro-max/`), run 2026-10-19 at
> commit `c226c53d`. The searches are for design decisions only; stack and code output is ignored.
>
> **Owner pick (2026-10-19): direction A, cel title card at night.** Persisted to
> `design-system/mars/MASTER.md`.

## What the generator can and cannot be steered by

`--design-system` takes its whole system (style, palette, fonts, effects, anti-patterns) from the
single product row the query matches in `products.csv`, then the reasoning rule for that
category in `ui-reasoning.csv`. Style words in the query don't change the result.
`"… retro neubrutalism hard shadow"`, `"… retro vaporwave night"` and
`"… flat bold hard shadow japanese"` all return the same system as the bare query, because they
all match the same product row. So the generated MASTER.md is a base. The era has to come from
the "90s Anime Overrides" section that Task 1.2 adds, not from the query.

| Query (`--design-system -p "MARS"`) | Product matched | Style | Fonts | Verdict |
| ----------------------------------- | --------------- | ----- | ----- | ------- |
| `anime recommendation entertainment retro` (the plan's query) | Gaming | 3D & Hyperrealism (WebGL, parallax; `cost:high`, `risk:high`) | Russo One / Chakra Petch (esports) | The drift the plan warned about. It breaks principle 1 (CSS-only texture, first-card budget), so reject it. |
| `anime video streaming personalized recommendation retro` | Video Streaming/OTT (`if_personalized` → add recommendations) | Dark Mode (OLED) (`cost:low`, `risk:low`) | Inter / Inter | Right product shape and a cheap, low-risk dark base. The fonts and palette get replaced by the overrides. |
| `anime streaming recommendation retro` | Video Streaming/OTT | Pixel Art (`risk:conditional`) | Press Start 2P / VT323 | Wrong era and medium (8-bit games, not cel animation). VT323 is a poor body face. |

## Shortlist

Each line is the catalog entry, then why it fits or doesn't.

### Style (`--domain style`)

- `"retro 90s"` and the retry `"retro"`: **no database match**.
- **Neubrutalism** (from the retry `"flat bold hard shadow"`): 3 px black borders, hard
  `4px 4px 0` shadow, flat color, no blur; `cost:low`, `risk:low`. This gives the cel /
  title-card mechanics (outlined, hard-edged, flat fill) without any IP. The generator can't
  reach it, so it gets recorded as an override.
- **Bauhaus**, same search: hard offset shadows and a press-to-translate active state; `cost:low`.
  Its "instant 0 ms transitions" rule is worth keeping for press feedback. The primary
  red/blue/yellow palette is the wrong era.
- **Vaporwave** (`"vaporwave VHS cel animation"`, the only hit): sunset gradients, neon glow,
  glitch, scanlines; `cost:moderate`, **`risk:high`**. Scanlines and the sunset palette are
  useful as accents. Glow text and glitch animation conflict with principle 3 (readability) and
  the reduced-motion rule.
- **Retro-Futurism** (the retry `"retro-futurism nostalgic"`): CRT scanlines via a `::before`
  overlay; neon on `#1A1A2E`; monospace fonts; **`risk:high`**. The scanline technique is the
  only part to take. The monospace + neon look is 80s cyberpunk, not 90s anime.

### Color (`--domain color`, `"entertainment streaming night"`)

- **Music Streaming**: `#0F0F23` background, `#1B1B30` card, `#94A3B8` muted text, indigo
  `#312E81` border. A night base close to the plan's navy. The green accent doesn't fit.
- **Video Streaming/OTT**: pure black `#000000`, card `#0C0C0D`, rose accent `#E11D48`. Too
  cinema-black for the night-sky palette. The rose accent is near the plan's magenta.
- **Sleep Tracker**: `#0F172A` background, indigo/violet. Night-sky hue but no warm accent, so
  no sunset.
- None of the three has the warm sunset/cream half of the brief. The plan's starting palette
  (night navy `#1B1F3B`, panel `#262B52`, sunset orange, magenta, sakura, cel cream, VHS teal)
  takes the night base from these and adds the warm accents itself. Contrast is tested in
  Task 1.2.

### Typography (`--domain typography`, `"bold display playful rounded"`)

- **Nunito / DM Sans** (Claymorphism Mobile): rounded headings, clean body. Friendly but reads
  as a children's-app look.
- **Fredoka / Nunito** (Playful Creative): rounded and warm, "entertainment" in Best For. No
  Japanese glyphs.
- **Baloo 2 / Comic Neue** (Kids/Education): the wrong audience.
- The retries `"japanese display"` and `--domain google-fonts` found what the brief needs:
  **Dela Gothic One** (Display, one weight 400, `japanese` subset) and **M PLUS Rounded 1c**
  (Sans, weights 100–900, `japanese` subset). That is a heavy poster-style display face with a
  rounded body face. Both cover katakana, so the decorative katakana accents in Task 2.4 don't
  need a third font. Noto Serif JP / Noto Sans JP ("Japanese Elegant", anime/manga in Best
  For) is the fallback if Dela Gothic One proves too heavy.

### Chart (`--domain chart`)

- `"recommendation results"`: **no database match** (closest known term "rest").
- The retry `"proportion part-to-whole"` covers the mix bar (popularity share of the top N).
  The catalog points to pie/donut (`risk:high`) or a waffle (`risk:low`). The existing single
  stacked bar with direct labels is fine. The rule to keep: label every segment with text and
  never encode the band by color alone (it ties to F1/F8).
- `"ranking comparison"`: Bar (`risk:low`) for the taste-profile genre bars; Radar
  (`risk:conditional`) for the existing taste radar, which needs direct series labels and point
  shapes as well as color.

## Directions for the owner to pick

| | Direction | Base generated into MASTER.md | Overrides (Task 1.2) | Cost / risk |
| - | --------- | ----------------------------- | -------------------- | ----------- |
| **A (recommended)** | **Cel title card at night**: flat cel fills, 3 px outlines, hard offset shadows, outlined display type, light scanlines on the background only | Video Streaming/OTT → Dark Mode (OLED) | Neubrutalism shadow/border mechanics; the plan's night-navy + sunset palette; Dela Gothic One + M PLUS Rounded 1c; scanlines ≤ 6 % from Retro-Futurism | `cost:low`, `risk:low`; fits principles 1–3 as written |
| B | **Vaporwave sunset**: gradient sky, neon glow headings, glitch accents | Video Streaming/OTT → Dark Mode (OLED) | Vaporwave palette and glow | `risk:high`; glow text and glitch fight the 4.5:1 test and reduced motion, so the tokens would need cutting back in 1.2 |
| C | **Take the generator as is** (Gaming → 3D & Hyperrealism) | Gaming | none | `cost:high`; WebGL and parallax break principle 1. Listed only for completeness. |

A matches the plan's Task 1.2 starting point. B is mostly a palette and effects swap on the same
base, so parts of it (the sunset gradient in the header, for example) can still be added to A at
the Task 1.3 mockup stage, where the "Full broadcast" intensity tests it.
