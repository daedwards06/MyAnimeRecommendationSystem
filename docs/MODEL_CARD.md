# Model Card: MARS (My Anime Recommendation System)

> Last updated: 2026-02-16  
> Project: MARS — My Anime Recommendation System  
> Type: Hybrid recommendation pipeline (collaborative + content + popularity)  

## Model Details

### Summary
MARS is a hybrid anime recommendation system that combines collaborative filtering (matrix factorization + item-based kNN) with content similarity (synopsis embeddings and metadata overlap) inside a deterministic, three-stage ranking pipeline:

- Stage 0: Candidate generation (neural/content neighbors + metadata overlap + popularity backfill)
- Stage 1: Shortlist construction (semantic admission + gating heuristics)
- Stage 2: Reranking (hybrid CF + content signals + penalties/bonuses)
- Post-processing: franchise cap, optional personalization blend, and display filtering

The system is designed for:
- explainable recommendations (component shares and metadata overlaps)
- reproducible offline evaluation (seeded runs)
- a Streamlit UI for interactive exploration

### Versioning & Artifacts
- MF model artifact stem (default): `mf_sgd_v2025.11.21_202756`
- kNN model artifact stem (default): `item_knn_sklearn_v2025.11.21_202756`
- Hybrid weights (balanced preset): `mf=0.93078`, `knn=0.06625`, `pop=0.00297`

Artifacts are loaded and validated at startup by `src/app/artifacts_loader.py`.

### Primary Components

#### Collaborative Filtering: FunkSVD (SGD Matrix Factorization)
- Implementation: `src/models/mf_sgd.py` (`FunkSVDRecommender`)
- Factors: 64
- Optimizer: SGD on centered explicit ratings
- Regularization: L2
- Training defaults (as implemented): `lr=0.005`, `reg=0.05`, `n_epochs=10`, `random_state=42`

#### Collaborative Filtering: Item-based kNN
- Implementation: `src/models/knn_sklearn.py` (`ItemKNNRecommender`)
- Similarity: cosine over an item-user matrix (optionally normalized)
- User profile: rating-weighted aggregation of seen-item vectors with shrinkage
- Includes a small popularity prior to stabilize ranking

#### Content Signals: Synopsis Embeddings + Metadata Overlap
- Synopsis embedding similarity utilities: `src/app/synopsis_embeddings.py`
- Embedding backend: deterministic TF-IDF + SVD pipeline (default `tfidf_svd_256`)
- Embedding dimensionality: 256 (SVD)
- Text policy: uses existing synopsis fields only; deterministic truncation to 240 chars

#### Diversification (Intra-list diversity)
- MMR reranking is available in `src/app/diversity.py` via `mmr_rerank()`.
- If enabled in the pipeline, MMR trades off relevance vs similarity using:
  $$\text{MMR}(i) = \lambda\,\text{rel}(i) - (1-\lambda)\max_{j \in S}\text{sim}(i, j)$$

Reference:
- Carbonell, J., & Goldstein, J. (1998). *The use of MMR, diversity-based reranking for reordering documents and producing summaries.* SIGIR.

## Intended Use

### Intended Users
- Anime fans who want discovery recommendations.
- Developers/reviewers evaluating a portfolio-grade recommender system implementation.

### Intended Use Cases
- Seed-based recommendations: “I liked X; recommend similar anime.”
- Personalized recommendations: import a user’s ratings and blend personalized CF with seed-based discovery.
- Explainability: view score component shares and metadata overlaps.

### Out of Scope
- Production deployment with strict SLAs, real-time retraining, or sensitive-user safety guarantees.
- Recommendations for minors with content moderation guarantees.
- Commercial use (dataset / upstream terms may restrict usage).

## Training Data

### Interaction Data (Collaborative Filtering)
- Source: Kaggle MyAnimeList ratings dataset (2019/2020 snapshot)
- Documented in: `DATA_SOURCES.md`
- Content: explicit user–anime ratings

### Metadata / Enrichment (Content Features)
- Source: Jikan API (unofficial MAL API)
- Fields: titles, synopsis, genres, themes, demographics, studios, popularity proxies, etc.
- Documented in: `DATA_SOURCES.md`

### Known Data Limitations
- Snapshot staleness: ratings reflect a frozen historical slice; new titles may be missing from CF training.
- Popularity and metadata drift: API-derived fields change over time.
- Language: synopsis similarity is effectively English-centric when using English stop-words and text processing.
- Representation: MyAnimeList user base is not demographically representative of all viewers.

## Evaluation Data

### Offline Evaluation Protocol
Offline evaluation uses held-out user interactions and ranking metrics at K (e.g., NDCG@K, MAP@K). The repo includes a “temporal split” analysis, noted as heuristic when timestamps are synthetic.

