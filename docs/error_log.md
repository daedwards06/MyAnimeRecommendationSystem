PS C:\Users\dedwa\OneDrive\Desktop\Dromund_Kass\MARS\MyAnimeRecommendationSystem> python -m pytest -q

================================================= ERRORS =================================================
_______________________ ERROR collecting scripts/test_personalized_integration.py ________________________ 
scripts\test_personalized_integration.py:80: in <module>
    seed_recs = recommender.get_top_n_for_user(
src\app\recommender.py:119: in get_top_n_for_user
    scores = scores.copy()
E   AttributeError: 'float' object has no attribute 'copy'
-------------------------------------------- Captured stdout --------------------------------------------- 
============================================================
PERSONALIZED INTEGRATION TEST
============================================================

1. Loading artifacts...
✓ Loaded metadata: 13037 anime
✓ Loaded 8 models

2. Loading user profile...
✓ Profile: Relentless649
  - Ratings: 106
  - Watched: 106
  - Avg rating: 9.17/10

3. Generating user embedding...
✓ Generated embedding: shape=(64,), norm=1.0000

4. Initializing HybridRecommender...
✓ HybridRecommender initialized

5. Getting seed-based recommendations...
____________________________ ERROR collecting scripts/test_quality_filter.py _____________________________ 
scripts\test_quality_filter.py:56: in <module>
    print(f'Pass filter: {action_passed} ({action_passed/len(action)*100:.1f}%)')
E   ZeroDivisionError: division by zero
-------------------------------------------- Captured stdout --------------------------------------------- 
Tokyo Ghoul: anime_id                                       22319
title_display                            Tokyo Ghoul
genres           [Action, Fantasy, Horror, Suspense]
Name: 9403, dtype: object

Genres: ['Action' 'Fantasy' 'Horror' 'Suspense']

================================================================================
FILTER IMPACT ANALYSIS
================================================================================

Total anime: 13037
Pass filter: 12823 (98.4%)
Filtered out: 214 (1.6%)

--------------------------------------------------------------------------------
FILTERED OUT BY REASON:
--------------------------------------------------------------------------------
Too few members (<200): 129
Low MAL score (<4.0): 84
Too obscure (>20k rank): 474
Missing synopsis: 402

--------------------------------------------------------------------------------
ACTION GENRE ANALYSIS (similar to Tokyo Ghoul):
--------------------------------------------------------------------------------
Total Action anime: 0
======================================== short test summary info =========================================--------------------------------------------------------------------------------
Total Action anime: 0
======================================== short test summary info =========================================                          
ERROR scripts/test_personalized_integration.py - AttributeError: 'float' object has no attribute 'copy'
ERROR scripts/test_quality_filter.py - ZeroDivisionError: division by zero
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
2 errors in 53.52s