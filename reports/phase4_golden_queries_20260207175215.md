# Phase 4 — Golden Queries Report

Generated: 2026-02-07T17:57:22.526656+00:00
Weight mode: Balanced
Golden file: data/samples/golden_queries_phase4.json

---

## tokyo_ghoul

Seeds (requested): Tokyo Ghoul
Seeds (resolved): Tokyo Ghoul
Seed IDs: [22319]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Tokyo Ghoul | exact | 22319 | Tokyo Ghoul |  |
Notes: Failure case: avoid recap/special/short content surfacing in top-N.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2549, stage0_after_hygiene=2437, stage0_after_cap=2437, stage0_src_raw(neural/meta_strict/pop)=1500/1223/100, stage1_universe=2437, universe_match=True, shortlist=600/600, scored=552, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=35.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.923, content_first_alpha=0.70, content_first_active(top20/top50/all)=18/42/109, avg_neural_sim_top20=0.4360, avg_hybrid_val_top20=0.2856, sem_top50_mean=0.484, sem_top50_p95=0.550, sem_top50_overlap_mean=0.510, sem_top50_any_match=0.98, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.398/0.429/0.577, forced_in_top20/top50=20/39, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=5/5, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=150, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=313, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[seinen], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=589, blocked_low_sim=300, bonus_fired=3, bonus_mean=0.00745, bonus_max=0.07015, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=7/19, theme_bonus_mean(top20/top50)=0.00050/0.00059, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=17, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=9, top50_moved_meta=21, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1165 | 47.8% |
| blocked_low_semantic_sim | 9 | 0.4% |
| blocked_low_overlap | 286 | 11.7% |
| blocked_other_admission | 425 | 17.4% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 552 | 22.7% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 30458 | Tokyo Ghoul: Jack | overlap | 1.00 | 0.563 |
| 54918 | Tokyo Revengers: Tenjiku Arc | overlap | 0.50 | 0.421 |
| 50608 | Tokyo Revengers: Christmas Showdown | overlap | 0.50 | 0.411 |
| 27899 | Tokyo Ghoul √A | overlap | 1.00 | 0.490 |
| 42249 | Tokyo Revengers | overlap | 0.50 | 0.355 |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 25 | 2356 | Amon: Apocalypse of Devilman | 0.667 | 0.00200 |
| 38 | 22535 | Parasyte: The Maxim | 0.667 | 0.00200 |
| 32 | 27899 | Tokyo Ghoul √A | 1.000 | 0.00200 |
| 2 | 30458 | Tokyo Ghoul: Jack | 1.000 | 0.00200 |
| 49 | 41006 | Higurashi: When They Cry – Gou | 0.667 | 0.00200 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 30458 | Tokyo Ghoul: Jack | OVA | 7.29 |  |  |
| 3 | 49413 | Link Click Season 2 |  | 8.64 |  |  |
| 4 | 46102 | Odd Taxi |  | 8.63 |  |  |
| 5 | 50330 | Bungo Stray Dogs 4 |  | 8.42 |  |  |
| 6 | 51009 | Jujutsu Kaisen Season 2 |  | 8.72 |  |  |
| 7 | 41467 | Bleach: Thousand-Year Blood War |  | 8.99 |  |  |
| 8 | 53998 | Bleach: Thousand-Year Blood War - The Separation |  | 8.70 |  |  |
| 9 | 52588 | Kaiju No. 8 |  | 8.25 |  |  |
| 10 | 41461 | Date A Live IV |  | 7.74 |  |  |
| 11 | 39575 | Somali and the Forest Spirit |  | 7.81 |  |  |
| 12 | 61026 | My Status as an Assassin Obviously Exceeds the Hero's |  | 7.11 |  |  |
| 13 | 51367 | JoJo's Bizarre Adventure: Stone Ocean Part 2 |  | 8.04 |  |  |
| 14 | 50709 | Lycoris Recoil |  | 8.15 |  |  |
| 15 | 52578 | The Dangers in My Heart |  | 8.22 |  |  |
| 16 | 43690 | High-Rise Invasion |  | 6.68 |  |  |
| 17 | 50613 | Rurouni Kenshin |  | 7.63 |  |  |
| 18 | 54918 | Tokyo Revengers: Tenjiku Arc |  | 7.82 |  |  |
| 19 | 32843 | Symphogear XV | TV | 8.19 |  |  |
| 20 | 37451 | Boogiepop and Others |  | 7.06 |  |  |

---

## attack_on_titan

Seeds (requested): Attack on Titan
Seeds (resolved): Attack on Titan
Seed IDs: [16498]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Attack on Titan | exact | 16498 | Attack on Titan |  |
Notes: Should mostly surface TV seasons/movies, not recap specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2058, stage0_after_hygiene=2000, stage0_after_cap=2000, stage0_src_raw(neural/meta_strict/pop)=1500/661/100, stage1_universe=2000, universe_match=True, shortlist=600/600, scored=462, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=45.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.828, content_first_alpha=0.70, content_first_active(top20/top50/all)=16/29/56, avg_neural_sim_top20=0.3984, avg_hybrid_val_top20=0.6963, sem_top50_mean=0.432, sem_top50_p95=0.520, sem_top50_overlap_mean=0.355, sem_top50_any_match=0.84, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.307/0.354/0.611, forced_in_top20/top50=19/47, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=4/4, top50_franchise_like(before/after)=5/5, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=145, top20_off_type=2, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=112, demo_override_top20=1, blocked_overlap=289, blocked_low_sim=501, bonus_fired=5, bonus_mean=0.01299, bonus_max=0.07680, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=6/16, theme_bonus_mean(top20/top50)=0.00057/0.00053, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=3, top50_moved_meta=23, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 820 | 41.0% |
| blocked_low_semantic_sim | 145 | 7.2% |
| blocked_low_overlap | 111 | 5.5% |
| blocked_other_admission | 462 | 23.1% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 462 | 23.1% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 25777 | Attack on Titan Season 2 | overlap | 1.00 | 0.611 |
| 35760 | Attack on Titan Season 3 | overlap | 1.00 | 0.505 |
| 48583 | Attack on Titan: Final Season Part 2 | overlap | 1.00 | 0.301 |
| 38524 | Attack on Titan Season 3 Part 2 | overlap | 1.00 | 0.380 |
| 40028 | Attack on Titan: Final Season | overlap | 1.00 | 0.291 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 25777 | Attack on Titan Season 2 | TV | 8.53 |  |  |
| 2 | 35760 | Attack on Titan Season 3 |  | 8.64 |  |  |
| 3 | 55255 | Alien Stage |  | 8.69 |  |  |
| 4 | 33502 | WorldEnd: What do you do at the end of the world? Are you busy? Will you save us? | TV | 7.67 |  |  |
| 5 | 31339 | Drifters | TV | 7.88 |  |  |
| 6 | 53393 | Heavenly Delusion |  | 8.21 |  |  |
| 7 | 53770 | Go! Go! Loser Ranger! |  | 7.31 |  |  |
| 8 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 9 | 39575 | Somali and the Forest Spirit |  | 7.81 |  |  |
| 10 | 52299 | Solo Leveling |  | 8.22 |  |  |
| 11 | 59205 | Clevatess |  | 7.85 |  |  |
| 12 | 40060 | BNA: Brand New Animal |  | 7.34 |  |  |
| 13 | 32843 | Symphogear XV | TV | 8.19 |  |  |
| 14 | 48583 | Attack on Titan: Final Season Part 2 |  | 8.77 |  |  |
| 15 | 22535 | Parasyte: The Maxim | TV | 8.32 |  |  |
| 16 | 39195 | Beastars |  | 7.79 |  |  |
| 17 | 38524 | Attack on Titan Season 3 Part 2 |  | 9.05 |  |  |
| 18 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 19 | 50175 | I'm Quitting Heroing |  | 7.00 |  |  |
| 20 | 30736 | Rage of Bahamut: Virgin Soul | TV | 7.42 |  |  |

