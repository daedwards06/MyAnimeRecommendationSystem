# UI / UX Redesign & Imagery Integration

## Goals
- Reduce cognitive load: clear separation between recommendation list, explanations, and diversity metrics.
- Accelerate comprehension: visual artwork anchors and structured typography.
- Accessibility: WCAG AA contrast, keyboard navigable components, descriptive alt text.
- Performance: time-to-first-rec <5s; incremental loading; image latency amortized via local cache.
- Personalization readiness: session persistence of persona, weight preset, and top-N.

## Primary User Journeys
1. Browse recommendations (scan cards, adjust weights, pick interesting titles).
2. Understand why an item appears (view contribution shares, badges, and genres).
3. Assess diversity/novelty (open metrics drawer, glance at coverage & genre exposure).
4. Iterate preferences (change persona or top-N, observe instant UI update).

## Information Architecture
- Persistent header: app title + weight toggle + latency badge.
- Left sidebar: persona selector, search box, filters (future), top-N slider.
- Main content: responsive grid of recommendation cards.
- Secondary drawer (collapsible): diversity metrics, sparklines, popularity distribution.
- Onboarding modal (first visit): quick usage tips (dismiss -> session flag).

## Component Breakdown
| Component | Responsibility |
|-----------|----------------|
| `layout.py` | Page scaffold, header, global containers |
| `state.py` | Session state management + URL param sync |
| `cards.py` | Recommendation card (image, title, genres, badges, expand explanation) |
| `tooltips.py` | Central registry for tooltip text + accessible descriptions |
| `diversity_panel.py` | Metrics drawer with charts & definitions |
| `images.py` | Image path resolution, placeholder logic, alt text assembly |

## Design System (Tokens)
Declare semantic tokens (colors, spacing, typography) in a single source (JSON or Python dict). Example keys:
- Colors: `background`, `surface`, `surface-alt`, `border`, `text-primary`, `text-secondary`, `accent`, `accent-alt`, `danger`, `focus-ring`.
- Spacing scale: `space-xxs (2)`, `xs (4)`, `sm (8)`, `md (12)`, `lg (16)`, `xl (24)`, `xxl (32)`.
- Typography: `font-family-base`, size ramp (`xs 12`, `sm 13`, `md 15`, `lg 17`, `xl 20`, `display 24+`).
- Radii: `radius-sm (4)`, `radius-md (8)`, `radius-lg (12)`.
Dark mode duplicates tokens with adjusted backgrounds & text contrast.

## Imagery Integration
### Source & Fields
Use Jikan API anime full endpoint. Extract primary poster URL & small variant. Extend metadata schema:
- `poster_url`
- `poster_thumb_url`
- `image_last_fetched`
- `image_attribution`
- `image_md5` (optional for change detection)

### Pipeline Overview
1. Collect IDs (existing metadata parquet ids).
2. Fetch image JSON (if not cached or expired >30 days).
3. Download original poster; validate content-type starts with `image/`.
4. Resize/compress to thumbnail (width ~180px) -> WebP or optimized JPEG.
5. Write thumbnail under `data/processed/images/posters/<anime_id>_<hash>.webp`.
6. Update metadata parquet with image fields.

### Caching & Refresh
- Use last-fetched timestamp + age threshold.
- Manual refresh flag (`--force-image-refresh`).

### Alt Text Strategy
`<title_display> anime poster` + optional truncated synopsis (first 12 words) for richer context.

### Accessibility & Fallback
- If image unavailable: placeholder SVG/PNG with neutral background and title initials.
- Provide ARIA-label mirroring alt text; ensure focus ring visible when card selected via keyboard.

### Performance Targets
- Additional network for initial batch < 1.5s amortized (cached thumbnails after first run).
- Thumbnails average size < 40KB.
- No blocking on images: cards render skeleton placeholders, then populate image.

## Metrics Drawer Design
Contents:
- Coverage: numeric + sparkline (recent sessions if stored).
- Genre Exposure Ratio: gauge or pie (top genres only).
- Novelty Average: numeric + histogram overlay of recommendation popularity ranks.
- Popularity Band Legend: textual list with thresholds.

## Tooltips & Help
Central dictionary keyed by metric or badge ID to ensure consistency:
```
TOOLTIPS = {
  'cold_start': 'Item shown due to minimal interaction data; content similarity path used.',
  'popularity_band': 'Relative popularity segment based on MAL member counts.',
  'novelty_ratio': 'Share of recommended items outside the user\'s historical genre footprint.',
  'genre_exposure_ratio': 'Unique genres in current recommendations divided by unique genres in catalog.'
}
```

## Session Persistence
Store persona, weight mode, top-N, collapsed state of drawer under `st.session_state`. Reflect changes into query params for shareable deep links (e.g., `?persona=action_fan&weights=diversity&n=15`).

## Roadmap Phases (Implementation Order)
1. Token & theming infrastructure + state module.
2. Card component (without images) refactor.
3. Image pipeline & thumbnail integration.
4. Metrics drawer & tooltips.
5. Performance indicators & latency badge.
6. Onboarding modal & empty/error states.
7. Dark mode toggle.
8. Accessibility audit and refinements.
9. Documentation & screenshots.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Image fetching rate limits | Respect throttle + incremental batches |
| Large image sizes inflate memory | Enforce width & compression; WebP conversion |
| Broken external URLs | Validate content-type; fallback placeholders |
| Accessibility regressions | Automated aXe scan + keyboard walkthrough |
| Performance regressions | Measure latency before/after; retain metrics badge |

## Success Metrics
- Time-to-first-render (cards skeleton) < 1s.
- Image load complete for top 8 cards < 2.5s (warm cache < 0.8s).
- Coverage & genre exposure accessible via one click (drawer) with keyboard focus.
- Zero contrast ratio violations (AA) in color audit.

---
Last Updated: 2025-11-22