- Report: `reports/phase4_evaluation.md`
- Ablation table: `reports/phase4_ablation.md` / `reports/phase4_ablation.csv`

## Metrics

All figures below come from one run: `scripts/run_unified_eval.py --k 10 --sample-users 1000`,
seed 42, ranking over the full ~13K catalog. Collaborative-filtering models are fit on the
**train split only**; the artifacts in `models/` are fit on every interaction and scoring them
offline would measure leakage. Full protocol and narrative: `reports/phase4_evaluation.md`.

### Ablation (K=10, 1,000 users, seed 42)

| Model | NDCG@10 | MAP@10 | Coverage@10 | Gini@10 | NDCG vs. popularity | NDCG vs. MF |
|:---|---:|---:|---:|---:|---:|---:|
| item_knn_sklearn | 0.0628 | 0.0513 | 0.1160 | 0.7280 | +81.1% | +92.6% |
| hybrid_rrf | 0.0586 | 0.0456 | 0.0784 | 0.8253 | +69.1% | +79.8% |
| popularity | 0.0347 | 0.0255 | 0.0056 | 0.7175 | — | +6.3% |
| mf_sgd | 0.0326 | 0.0266 | 0.0668 | 0.7875 | −6.0% | — |
| hybrid_weighted | 0.0324 | 0.0249 | 0.0615 | 0.7993 | −6.5% | −0.6% |
| content_tfidf | 0.0211 | 0.0166 | 0.1711 | 0.6334 | −39.1% | −35.2% |
| content_embeddings | 0.0101 | 0.0069 | 0.0588 | 0.8620 | −70.7% | −68.9% |

Source: `reports/phase4_ablation.csv` / `.md`, regenerated by
`scripts/generate_phase4_ablation.py` from `data/processed/phase4/metrics_by_k.parquet`.

**Reading the table.** The shipped blend (`hybrid_weighted`, 93% MF) performs like MF, which is
what it mostly is: within 0.6% on NDCG, near the popularity baseline on accuracy, and worth
10.9× popularity's catalog coverage. Item-kNN alone is the strongest model measured. Its
historical near-zero score (NDCG 0.0017) was an evaluation defect — `exclude_seen` masked the
held-out item using the model's own full-fit matrix — not a property of the model; see
`reports/phase4_evaluation.md` §8. The blend weights were tuned under that defective protocol and
have not yet been re-tuned.

### Temporal Split (heuristic only)

A synthetic temporal split (timestamps derived from row index, no real interaction dates in the
snapshot) reports NDCG@10 = 0.4383 and Coverage@10 = 0.0018. These values are an order of
magnitude above every like-for-like measurement above, which indicates ordering artifacts rather
than better ranking. They are retained as a robustness check only, in
`reports/phase4_evaluation.md` §6, and are not an accuracy claim.

### Cold-Start

The cold-start-restricted run returned NDCG@10 = 0.0 at this cohort: none of the 1,000 sampled
users had a held-out item that was a cold item, so the metric has no support. Content-only
performance over the full catalog is `content_tfidf` / `content_embeddings` in the table above.

## Ethical Considerations

### Popularity Bias / Concentration
Collaborative filtering and popularity priors can over-recommend mainstream titles and under-expose long-tail content. Low Coverage@10 and higher Gini are indicators of concentration risk.

### Filter Bubbles
Strong similarity signals (especially seed-based and CF) can produce narrow recommendations, reinforcing existing preferences.

### Demographic & Content Sensitivity
Anime content includes mature themes and violence; the system does not implement content moderation or age gating.

### Licensing / Terms of Use
The system relies on datasets and APIs with their own terms. See `DATA_SOURCES.md` and ensure downstream usage complies with Kaggle dataset licensing and any upstream platform terms.

## Limitations & Known Issues

- Cold-start users/items: users with very few ratings and items not present in the CF training snapshot rely on content similarity and popularity.
- Temporal modeling: no true time-aware decay; “temporal split” evaluation may be synthetic.
- Language: synopsis processing assumes English-like text (stop words, tokenization).
- Concentration: beyond-accuracy metrics suggest popularity/CF concentration; additional diversification may be needed.
- Hand-tuned thresholds: the pipeline contains multiple heuristic gates and weights (see `src/app/constants.py`).
- No online evaluation: no A/B testing; results are offline only.

## Recommendations for Use

- Use seed-based mode for “more like this” discovery.
- Use personalization mode when the user can provide a meaningful rating history.
- For exploration and novelty, enable/extend diversification (e.g., franchise cap, MMR) and monitor coverage/Gini shifts.

## References

- Carbonell, J., & Goldstein, J. (1998). *The use of MMR, diversity-based reranking for reordering documents and producing summaries.* SIGIR.
- Mitchell, M., Wu, S., Zaldivar, A., et al. (2019). *Model Cards for Model Reporting.* (Model card concept).