---

## death_note

Seeds (requested): Death Note
Seeds (resolved): Death Note
Seed IDs: [1535]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Death Note | exact | 1535 | Death Note |  |
Notes: Sanity: similar psychological/thriller TV shows.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2456, stage0_after_hygiene=2294, stage0_after_cap=2294, stage0_src_raw(neural/meta_strict/pop)=1500/1290/100, stage1_universe=2294, universe_match=True, shortlist=600/600, scored=563, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=70.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.906, content_first_alpha=0.70, content_first_active(top20/top50/all)=17/37/127, avg_neural_sim_top20=0.4513, avg_hybrid_val_top20=0.1525, sem_top50_mean=0.488, sem_top50_p95=0.546, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.66, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.417/0.703, forced_in_top20/top50=17/37, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=3/3, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.703/0.703/0.703, high_sim_override_sim_min/mean/max(all)=0.703/0.703/0.703, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=122, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=129, demo_override_top20=1, blocked_overlap=470, blocked_low_sim=212, bonus_fired=1, bonus_mean=0.00032, bonus_max=0.00640, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=1/7, theme_bonus_mean(top20/top50)=0.00010/0.00028, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=16, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=11, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Stage 0 audit:

| seed title | stage0_after_cap | % neural | % meta_strict | % popularity |
|---|---:|---:|---:|---:|
| Death Note | 2294 | 63.3% | 50.8% | 4.3% |

Stage 0 details:

| metric | value |
|---|---:|
| stage0_pool_raw | 2456 |
| stage0_after_hygiene | 2294 |
| stage0_after_cap | 2294 |
| stage0_src_raw(neural/meta_strict/pop) | 1500/1290/100 |
| stage0_src_after_cap(neural/meta_strict/pop) | 1451/1166/99 |
| stage1_candidate_universe_count | 2294 |
| stage0_stage1_universe_match | True |
| final_scored_candidate_count | 563 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 50 |

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 790 | 34.4% |
| blocked_low_semantic_sim | 30 | 1.3% |
| blocked_low_overlap | 372 | 16.2% |
| blocked_other_admission | 539 | 23.5% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 563 | 24.5% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 2994 | Death Note: Relight | overlap | 1.00 | 0.703 |
| 53613 | Dead Mount Death Play | overlap | 0.50 | 0.554 |
| 28223 | Death Parade | overlap | 0.50 | 0.475 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |
| 2 | 53613 | Dead Mount Death Play |  | 7.26 |  |  |
| 3 | 47194 | Summer Time Rendering |  | 8.47 |  |  |
| 4 | 38759 | The Helpful Fox Senko-san |  | 7.31 |  |  |
| 5 | 49709 | To Your Eternity Season 2 |  | 8.11 |  |  |
| 6 | 46569 | Hell's Paradise |  | 8.09 |  |  |
| 7 | 53998 | Bleach: Thousand-Year Blood War - The Separation |  | 8.70 |  |  |
| 8 | 32937 | KonoSuba: God's Blessing on This Wonderful World! 2 | TV | 8.24 |  |  |
| 9 | 56784 | Bleach: Thousand-Year Blood War - The Conflict |  | 8.67 |  |  |
| 10 | 6547 | Angel Beats! | TV | 8.05 |  |  |
| 11 | 33253 | Ajin: Demi-Human 2nd Season | TV | 7.55 |  |  |
| 12 | 40748 | Jujutsu Kaisen |  | 8.53 |  |  |
| 13 | 49413 | Link Click Season 2 |  | 8.64 |  |  |
| 14 | 44942 | Record of Ragnarok |  | 6.81 |  |  |
| 15 | 48413 | The Devil is a Part-Timer! Season 2 |  | 6.65 |  |  |
| 16 | 47790 | The World's Finest Assassin Gets Reincarnated in Another World as an Aristocrat |  | 7.32 |  |  |
| 17 | 37520 | Dororo |  | 8.26 |  |  |
| 18 | 46102 | Odd Taxi |  | 8.63 |  |  |
| 19 | 50346 | Call of the Night |  | 7.95 |  |  |
| 20 | 392 | Yu Yu Hakusho: Ghost Files | TV | 8.46 |  |  |

---

## steins_gate

Seeds (requested): Steins;Gate
Seeds (resolved): Steins;Gate
Seed IDs: [9253]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Steins;Gate | exact | 9253 | Steins;Gate |  |
Notes: Sanity: time-travel sci-fi; avoid short specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2277, stage0_after_hygiene=2119, stage0_after_cap=2119, stage0_src_raw(neural/meta_strict/pop)=1500/830/100, stage1_universe=2119, universe_match=True, shortlist=600/600, scored=449, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=35.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.794, content_first_alpha=0.70, content_first_active(top20/top50/all)=14/25/48, avg_neural_sim_top20=0.3917, avg_hybrid_val_top20=0.3507, sem_top50_mean=0.410, sem_top50_p95=0.514, sem_top50_overlap_mean=0.693, sem_top50_any_match=1.00, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.321/0.353/0.683, forced_in_top20/top50=19/47, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=3/3, top50_franchise_like(before/after)=3/3, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.612/0.612/0.612, high_sim_override_sim_min/mean/max(all)=0.612/0.612/0.612, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=146, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=674, blocked_low_sim=335, bonus_fired=3, bonus_mean=0.00107, bonus_max=0.00954, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/10, theme_bonus_mean(top20/top50)=0.00050/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Stage 0 audit:

| seed title | stage0_after_cap | % neural | % meta_strict | % popularity |
|---|---:|---:|---:|---:|
| Steins;Gate | 2119 | 65.5% | 36.8% | 4.7% |

