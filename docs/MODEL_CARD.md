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
- Hybrid weights: Balanced preset `mf=0.0475`, `knn=0.9522`, `pop=0.0003` (the Task 0.6 re-tune); Diversity preset item-kNN alone. Item-kNN is scored per request from the seed titles, or from profile ratings when personalized (see § Metrics, "What the app serves")

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

| Model | NDCG@10 | NDCG@10 95% CI | MAP@10 | Coverage@10 | Gini@10 | ΔNDCG vs. popularity, paired 95% CI | ΔNDCG vs. item-kNN, paired 95% CI |
|:---|---:|:---:|---:|---:|---:|:---:|:---:|
| implicit_als | 0.1890 | [0.1691, 0.2106] | 0.1516 | 0.0927 | 0.6542 | [+0.1340, +0.1750] | [+0.1059, +0.1475] |
| hybrid_mf_knn | 0.0667 | [0.0540, 0.0802] | 0.0529 | 0.1076 | 0.7507 | [+0.0184, +0.0465] | [−0.0027, +0.0096] |
| hybrid_weighted_tuned | 0.0658 | [0.0535, 0.0795] | 0.0521 | 0.1029 | 0.7601 | [+0.0175, +0.0454] | [−0.0036, +0.0091] |
| item_knn_sklearn | 0.0632 | [0.0507, 0.0775] | 0.0516 | 0.1168 | 0.7276 | [+0.0140, +0.0441] | — |
| hybrid_rrf | 0.0547 | [0.0445, 0.0674] | 0.0419 | 0.0782 | 0.8281 | [+0.0099, +0.0308] | [−0.0180, +0.0006] |
| popularity | 0.0347 | [0.0259, 0.0444] | 0.0255 | 0.0056 | 0.7175 | — | [−0.0441, −0.0140] |
| hybrid_weighted | 0.0324 | [0.0237, 0.0424] | 0.0249 | 0.0615 | 0.7993 | [−0.0129, +0.0086] | [−0.0447, −0.0188] |
| mf_sgd | 0.0282 | [0.0196, 0.0379] | 0.0224 | 0.0667 | 0.7910 | [−0.0171, +0.0046] | [−0.0485, −0.0234] |
| content_tfidf | 0.0211 | [0.0138, 0.0288] | 0.0166 | 0.1711 | 0.6334 | [−0.0260, −0.0014] | [−0.0566, −0.0289] |
| content_embeddings | 0.0101 | [0.0059, 0.0154] | 0.0069 | 0.0588 | 0.8620 | [−0.0352, −0.0148] | [−0.0681, −0.0396] |

Source: `reports/phase4_ablation.csv` / `.md`, regenerated by
`scripts/generate_phase4_ablation.py` from `data/processed/phase4/metrics_by_k.parquet` and
`per_user_metrics.parquet`. Intervals: percentile bootstrap over users, 1,000 resamples, seed 42;
the Δ columns are paired (both models resampled on the same users). `hybrid_weighted` uses the
weights the app served before Task 0.9 (mf 0.931 / knn 0.066 / pop 0.003); `hybrid_weighted_tuned`
uses the weights from the Task 0.6 sweep (mf 0.048 / knn 0.952 / pop 0.0003), tuned on 1,000
validation users disjoint from this cohort, and is the blend the app now serves.
`hybrid_mf_knn` is that blend with its popularity term removed and the rest renormalized.
`implicit_als` is the implicit-feedback MF from `reports/mf_diagnostic.md` (Task 2.1); it is
evaluated offline only and **not served**. The same variants at K = 5 and 20 are in
`reports/phase4_ablation.md` ("Across K") and `reports/phase4_ablation_by_k.csv`.

**Reading the table.** Among the served models, item-kNN carries the accuracy; implicit ALS,
which is not served, beats every one of them by a wide margin. Item-kNN, the kNN-led re-tuned blend and
RRF all beat popularity and MF, and none of the three can be told apart from the others on this
cohort. Dropping the popularity term from the served blend (`hybrid_mf_knn`) changes nothing
measurable either. MF is tied with popularity and below the config-weight blend, whose popularity term
ranks the 33 cohort users MF never saw. MF's contribution is coverage (11.9× popularity), not
ranking accuracy; `reports/mf_diagnostic.md` shows why (see Limitations). Item-kNN's historical near-zero score
(NDCG 0.0017) was an evaluation defect, not a property of the model: `exclude_seen` masked the
held-out item using the model's own full-fit matrix. See `reports/phase4_evaluation.md` §8.

**What the app serves.** The *Balanced* preset serves `hybrid_weighted_tuned`; *Diversity* serves
`item_knn_sklearn`, tied with it on NDCG with higher coverage and lower Gini. The kNN artifact
scores a profile built per request from the seed titles (each counted as one liked item) or from
the profile's mean-centred ratings, with the same formula `score_all` uses offline. Seedless runs
have neither, so they rank by MF with a small popularity prior. Two limits: the offline table
scores the CF blend alone, while in the app it is one Stage-2 signal among content signals; and
the "kNN" share on cards still also contains content signals. Reasoning: `docs/decisions.md`
(2026-10-18).

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
- FunkSVD learns ratings, not choices (`reports/mf_diagnostic.md`, Task 2.1). 19% of the ratings are 0, which is Kaggle's "watched, not rated" code clipped from −1, and FunkSVD fits them as the worst possible score. It ranks a watched-but-unrated holdout at a median 9,463 of 11,200, and dropping those rows makes it worse, not better. An implicit-feedback ALS on watched / not watched scores NDCG@10 0.1890 against FunkSVD's 0.0282 (paired +0.1608, CI [+0.1408, +0.1801]), and it is also ahead on liked holdouts alone. The *For me* mode still builds its user vector from FunkSVD item factors; swapping in ALS is a candidate, not done. The protocol holds out a random *watched* item, which favours an implicit objective, so the size of that lead needs confirming on a liked-only or graded protocol first.
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
