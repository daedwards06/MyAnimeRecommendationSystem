# Jikan Feature Probe (Side Test)

Generated: 2025-12-29T18:13:40.246238+00:00
Golden artifact: reports/artifacts/phase4_golden_queries_20251229165531.json

This probe checks whether simple seed→candidate feature overlap differs between items flagged as golden violations vs non-violations.
It does not change app logic; it is meant to inform which metadata features are worth wiring in Chunk A3.

| Feature | Violation mean | Non-violation mean | Delta (non - viol) | N | Violations |
|---|---:|---:|---:|---:|---:|
| overlap_genres | 0.4352 | 0.4342 | -0.0010 | 240 | 44 |
| overlap_themes | 0.0455 | 0.0831 | 0.0377 | 240 | 44 |
| overlap_studios | 0.0227 | 0.0204 | -0.0023 | 240 | 44 |
| overlap_demographics | 0.0227 | 0.0332 | 0.0104 | 240 | 44 |
| overlap_producers | 0.0227 | 0.0032 | -0.0195 | 240 | 44 |
| type_match | 0.0000 | 0.0816 | 0.0816 | 240 | 44 |
| source_match | 0.1591 | 0.1633 | 0.0042 | 240 | 44 |
