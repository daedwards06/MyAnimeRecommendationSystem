# Phase 4 / Chunk A3 — Next Chat Prompt (Context Reset Helper)

## Goal
Continue Phase 4 / Track A / Chunk A3: content features (parquet + optional new data) that are:
- deterministic,
- measurable via the existing Phase 4 golden harness,
- safe (golden `violation_count` must not increase).

## Current A3 status (already implemented)
- Implemented a conservative metadata rerank bonus using `data/processed/anime_metadata.parquet` columns:
  - categorical overlap: `studios`, `themes`
  - numeric proximity: `aired_from` year
- Guardrail: **year alone cannot generate affinity**; requires studios OR themes overlap.
- Fixed a mismatch bug by ensuring pruned metadata retains `themes` (pruning contract previously dropped it).
- Harness integration: seed-based scorer records `metadata_affinity` + `metadata_bonus` signals per recommendation.

## Key files (A3)
- Scoring utilities/constants: `src/app/metadata_features.py`
- Metadata pruning contract: `src/app/constants.py` (includes `themes` in minimum columns)
- Golden harness: `scripts/evaluate_phase4_golden.py`
- Unit tests: `tests/test_metadata_features.py`
- Playbook tracking: `docs/IMPLEMENTATION_PLAYBOOK.md` (Chunk A3 expanded next steps)

## Golden harness artifacts to compare
- Baseline (A2):
  - `reports/artifacts/phase4_golden_queries_20251229175855.json`
- Latest A3 (after gating + themes retained):
  - `reports/artifacts/phase4_golden_queries_20251229210520.json`
  - `experiments/metrics/phase4_eval_20251229210520.json`
  - `reports/phase4_golden_queries_20251229210520.md`

## Safety constraints
- Do not increase golden `violation_count`.
- Keep determinism: stable sorting and seeded randomness in eval.
- Do not change UX; only ranked scoring paths + offline evaluation.

## Commands to run
- Tests:
  - `python -m pytest -q`
- Golden harness:
  - `python scripts/evaluate_phase4_golden.py --k 10 --sample-users 50`

## Suggested next steps within A3 (pick one)
1) Improve measurement sensitivity:
   - Add rank-movement + top-20 overlap reporting so improvements show without changing top-10 membership.
2) Strengthen but keep safe:
   - Replace binary overlap with graded overlap (e.g., Jaccard) + thresholding; then re-tune coefficients.
3) Add “new data” deterministically:
   - TF-IDF synopsis similarity rerank (artifact built once; fast cosine at inference; log signals).

## What to report after changes
- Golden safety: list any queries where `violation_count` increased (should be none).
- At least two query deltas (Tokyo Ghoul + one other): show rank movement/top-20 changes.
- Any coefficient/threshold changes and why.
