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

### Ranking Metrics (Temporal Split Heuristic)
From `reports/phase4_evaluation.md` (synthetic temporal ordering; treat as heuristic):

| Metric | Value |
|--------|-------|
| NDCG@5 | 0.4399 |
| NDCG@10 | 0.4383 |
| NDCG@20 | 0.4453 |
| MAP@5 | 0.1534 |
| MAP@10 | 0.0897 |
| MAP@20 | 0.0739 |
| Coverage@10 | 0.0018 |
| Gini@10 | 0.5000 |

Interpretation notes (from the report):
- Scores may be inflated by synthetic ordering effects.
- Coverage is very low (0.18% of catalog exposure in top-10), indicating concentration risk.

### Cold-Start (Content-only)
From `reports/phase4_evaluation.md`:

| Model | NDCG@10 | MAP@10 |
|-------|---------|--------|
| TF-IDF Content | 0.02528 | 0.02073 |
| Embeddings Content | 0.01558 | 0.01317 |

### Ablation (K=10)
From `reports/phase4_ablation.md` (table snapshot) and `reports/phase4_ablation.csv`:

- Popularity baseline: NDCG@10 ≈ 0.0307, MAP@10 ≈ 0.0183
- One hybrid variant entry shows: NDCG@10 ≈ 0.04385, MAP@10 ≈ 0.02959, Coverage@10 ≈ 0.00563

Note: the CSV currently contains repeated rows labeled “popularity” with multiple metric lines. Treat the ablation artifact as a draft and prefer the most clearly labeled, deduplicated experiment outputs when available.

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
