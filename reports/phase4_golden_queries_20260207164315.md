# Phase 4 — Golden Queries Report

Generated: 2026-02-07T16:48:12.900567+00:00
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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2549, stage0_after_hygiene=2437, stage0_after_cap=2437, stage0_src_raw(neural/meta_strict/pop)=1500/1223/100, stage1_universe=2437, universe_match=True, shortlist=600/600, scored=556, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=80.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.923, content_first_alpha=0.70, content_first_active(top20/top50/all)=10/31/110, avg_neural_sim_top20=0.4440, avg_hybrid_val_top20=1.5010, sem_top50_mean=0.484, sem_top50_p95=0.550, sem_top50_overlap_mean=0.510, sem_top50_any_match=0.98, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.398/0.429/0.577, forced_in_top20/top50=15/38, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=4/4, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=150, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=313, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[seinen], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=589, blocked_low_sim=300, bonus_fired=3, bonus_mean=0.00111, bonus_max=0.00990, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=9/14, theme_bonus_mean(top20/top50)=0.00070/0.00041, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=19, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1165 | 47.8% |
| blocked_low_semantic_sim | 9 | 0.4% |
| blocked_low_overlap | 286 | 11.7% |
| blocked_other_admission | 421 | 17.3% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 556 | 22.8% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 30458 | Tokyo Ghoul: Jack | overlap | 1.00 | 0.563 |
| 27899 | Tokyo Ghoul √A | overlap | 1.00 | 0.490 |
| 54918 | Tokyo Revengers: Tenjiku Arc | overlap | 0.50 | 0.421 |
| 50608 | Tokyo Revengers: Christmas Showdown | overlap | 0.50 | 0.411 |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 9 | 2356 | Amon: Apocalypse of Devilman | 0.667 | 0.00200 |
| 16 | 27899 | Tokyo Ghoul √A | 1.000 | 0.00200 |
| 5 | 30458 | Tokyo Ghoul: Jack | 1.000 | 0.00200 |
| 44 | 13125 | From the New World | 0.333 | 0.00133 |
| 1 | 31339 | Drifters | 0.333 | 0.00133 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 30463 | Horror News | ONA | 5.43 |  |  |
| 3 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 4 | 30412 | Zombie Brother | ONA | 6.51 |  |  |
| 5 | 30458 | Tokyo Ghoul: Jack | OVA | 7.29 |  |  |
| 6 | 43690 | High-Rise Invasion |  | 6.68 |  |  |
| 7 | 33814 | Aooni The Blue Monster | TV | 5.11 |  |  |
| 8 | 58811 | Tougen Anki |  | 6.58 |  |  |
| 9 | 2356 | Amon: Apocalypse of Devilman | OVA | 6.50 |  |  |
| 10 | 61026 | My Status as an Assassin Obviously Exceeds the Hero's |  | 7.11 |  |  |
| 11 | 50392 | Chained Soldier |  | 6.85 |  |  |
| 12 | 41461 | Date A Live IV |  | 7.74 |  |  |
| 13 | 37451 | Boogiepop and Others |  | 7.06 |  |  |
| 14 | 4821 | Lesson of Darkness | OVA | 5.19 |  |  |
| 15 | 34467 | Theatre of Darkness: Yamishibai 4 | TV | 5.81 |  |  |
| 16 | 27899 | Tokyo Ghoul √A | TV | 7.03 |  |  |
| 17 | 29089 | Monster List | ONA | 6.80 |  |  |
| 18 | 52588 | Kaiju No. 8 |  | 8.25 |  |  |
| 19 | 50330 | Bungo Stray Dogs 4 |  | 8.42 |  |  |
| 20 | 5760 | Dororo | TV | 7.27 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2058, stage0_after_hygiene=2000, stage0_after_cap=2000, stage0_src_raw(neural/meta_strict/pop)=1500/661/100, stage1_universe=2000, universe_match=True, shortlist=600/600, scored=534, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=95.0%, top20_from_meta_strict=35.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.828, content_first_alpha=0.70, content_first_active(top20/top50/all)=6/20/58, avg_neural_sim_top20=0.3646, avg_hybrid_val_top20=2.9580, sem_top50_mean=0.432, sem_top50_p95=0.520, sem_top50_overlap_mean=0.355, sem_top50_any_match=0.84, top20_pools(A/B/C)=19/1/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.307/0.354/0.611, forced_in_top20/top50=19/45, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=3/3, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=145, top20_off_type=5, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=112, demo_override_top20=2, blocked_overlap=289, blocked_low_sim=501, bonus_fired=3, bonus_mean=0.00779, bonus_max=0.07680, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/9, theme_bonus_mean(top20/top50)=0.00043/0.00031, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=7, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 820 | 41.0% |
| blocked_low_semantic_sim | 145 | 7.2% |
| blocked_low_overlap | 111 | 5.5% |
| blocked_other_admission | 390 | 19.5% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 534 | 26.7% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 25777 | Attack on Titan Season 2 | overlap | 1.00 | 0.611 |
| 35760 | Attack on Titan Season 3 | overlap | 1.00 | 0.505 |
| 48583 | Attack on Titan: Final Season Part 2 | overlap | 1.00 | 0.301 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 25777 | Attack on Titan Season 2 | TV | 8.53 |  |  |
| 2 | 31339 | Drifters | TV | 7.88 |  |  |
| 3 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 4 | 35760 | Attack on Titan Season 3 |  | 8.64 |  |  |
| 5 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 6 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 7 | 55255 | Alien Stage |  | 8.69 |  |  |
| 8 | 4933 | The White Whale of Mu | TV | 6.32 |  |  |
| 9 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 10 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 11 | 33502 | WorldEnd: What do you do at the end of the world? Are you busy? Will you save us? | TV | 7.67 |  |  |
| 12 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 13 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 14 | 3846 | Microid S | TV | 6.00 |  |  |
| 15 | 53770 | Go! Go! Loser Ranger! |  | 7.31 |  |  |
| 16 | 33220 | Summer's Puke is Winter's Delight | Movie | 3.84 |  |  |
| 17 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 18 | 33266 | NANOCORE | ONA | 5.97 |  |  |
| 19 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 20 | 40623 | SUPER HXEROS |  | 5.75 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2456, stage0_after_hygiene=2294, stage0_after_cap=2294, stage0_src_raw(neural/meta_strict/pop)=1500/1290/100, stage1_universe=2294, universe_match=True, shortlist=600/600, scored=563, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=95.0%, top20_from_meta_strict=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.906, content_first_alpha=0.70, content_first_active(top20/top50/all)=8/24/127, avg_neural_sim_top20=0.4074, avg_hybrid_val_top20=2.4395, sem_top50_mean=0.488, sem_top50_p95=0.546, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.66, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.417/0.703, forced_in_top20/top50=14/35, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.703/0.703/0.703, high_sim_override_sim_min/mean/max(all)=0.703/0.703/0.703, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=122, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=129, demo_override_top20=0, blocked_overlap=470, blocked_low_sim=212, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00640, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/13, theme_bonus_mean(top20/top50)=0.00040/0.00052, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=11, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=7, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 30463 | Horror News | ONA | 5.43 |  |  |
| 3 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |
| 4 | 30485 | ChäoS;Child | TV | 6.30 |  |  |
| 5 | 47194 | Summer Time Rendering |  | 8.47 |  |  |
| 6 | 38759 | The Helpful Fox Senko-san |  | 7.31 |  |  |
| 7 | 24663 | Dororonpa! | TV | 6.18 |  |  |
| 8 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 9 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 10 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 11 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 12 | 48413 | The Devil is a Part-Timer! Season 2 |  | 6.65 |  |  |
| 13 | 33339 | Zhongguo Jingqi Xiansheng | ONA | 6.05 |  |  |
| 14 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 15 | 44961 | Platinum End |  | 6.02 |  |  |
| 16 | 33144 | The Hell (Two Kinds of Life) | Movie | 5.73 |  |  |
| 17 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 18 | 49709 | To Your Eternity Season 2 |  | 8.11 |  |  |
| 19 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 20 | 46569 | Hell's Paradise |  | 8.09 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2277, stage0_after_hygiene=2119, stage0_after_cap=2119, stage0_src_raw(neural/meta_strict/pop)=1500/830/100, stage1_universe=2119, universe_match=True, shortlist=600/600, scored=524, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=20.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.794, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/6/53, avg_neural_sim_top20=0.3915, avg_hybrid_val_top20=4.1669, sem_top50_mean=0.410, sem_top50_p95=0.514, sem_top50_overlap_mean=0.693, sem_top50_any_match=1.00, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.321/0.353/0.683, forced_in_top20/top50=19/48, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=3/3, top50_franchise_like(before/after)=3/3, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.612/0.612/0.612, high_sim_override_sim_min/mean/max(all)=0.612/0.612/0.612, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=146, top20_off_type=11, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=674, blocked_low_sim=335, bonus_fired=3, bonus_mean=0.00107, bonus_max=0.00954, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/8, theme_bonus_mean(top20/top50)=0.00030/0.00032, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=11, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=1, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| final_scored_candidate_count | 524 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 50 |

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 724 | 34.2% |
| blocked_low_semantic_sim | 49 | 2.3% |
| blocked_low_overlap | 339 | 16.0% |
| blocked_other_admission | 483 | 22.8% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 524 | 24.7% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 30484 | Steins;Gate 0 | overlap | 1.00 | 0.683 |
| 32188 | Steins;Gate: Open the Missing Link - Divide By Zero | overlap | 1.00 | 0.612 |
| 27957 | Steins;Gate: The Sagacious Wisdom of Cognitive Computing | overlap | 1.00 | 0.564 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30484 | Steins;Gate 0 | TV | 8.55 |  |  |
| 2 | 31517 | Ohayou Ninja-tai Gatchaman | TV | 5.46 |  |  |
| 3 | 31238 | Stitch! Perfect Memory | TV Special | 5.74 |  |  |
| 4 | 32188 | Steins;Gate: Open the Missing Link - Divide By Zero | TV Special | 8.26 |  |  |
| 5 | 6727 | Mechanical Boy Dotakon | TV | 5.85 |  |  |
| 6 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 7 | 6636 | Super High Speed Galvion | TV | 5.84 |  |  |
| 8 | 28815 | Bamboo Blade: CM Fanfu-Fufe-Fo | CM | 5.52 |  |  |
| 9 | 6889 | Time Bokan Series: Zenderman | TV | 5.84 |  |  |
| 10 | 2740 | Monkey Turn | TV | 6.43 |  |  |
| 11 | 29729 | Peeping Life x I-O Data: Quiz!! Input Output | ONA | 5.28 |  |  |
| 12 | 32149 | Tatsunoko Pro x Peeping Life | ONA | 5.58 |  |  |
| 13 | 29795 | The Soba Flower of Mt. Oni | Movie | 5.75 |  |  |
| 14 | 29796 | Oshizuka ni | Movie | 5.35 |  |  |
| 15 | 29797 | Panache the Squirrel | Movie | 5.62 |  |  |
| 16 | 29799 | Tabi wa Michizure Yo wa Nasake | Movie | 5.13 |  |  |
| 17 | 29587 | Home My Home | Movie | 5.21 |  |  |
| 18 | 30905 | Owanko | ONA | 5.56 |  |  |
| 19 | 27957 | Steins;Gate: The Sagacious Wisdom of Cognitive Computing | ONA | 7.44 |  |  |
| 20 | 13125 | From the New World | TV | 8.25 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2505, stage0_after_hygiene=2337, stage0_after_cap=2337, stage0_src_raw(neural/meta_strict/pop)=1500/1435/100, stage1_universe=2337, universe_match=True, shortlist=600/600, scored=549, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=90.0%, top20_from_meta_strict=75.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.793, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/10/34, avg_neural_sim_top20=0.3417, avg_hybrid_val_top20=3.1653, sem_top50_mean=0.423, sem_top50_p95=0.499, sem_top50_overlap_mean=0.673, sem_top50_any_match=1.00, top20_pools(A/B/C)=18/2/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.311/0.355/0.522, forced_in_top20/top50=14/37, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=0/0, top50_franchise_like(before/after)=0/0, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=172, top20_off_type=2, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=95, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=400, blocked_low_sim=645, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/13, theme_bonus_mean(top20/top50)=0.00050/0.00052, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=9, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| final_scored_candidate_count | 549 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 50 |

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1178 | 50.4% |
| blocked_low_semantic_sim | 193 | 8.3% |
| blocked_low_overlap | 90 | 3.9% |
| blocked_other_admission | 327 | 14.0% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 549 | 23.5% |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 28673 | Die Now | ONA | 6.37 |  |  |
| 2 | 11405 | Skyers 5 | TV | 5.92 |  |  |
| 3 | 22997 | Shin Skyers 5 | TV |  |  |  |
| 4 | 27455 | Pororo the Little Penguin 3 | TV | 5.73 |  |  |
| 5 | 2697 | High Speed Jessie | OVA | 6.10 |  |  |
| 6 | 16159 | Mirai Kara Kita Shounen Super Jetter | TV | 5.86 |  |  |
| 7 | 12139 | Wanpaku Tanteidan | TV | 6.10 |  |  |
| 8 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 9 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 10 | 7900 | Super Child | Movie | 2.92 |  |  |
| 11 | 20083 | Doteraman | TV | 5.77 |  |  |
| 12 | 4240 | Galactic Cyclone Braiger | TV | 6.66 |  |  |
| 13 | 16822 | Captain of Cosmos | Movie | 3.52 |  |  |
| 14 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 15 | 9781 | Hyouga Senshi Gaislugger | TV | 5.70 |  |  |
| 16 | 41433 | Akudama Drive |  | 7.57 |  |  |
| 17 | 8553 | Time Bokan Series: Time Patroltai Otasukeman | TV | 6.27 |  |  |
| 18 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 19 | 52093 | Trigun Stampede |  | 7.83 |  |  |
| 20 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=3853, stage0_after_hygiene=3614, stage0_after_cap=3000, stage0_src_raw(neural/meta_strict/pop)=1500/2855/100, stage1_universe=3000, universe_match=True, shortlist=600/600, scored=548, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=85.0%, top20_from_meta_strict=60.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.712, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/4/13, avg_neural_sim_top20=0.2951, avg_hybrid_val_top20=3.1294, sem_top50_mean=0.377, sem_top50_p95=0.476, sem_top50_overlap_mean=0.535, sem_top50_any_match=0.94, top20_pools(A/B/C)=17/3/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.253/0.294/0.828, forced_in_top20/top50=13/34, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.741/0.741/0.741, high_sim_override_sim_min/mean/max(all)=0.741/0.741/0.741, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=162, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=79, demo_override_top20=3, blocked_overlap=62, blocked_low_sim=1110, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00610, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/5, theme_bonus_mean(top20/top50)=0.00030/0.00020, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=10, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1963 | 65.4% |
| blocked_low_semantic_sim | 147 | 4.9% |
| blocked_low_overlap | 3 | 0.1% |
| blocked_other_admission | 339 | 11.3% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 548 | 18.3% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | overlap | 0.67 | 0.741 |
| 121 | Fullmetal Alchemist | overlap | 0.67 | 0.828 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | Movie | 7.50 |  |  |
| 2 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 3 | 8777 | Julie the Wild Rose | TV | 6.00 |  |  |
| 4 | 31966 | Sword Gai | ONA | 5.61 |  |  |
| 5 | 3819 | Nozomi In The Sun | TV | 6.43 |  |  |
| 6 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 7 | 54853 | Demon Lord 2099 |  | 7.42 |  |  |
| 8 | 22065 | The Adventures of T-Rex | TV |  |  |  |
| 9 | 19467 | Revbahaf Wang-gug Jaegeon-soelgi | TV |  |  |  |
| 10 | 9811 | Hanasaka Tenshi Tenten-kun | TV |  |  |  |
| 11 | 19311 | Turuturutu Narongi | TV |  |  |  |
| 12 | 5476 | Marvelous Melmo | TV | 6.14 |  |  |
| 13 | 30862 | Woman Who Stole Fingers | Movie | 5.85 |  |  |
| 14 | 37345 | Plunderer |  | 6.65 |  |  |
| 15 | 18321 | Kkomaeosa Ttori | Movie |  |  |  |
| 16 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 17 | 9613 | Big X | TV | 6.07 |  |  |
| 18 | 22613 | Keroppi in the Adventures of the Coward Prince | OVA | 5.74 |  |  |
| 19 | 5581 | Kaitei Daisensou: Ai no 20,000 Miles | TV Special | 5.20 |  |  |
| 20 | 20 | Naruto | TV | 8.01 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=3327, stage0_after_hygiene=3150, stage0_after_cap=3000, stage0_src_raw(neural/meta_strict/pop)=1500/2177/100, stage1_universe=3000, universe_match=True, shortlist=600/600, scored=586, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=90.0%, top20_from_meta_strict=90.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.991, content_first_alpha=0.70, content_first_active(top20/top50/all)=5/27/143, avg_neural_sim_top20=0.5075, avg_hybrid_val_top20=2.1419, sem_top50_mean=0.542, sem_top50_p95=0.616, sem_top50_overlap_mean=0.607, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.431/0.470/0.672, forced_in_top20/top50=16/34, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=7/7, top50_franchise_like(before/after)=7/7, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=3/3/3, high_sim_override_sim_min/mean/max(top50)=0.603/0.623/0.638, high_sim_override_sim_min/mean/max(all)=0.603/0.623/0.638, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=130, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=538, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=184, demo_override_top20=0, blocked_overlap=477, blocked_low_sim=297, bonus_fired=7, bonus_mean=0.00454, bonus_max=0.04800, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/5, theme_bonus_mean(top20/top50)=0.00030/0.00020, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=4, top50_moved_meta=4, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1878 | 62.6% |
| blocked_low_semantic_sim | 2 | 0.1% |
| blocked_low_overlap | 246 | 8.2% |
| blocked_other_admission | 288 | 9.6% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 586 | 19.5% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 1735 | Naruto Shippuden | overlap | 1.00 | 0.672 |
| 10589 | Naruto Shippuden the Movie 5: Blood Prison | overlap | 1.00 | 0.638 |
| 4437 | Naruto Shippuden the Movie 2: Bonds | overlap | 1.00 | 0.627 |
| 13667 | Naruto Shippuden the Movie 6: Road to Ninja | overlap | 1.00 | 0.603 |
| 28755 | Boruto: Naruto the Movie | overlap | 1.00 | 0.600 |
| 8246 | Naruto Shippuden the Movie 4: The Lost Tower | overlap | 1.00 | 0.595 |
| 16870 | Naruto Shippuden the Movie 7: The Last | overlap | 1.00 | 0.599 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 1735 | Naruto Shippuden | TV | 8.28 |  |  |
| 3 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 4 | 30463 | Horror News | ONA | 5.43 |  |  |
| 5 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 6 | 45560 | Orient |  | 6.61 |  |  |
| 7 | 10589 | Naruto Shippuden the Movie 5: Blood Prison | Movie | 7.46 |  |  |
| 8 | 4437 | Naruto Shippuden the Movie 2: Bonds | Movie | 7.28 |  |  |
| 9 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 10 | 56690 | Re:Monster |  | 6.54 |  |  |
| 11 | 5760 | Dororo | TV | 7.27 |  |  |
| 12 | 37520 | Dororo |  | 8.26 |  |  |
| 13 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 14 | 13667 | Naruto Shippuden the Movie 6: Road to Ninja | Movie | 7.69 |  |  |
| 15 | 28755 | Boruto: Naruto the Movie | Movie | 7.37 |  |  |
| 16 | 9768 | Shima Shima Tora no Shimajirou | TV | 5.93 |  |  |
| 17 | 8246 | Naruto Shippuden the Movie 4: The Lost Tower | Movie | 7.42 |  |  |
| 18 | 16870 | Naruto Shippuden the Movie 7: The Last | Movie | 7.79 |  |  |
| 19 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 20 | 50932 | The Reincarnation of the Strongest Exorcist in Another World |  | 7.10 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=3087, stage0_after_hygiene=2907, stage0_after_cap=2907, stage0_src_raw(neural/meta_strict/pop)=1500/2015/100, stage1_universe=2907, universe_match=True, shortlist=600/600, scored=577, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.902, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/3/16, avg_neural_sim_top20=0.4405, avg_hybrid_val_top20=2.4520, sem_top50_mean=0.466, sem_top50_p95=0.608, sem_top50_overlap_mean=0.713, sem_top50_any_match=0.94, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.279/0.335/0.722, forced_in_top20/top50=16/33, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=8/8, top50_franchise_like(before/after)=8/8, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=5/5/5, high_sim_override_sim_min/mean/max(top50)=0.600/0.631/0.722, high_sim_override_sim_min/mean/max(all)=0.600/0.631/0.722, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=186, top20_off_type=10, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=86, demo_override_top20=0, blocked_overlap=117, blocked_low_sim=1117, bonus_fired=9, bonus_mean=0.00984, bonus_max=0.06769, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=6, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1889 | 65.0% |
| blocked_low_semantic_sim | 151 | 5.2% |
| blocked_low_overlap | 28 | 1.0% |
| blocked_other_admission | 262 | 9.0% |
| missing_semantic_vector | 0 | 0.0% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 577 | 19.8% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 60022 | One Piece Fan Letter | overlap | 1.00 | 0.722 |
| 38234 | One Piece: Stampede | overlap | 1.00 | 0.608 |
| 12859 | One Piece Film: Z | overlap | 1.00 | 0.599 |
| 4155 | One Piece Film: Strong World | overlap | 1.00 | 0.618 |
| 5252 | One Piece: Romance Dawn Story | overlap | 1.00 | 0.607 |
| 464 | One Piece: Baron Omatsuri and the Secret Island | overlap | 1.00 | 0.600 |
| 459 | One Piece: The Movie | overlap | 1.00 | 0.580 |
| 31490 | One Piece Film: Gold | overlap | 1.00 | 0.581 |