Stage 0 details:

| metric | value |
|---|---:|
| stage0_pool_raw | 2277 |
| stage0_after_hygiene | 2119 |
| stage0_after_cap | 2119 |
| stage0_src_raw(neural/meta_strict/pop) | 1500/830/100 |
| stage0_src_after_cap(neural/meta_strict/pop) | 1388/780/99 |
| stage1_candidate_universe_count | 2119 |
| stage0_stage1_universe_match | True |
| final_scored_candidate_count | 449 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 50 |

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 724 | 34.2% |
| blocked_low_semantic_sim | 49 | 2.3% |
| blocked_low_overlap | 339 | 16.0% |
| blocked_other_admission | 558 | 26.3% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 449 | 21.2% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 30484 | Steins;Gate 0 | overlap | 1.00 | 0.683 |
| 32188 | Steins;Gate: Open the Missing Link - Divide By Zero | overlap | 1.00 | 0.612 |
| 27957 | Steins;Gate: The Sagacious Wisdom of Cognitive Computing | overlap | 1.00 | 0.564 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30484 | Steins;Gate 0 | TV | 8.55 |  |  |
| 2 | 32188 | Steins;Gate: Open the Missing Link - Divide By Zero | TV Special | 8.26 |  |  |
| 3 | 27957 | Steins;Gate: The Sagacious Wisdom of Cognitive Computing | ONA | 7.44 |  |  |
| 4 | 46102 | Odd Taxi |  | 8.63 |  |  |
| 5 | 57433 | Rascal Does Not Dream of Santa Claus |  | 8.18 |  |  |
| 6 | 37491 | Gintama. Silver Soul Arc - Second Half War |  | 8.88 |  |  |
| 7 | 38080 | Kono Oto Tomare!: Sounds of Life |  | 7.94 |  |  |
| 8 | 43299 | Wonder Egg Priority |  | 7.55 |  |  |
| 9 | 38691 | Dr. Stone |  | 8.26 |  |  |
| 10 | 53407 | Bartender Glass of God |  | 7.38 |  |  |
| 11 | 13125 | From the New World | TV | 8.25 |  |  |
| 12 | 43470 | Science Fell in Love, So I Tried to Prove It r=1-sinθ |  | 7.30 |  |  |
| 13 | 39783 | The Quintessential Quintuplets 2 |  | 8.01 |  |  |
| 14 | 339 | Serial Experiments Lain | TV | 8.10 |  |  |
| 15 | 42670 | Princess Connect! Re:Dive Season 2 |  | 7.73 |  |  |
| 16 | 51009 | Jujutsu Kaisen Season 2 |  | 8.72 |  |  |
| 17 | 32962 | Occultic;Nine | TV | 6.89 |  |  |
| 18 | 59226 | Blue Exorcist: The Blue Night Saga |  | 8.00 |  |  |
| 19 | 329 | Planetes | TV | 8.24 |  |  |
| 20 | 48549 | Dr. Stone: New World |  | 8.15 |  |  |

---

## cowboy_bebop

Seeds (requested): Cowboy Bebop
Seeds (resolved): Cowboy Bebop
Seed IDs: [1]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Cowboy Bebop | exact | 1 | Cowboy Bebop |  |
Notes: Sanity: classic sci-fi/action; avoid music videos/specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2505, stage0_after_hygiene=2337, stage0_after_cap=2337, stage0_src_raw(neural/meta_strict/pop)=1500/1435/100, stage1_universe=2337, universe_match=True, shortlist=600/600, scored=457, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=75.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.793, content_first_alpha=0.70, content_first_active(top20/top50/all)=11/15/34, avg_neural_sim_top20=0.3832, avg_hybrid_val_top20=0.7862, sem_top50_mean=0.423, sem_top50_p95=0.499, sem_top50_overlap_mean=0.673, sem_top50_any_match=1.00, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.311/0.355/0.522, forced_in_top20/top50=19/41, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=0/0, top50_franchise_like(before/after)=0/0, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=172, top20_off_type=0, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=95, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=400, blocked_low_sim=645, bonus_fired=1, bonus_mean=0.00028, bonus_max=0.00550, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=10/22, theme_bonus_mean(top20/top50)=0.00100/0.00088, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=13, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Stage 0 audit:

| seed title | stage0_after_cap | % neural | % meta_strict | % popularity |
|---|---:|---:|---:|---:|
| Cowboy Bebop | 2337 | 61.5% | 56.0% | 4.2% |

Stage 0 details:

| metric | value |
|---|---:|
| stage0_pool_raw | 2505 |
| stage0_after_hygiene | 2337 |
| stage0_after_cap | 2337 |
| stage0_src_raw(neural/meta_strict/pop) | 1500/1435/100 |
| stage0_src_after_cap(neural/meta_strict/pop) | 1438/1309/99 |
| stage1_candidate_universe_count | 2337 |
| stage0_stage1_universe_match | True |
| final_scored_candidate_count | 457 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 50 |

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1178 | 50.4% |
| blocked_low_semantic_sim | 193 | 8.3% |
| blocked_low_overlap | 90 | 3.9% |
| blocked_other_admission | 419 | 17.9% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 457 | 19.6% |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 41433 | Akudama Drive |  | 7.57 |  |  |
| 2 | 52093 | Trigun Stampede |  | 7.83 |  |  |
| 3 | 39198 | Astra Lost in Space |  | 8.07 |  |  |
| 4 | 52299 | Solo Leveling |  | 8.22 |  |  |
| 5 | 28673 | Die Now | ONA | 6.37 |  |  |
| 6 | 5074 | Birdy the Mighty: Decode 02 | TV | 7.70 |  |  |
| 7 | 43325 | Moriarty the Patriot Part 2 |  | 8.29 |  |  |
| 8 | 37991 | JoJo's Bizarre Adventure: Golden Wind |  | 8.58 |  |  |
| 9 | 6 | Trigun | TV | 8.22 |  |  |
| 10 | 11405 | Skyers 5 | TV | 5.92 |  |  |
| 11 | 2904 | Code Geass: Lelouch of the Rebellion R2 | TV | 8.91 |  |  |
| 12 | 40052 | Great Pretender |  | 8.19 |  |  |
| 13 | 59205 | Clevatess |  | 7.85 |  |  |
| 14 | 50608 | Tokyo Revengers: Christmas Showdown |  | 7.62 |  |  |
| 15 | 22997 | Shin Skyers 5 | TV |  |  |  |
| 16 | 32843 | Symphogear XV | TV | 8.19 |  |  |
| 17 | 467 | Ghost in the Shell: Stand Alone Complex | TV | 8.42 |  |  |
| 18 | 235 | Case Closed | TV | 8.18 |  |  |
| 19 | 2158 | Toward the Terra (TV) | TV | 7.85 |  |  |
| 20 | 1000 | Space Pirate Captain Harlock | TV | 7.68 |  |  |

