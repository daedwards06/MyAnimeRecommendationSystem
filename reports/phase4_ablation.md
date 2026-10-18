# Phase 4 Ablation (K=10)

One cohort: 1000 sampled users, seed 42, ranking over the full catalog.
Lifts are relative percentages against popularity, MF and item-kNN (the strongest single model).
Intervals are 95% percentile bootstrap (users resampled, 1,000 resamples, seed 42); the
`ndcg_diff` intervals are paired (same users resampled for both models), so an interval
that spans zero means the two models are not distinguishable on this cohort.
MAP lifts and every interval bound are in the CSV.

| model | users_evaluated | ndcg@10 | ndcg@10 95% CI | map@10 | map@10 95% CI | coverage@10 | gini@10 | ndcg_lift_vs_popularity_pct | ndcg_diff_vs_popularity 95% CI | ndcg_lift_vs_mf_sgd_pct | ndcg_diff_vs_mf_sgd 95% CI | ndcg_lift_vs_item_knn_sklearn_pct | ndcg_diff_vs_item_knn_sklearn 95% CI |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hybrid_weighted_tuned | 1000 | 0.0658 | [0.0535, 0.0795] | 0.0521 | [0.0404, 0.0648] | 0.1029 | 0.7596 | 89.9314 | [+0.0175, +0.0454] | 101.9592 | [+0.0222, +0.0448] | 4.8638 | [-0.0033, +0.0097] |
| item_knn_sklearn | 1000 | 0.0628 | [0.0503, 0.0767] | 0.0513 | [0.0399, 0.0646] | 0.1160 | 0.7280 | 81.1219 | [+0.0134, +0.0438] | 92.5918 | [+0.0173, +0.0441] | 0.0000 | [+0.0000, +0.0000] |
| hybrid_rrf | 1000 | 0.0586 | [0.0475, 0.0713] | 0.0456 | [0.0354, 0.0571] | 0.0784 | 0.8253 | 69.1005 | [+0.0132, +0.0358] | 79.8091 | [+0.0189, +0.0335] | -6.6372 | [-0.0141, +0.0056] |
| popularity | 1000 | 0.0347 | [0.0259, 0.0444] | 0.0255 | [0.0182, 0.0343] | 0.0056 | 0.7175 | 0.0000 | [+0.0000, +0.0000] | 6.3327 | [-0.0102, +0.0139] | -44.7886 | [-0.0438, -0.0134] |
| mf_sgd | 1000 | 0.0326 | [0.0229, 0.0428] | 0.0266 | [0.0176, 0.0359] | 0.0668 | 0.7875 | -5.9556 | [-0.0139, +0.0102] | 0.0000 | [+0.0000, +0.0000] | -48.0767 | [-0.0441, -0.0173] |
| hybrid_weighted | 1000 | 0.0324 | [0.0237, 0.0424] | 0.0249 | [0.0166, 0.0337] | 0.0615 | 0.7993 | -6.5096 | [-0.0129, +0.0086] | -0.5892 | [-0.0053, +0.0041] | -48.3826 | [-0.0439, -0.0183] |
| content_tfidf | 1000 | 0.0211 | [0.0138, 0.0288] | 0.0166 | [0.0099, 0.0240] | 0.1711 | 0.6334 | -39.0604 | [-0.0260, -0.0014] | -35.2012 | [-0.0235, +0.0013] | -66.3544 | [-0.0563, -0.0284] |
| content_embeddings | 1000 | 0.0101 | [0.0059, 0.0154] | 0.0069 | [0.0036, 0.0114] | 0.0588 | 0.8620 | -70.7366 | [-0.0352, -0.0148] | -68.8834 | [-0.0333, -0.0115] | -83.8432 | [-0.0675, -0.0390] |