Franchise-cap audit (One Piece): top10 by title_overlap

| anime_id | Title | title_overlap | franchise_like | reason |
|---:|---|---:|:---:|---|
| 459 | One Piece: The Movie | 1.00 | Y | overlap |
| 464 | One Piece: Baron Omatsuri and the Secret Island | 1.00 | Y | overlap |
| 4155 | One Piece Film: Strong World | 1.00 | Y | overlap |
| 5252 | One Piece: Romance Dawn Story | 1.00 | Y | overlap |
| 12859 | One Piece Film: Z | 1.00 | Y | overlap |
| 31490 | One Piece Film: Gold | 1.00 | Y | overlap |
| 38234 | One Piece: Stampede | 1.00 | Y | overlap |
| 60022 | One Piece Fan Letter | 1.00 | Y | overlap |
| 20 | Naruto | 0.00 | N |  |
| 121 | Fullmetal Alchemist | 0.00 | N |  |

Content-first audit: top10 items by neural_sim (rank movement)

| anime_id | Title | neural_sim | hybrid_val | score_before | score_after | rank_before | rank_after |
|---:|---|---:|---:|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter | 0.7222 | 0.00000 | 2.02040 | 2.62752 | 1 | 1 |
| 4155 | One Piece Film: Strong World | 0.6178 | 0.07884 | 1.75548 | 1.75548 | 5 | 6 |
| 38234 | One Piece: Stampede | 0.6082 | 0.00000 | 1.72410 | 2.24189 | 6 | 2 |
| 5252 | One Piece: Romance Dawn Story | 0.6072 | -0.06775 | 1.69919 | 1.69919 | 7 | 7 |
| 464 | One Piece: Baron Omatsuri and the Secret Island | 0.6000 | -0.05454 | 1.68589 | 1.68589 | 8 | 8 |
| 12859 | One Piece Film: Z | 0.5993 | 0.51676 | 1.80532 | 1.80532 | 3 | 4 |
| 31490 | One Piece Film: Gold | 0.5806 | -0.03002 | 1.59053 | 1.59053 | 13 | 13 |
| 459 | One Piece: The Movie | 0.5802 | -0.04647 | 1.62677 | 1.62677 | 11 | 11 |
| 462 | One Piece: Dead End Adventure | 0.5461 | -0.01895 | 0.74768 | 0.74768 | 202 | 205 |
| 460 | One Piece: Clockwork Island Adventure | 0.5427 | 0.11849 | 0.77859 | 0.77859 | 185 | 190 |

