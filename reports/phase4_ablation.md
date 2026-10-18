# Phase 4 Ablation (K=10)

One cohort: 1000 sampled users, seed 42, ranking over the full catalog.
Lifts are relative percentages against popularity, MF and item-kNN (the strongest single model).
Intervals are 95% percentile bootstrap (users resampled, 1,000 resamples, seed 42); the
`ndcg_diff` intervals are paired (same users resampled for both models), so an interval
that spans zero means the two models are not distinguishable on this cohort.
MAP lifts and every interval bound are in the CSV.

| model | users_evaluated | ndcg@10 | ndcg@10 95% CI | map@10 | map@10 95% CI | coverage@10 | gini@10 | ndcg_lift_vs_popularity_pct | ndcg_diff_vs_popularity 95% CI | ndcg_lift_vs_mf_sgd_pct | ndcg_diff_vs_mf_sgd 95% CI | ndcg_lift_vs_item_knn_sklearn_pct | ndcg_diff_vs_item_knn_sklearn 95% CI |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hybrid_weighted_tuned | 1000 | 0.0658 | [0.0535, 0.0795] | 0.0521 | [0.0404, 0.0648] | 0.1029 | 0.7601 | 89.9314 | [+0.0175, +0.0454] | 133.7347 | [+0.0275, +0.0483] | 4.1295 | [-0.0036, +0.0091] |
| item_knn_sklearn | 1000 | 0.0632 | [0.0507, 0.0775] | 0.0516 | [0.0404, 0.0649] | 0.1168 | 0.7276 | 82.3992 | [+0.0140, +0.0441] | 124.4654 | [+0.0234, +0.0485] | 0.0000 | [+0.0000, +0.0000] |
| hybrid_rrf | 1000 | 0.0547 | [0.0445, 0.0674] | 0.0419 | [0.0323, 0.0534] | 0.0782 | 0.8281 | 57.7586 | [+0.0099, +0.0308] | 94.1420 | [+0.0194, +0.0340] | -13.5091 | [-0.0180, +0.0006] |
| popularity | 1000 | 0.0347 | [0.0259, 0.0444] | 0.0255 | [0.0182, 0.0343] | 0.0056 | 0.7175 | 0.0000 | [+0.0000, +0.0000] | 23.0627 | [-0.0046, +0.0171] | -45.1752 | [-0.0441, -0.0140] |
| hybrid_weighted | 1000 | 0.0324 | [0.0237, 0.0424] | 0.0249 | [0.0166, 0.0337] | 0.0615 | 0.7993 | -6.5096 | [-0.0129, +0.0086] | 15.0518 | [+0.0020, +0.0067] | -48.7441 | [-0.0447, -0.0188] |
| mf_sgd | 1000 | 0.0282 | [0.0196, 0.0379] | 0.0224 | [0.0143, 0.0313] | 0.0667 | 0.7910 | -18.7406 | [-0.0171, +0.0046] | 0.0000 | [+0.0000, +0.0000] | -55.4497 | [-0.0485, -0.0234] |
| content_tfidf | 1000 | 0.0211 | [0.0138, 0.0288] | 0.0166 | [0.0099, 0.0240] | 0.1711 | 0.6334 | -39.0604 | [-0.0260, -0.0014] | -25.0060 | [-0.0185, +0.0048] | -66.5900 | [-0.0566, -0.0289] |
| content_embeddings | 1000 | 0.0101 | [0.0059, 0.0154] | 0.0069 | [0.0036, 0.0114] | 0.0588 | 0.8620 | -70.7366 | [-0.0352, -0.0148] | -63.9877 | [-0.0288, -0.0086] | -83.9564 | [-0.0681, -0.0396] |