---

## fmab

Seeds (requested): Fullmetal Alchemist: Brotherhood
Seeds (resolved): Fullmetal Alchemist: Brotherhood
Seed IDs: [5114]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Fullmetal Alchemist: Brotherhood | exact | 5114 | Fullmetal Alchemist: Brotherhood |  |
Notes: Sanity: shounen/adventure; avoid recap/summary content.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=3853, stage0_after_hygiene=3614, stage0_after_cap=3000, stage0_src_raw(neural/meta_strict/pop)=1500/2855/100, stage1_universe=3000, universe_match=True, shortlist=600/600, scored=418, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=75.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.712, content_first_alpha=0.70, content_first_active(top20/top50/all)=6/9/13, avg_neural_sim_top20=0.3927, avg_hybrid_val_top20=0.7753, sem_top50_mean=0.377, sem_top50_p95=0.476, sem_top50_overlap_mean=0.535, sem_top50_any_match=0.94, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.253/0.294/0.828, forced_in_top20/top50=20/41, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.741/0.741/0.741, high_sim_override_sim_min/mean/max(all)=0.741/0.741/0.741, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=162, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=79, demo_override_top20=2, blocked_overlap=62, blocked_low_sim=1110, bonus_fired=3, bonus_mean=0.00108, bonus_max=0.00954, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/5, theme_bonus_mean(top20/top50)=0.00030/0.00020, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=6, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1963 | 65.4% |
| blocked_low_semantic_sim | 147 | 4.9% |
| blocked_low_overlap | 3 | 0.1% |
| blocked_other_admission | 469 | 15.6% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 418 | 13.9% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 121 | Fullmetal Alchemist | overlap | 0.67 | 0.828 |
| 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | overlap | 0.67 | 0.741 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 2 | 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | Movie | 7.50 |  |  |
| 3 | 54853 | Demon Lord 2099 |  | 7.42 |  |  |
| 4 | 37345 | Plunderer |  | 6.65 |  |  |
| 5 | 2251 | Baccano! | TV | 8.35 |  |  |
| 6 | 59027 | Spy x Family Season 3 |  | 8.19 |  |  |
| 7 | 6707 | Black Butler II | TV | 7.12 |  |  |
| 8 | 53835 | Unnamed Memory |  | 6.78 |  |  |
| 9 | 267 | Gungrave | TV | 7.81 |  |  |
| 10 | 32998 | 91 Days | TV | 7.82 |  |  |
| 11 | 53434 | An Archdemon's Dilemma: How to Love Your Elf Bride |  | 7.29 |  |  |
| 12 | 1017 | Orphen | TV | 7.07 |  |  |
| 13 | 1482 | D.Gray-man | TV | 8.00 |  |  |
| 14 | 269 | Bleach | TV | 7.98 |  |  |
| 15 | 49979 | I'm the Villainess, So I'm Taming the Final Boss |  | 7.20 |  |  |
| 16 | 3819 | Nozomi In The Sun | TV | 6.43 |  |  |
| 17 | 2559 | Romeo's Blue Skies | TV | 8.31 |  |  |
| 18 | 953 | Jyu-Oh-Sei: Planet of the Beast King | TV | 7.17 |  |  |
| 19 | 32370 | D.Gray-man HALLOW | TV | 7.68 |  |  |
| 20 | 8777 | Julie the Wild Rose | TV | 6.00 |  |  |

---

## naruto

Seeds (requested): Naruto
Seeds (resolved): Naruto
Seed IDs: [20]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Naruto | exact | 20 | Naruto |  |
Notes: Sanity: long-running shounen; watch for many specials/recaps.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=3327, stage0_after_hygiene=3150, stage0_after_cap=3000, stage0_src_raw(neural/meta_strict/pop)=1500/2177/100, stage1_universe=3000, universe_match=True, shortlist=600/600, scored=573, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=75.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.991, content_first_alpha=0.70, content_first_active(top20/top50/all)=12/39/143, avg_neural_sim_top20=0.5353, avg_hybrid_val_top20=0.4360, sem_top50_mean=0.542, sem_top50_p95=0.616, sem_top50_overlap_mean=0.607, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.431/0.470/0.672, forced_in_top20/top50=20/35, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=7/7, top50_franchise_like(before/after)=8/8, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=3/3/3, high_sim_override_sim_min/mean/max(top50)=0.603/0.623/0.638, high_sim_override_sim_min/mean/max(all)=0.603/0.623/0.638, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=130, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=538, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=184, demo_override_top20=2, blocked_overlap=477, blocked_low_sim=297, bonus_fired=7, bonus_mean=0.00454, bonus_max=0.04800, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/3, theme_bonus_mean(top20/top50)=0.00020/0.00012, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1878 | 62.6% |
| blocked_low_semantic_sim | 2 | 0.1% |
| blocked_low_overlap | 246 | 8.2% |
| blocked_other_admission | 301 | 10.0% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 573 | 19.1% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 1735 | Naruto Shippuden | overlap | 1.00 | 0.672 |
| 10589 | Naruto Shippuden the Movie 5: Blood Prison | overlap | 1.00 | 0.638 |
| 13667 | Naruto Shippuden the Movie 6: Road to Ninja | overlap | 1.00 | 0.603 |
| 4437 | Naruto Shippuden the Movie 2: Bonds | overlap | 1.00 | 0.627 |
| 16870 | Naruto Shippuden the Movie 7: The Last | overlap | 1.00 | 0.599 |
| 28755 | Boruto: Naruto the Movie | overlap | 1.00 | 0.600 |
| 8246 | Naruto Shippuden the Movie 4: The Lost Tower | overlap | 1.00 | 0.595 |
| 1074 | Naruto: Finally a Clash!! Jounin vs. Genin! | overlap | 1.00 | 0.586 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 1735 | Naruto Shippuden | TV | 8.28 |  |  |
| 2 | 31339 | Drifters | TV | 7.88 |  |  |
| 3 | 50172 | Mob Psycho 100 III |  | 8.71 |  |  |
| 4 | 10589 | Naruto Shippuden the Movie 5: Blood Prison | Movie | 7.46 |  |  |
| 5 | 37520 | Dororo |  | 8.26 |  |  |
| 6 | 13667 | Naruto Shippuden the Movie 6: Road to Ninja | Movie | 7.69 |  |  |
| 7 | 44511 | Chainsaw Man |  | 8.44 |  |  |
| 8 | 4437 | Naruto Shippuden the Movie 2: Bonds | Movie | 7.28 |  |  |
| 9 | 16870 | Naruto Shippuden the Movie 7: The Last | Movie | 7.79 |  |  |
| 10 | 37510 | Mob Psycho 100 II |  | 8.78 |  |  |
| 11 | 28755 | Boruto: Naruto the Movie | Movie | 7.37 |  |  |
| 12 | 8246 | Naruto Shippuden the Movie 4: The Lost Tower | Movie | 7.42 |  |  |
| 13 | 50608 | Tokyo Revengers: Christmas Showdown |  | 7.62 |  |  |
| 14 | 45560 | Orient |  | 6.61 |  |  |
| 15 | 46569 | Hell's Paradise |  | 8.09 |  |  |
| 16 | 54918 | Tokyo Revengers: Tenjiku Arc |  | 7.82 |  |  |
| 17 | 49613 | The Wrong Way to Use Healing Magic |  | 7.53 |  |  |
| 18 | 5760 | Dororo | TV | 7.27 |  |  |
| 19 | 50932 | The Reincarnation of the Strongest Exorcist in Another World |  | 7.10 |  |  |
| 20 | 33095 | Descending Stories: Showa Genroku Rakugo Shinju | TV | 8.70 |  |  |