Forced-neural top10 neighbors (by similarity):

| anime_id | Title | Type | sim | in_shortlist | rank@50 | in_top20 |
|---:|---|---|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter |  | 0.7222 | True | 1 | True |
| 4155 | One Piece Film: Strong World | Movie | 0.6178 | True | 6 | True |
| 38234 | One Piece: Stampede |  | 0.6082 | True | 2 | True |
| 5252 | One Piece: Romance Dawn Story | OVA | 0.6072 | True | 7 | True |
| 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 0.6000 | True | 8 | True |
| 12859 | One Piece Film: Z | Movie | 0.5993 | True | 4 | True |
| 31490 | One Piece Film: Gold | Movie | 0.5806 | True | 13 | True |
| 459 | One Piece: The Movie | Movie | 0.5802 | True | 11 | True |
| 462 | One Piece: Dead End Adventure | Movie | 0.5461 | True |  | False |
| 460 | One Piece: Clockwork Island Adventure | Movie | 0.5427 | True |  | False |

Stage 2 high-sim override audit (top10 neural neighbors):

| anime_id | sim | type | final_rank | score | Δ_to_top20_cutoff | hybrid | overlap | coverage | neural_bonus | penalty_before | penalty_after | stage2_override |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 60022 | 0.7222 |  | 1 | 2.62752 | -1.15664 | 0.00000 | 1.000 | 1.000 | 1.18048 | -0.01000 | 0.00000 | True |
| 4155 | 0.6178 | Movie | 6 | 1.75548 | -0.28461 | 0.07884 | 1.000 | 1.000 | 0.91959 | -0.01000 | 0.00000 | True |
| 38234 | 0.6082 |  | 2 | 2.24189 | -0.77101 | 0.00000 | 1.000 | 1.000 | 0.89558 | -0.01000 | 0.00000 | True |
| 5252 | 0.6072 | OVA | 7 | 1.69919 | -0.22832 | -0.06775 | 1.000 | 1.000 | 0.89309 | -0.01000 | 0.00000 | True |
| 464 | 0.6000 | Movie | 8 | 1.68589 | -0.21501 | -0.05454 | 1.000 | 1.000 | 0.87502 | -0.01000 | 0.00000 | True |
| 12859 | 0.5993 | Movie | 4 | 1.80532 | -0.33444 | 0.51676 | 1.000 | 1.000 | 0.87326 | -0.01000 | -0.01000 | False |
| 31490 | 0.5806 | Movie | 13 | 1.59053 | -0.11965 | -0.03002 | 1.000 | 1.000 | 0.82655 | -0.01000 | -0.01000 | False |
| 459 | 0.5802 | Movie | 11 | 1.62677 | -0.15589 | -0.04647 | 1.000 | 1.000 | 0.82551 | -0.01000 | -0.01000 | False |
| 462 | 0.5461 | Movie | 205 | 0.74768 | 0.72320 | -0.01895 | 1.000 | 1.000 | 0.00000 | -0.05389 | -0.05389 | False |
| 460 | 0.5427 | Movie | 190 | 0.77859 | 0.69229 | 0.11849 | 1.000 | 1.000 | 0.00000 | -0.05726 | -0.05726 | False |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 39 | 20 | Naruto |  | 0.00000 |
| 50 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 11 | 459 | One Piece: The Movie |  | 0.00000 |
| 8 | 464 | One Piece: Baron Omatsuri and the Secret Island |  | 0.00000 |
| 48 | 1482 | D.Gray-man |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 60022 | One Piece Fan Letter |  | 9.03 |  |  |
| 2 | 38234 | One Piece: Stampede |  | 8.18 |  |  |
| 3 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 4 | 12859 | One Piece Film: Z | Movie | 8.10 |  |  |
| 5 | 19505 | Kaizoku Ouji | TV | 5.90 |  |  |
| 6 | 4155 | One Piece Film: Strong World | Movie | 8.04 |  |  |
| 7 | 5252 | One Piece: Romance Dawn Story | OVA | 7.32 |  |  |
| 8 | 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 7.78 |  |  |
| 9 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 10 | 30738 | Air Bound | Movie | 5.63 |  |  |
| 11 | 459 | One Piece: The Movie | Movie | 7.09 |  |  |
| 12 | 5071 | Croket! | TV | 6.90 |  |  |
| 13 | 31490 | One Piece Film: Gold | Movie | 7.87 |  |  |
| 14 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 15 | 15579 | Shinkai Densetsu Meremanoid | TV | 5.66 |  |  |
| 16 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 17 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 18 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 19 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 20 | 33484 | Shiroi Zou | Movie | 5.68 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2485, stage0_after_hygiene=2368, stage0_after_cap=2368, stage0_src_raw(neural/meta_strict/pop)=1500/1191/100, stage1_universe=2368, universe_match=True, shortlist=600/600, scored=560, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=90.0%, top20_from_meta_strict=50.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.861, content_first_alpha=0.70, content_first_active(top20/top50/all)=9/28/96, avg_neural_sim_top20=0.4311, avg_hybrid_val_top20=2.0109, sem_top50_mean=0.471, sem_top50_p95=0.519, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.72, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.385/0.419/0.600, forced_in_top20/top50=16/42, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=1/1, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.600/0.600/0.600, high_sim_override_sim_min/mean/max(all)=0.600/0.600/0.600, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=154, top20_off_type=2, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=101, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=156, demo_override_top20=6, blocked_overlap=539, blocked_low_sim=247, bonus_fired=1, bonus_mean=0.00244, bonus_max=0.04880, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/6, theme_bonus_mean(top20/top50)=0.00040/0.00024, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 619 | 26.1% |
| blocked_low_semantic_sim | 141 | 6.0% |
| blocked_low_overlap | 268 | 11.3% |
| blocked_other_admission | 765 | 32.3% |
| missing_semantic_vector | 15 | 0.6% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 560 | 23.6% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc | overlap | 1.00 | 0.600 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc |  | 8.17 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 34467 | Theatre of Darkness: Yamishibai 4 | TV | 5.81 |  |  |
| 4 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 5 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 6 | 40748 | Jujutsu Kaisen |  | 8.53 |  |  |
| 7 | 7619 | Spooky Kitaro | TV | 6.79 |  |  |
| 8 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 9 | 34019 | Tsugumomo | TV | 7.03 |  |  |
| 10 | 60543 | Dan Da Dan Season 2 |  | 8.47 |  |  |
| 11 | 37520 | Dororo |  | 8.26 |  |  |
| 12 | 44511 | Chainsaw Man |  | 8.44 |  |  |
| 13 | 38759 | The Helpful Fox Senko-san |  | 7.31 |  |  |
| 14 | 12391 | Mouretsu Atarou (1990) | TV |  |  |  |
| 15 | 58811 | Tougen Anki |  | 6.58 |  |  |
| 16 | 30664 | Artificial Paradise | Movie | 4.55 |  |  |
| 17 | 5760 | Dororo | TV | 7.27 |  |  |
| 18 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 19 | 27757 | Anisava | TV | 5.52 |  |  |
| 20 | 30947 | Kurayami Santa | TV | 5.16 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2980, stage0_after_hygiene=2729, stage0_after_cap=2729, stage0_src_raw(neural/meta_strict/pop)=1500/1802/100, stage1_universe=2729, universe_match=True, shortlist=600/600, scored=562, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=95.0%, top20_from_meta_strict=55.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.883, content_first_alpha=0.70, content_first_active(top20/top50/all)=10/31/109, avg_neural_sim_top20=0.3993, avg_hybrid_val_top20=1.7344, sem_top50_mean=0.469, sem_top50_p95=0.531, sem_top50_overlap_mean=0.420, sem_top50_any_match=0.80, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.377/0.411/0.556, forced_in_top20/top50=15/38, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=0/0, top50_franchise_like(before/after)=0/0, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=137, top20_off_type=0, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=110, theme_override=1, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=233, demo_override_top20=3, blocked_overlap=663, blocked_low_sim=400, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/8, theme_bonus_mean(top20/top50)=0.00030/0.00032, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=11, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 732 | 26.8% |
| blocked_low_semantic_sim | 281 | 10.3% |
| blocked_low_overlap | 339 | 12.4% |
| blocked_other_admission | 810 | 29.7% |
| missing_semantic_vector | 5 | 0.2% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 562 | 20.6% |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 3 | 8685 | Ryuuichi Manga Gekijou Onbu Obake | TV |  |  |  |
| 4 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 5 | 38000 | Demon Slayer: Kimetsu no Yaiba |  | 8.42 |  |  |
| 6 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 7 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 8 | 47163 | My Isekai Life: I Gained a Second Character Class and Became the Strongest Sage in the World |  | 6.33 |  |  |
| 9 | 52830 | I Got a Cheat Skill in Another World and Became Unrivaled in The Real World, Too |  | 6.34 |  |  |
| 10 | 19989 | Tatakae! Osper | TV |  |  |  |
| 11 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 12 | 33506 | Blue Exorcist: Kyoto Saga | TV | 7.34 |  |  |
| 13 | 39071 | The Demon Girl Next Door |  | 7.63 |  |  |
| 14 | 27783 | Sword Gai The Animation | ONA | 5.74 |  |  |
| 15 | 29089 | Monster List | ONA | 6.80 |  |  |
| 16 | 60543 | Dan Da Dan Season 2 |  | 8.47 |  |  |
| 17 | 33253 | Ajin: Demi-Human 2nd Season | TV | 7.55 |  |  |
| 18 | 34451 | Blood Blockade Battlefront & Beyond | TV | 7.77 |  |  |
| 19 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 20 | 34467 | Theatre of Darkness: Yamishibai 4 | TV | 5.81 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=4822, stage0_after_hygiene=4403, stage0_after_cap=3000, stage0_src_raw(neural/meta_strict/pop)=1500/4029/100, stage1_universe=3000, universe_match=True, shortlist=600/600, scored=567, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=100.0%, top20_from_meta_strict=100.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.863, content_first_alpha=0.70, content_first_active(top20/top50/all)=11/32/158, avg_neural_sim_top20=0.4342, avg_hybrid_val_top20=1.7308, sem_top50_mean=0.463, sem_top50_p95=0.532, sem_top50_overlap_mean=0.680, sem_top50_any_match=0.68, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.409/0.652, forced_in_top20/top50=16/34, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=5/5, top50_franchise_like(before/after)=7/7, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.609/0.609/0.609, high_sim_override_sim_min/mean/max(all)=0.609/0.609/0.609, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=99, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=416, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=181, demo_override_top20=0, blocked_overlap=554, blocked_low_sim=392, bonus_fired=3, bonus_mean=0.01024, bonus_max=0.07920, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=9/18, theme_bonus_mean(top20/top50)=0.00090/0.00072, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=16, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=7, top50_moved_meta=17, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 1306 | 43.5% |
| blocked_low_semantic_sim | 108 | 3.6% |
| blocked_low_overlap | 442 | 14.7% |
| blocked_other_admission | 574 | 19.1% |
| missing_semantic_vector | 3 | 0.1% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 567 | 18.9% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 38408 | My Hero Academia Season 4 | overlap | 1.00 | 0.652 |
| 44200 | My Hero Academia: World Heroes' Mission | overlap | 1.00 | 0.609 |
| 33486 | My Hero Academia Season 2 | overlap | 1.00 | 0.475 |
| 53447 | To Be Hero X | overlap | 0.50 | 0.476 |
| 60593 | My Hero Academia: Vigilantes | overlap | 1.00 | 0.425 |
| 54789 | My Hero Academia Season 7 | overlap | 1.00 | 0.378 |
| 56854 | Hero Without a Class: Who Even Needs Skills?! | overlap | 0.50 | 0.371 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 38408 | My Hero Academia Season 4 |  | 7.86 |  |  |
| 2 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 3 | 31339 | Drifters | TV | 7.88 |  |  |
| 4 | 44200 | My Hero Academia: World Heroes' Mission |  | 7.58 |  |  |
| 5 | 21491 | Ninjaman Ippei | TV | 6.03 |  |  |
| 6 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 7 | 33486 | My Hero Academia Season 2 | TV | 8.05 |  |  |
| 8 | 39463 | Gleipnir |  | 6.95 |  |  |
| 9 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 10 | 53447 | To Be Hero X |  | 8.72 |  |  |
| 11 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 12 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 13 | 47162 | The Executioner and Her Way of Life |  | 6.76 |  |  |
| 14 | 52741 | Undead Unluck |  | 7.75 |  |  |
| 15 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 16 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 17 | 60593 | My Hero Academia: Vigilantes |  | 7.60 |  |  |
| 18 | 54918 | Tokyo Revengers: Tenjiku Arc |  | 7.82 |  |  |
| 19 | 51009 | Jujutsu Kaisen Season 2 |  | 8.72 |  |  |
| 20 | 42249 | Tokyo Revengers |  | 7.84 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2769, stage0_after_hygiene=2504, stage0_after_cap=2504, stage0_src_raw(neural/meta_strict/pop)=1500/1880/100, stage1_universe=2504, universe_match=True, shortlist=600/600, scored=557, top20_in_stage0=20, top50_in_stage0=50, top20_from_neural=80.0%, top20_from_meta_strict=100.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.933, content_first_alpha=0.70, content_first_active(top20/top50/all)=4/14/96, avg_neural_sim_top20=0.4113, avg_hybrid_val_top20=2.6499, sem_top50_mean=0.493, sem_top50_p95=0.557, sem_top50_overlap_mean=0.900, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.366/0.410/0.857, forced_in_top20/top50=11/32, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=3/3, top50_franchise_like(before/after)=4/4, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.857/0.857/0.857, high_sim_override_sim_min/mean/max(all)=0.857/0.857/0.857, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=100, top20_off_type=2, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=234, demo_override_top20=0, blocked_overlap=673, blocked_low_sim=406, bonus_fired=7, bonus_mean=0.01028, bonus_max=0.07520, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=12/30, theme_bonus_mean(top20/top50)=0.00120/0.00120, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=4, top50_moved_meta=11, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Why not scored (Stage 0 universe):

