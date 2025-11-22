PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> # Generate sample recommendations + popularity counts
PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> python scripts/generate_recommendations_sample.py --k 10 --sample-users 500
[ok] Wrote data\processed\recommendations_sample.parquet and data\processed\popularity.parquet (users=500, k=10)

PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> # Genre exposure (hybrid model)
PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> python scripts/genre_exposure_scan.py --recommendations data/processed/recommendations_sample.parquet --items data/processed/anime_metadata_normalized.parquet --model hybrid
Traceback (most recent call last):
  File "C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\genre_exposure_scan.py", line 85, in <module>
    main(p.parse_args())
  File "C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\genre_exposure_scan.py", line 73, in main
    result = compute_distributions(items, recs, args.model)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\genre_exposure_scan.py", line 36, in compute_distributions
    catalog_genres = _explode_genres(items).value_counts(normalize=True)
                     ^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\genre_exposure_scan.py", line 31, in _explode_genres
    df[col] = df[col].apply(_split)
              ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\dedwa\Anaconda3\Lib\site-packages\pandas\core\series.py", line 4924, in apply
    ).apply()
      ^^^^^^^
  File "C:\Users\dedwa\Anaconda3\Lib\site-packages\pandas\core\apply.py", line 1427, in apply
    return self.apply_standard()
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\dedwa\Anaconda3\Lib\site-packages\pandas\core\apply.py", line 1507, in apply_standard
    mapped = obj._map_values(
             ^^^^^^^^^^^^^^^^
  File "C:\Users\dedwa\Anaconda3\Lib\site-packages\pandas\core\base.py", line 921, in _map_values
    return algorithms.map_array(arr, mapper, na_action=na_action, convert=convert)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\dedwa\Anaconda3\Lib\site-packages\pandas\core\algorithms.py", line 1743, in map_array
    return lib.map_infer(values, mapper, convert=convert)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "lib.pyx", line 2972, in pandas._libs.lib.map_infer
  File "C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\genre_exposure_scan.py", line 27, in _split
    if pd.isna(x):
       ^^^^^^^^^^
ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()

PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> # Novelty / popularity bias
PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> python scripts/novelty_bias_plot.py --recommendations data/processed/recommendations_sample.parquet --popularity data/processed/popularity.parquet
C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem\scripts\novelty_bias_plot.py:38: FutureWarning: 

Passing `palette` without assigning `hue` is deprecated and will be removed in v0.14.0. Assign the `x` variable to `hue` and set `legend=False` for the same effect.

  sns.barplot(data=df, x="model", y="avg_pop_percentile", palette="colorblind")
[ok] Saved novelty artifacts: reports\artifacts\novelty_bias.json, reports\figures\phase4\novelty_bias.png

PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> # Alternate hybrid explanations (diversity-emphasized weights)
PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> python scripts/explain_hybrid_examples.py --k 10 --sample-users 500 --w-mf 0.7 --w-knn 0.2 --w-pop 0.1 --max-users 3 --out-suffix alt
{
  "14593": {
    "top": [
      199,
      1,
      4224,
      245,
      23273,
      431,
      6746,
      9756,
      2251,
      7311
    ],
    "contributions": {
      "199": {
        "mf": 5.904213237762451,
        "knn": 0.06298515777822519,
        "pop": 7.577786244936957,
        "mf_share": 0.4358966358749782,
        "knn_share": 0.004650072292441091,
        "pop_share": 0.5594532918325807,
        "total": 13.544984640477633
      },
      "1": {
        "mf": 6.07420711517334,
        "knn": 0.059471682015159344,
        "pop": 7.403129691545189,
        "mf_share": 0.44871781411613637,
        "knn_share": 0.004393331121191231,
        "pop_share": 0.5468888547626725,
        "total": 13.536808488733687
      },
      "4224": {
        "mf": 5.840753841400146,
        "knn": 0.061358127805257234,
        "pop": 7.436742699004222,
        "mf_share": 0.4378752139282515,
        "knn_share": 0.004599954743602651,
        "pop_share": 0.5575248313281458,
        "total": 13.338854668209626
      },
      "245": {
        "mf": 6.05099630355835,
        "knn": 0.04027975291204815,
        "pop": 7.0868828765674285,
        "mf_share": 0.4591685632496371,
        "knn_share": 0.0030565538871341314,
        "pop_share": 0.5377748828632287,
        "total": 13.178158933037826
      },
      "23273": {
        "mf": 5.950528049468994,
        "knn": 0.028969757425327425,
        "pop": 7.1857055125452725,
        "mf_share": 0.4519890733994597,
        "knn_share": 0.0022004793030845943,
        "pop_share": 0.5458104472974556,
        "total": 13.165203319439595
      }
    }
  },
  "3279": {
    "top": [
      1535,
      11061,
      2001,
      9989,
      32281,
      22535,
      918,
      431,
      28223,
      1
    ],
    "contributions": {
      "1535": {
        "mf": 5.54108543395996,
        "knn": 0.04373138063587595,
        "pop": 8.090401914027177,
        "mf_share": 0.4051917226275988,
        "knn_share": 0.003197856027292907,
        "pop_share": 0.5916104213451083,
        "total": 13.675218728623014
      },
      "11061": {
        "mf": 6.038801765441894,
        "knn": 0.07080675610628827,
        "pop": 7.282394442209192,
        "mf_share": 0.45092595796048096,
        "knn_share": 0.005287241669368786,
        "pop_share": 0.5437868003701503,
        "total": 13.392002963757374
      },
      "2001": {
        "mf": 5.549841976165771,
        "knn": 0.03731209421927866,
        "pop": 7.710834523585195,
        "mf_share": 0.4173444680710777,
        "knn_share": 0.0028058449558452186,
        "pop_share": 0.5798496869730769,
        "total": 13.297988593970246
      },
      "9989": {
        "mf": 5.773954582214355,
        "knn": 0.060259000572218974,
        "pop": 7.384402823247497,
        "mf_share": 0.4368047611683961,
        "knn_share": 0.004558646587604416,
        "pop_share": 0.5586365922439995,
        "total": 13.218616406034071
      },
      "32281": {
        "mf": 6.636001682281494,
        "knn": 0.05400855526794867,
        "pop": 6.465067776442638,
        "mf_share": 0.5044441146774858,
        "knn_share": 0.004105529074818392,
        "pop_share": 0.49145035624769573,
        "total": 13.15507801399208
      }
    }
  },
  "36049": {
    "top": [
      5114,
      2001,
      11061,
      30276,
      16498,
      199,
      1,
      23273,
      9989,
      4224
    ],
    "contributions": {
      "5114": {
        "mf": 6.761677455902099,
        "knn": 0.06094172313092327,
        "pop": 8.225799743124243,
        "mf_share": 0.4493280982460036,
        "knn_share": 0.0040497093712079475,
        "pop_share": 0.5466221923827885,
        "total": 15.048418922157264
      },
      "2001": {
        "mf": 6.468481159210205,
        "knn": 0.05229429598100932,
        "pop": 7.710834523585195,
        "mf_share": 0.45451506673220016,
        "knn_share": 0.0036745172232091642,
        "pop_share": 0.5418104160445908,
        "total": 14.231609978776408
      },
      "11061": {
        "mf": 6.775040245056152,
        "knn": 0.0557992252999048,
        "pop": 7.282394442209192,
        "mf_share": 0.4800487462355612,
        "knn_share": 0.0039536810376412605,
        "pop_share": 0.5159975727267975,
        "total": 14.11323391256525
      },
      "30276": {
        "mf": 6.723786067962646,
        "knn": 0.06884910707769094,
        "pop": 7.181591844041084,
        "mf_share": 0.4811562069788548,
        "knn_share": 0.004926863359503133,
        "pop_share": 0.513916929661642,
        "total": 13.974227019081422
      },
      "16498": {
        "mf": 6.254130458831787,
        "knn": 0.058423051201818,
        "pop": 7.655709506432212,
        "mf_share": 0.44773859508941133,
        "knn_share": 0.004182556638069372,
        "pop_share": 0.5480788482725194,
        "total": 13.968263016465816
      }
    }
  }
}
explain_hybrid_examples.py: error: unrecognized arguments: --out-suffix alt