---

## one_piece

Seeds (requested): One Piece
Seeds (resolved): One Piece
Seed IDs: [21]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| One Piece | exact | 21 | One Piece |  |
Notes: Sanity: long-running shounen; watch for specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=3087, stage0_after_hygiene=2907, stage0_after_cap=2907, stage0_src_raw(neural/meta_strict/pop)=1500/2015/100, stage1_universe=2907, universe_match=True, shortlist=600/600, scored=488, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.902, content_first_alpha=0.70, content_first_active(top20/top50/all)=5/9/16, avg_neural_sim_top20=0.4651, avg_hybrid_val_top20=1.0166, sem_top50_mean=0.466, sem_top50_p95=0.608, sem_top50_overlap_mean=0.713, sem_top50_any_match=0.94, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.279/0.335/0.722, forced_in_top20/top50=17/40, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=9/9, top50_franchise_like(before/after)=14/14, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=5/5/5, high_sim_override_sim_min/mean/max(top50)=0.600/0.631/0.722, high_sim_override_sim_min/mean/max(all)=0.600/0.631/0.722, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=186, top20_off_type=9, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=86, demo_override_top20=0, blocked_overlap=117, blocked_low_sim=1117, bonus_fired=10, bonus_mean=0.01322, bonus_max=0.06769, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=6, top50_moved_meta=20, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1889 | 65.0% |
| blocked_low_semantic_sim | 151 | 5.2% |
| blocked_low_overlap | 28 | 1.0% |
| blocked_other_admission | 351 | 12.1% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 488 | 16.8% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 60022 | One Piece Fan Letter | overlap | 1.00 | 0.722 |
| 38234 | One Piece: Stampede | overlap | 1.00 | 0.608 |
| 4155 | One Piece Film: Strong World | overlap | 1.00 | 0.618 |
| 12859 | One Piece Film: Z | overlap | 1.00 | 0.599 |
| 464 | One Piece: Baron Omatsuri and the Secret Island | overlap | 1.00 | 0.600 |
| 5252 | One Piece: Romance Dawn Story | overlap | 1.00 | 0.607 |
| 31490 | One Piece Film: Gold | overlap | 1.00 | 0.581 |
| 459 | One Piece: The Movie | overlap | 1.00 | 0.580 |
| 50410 | One Piece Film: Red | overlap | 1.00 | 0.400 |
| 462 | One Piece: Dead End Adventure | overlap | 1.00 | 0.546 |

Franchise-cap audit (One Piece): top10 by title_overlap

| anime_id | Title | title_overlap | franchise_like | reason |
|---:|---|---:|:---:|---|
| 459 | One Piece: The Movie | 1.00 | Y | overlap |
| 460 | One Piece: Clockwork Island Adventure | 1.00 | Y | overlap |
| 462 | One Piece: Dead End Adventure | 1.00 | Y | overlap |
| 464 | One Piece: Baron Omatsuri and the Secret Island | 1.00 | Y | overlap |
| 1238 | One Piece: Protect! The Last Great Performance | 1.00 | Y | overlap |
| 4155 | One Piece Film: Strong World | 1.00 | Y | overlap |
| 5252 | One Piece: Romance Dawn Story | 1.00 | Y | overlap |
| 12859 | One Piece Film: Z | 1.00 | Y | overlap |
| 15323 | One Piece: Episode of Nami - Tears of a Navigator and the Bonds of Friends | 1.00 | Y | overlap |
| 19123 | One Piece: Episode of Merry - The Tale of One More Friend | 1.00 | Y | overlap |

Content-first audit: top10 items by neural_sim (rank movement)

| anime_id | Title | neural_sim | hybrid_val | score_before | score_after | rank_before | rank_after |
|---:|---|---:|---:|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter | 0.7222 | 0.00000 | 2.80369 | 3.41081 | 1 | 1 |
| 4155 | One Piece Film: Strong World | 0.6178 | 0.07884 | 2.15193 | 2.15193 | 2 | 3 |
| 38234 | One Piece: Stampede | 0.6082 | 0.00000 | 2.14942 | 2.66720 | 4 | 2 |
| 5252 | One Piece: Romance Dawn Story | 0.6072 | -0.06775 | 1.92749 | 1.92749 | 6 | 6 |
| 464 | One Piece: Baron Omatsuri and the Secret Island | 0.6000 | -0.05454 | 2.01140 | 2.01140 | 5 | 5 |
| 12859 | One Piece Film: Z | 0.5993 | 0.51676 | 2.15033 | 2.15033 | 3 | 4 |
| 31490 | One Piece Film: Gold | 0.5806 | -0.03002 | 1.91542 | 1.91542 | 7 | 7 |
| 459 | One Piece: The Movie | 0.5802 | -0.04647 | 1.78151 | 1.78151 | 8 | 8 |
| 462 | One Piece: Dead End Adventure | 0.5461 | -0.01895 | 0.96360 | 0.96360 | 22 | 26 |
| 460 | One Piece: Clockwork Island Adventure | 0.5427 | 0.11849 | 0.89008 | 0.89008 | 32 | 38 |

Forced-neural top10 neighbors (by similarity):

| anime_id | Title | Type | sim | in_shortlist | rank@50 | in_top20 |
|---:|---|---|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter |  | 0.7222 | True | 1 | True |
| 4155 | One Piece Film: Strong World | Movie | 0.6178 | True | 3 | True |
| 38234 | One Piece: Stampede |  | 0.6082 | True | 2 | True |
| 5252 | One Piece: Romance Dawn Story | OVA | 0.6072 | True | 6 | True |
| 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 0.6000 | True | 5 | True |
| 12859 | One Piece Film: Z | Movie | 0.5993 | True | 4 | True |
| 31490 | One Piece Film: Gold | Movie | 0.5806 | True | 7 | True |
| 459 | One Piece: The Movie | Movie | 0.5802 | True | 8 | True |
| 462 | One Piece: Dead End Adventure | Movie | 0.5461 | True | 26 | False |
| 460 | One Piece: Clockwork Island Adventure | Movie | 0.5427 | True | 38 | False |