| reason | count | % of stage0_after_cap |
|---|---:|---:|
| not_in_stage1_shortlist | 280 | 11.2% |
| blocked_low_semantic_sim | 353 | 14.1% |
| blocked_low_overlap | 560 | 22.4% |
| blocked_other_admission | 749 | 29.9% |
| missing_semantic_vector | 5 | 0.2% |
| dropped_by_quality_filters | 0 | 0.0% |
| scored | 557 | 22.2% |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 29755 | Haikyu!! the Movie: The End and the Beginning | overlap | 1.00 | 0.857 |
| 40776 | Haikyu!! To the Top 2nd-cour | overlap | 1.00 | 0.513 |
| 38883 | Haikyu!! To the Top | overlap | 1.00 | 0.512 |
| 25303 | Haikyu!!: Lev Appears! | overlap | 1.00 | 0.581 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 29755 | Haikyu!! the Movie: The End and the Beginning | Movie | 8.10 |  |  |
| 2 | 9905 | Captain (TV) | TV | 6.45 |  |  |
| 3 | 32871 | Winter Cup Highlights Episode 3 – Winter Cup Highlights -Crossing the Door- | Movie | 7.83 |  |  |
| 4 | 40776 | Haikyu!! To the Top 2nd-cour |  | 8.56 |  |  |
| 5 | 38883 | Haikyu!! To the Top |  | 8.37 |  |  |
| 6 | 37403 | Ahiru no Sora |  | 7.26 |  |  |
| 7 | 33031 | Scorching Ping Pong Girls | TV | 7.05 |  |  |
| 8 | 23011 | Otoko Doahou! Koushien | TV |  |  |  |
| 9 | 7479 | Karate Master | TV | 6.64 |  |  |
| 10 | 11919 | Zoku Attacker You! Kin Medal e no Michi | TV | 6.25 |  |  |
| 11 | 5834 | Kyojin no Hoshi | TV | 6.91 |  |  |
| 12 | 11857 | Judo Sanka | TV | 6.19 |  |  |
| 13 | 25967 | Bernard | TV | 5.81 |  |  |
| 14 | 19947 | Ikkyuu-san (1978) | TV | 6.25 |  |  |
| 15 | 16650 | Pro Golfer Saru (TV) | TV | 6.35 |  |  |
| 16 | 17893 | Cheonbangjichuk Hani | TV | 6.45 |  |  |
| 17 | 20237 | Anime Document: München e no Michi | TV |  |  |  |
| 18 | 17671 | Animal 1 | TV | 6.01 |  |  |
| 19 | 10360 | Kinniku Banzuke: Kongou-kun no Daibouken! | TV | 4.99 |  |  |
| 20 | 3825 | Dokaben | TV | 6.15 |  |  |

