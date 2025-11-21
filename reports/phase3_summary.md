# Phase 3 Summary (Closed 2025-11-21)

## Overview
Phase 3 delivered baseline CF & content models, hybrid blending (weighted, RRF), diversity & coverage metrics, explanations, and diversity-aware tuning. Balanced hybrid weights (mf=0.93078, knn=0.06625, pop=0.00297) were frozen after Optuna runs with a coverage reward and popularity cap.

Historical intermediate tables are retained below for provenance; the final table (latest generation) should be used for narrative and Phase 4 evaluation baselines.

## Initial Metrics (historical, early slice)

| Model                | NDCG@10  | MAP@10  | Users |
|----------------------|----------|---------|-------|
| Popularity Baseline  | 0.04385  | 0.02959 | 500   |
| MF (FunkSVD, SGD)    | 0.04281  | 0.03066 | 500   |
| Item kNN (profile)   | 0.00338  | 0.00262 | 500   |
| Hybrid Weighted      | 0.02196  | 0.01385 | 300   |
| Hybrid RRF           | 0.02345  | 0.01357 | 300   |

Notes:
- Popularity scores computed as log(1+count) * mean_rating.
- MF is trained with centered ratings, lr=0.005, reg=0.05, 64 factors.
- Item kNN uses rating-weighted, centered user profiles against an item-user cosine matrix with profile shrinkage and a small popularity prior.
- Hybrid results will populate after running the hybrid evaluator (below).

## Example recommendations (top-5)

After running the hybrid evaluator, examples will be saved to `experiments/metrics/hybrid_examples_YYYYMMDDHHMMSS.json`.
If the examples file isn't present, re-run the hybrid evaluator once more; examples are captured for the first couple of users processed.

- Example user A (user_id):
  - KNN: [...]
  - MF: [...]
  - Popularity: [...]
  - Hybrid (Weighted): [...]
  - Hybrid (RRF): [...]

- Example user B (user_id):
  - KNN: [...]
  - MF: [...]
  - Popularity: [...]
  - Hybrid (Weighted): [...]
  - Hybrid (RRF): [...]

## How to run

Use PowerShell:

```powershell
# Train updated Item kNN (centering, shrinkage, popularity prior)
python .\scripts\train_knn_sklearn.py

# Evaluate individual models with CLI flags
python .\scripts\evaluate_knn_mf.py --k 10 --sample-users 500

# Evaluate hybrids (weighted blend and RRF)
python .\scripts\evaluate_hybrid.py --k 10 --sample-users 300 --w-mf 0.6 --w-knn 0.3 --w-pop 0.1
```

Artifacts:
- Models: `models/`
- Metrics JSON and summary CSV: `experiments/metrics/`
- Examples: `experiments/metrics/hybrid_examples_*.json`

## Hybrid weight sweep (K=10, users=300)

Tried weighted blends; sweep found a weighted configuration that outperforms RRF on this 300-user slice:

| Weights (mf/knn/pop) | NDCG@10 | MAP@10 |
|----------------------|---------|--------|
| 0.556 / 0.222 / 0.222| 0.02851 | 0.01631 |
| 0.6 / 0.3 / 0.1      | 0.02196 | 0.01385 |
| RRF (k=60)           | 0.02345 | 0.01357 |

Source: `experiments/metrics/hybrid_weight_sweep_*.csv`. You can sweep additional weights quickly using `scripts/sweep_hybrid_weights.py` or `scripts/evaluate_hybrid.py` flags.


## Auto-generated metrics (latest)

Generated: 2025-11-15 20:03 UTC

| Model | NDCG@10 | MAP@10 | Users |
|---|---|---|---|
| Popularity Baseline | 0.03072 | 0.01833 | 300 |
| MF (FunkSVD, SGD) | 0.04031 | 0.02875 | 300 |
| Item kNN (profile) | 0.00563 | 0.00437 | 300 |
| Hybrid Weighted | 0.02196 | 0.01385 | 300 |
| Hybrid RRF | 0.02345 | 0.01357 | 300 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 |
| Content Embeddings | 0.01558 | 0.01317 | 300 |


## Auto-generated metrics (historical snapshots)

Generated: 2025-11-17 14:18 UTC (pre diversity-aware tuning)

| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |
|---|---|---|---|---|---|
| Popularity Baseline | 0.04385 | 0.02959 | 500 | 0.006 | 0.708 |
| MF (FunkSVD, SGD) | 0.04281 | 0.03066 | 500 | 0.056 | 0.736 |
| Item kNN (profile) | 0.00338 | 0.00262 | 500 | 0.085 | 0.664 |
| Hybrid Weighted | 0.04441 | 0.02977 | 500 | 0.006 | 0.702 |
| Hybrid RRF | 0.03110 | 0.01725 | 500 | 0.059 | 0.775 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 | 0.000 | 0.000 |
| Content Embeddings | 0.01558 | 0.01317 | 300 | 0.000 | 0.000 |