Stage 2 high-sim override audit (top10 neural neighbors):

| anime_id | sim | type | final_rank | score | Δ_to_top20_cutoff | hybrid | overlap | coverage | neural_bonus | penalty_before | penalty_after | stage2_override |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 60022 | 0.7222 |  | 1 | 3.41081 | -2.38617 | 0.00000 | 1.000 | 1.000 | 1.18048 | -0.01000 | 0.00000 | True |
| 4155 | 0.6178 | Movie | 3 | 2.15193 | -1.12729 | 0.07884 | 1.000 | 1.000 | 0.91959 | -0.01000 | 0.00000 | True |
| 38234 | 0.6082 |  | 2 | 2.66720 | -1.64256 | 0.00000 | 1.000 | 1.000 | 0.89558 | -0.01000 | 0.00000 | True |
| 5252 | 0.6072 | OVA | 6 | 1.92749 | -0.90285 | -0.06775 | 1.000 | 1.000 | 0.89309 | -0.01000 | 0.00000 | True |
| 464 | 0.6000 | Movie | 5 | 2.01140 | -0.98676 | -0.05454 | 1.000 | 1.000 | 0.87502 | -0.01000 | 0.00000 | True |
| 12859 | 0.5993 | Movie | 4 | 2.15033 | -1.12569 | 0.51676 | 1.000 | 1.000 | 0.87326 | -0.01000 | -0.01000 | False |
| 31490 | 0.5806 | Movie | 7 | 1.91542 | -0.89078 | -0.03002 | 1.000 | 1.000 | 0.82655 | -0.01000 | -0.01000 | False |
| 459 | 0.5802 | Movie | 8 | 1.78151 | -0.75687 | -0.04647 | 1.000 | 1.000 | 0.82551 | -0.01000 | -0.01000 | False |
| 462 | 0.5461 | Movie | 26 | 0.96360 | 0.06104 | -0.01895 | 1.000 | 1.000 | 0.00000 | -0.05389 | -0.05389 | False |
| 460 | 0.5427 | Movie | 38 | 0.89008 | 0.13457 | 0.11849 | 1.000 | 1.000 | 0.00000 | -0.05726 | -0.05726 | False |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 46 | 33 | Berserk |  | 0.00000 |
| 21 | 223 | Dragon Ball |  | 0.00000 |
| 41 | 392 | Yu Yu Hakusho: Ghost Files |  | 0.00000 |
| 8 | 459 | One Piece: The Movie |  | 0.00000 |
| 38 | 460 | One Piece: Clockwork Island Adventure |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 60022 | One Piece Fan Letter |  | 9.03 |  |  |
| 2 | 38234 | One Piece: Stampede |  | 8.18 |  |  |
| 3 | 4155 | One Piece Film: Strong World | Movie | 8.04 |  |  |
| 4 | 12859 | One Piece Film: Z | Movie | 8.10 |  |  |
| 5 | 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 7.78 |  |  |
| 6 | 5252 | One Piece: Romance Dawn Story | OVA | 7.32 |  |  |
| 7 | 31490 | One Piece Film: Gold | Movie | 7.87 |  |  |
| 8 | 459 | One Piece: The Movie | Movie | 7.09 |  |  |
| 9 | 58567 | Solo Leveling Season 2: Arise from the Shadow |  | 8.62 |  |  |
| 10 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 11 | 19505 | Kaizoku Ouji | TV | 5.90 |  |  |
| 12 | 5071 | Croket! | TV | 6.90 |  |  |
| 13 | 53516 | I Was Reincarnated as the 7th Prince so I Can Take My Time Perfecting My Magical Ability |  | 7.42 |  |  |
| 14 | 50410 | One Piece Film: Red |  | 7.82 |  |  |
| 15 | 1250 | Elemental Gelade | TV | 7.23 |  |  |
| 16 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 17 | 889 | Black Lagoon | TV | 8.03 |  |  |
| 18 | 2451 | Space Adventure Cobra | TV | 7.67 |  |  |
| 19 | 2618 | Treasure Island | TV | 7.93 |  |  |
| 20 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |

---

## demon_slayer

Seeds (requested): Demon Slayer: Kimetsu no Yaiba
Seeds (resolved): Demon Slayer: Kimetsu no Yaiba
Seed IDs: [38000]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Demon Slayer: Kimetsu no Yaiba | exact | 38000 | Demon Slayer: Kimetsu no Yaiba |  |
Notes: Sanity: modern action; avoid recap edits.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2485, stage0_after_hygiene=2368, stage0_after_cap=2368, stage0_src_raw(neural/meta_strict/pop)=1500/1191/100, stage1_universe=2368, universe_match=True, shortlist=600/600, scored=528, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=50.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.861, content_first_alpha=0.70, content_first_active(top20/top50/all)=20/44/95, avg_neural_sim_top20=0.4321, avg_hybrid_val_top20=0.0000, sem_top50_mean=0.471, sem_top50_p95=0.519, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.72, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.385/0.419/0.600, forced_in_top20/top50=17/36, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=4/4, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.600/0.600/0.600, high_sim_override_sim_min/mean/max(all)=0.600/0.600/0.600, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=154, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=101, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=156, demo_override_top20=7, blocked_overlap=539, blocked_low_sim=247, bonus_fired=1, bonus_mean=0.00244, bonus_max=0.04880, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/13, theme_bonus_mean(top20/top50)=0.00050/0.00052, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=0.960, top20_moved_meta=0, top50_moved_meta=13, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 619 | 26.1% |
| blocked_low_semantic_sim | 141 | 6.0% |
| blocked_low_overlap | 268 | 11.3% |
| blocked_other_admission | 797 | 33.7% |
| missing_semantic_vector | 15 | 0.6% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 528 | 22.3% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc | overlap | 1.00 | 0.600 |
| 40456 | Demon Slayer: Kimetsu no Yaiba - The Movie: Mugen Train | overlap | 1.00 | 0.464 |
| 47778 | Demon Slayer: Kimetsu no Yaiba Entertainment District Arc | overlap | 1.00 | 0.424 |
| 55701 | Demon Slayer: Kimetsu no Yaiba Hashira Training Arc | overlap | 1.00 | 0.457 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc |  | 8.17 |  |  |
| 2 | 44511 | Chainsaw Man |  | 8.44 |  |  |
| 3 | 37520 | Dororo |  | 8.26 |  |  |
| 4 | 40748 | Jujutsu Kaisen |  | 8.53 |  |  |
| 5 | 60543 | Dan Da Dan Season 2 |  | 8.47 |  |  |
| 6 | 38759 | The Helpful Fox Senko-san |  | 7.31 |  |  |
| 7 | 34019 | Tsugumomo | TV | 7.03 |  |  |
| 8 | 58913 | The Summer Hikaru Died |  | 8.06 |  |  |
| 9 | 47194 | Summer Time Rendering |  | 8.47 |  |  |
| 10 | 59062 | Gachiakuta |  | 8.06 |  |  |
| 11 | 40956 | Fire Force Season 2 |  | 7.82 |  |  |
| 12 | 50172 | Mob Psycho 100 III |  | 8.71 |  |  |
| 13 | 54790 | Undead Murder Farce |  | 7.85 |  |  |
| 14 | 34076 | The Eccentric Family 2 | TV | 8.07 |  |  |
| 15 | 46569 | Hell's Paradise |  | 8.09 |  |  |
| 16 | 50932 | The Reincarnation of the Strongest Exorcist in Another World |  | 7.10 |  |  |
| 17 | 42340 | The Dungeon of Black Company |  | 7.21 |  |  |
| 18 | 54724 | The Elusive Samurai |  | 7.79 |  |  |
| 19 | 41467 | Bleach: Thousand-Year Blood War |  | 8.99 |  |  |
| 20 | 58811 | Tougen Anki |  | 6.58 |  |  |

