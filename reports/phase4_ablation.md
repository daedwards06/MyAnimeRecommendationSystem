# Phase 4 Ablation (K=10)

One cohort: 1000 sampled users, seed 42, ranking over the full catalog.
Lifts are relative percentages against the popularity baseline and against MF.

| model | users_evaluated | ndcg@10 | map@10 | coverage@10 | gini@10 | ndcg_lift_vs_popularity_pct | map_lift_vs_popularity_pct | ndcg_lift_vs_mf_sgd_pct | map_lift_vs_mf_sgd_pct |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| item_knn_sklearn | 1000 | 0.0628 | 0.0513 | 0.1160 | 0.7280 | 81.1219 | 101.4836 | 92.5918 | 92.6911 |
| hybrid_rrf | 1000 | 0.0586 | 0.0456 | 0.0784 | 0.8253 | 69.1005 | 78.8945 | 79.8091 | 71.0877 |
| popularity | 1000 | 0.0347 | 0.0255 | 0.0056 | 0.7175 | 0.0000 | 0.0000 | 6.3327 | -4.3639 |
| mf_sgd | 1000 | 0.0326 | 0.0266 | 0.0668 | 0.7875 | -5.9556 | 4.5630 | 0.0000 | 0.0000 |
| hybrid_weighted | 1000 | 0.0324 | 0.0249 | 0.0615 | 0.7993 | -6.5096 | -2.3361 | -0.5892 | -6.5980 |
| content_tfidf | 1000 | 0.0211 | 0.0166 | 0.1711 | 0.6334 | -39.0604 | -34.6762 | -35.2012 | -37.5268 |
| content_embeddings | 1000 | 0.0101 | 0.0069 | 0.0588 | 0.8620 | -70.7366 | -72.9148 | -68.8834 | -74.0968 |