Generated: 2025-11-17 14:42 UTC (consistency check)

| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |
|---|---|---|---|---|---|
| Popularity Baseline | 0.04385 | 0.02959 | 500 | 0.006 | 0.708 |
| MF (FunkSVD, SGD) | 0.04281 | 0.03066 | 500 | 0.056 | 0.736 |
| Item kNN (profile) | 0.00338 | 0.00262 | 500 | 0.085 | 0.664 |
| Hybrid Weighted | 0.04441 | 0.02977 | 500 | 0.006 | 0.702 |
| Hybrid RRF | 0.03110 | 0.01725 | 500 | 0.059 | 0.775 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 | 0.000 | 0.000 |
| Content Embeddings | 0.01558 | 0.01317 | 300 | 0.000 | 0.000 |


Generated: 2025-11-17 16:50 UTC (larger user slice, popularity-heavy hybrid)

| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |
|---|---|---|---|---|---|
| Popularity Baseline | 0.04120 | 0.02785 | 1000 | 0.006 | 0.726 |
| MF (FunkSVD, SGD) | 0.05036 | 0.03900 | 1000 | 0.071 | 0.784 |
| Item kNN (profile) | 0.00169 | 0.00131 | 1000 | 0.118 | 0.728 |
| Hybrid Weighted | 0.04135 | 0.02780 | 1000 | 0.006 | 0.717 |
| Hybrid RRF | 0.03910 | 0.02511 | 1000 | 0.083 | 0.821 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 | 0.000 | 0.000 |
| Content Embeddings | 0.01558 | 0.01317 | 300 | 0.000 | 0.000 |


Generated: 2025-11-17 22:25 UTC (duplicate hybrid weights entry)

| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |
|---|---|---|---|---|---|
| Popularity Baseline | 0.04120 | 0.02785 | 1000 | 0.006 | 0.726 |
| MF (FunkSVD, SGD) | 0.05036 | 0.03900 | 1000 | 0.071 | 0.784 |
| Item kNN (profile) | 0.00169 | 0.00131 | 1000 | 0.118 | 0.728 |
| Hybrid Weighted | 0.04120 | 0.02785 | 1000 | 0.006 | 0.726 |
| Hybrid RRF | 0.03910 | 0.02511 | 1000 | 0.083 | 0.821 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 | 0.000 | 0.000 |
| Content Embeddings | 0.01558 | 0.01317 | 300 | 0.000 | 0.000 |


Generated: 2025-11-17 23:45 UTC (first balanced hybrid improvement)

| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |
|---|---|---|---|---|---|
| Popularity Baseline | 0.04120 | 0.02785 | 1000 | 0.006 | 0.726 |
| MF (FunkSVD, SGD) | 0.05036 | 0.03900 | 1000 | 0.071 | 0.784 |
| Item kNN (profile) | 0.00169 | 0.00131 | 1000 | 0.118 | 0.728 |
| Hybrid Weighted | 0.04973 | 0.03844 | 1000 | 0.066 | 0.791 |
| Hybrid RRF | 0.03910 | 0.02511 | 1000 | 0.083 | 0.821 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 | 0.000 | 0.000 |
| Content Embeddings | 0.01558 | 0.01317 | 300 | 0.000 | 0.000 |


## Final Metrics (Latest Unified Slice)

Generated: 2025-11-21 20:25 UTC

| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |
|---|---|---|---|---|---|
| Popularity Baseline | 0.04120 | 0.02785 | 1000 | 0.006 | 0.726 |
| MF (FunkSVD, SGD) | 0.05036 | 0.03900 | 1000 | 0.071 | 0.784 |
| Item kNN (profile) | 0.00169 | 0.00131 | 1000 | 0.118 | 0.728 |
| Hybrid Weighted (Balanced) | 0.04973 | 0.03844 | 1000 | 0.066 | 0.791 |
### Final Hybrid Weights
Frozen weights (normalized):
- mf = 0.9307796791956574
- knn = 0.06624663364738044
- pop = 0.0029736871569621902

Rationale: Maintains ~99% of MF NDCG while providing broader exposure than popularity alone. Popularity weight minimized after coverage-aware objective reduced reliance on globally popular titles.

### How to Reproduce Final Metrics
```powershell
python .\scripts\evaluate_hybrid.py --k 10 --sample-users 1000
python .\scripts\update_phase3_report.py
```

### Notes for Phase 4
- Use the final table above for plotting NDCG/MAP vs K and coverage/Gini curves.
- Historical tables demonstrate evolution (sweep → popularity-heavy → balanced diversity-aware tuning).
- Item kNN retained for diversity contribution despite low standalone ranking performance.
| Hybrid RRF | 0.03910 | 0.02511 | 1000 | 0.083 | 0.821 |
| Content TF-IDF | 0.02528 | 0.02073 | 300 | 0.000 | 0.000 |
| Content Embeddings | 0.01558 | 0.01317 | 300 | 0.000 | 0.000 |