---

## jujutsu_kaisen

Seeds (requested): Jujutsu Kaisen
Seeds (resolved): Jujutsu Kaisen
Seed IDs: [40748]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Jujutsu Kaisen | exact | 40748 | Jujutsu Kaisen |  |
Notes: Sanity: modern action; avoid specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2980, stage0_after_hygiene=2729, stage0_after_cap=2729, stage0_src_raw(neural/meta_strict/pop)=1500/1802/100, stage1_universe=2729, universe_match=True, shortlist=600/600, scored=551, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=60.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.883, content_first_alpha=0.70, content_first_active(top20/top50/all)=18/40/108, avg_neural_sim_top20=0.4298, avg_hybrid_val_top20=0.0874, sem_top50_mean=0.469, sem_top50_p95=0.531, sem_top50_overlap_mean=0.420, sem_top50_any_match=0.80, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.377/0.411/0.556, forced_in_top20/top50=17/31, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=1/1, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=137, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=110, theme_override=1, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=233, demo_override_top20=1, blocked_overlap=663, blocked_low_sim=400, bonus_fired=1, bonus_mean=0.00256, bonus_max=0.05120, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=6/13, theme_bonus_mean(top20/top50)=0.00060/0.00052, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=3, top50_moved_meta=18, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 732 | 26.8% |
| blocked_low_semantic_sim | 281 | 10.3% |
| blocked_low_overlap | 339 | 12.4% |
| blocked_other_admission | 821 | 30.1% |
| missing_semantic_vector | 5 | 0.2% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 551 | 20.2% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 48561 | Jujutsu Kaisen 0 | overlap | 1.00 | 0.529 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 39071 | The Demon Girl Next Door |  | 7.63 |  |  |
| 2 | 38000 | Demon Slayer: Kimetsu no Yaiba |  | 8.42 |  |  |
| 3 | 57864 | Monogatari Series: Off & Monster Season |  | 8.65 |  |  |
| 4 | 34451 | Blood Blockade Battlefront & Beyond | TV | 7.77 |  |  |
| 5 | 39247 | Miss Kobayashi's Dragon Maid S |  | 8.21 |  |  |
| 6 | 60543 | Dan Da Dan Season 2 |  | 8.47 |  |  |
| 7 | 32962 | Occultic;Nine | TV | 6.89 |  |  |
| 8 | 33206 | Miss Kobayashi's Dragon Maid | TV | 7.91 |  |  |
| 9 | 48561 | Jujutsu Kaisen 0 |  | 8.39 |  |  |
| 10 | 37510 | Mob Psycho 100 II |  | 8.78 |  |  |
| 11 | 33506 | Blue Exorcist: Kyoto Saga | TV | 7.34 |  |  |
| 12 | 58913 | The Summer Hikaru Died |  | 8.06 |  |  |
| 13 | 15451 | High School DxD New | TV | 7.46 |  |  |
| 14 | 47163 | My Isekai Life: I Gained a Second Character Class and Became the Strongest Sage in the World |  | 6.33 |  |  |
| 15 | 33253 | Ajin: Demi-Human 2nd Season | TV | 7.55 |  |  |
| 16 | 41467 | Bleach: Thousand-Year Blood War |  | 8.99 |  |  |
| 17 | 52816 | The Witch and the Beast |  | 7.44 |  |  |
| 18 | 59226 | Blue Exorcist: The Blue Night Saga |  | 8.00 |  |  |
| 19 | 392 | Yu Yu Hakusho: Ghost Files | TV | 8.46 |  |  |
| 20 | 52830 | I Got a Cheat Skill in Another World and Became Unrivaled in The Real World, Too |  | 6.34 |  |  |

---

## my_hero_academia

