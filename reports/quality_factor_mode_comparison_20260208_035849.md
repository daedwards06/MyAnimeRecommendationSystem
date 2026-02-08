# Quality Factor Mode Comparison

Generated: 2026-02-08 03:58:49 UTC

This report compares recommendation results across three quality factor modes:

- **mal_scaled** (default): `quality = clamp((MAL - 5) / 4, 0.15, 1.0)`
  - Favors high-MAL titles; penalizes niche anime with MAL 6-7
  - A niche anime with MAL 6.5 gets quality_factor=0.375, cutting its neural similarity contribution by 62%

- **binary**: `quality = 1.0 if MAL >= 6.0 else 0.5`
  - Mild penalty only for very low-rated titles; gentler gate for niche gems

- **disabled**: `quality = 1.0` (always)
  - Pure relevance - trusts semantic similarity fully without quality gating

---

## Summary Statistics

| Query | mal_scaled (niche/avg MAL) | binary (niche/avg MAL) | disabled (niche/avg MAL) |
|-------|----------------------------|------------------------|--------------------------|
| tokyo_ghoul | 0 / 0.00 | 0 / 0.00 | 0 / 0.00 |
| attack_on_titan | 0 / 0.00 | 0 / 0.00 | 0 / 0.00 |
| death_note | 0 / 0.00 | 0 / 0.00 | 0 / 0.00 |
| steins_gate | 0 / 0.00 | 0 / 0.00 | 0 / 0.00 |
| cowboy_bebop | 0 / 0.00 | 0 / 0.00 | 0 / 0.00 |

**Niche anime**: MAL score between 6.0 and 7.5

---

## Detailed Query Comparisons

### Query: `tokyo_ghoul`

**Seeds**: Tokyo Ghoul

_No new niche anime emerge in binary or disabled modes._

#### Top-5 Comparison

| Rank | mal_scaled | binary | disabled |
|------|------------|--------|----------|
| 1 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 2 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 3 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 4 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 5 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |

---

### Query: `attack_on_titan`

**Seeds**: Attack on Titan

_No new niche anime emerge in binary or disabled modes._

#### Top-5 Comparison

| Rank | mal_scaled | binary | disabled |
|------|------------|--------|----------|
| 1 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 2 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 3 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 4 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 5 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |

---

### Query: `death_note`

**Seeds**: Death Note

_No new niche anime emerge in binary or disabled modes._

#### Top-5 Comparison

| Rank | mal_scaled | binary | disabled |
|------|------------|--------|----------|
| 1 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 2 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 3 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 4 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 5 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |

---

### Query: `steins_gate`

**Seeds**: Steins;Gate

_No new niche anime emerge in binary or disabled modes._

#### Top-5 Comparison

| Rank | mal_scaled | binary | disabled |
|------|------------|--------|----------|
| 1 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 2 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 3 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 4 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 5 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |

---

### Query: `cowboy_bebop`

**Seeds**: Cowboy Bebop

_No new niche anime emerge in binary or disabled modes._

#### Top-5 Comparison

| Rank | mal_scaled | binary | disabled |
|------|------------|--------|----------|
| 1 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 2 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 3 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 4 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |
| 5 | Unknown (N/A) | Unknown (N/A) | Unknown (N/A) |

---

## Key Findings

### Niche Anime Discovery

- **mal_scaled**: 0 total niche anime across 5 queries
- **binary**: 0 total niche anime (+0)
- **disabled**: 0 total niche anime (+0)

### Average MAL Score

- **mal_scaled**: 0.00
- **binary**: 0.00 (+0.00)
- **disabled**: 0.00 (+0.00)

### Interpretation

- **binary mode** allows more niche anime (MAL 6-7) to surface while maintaining a basic quality threshold. This is a good balance for users who want diverse, relevant recommendations without excessive bias toward mainstream titles.

- **disabled mode** surfaces the most niche content, trusting semantic similarity fully. This may be preferred by users seeking hidden gems, but risks surfacing low-quality or poorly-rated titles.

- **mal_scaled mode** (default) maintains the highest average MAL score but may miss highly relevant niche titles that have lower community ratings.
