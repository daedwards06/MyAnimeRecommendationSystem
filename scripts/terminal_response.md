dedwa@DESKTOP-7NHEL71 MINGW64 ~/OneDrive/Desktop/Dromund_Kass/MARS/MyAnimeRecommendationSystem (main)
$ python scripts/evaluate_content_only.py --k 10 --sample-users 300
C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\evaluate_content_only.py:35: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  .apply(lambda g: g.sample(1, random_state=rng.randint(0, 1_000_000)))
{
  "tfidf": {
    "model": "content_tfidf",
    "k": 10,
    "users_evaluated": 300,
    "ndcg@k_mean": 0.025275788507117,
    "map@k_mean": 0.02073148148148148
  },
  "embeddings": {
    "model": "content_embeddings",
    "k": 10,
    "users_evaluated": 300,
    "ndcg@k_mean": 0.01557912184138652,
    "map@k_mean": 0.013166666666666667
  }
}
(.venv)

dedwa@DESKTOP-7NHEL71 MINGW64 ~/OneDrive/Desktop/Dromund_Kass/MARS/MyAnimeRecommendationSystem (main)
$ python scripts/sweep_hybrid_weights.py --k 10 --grid-mf 0.5,0.6,0.7 --grid-knn 0.2,0.3,0.4 --grid-pop 0.1,0.2
C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\sweep_hybrid_weights.py:39: FutureWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  .apply(lambda g: g.sample(1, random_state=rng.randint(0, 1_000_000)))
{
  "best": {
    "w_mf": 0.5555555555555556,
    "w_knn": 0.22222222222222227,
    "w_pop": 0.22222222222222227,
    "k": 10.0,
    "users": 300.0,
    "ndcg@k": 0.02851177382448431,
    "map@k": 0.016312169312169313
  },
  "file": "experiments\\metrics\\hybrid_weight_sweep_20251115191145.csv"
}
(.venv)
dedwa@DESKTOP-7NHEL71 MINGW64 ~/OneDrive/Desktop/Dromund_Kass/MARS/MyAnimeRecommendationSystem (main)

$ python scripts/update_phase3_report.py
Updated report with latest metrics table.
(.venv)