Seeds (requested): My Hero Academia
Seeds (resolved): My Hero Academia
Seed IDs: [31964]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| My Hero Academia | exact | 31964 | My Hero Academia |  |
Notes: Sanity: modern shounen; avoid recap specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=4822, stage0_after_hygiene=4403, stage0_after_cap=3000, stage0_src_raw(neural/meta_strict/pop)=1500/4029/100, stage1_universe=3000, universe_match=True, shortlist=600/600, scored=569, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=95.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.863, content_first_alpha=0.70, content_first_active(top20/top50/all)=18/43/157, avg_neural_sim_top20=0.4480, avg_hybrid_val_top20=0.5663, sem_top50_mean=0.463, sem_top50_p95=0.532, sem_top50_overlap_mean=0.680, sem_top50_any_match=0.68, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.409/0.652, forced_in_top20/top50=16/31, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=6/6, top50_franchise_like(before/after)=9/9, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.609/0.609/0.609, high_sim_override_sim_min/mean/max(all)=0.609/0.609/0.609, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=99, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=416, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=181, demo_override_top20=0, blocked_overlap=554, blocked_low_sim=392, bonus_fired=4, bonus_mean=0.01392, bonus_max=0.07920, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=10/20, theme_bonus_mean(top20/top50)=0.00100/0.00080, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=20, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=13, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1306 | 43.5% |
| blocked_low_semantic_sim | 108 | 3.6% |
| blocked_low_overlap | 442 | 14.7% |
| blocked_other_admission | 572 | 19.1% |
| missing_semantic_vector | 3 | 0.1% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 569 | 19.0% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 38408 | My Hero Academia Season 4 | overlap | 1.00 | 0.652 |
| 44200 | My Hero Academia: World Heroes' Mission | overlap | 1.00 | 0.609 |
| 53447 | To Be Hero X | overlap | 0.50 | 0.476 |
| 33486 | My Hero Academia Season 2 | overlap | 1.00 | 0.475 |
| 60593 | My Hero Academia: Vigilantes | overlap | 1.00 | 0.425 |
| 54789 | My Hero Academia Season 7 | overlap | 1.00 | 0.378 |
| 39565 | My Hero Academia: Heroes Rising | overlap | 1.00 | 0.530 |
| 34445 | Yuki Yuna is a Hero: The Hero Chapter | overlap | 0.50 | 0.441 |
| 61026 | My Status as an Assassin Obviously Exceeds the Hero's | overlap | 0.50 | 0.364 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 38408 | My Hero Academia Season 4 |  | 7.86 |  |  |
| 2 | 44200 | My Hero Academia: World Heroes' Mission |  | 7.58 |  |  |
| 3 | 53447 | To Be Hero X |  | 8.72 |  |  |
| 4 | 33486 | My Hero Academia Season 2 | TV | 8.05 |  |  |
| 5 | 39463 | Gleipnir |  | 6.95 |  |  |
| 6 | 39792 | Keep Your Hands Off Eizouken! |  | 8.13 |  |  |
| 7 | 51009 | Jujutsu Kaisen Season 2 |  | 8.72 |  |  |
| 8 | 31339 | Drifters | TV | 7.88 |  |  |
| 9 | 52741 | Undead Unluck |  | 7.75 |  |  |
| 10 | 54918 | Tokyo Revengers: Tenjiku Arc |  | 7.82 |  |  |
| 11 | 42249 | Tokyo Revengers |  | 7.84 |  |  |
| 12 | 37520 | Dororo |  | 8.26 |  |  |
| 13 | 60593 | My Hero Academia: Vigilantes |  | 7.60 |  |  |
| 14 | 1735 | Naruto Shippuden | TV | 8.28 |  |  |
| 15 | 47162 | The Executioner and Her Way of Life |  | 6.76 |  |  |
| 16 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 17 | 33095 | Descending Stories: Showa Genroku Rakugo Shinju | TV | 8.70 |  |  |
| 18 | 54789 | My Hero Academia Season 7 |  | 8.09 |  |  |
| 19 | 44511 | Chainsaw Man |  | 8.44 |  |  |
| 20 | 40052 | Great Pretender |  | 8.19 |  |  |

---

## haikyuu

Seeds (requested): Haikyu!!
Seeds (resolved): Haikyu!!
Seed IDs: [20583]

Seed resolution details:

| Query | Method | Resolved anime_id | Matched title | Score |
|---|---|---:|---|---:|
| Haikyu!! | exact | 20583 | Haikyu!! |  |
Notes: Sanity: sports; avoid shorts/specials.
Top-N: 20
Violations: 0
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2769, stage0_after_hygiene=2504, stage0_after_cap=2504, stage0_src_raw(neural/meta_strict/pop)=1500/1880/100, stage1_universe=2504, universe_match=True, shortlist=600/600, scored=569, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=95.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.933, content_first_alpha=0.70, content_first_active(top20/top50/all)=13/22/95, avg_neural_sim_top20=0.4921, avg_hybrid_val_top20=0.4756, sem_top50_mean=0.493, sem_top50_p95=0.557, sem_top50_overlap_mean=0.900, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.366/0.410/0.857, forced_in_top20/top50=20/46, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=7/7, top50_franchise_like(before/after)=8/8, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.857/0.857/0.857, high_sim_override_sim_min/mean/max(all)=0.857/0.857/0.857, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=100, top20_off_type=5, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=234, demo_override_top20=1, blocked_overlap=673, blocked_low_sim=406, bonus_fired=12, bonus_mean=0.02000, bonus_max=0.07520, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=16/36, theme_bonus_mean(top20/top50)=0.00160/0.00144, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=19, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=6, top50_moved_meta=19, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 280 | 11.2% |
| blocked_low_semantic_sim | 353 | 14.1% |
| blocked_low_overlap | 560 | 22.4% |
| blocked_other_admission | 737 | 29.4% |
| missing_semantic_vector | 5 | 0.2% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 569 | 22.7% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 29755 | Haikyu!! the Movie: The End and the Beginning | overlap | 1.00 | 0.857 |
| 40776 | Haikyu!! To the Top 2nd-cour | overlap | 1.00 | 0.513 |
| 38883 | Haikyu!! To the Top | overlap | 1.00 | 0.512 |
| 25303 | Haikyu!!: Lev Appears! | overlap | 1.00 | 0.581 |
| 52742 | Haikyu!! Movie: The Dumpster Battle | overlap | 1.00 | 0.546 |
| 28891 | Haikyu!! 2nd Season | overlap | 1.00 | 0.527 |
| 32935 | Haikyu!! 3rd Season | overlap | 1.00 | 0.498 |
| 40262 | Haikyu!! Land vs. Air | overlap | 1.00 | 0.478 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 29755 | Haikyu!! the Movie: The End and the Beginning | Movie | 8.10 |  |  |
| 2 | 40776 | Haikyu!! To the Top 2nd-cour |  | 8.56 |  |  |
| 3 | 38883 | Haikyu!! To the Top |  | 8.37 |  |  |
| 4 | 37403 | Ahiru no Sora |  | 7.26 |  |  |
| 5 | 33031 | Scorching Ping Pong Girls | TV | 7.05 |  |  |
| 6 | 25303 | Haikyu!!: Lev Appears! | OVA | 7.70 |  |  |
| 7 | 49052 | Aoashi |  | 8.15 |  |  |
| 8 | 57181 | Blue Box |  | 8.18 |  |  |
| 9 | 52742 | Haikyu!! Movie: The Dumpster Battle |  | 8.61 |  |  |
| 10 | 28891 | Haikyu!! 2nd Season | TV | 8.62 |  |  |
| 11 | 32935 | Haikyu!! 3rd Season | TV | 8.77 |  |  |
| 12 | 42923 | SK8 the Infinity |  | 8.00 |  |  |
| 13 | 55318 | Medalist |  | 8.37 |  |  |
| 14 | 32871 | Winter Cup Highlights Episode 3 – Winter Cup Highlights -Crossing the Door- | Movie | 7.83 |  |  |
| 15 | 45649 | The First Slam Dunk |  | 8.71 |  |  |
| 16 | 33094 | WWW.WAGNARIA!! | TV | 7.41 |  |  |
| 17 | 5834 | Kyojin no Hoshi | TV | 6.91 |  |  |
| 18 | 37972 | Stars Align |  | 7.59 |  |  |
| 19 | 15 | Eyeshield 21 | TV | 7.91 |  |  |
| 20 | 48926 | Komi Can't Communicate |  | 7.80 |  |  |

