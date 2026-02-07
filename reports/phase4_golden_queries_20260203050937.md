# Phase 4 — Golden Queries Report

Generated: 2026-02-03T05:12:53.259980+00:00
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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=5306, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=971/2481/281/102, stage1_universe=3000, shortlist=600/600, scored=533, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=90.0%, top20_from_genre_or_theme=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.923, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/0, avg_neural_sim_top20=0.3956, avg_hybrid_val_top20=3.3830, sem_top50_mean=0.484, sem_top50_p95=0.550, sem_top50_overlap_mean=0.510, sem_top50_any_match=0.98, top20_pools(A/B/C)=18/2/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.398/0.429/0.577, forced_in_top20/top50=14/26, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=150, top20_off_type=10, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=180, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[seinen], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=637, blocked_low_sim=480, bonus_fired=3, bonus_mean=0.00105, bonus_max=0.00990, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/14, theme_bonus_mean(top20/top50)=0.00017/0.00048, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=6, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=5, top50_moved_meta=15, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 27899 | Tokyo Ghoul √A | overlap | 1.00 | 0.490 |
| 30458 | Tokyo Ghoul: Jack | overlap | 1.00 | 0.563 |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 40 | 33 | Berserk | 0.667 | 0.00200 |
| 45 | 226 | Elfen Lied | 0.667 | 0.00200 |
| 46 | 384 | Gantz | 0.667 | 0.00200 |
| 38 | 395 | Gantz: Second Stage | 0.667 | 0.00200 |
| 26 | 10620 | The Future Diary | 0.667 | 0.00200 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 30412 | Zombie Brother | ONA | 6.51 |  |  |
| 4 | 8145 | Spooky Kitaro: Japan Explodes!! | Movie | 6.49 |  |  |
| 5 | 8146 | Spooky Kitaro: Giant Sea Monster | Movie | 6.17 |  |  |
| 6 | 23723 | Teppen | OVA |  |  |  |
| 7 | 19533 | Fujiko Fujio A no Mumako | TV Special | 5.47 |  |  |
| 8 | 27495 | Sore Ike! Anpanman: Kaiketsu Naganegiman to Yakisobapanman | Movie | 6.04 |  |  |
| 9 | 25815 | Yokohama Bakkure-tai | OVA |  |  |  |
| 10 | 5760 | Dororo | TV | 7.27 |  |  |
| 11 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 12 | 9882 | High School Mystery: Gakuen Nanafushigi | TV | 6.39 |  |  |
| 13 | 20083 | Doteraman | TV | 5.77 |  |  |
| 14 | 27899 | Tokyo Ghoul √A | TV | 7.03 |  |  |
| 15 | 10237 | Ki Fighter | TV |  |  |  |
| 16 | 4923 | Akai Hayate | OVA | 5.31 |  |  |
| 17 | 8353 | Ketsuinu | TV |  |  |  |
| 18 | 9824 | Jigokudou Reikai Tsuushin | OVA | 6.10 |  |  |
| 19 | 20 | Naruto | TV | 8.01 |  |  |
| 20 | 30663 | Two Lovely Maid | ONA | 4.14 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=5192, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=978/2513/360/116, stage1_universe=3000, shortlist=600/600, scored=512, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=95.0%, top20_from_genre_or_theme=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.828, content_first_alpha=0.70, content_first_active(top20/top50/all)=1/1/1, avg_neural_sim_top20=0.3390, avg_hybrid_val_top20=3.6892, sem_top50_mean=0.432, sem_top50_p95=0.520, sem_top50_overlap_mean=0.355, sem_top50_any_match=0.84, top20_pools(A/B/C)=19/1/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.307/0.354/0.611, forced_in_top20/top50=19/33, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=145, top20_off_type=8, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=92, demo_override_top20=0, blocked_overlap=289, blocked_low_sim=932, bonus_fired=2, bonus_mean=0.00399, bonus_max=0.07680, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/11, theme_bonus_mean(top20/top50)=0.00033/0.00037, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=4, top50_moved_meta=14, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 25777 | Attack on Titan Season 2 | overlap | 1.00 | 0.611 |
| 35760 | Attack on Titan Season 3 | overlap | 1.00 | 0.505 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 4 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 5 | 25777 | Attack on Titan Season 2 | TV | 8.53 |  |  |
| 6 | 4933 | The White Whale of Mu | TV | 6.32 |  |  |
| 7 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 8 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 9 | 33220 | Summer's Puke is Winter's Delight | Movie | 3.84 |  |  |
| 10 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 11 | 33266 | NANOCORE | ONA | 5.97 |  |  |
| 12 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 13 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 14 | 3846 | Microid S | TV | 6.00 |  |  |
| 15 | 16822 | Captain of Cosmos | Movie | 3.52 |  |  |
| 16 | 17621 | Ultraman Super Fighter Legend | OVA | 5.92 |  |  |
| 17 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 18 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 19 | 7867 | Gon | TV | 5.98 |  |  |
| 20 | 5581 | Kaitei Daisensou: Ai no 20,000 Miles | TV Special | 5.20 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2119, stage0_after_hygiene=1973, stage0_src(neural/genre/theme/pop)=971/1065/278/197, stage1_universe=1973, shortlist=600/600, scored=551, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=60.0%, top20_from_genre_or_theme=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.906, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/1, avg_neural_sim_top20=0.3804, avg_hybrid_val_top20=3.6226, sem_top50_mean=0.488, sem_top50_p95=0.546, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.66, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.417/0.703, forced_in_top20/top50=10/24, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=1/1, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.703/0.703/0.703, high_sim_override_sim_min/mean/max(all)=0.703/0.703/0.703, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=122, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=111, demo_override_top20=0, blocked_overlap=342, blocked_low_sim=236, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00640, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=6/19, theme_bonus_mean(top20/top50)=0.00060/0.00076, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=8, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 2994 | Death Note: Relight | overlap | 1.00 | 0.703 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30463 | Horror News | ONA | 5.43 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 4 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 5 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 6 | 24663 | Dororonpa! | TV | 6.18 |  |  |
| 7 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 8 | 33144 | The Hell (Two Kinds of Life) | Movie | 5.73 |  |  |
| 9 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 10 | 28991 | Ninja & Soldier | Movie | 5.72 |  |  |
| 11 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 12 | 19533 | Fujiko Fujio A no Mumako | TV Special | 5.47 |  |  |
| 13 | 32071 | Gantz:O | Movie | 7.40 |  |  |
| 14 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 15 | 9345 | Gakkou no Kowai Uwasa Shin: Hanako-san ga Kita!! | TV | 6.14 |  |  |
| 16 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 17 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 18 | 2246 | Mononoke | TV | 8.41 |  |  |
| 19 | 2366 | Touma Kishinden Oni | TV | 6.28 |  |  |
| 20 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=4750, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=940/2422/174/80, stage1_universe=3000, shortlist=600/600, scored=507, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=100.0%, top20_from_genre_or_theme=35.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.794, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/0, avg_neural_sim_top20=0.3685, avg_hybrid_val_top20=5.1172, sem_top50_mean=0.410, sem_top50_p95=0.514, sem_top50_overlap_mean=0.680, sem_top50_any_match=1.00, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.321/0.353/0.683, forced_in_top20/top50=20/40, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=1/1, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/1, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.612/0.612/0.612, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=146, top20_off_type=13, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=45, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=555, blocked_low_sim=809, bonus_fired=1, bonus_mean=0.00029, bonus_max=0.00580, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=1/7, theme_bonus_mean(top20/top50)=0.00010/0.00028, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Stage 0 audit:

| seed title | stage0_after_hygiene_size | % neural | % genre/theme | % popularity |
|---|---:|---:|---:|---:|
| Steins;Gate | 3000 | 31.3% | 81.0% | 2.7% |

Stage 0 details:

| metric | value |
|---|---:|
| stage0_pool_raw | 4750 |
| stage0_after_hygiene_size | 3000 |
| stage0_sources(neural/genre/theme/pop) | 940/2422/174/80 |
| stage1_candidate_universe_count | 3000 |
| final_scored_candidate_count | 507 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 20 |

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 30484 | Steins;Gate 0 | overlap | 1.00 | 0.683 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30484 | Steins;Gate 0 | TV | 8.55 |  |  |
| 2 | 31238 | Stitch! Perfect Memory | TV Special | 5.74 |  |  |
| 3 | 31517 | Ohayou Ninja-tai Gatchaman | TV | 5.46 |  |  |
| 4 | 6727 | Mechanical Boy Dotakon | TV | 5.85 |  |  |
| 5 | 29729 | Peeping Life x I-O Data: Quiz!! Input Output | ONA | 5.28 |  |  |
| 6 | 32149 | Tatsunoko Pro x Peeping Life | ONA | 5.58 |  |  |
| 7 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 8 | 6636 | Super High Speed Galvion | TV | 5.84 |  |  |
| 9 | 29795 | The Soba Flower of Mt. Oni | Movie | 5.75 |  |  |
| 10 | 29796 | Oshizuka ni | Movie | 5.35 |  |  |
| 11 | 29797 | Panache the Squirrel | Movie | 5.62 |  |  |
| 12 | 29799 | Tabi wa Michizure Yo wa Nasake | Movie | 5.13 |  |  |
| 13 | 29587 | Home My Home | Movie | 5.21 |  |  |
| 14 | 30905 | Owanko | ONA | 5.56 |  |  |
| 15 | 28815 | Bamboo Blade: CM Fanfu-Fufe-Fo | CM | 5.52 |  |  |
| 16 | 29141 | Atama wa Tsukaiyou. Card mo Tsukaiyou. | CM | 5.34 |  |  |
| 17 | 29798 | From Cherry Blossoms With Love | Movie | 5.26 |  |  |
| 18 | 29800 | Urameshi Denwa | Movie | 5.07 |  |  |
| 19 | 29793 | The Strong Bridge | Movie | 5.45 |  |  |
| 20 | 6889 | Time Bokan Series: Zenderman | TV | 5.84 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=4869, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=968/2740/488/108, stage1_universe=3000, shortlist=600/600, scored=544, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=80.0%, top20_from_genre_or_theme=100.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.793, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/0, avg_neural_sim_top20=0.3106, avg_hybrid_val_top20=3.4585, sem_top50_mean=0.423, sem_top50_p95=0.499, sem_top50_overlap_mean=0.673, sem_top50_any_match=1.00, top20_pools(A/B/C)=16/4/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.311/0.355/0.522, forced_in_top20/top50=12/30, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=0/0, top50_franchise_like(before/after)=0/0, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=172, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=92, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=368, blocked_low_sim=839, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/9, theme_bonus_mean(top20/top50)=0.00020/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=7, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=4, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Stage 0 audit:

| seed title | stage0_after_hygiene_size | % neural | % genre/theme | % popularity |
|---|---:|---:|---:|---:|
| Cowboy Bebop | 3000 | 32.3% | 91.9% | 3.6% |

Stage 0 details:

| metric | value |
|---|---:|
| stage0_pool_raw | 4869 |
| stage0_after_hygiene_size | 3000 |
| stage0_sources(neural/genre/theme/pop) | 968/2740/488/108 |
| stage1_candidate_universe_count | 3000 |
| final_scored_candidate_count | 544 |
| top20_in_stage0_count | 20 |
| top50_in_stage0_count | 20 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 28673 | Die Now | ONA | 6.37 |  |  |
| 2 | 2697 | High Speed Jessie | OVA | 6.10 |  |  |
| 3 | 11405 | Skyers 5 | TV | 5.92 |  |  |
| 4 | 22997 | Shin Skyers 5 | TV |  |  |  |
| 5 | 16159 | Mirai Kara Kita Shounen Super Jetter | TV | 5.86 |  |  |
| 6 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 7 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 8 | 7900 | Super Child | Movie | 2.92 |  |  |
| 9 | 16822 | Captain of Cosmos | Movie | 3.52 |  |  |
| 10 | 27455 | Pororo the Little Penguin 3 | TV | 5.73 |  |  |
| 11 | 12139 | Wanpaku Tanteidan | TV | 6.10 |  |  |
| 12 | 20083 | Doteraman | TV | 5.77 |  |  |
| 13 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 14 | 9781 | Hyouga Senshi Gaislugger | TV | 5.70 |  |  |
| 15 | 4240 | Galactic Cyclone Braiger | TV | 6.66 |  |  |
| 16 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 17 | 8553 | Time Bokan Series: Time Patroltai Otasukeman | TV | 6.27 |  |  |
| 18 | 9500 | Starlight Scramble Renai Kouhosei | OVA | 5.58 |  |  |
| 19 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 20 | 2769 | Galactic Patrol Lensman | TV | 6.28 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=7046, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=965/2708/196/85, stage1_universe=3000, shortlist=600/600, scored=542, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=95.0%, top20_from_genre_or_theme=90.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.712, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/0, avg_neural_sim_top20=0.3083, avg_hybrid_val_top20=3.3445, sem_top50_mean=0.377, sem_top50_p95=0.476, sem_top50_overlap_mean=0.535, sem_top50_any_match=0.94, top20_pools(A/B/C)=19/1/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.253/0.294/0.828, forced_in_top20/top50=14/28, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.741/0.741/0.741, high_sim_override_sim_min/mean/max(all)=0.741/0.741/0.741, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=162, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=72, demo_override_top20=4, blocked_overlap=62, blocked_low_sim=1218, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00610, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/4, theme_bonus_mean(top20/top50)=0.00020/0.00016, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=6, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 121 | Fullmetal Alchemist | overlap | 0.67 | 0.828 |
| 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | overlap | 0.67 | 0.741 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31966 | Sword Gai | ONA | 5.61 |  |  |
| 2 | 8777 | Julie the Wild Rose | TV | 6.00 |  |  |
| 3 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 4 | 3819 | Nozomi In The Sun | TV | 6.43 |  |  |
| 5 | 22065 | The Adventures of T-Rex | TV |  |  |  |
| 6 | 9811 | Hanasaka Tenshi Tenten-kun | TV |  |  |  |
| 7 | 19467 | Revbahaf Wang-gug Jaegeon-soelgi | TV |  |  |  |
| 8 | 19311 | Turuturutu Narongi | TV |  |  |  |
| 9 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 10 | 30862 | Woman Who Stole Fingers | Movie | 5.85 |  |  |
| 11 | 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | Movie | 7.50 |  |  |
| 12 | 5476 | Marvelous Melmo | TV | 6.14 |  |  |
| 13 | 9613 | Big X | TV | 6.07 |  |  |
| 14 | 22613 | Keroppi in the Adventures of the Coward Prince | OVA | 5.74 |  |  |
| 15 | 5581 | Kaitei Daisensou: Ai no 20,000 Miles | TV Special | 5.20 |  |  |
| 16 | 20 | Naruto | TV | 8.01 |  |  |
| 17 | 2314 | Fly! Peek the Whale | Movie | 6.16 |  |  |
| 18 | 4597 | Kouya no Shounen Isamu | TV | 6.30 |  |  |
| 19 | 6771 | Mock & Sweet | TV | 6.23 |  |  |
| 20 | 25605 | The Tree of Courage | OVA |  |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=5796, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=966/2557/167/89, stage1_universe=3000, shortlist=600/600, scored=579, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=70.0%, top20_from_genre_or_theme=95.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.991, content_first_alpha=0.70, content_first_active(top20/top50/all)=1/1/1, avg_neural_sim_top20=0.4185, avg_hybrid_val_top20=3.8272, sem_top50_mean=0.542, sem_top50_p95=0.616, sem_top50_overlap_mean=0.607, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.431/0.470/0.672, forced_in_top20/top50=9/24, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=3/3, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/2/3, high_sim_override_sim_min/mean/max(top50)=0.603/0.621/0.638, high_sim_override_sim_min/mean/max(all)=0.603/0.623/0.638, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=130, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=330, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=176, demo_override_top20=5, blocked_overlap=538, blocked_low_sim=429, bonus_fired=2, bonus_mean=0.00282, bonus_max=0.04800, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/10, theme_bonus_mean(top20/top50)=0.00030/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=4, top50_moved_meta=8, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 1735 | Naruto Shippuden | overlap | 1.00 | 0.672 |
| 10589 | Naruto Shippuden the Movie 5: Blood Prison | overlap | 1.00 | 0.638 |
| 13667 | Naruto Shippuden the Movie 6: Road to Ninja | overlap | 1.00 | 0.603 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 30463 | Horror News | ONA | 5.43 |  |  |
| 4 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 5 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 6 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 7 | 9768 | Shima Shima Tora no Shimajirou | TV | 5.93 |  |  |
| 8 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 9 | 1735 | Naruto Shippuden | TV | 8.28 |  |  |
| 10 | 5923 | Utsunomiko: Heaven Chapter | OVA | 6.06 |  |  |
| 11 | 5760 | Dororo | TV | 7.27 |  |  |
| 12 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 13 | 28991 | Ninja & Soldier | Movie | 5.72 |  |  |
| 14 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 15 | 7479 | Karate Master | TV | 6.64 |  |  |
| 16 | 9691 | Kyomu Senshi Miroku | OVA | 5.66 |  |  |
| 17 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 18 | 29089 | Monster List | ONA | 6.80 |  |  |
| 19 | 5292 | Getter Robo Go | TV | 6.27 |  |  |
| 20 | 4049 | Pandalian | TV | 6.27 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=5659, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=957/2690/0/68, stage1_universe=3000, shortlist=600/600, scored=577, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=95.0%, top20_from_genre_or_theme=100.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.902, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/2/2, avg_neural_sim_top20=0.3301, avg_hybrid_val_top20=3.4285, sem_top50_mean=0.466, sem_top50_p95=0.608, sem_top50_overlap_mean=0.713, sem_top50_any_match=0.94, top20_pools(A/B/C)=17/3/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.279/0.335/0.722, forced_in_top20/top50=12/26, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=2/2, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=2/2/5, high_sim_override_sim_min/mean/max(top50)=0.608/0.665/0.722, high_sim_override_sim_min/mean/max(all)=0.600/0.631/0.722, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=186, top20_off_type=5, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=61, demo_override_top20=1, blocked_overlap=117, blocked_low_sim=1096, bonus_fired=4, bonus_mean=0.00762, bonus_max=0.06769, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=11, top50_moved_meta=15, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 60022 | One Piece Fan Letter | overlap | 1.00 | 0.722 |
| 38234 | One Piece: Stampede | overlap | 1.00 | 0.608 |

Franchise-cap audit (One Piece): top10 by title_overlap

| anime_id | Title | title_overlap | franchise_like | reason |
|---:|---|---:|:---:|---|
| 38234 | One Piece: Stampede | 1.00 | Y | overlap |
| 60022 | One Piece Fan Letter | 1.00 | Y | overlap |
| 20 | Naruto | 0.00 | N |  |
| 121 | Fullmetal Alchemist | 0.00 | N |  |
| 1482 | D.Gray-man | 0.00 | N |  |
| 1818 | Claymore | 0.00 | N |  |
| 2503 | Nangoku Shounen Papuwa-kun | 0.00 | N |  |
| 2740 | Monkey Turn | 0.00 | N |  |
| 2769 | Galactic Patrol Lensman | 0.00 | N |  |
| 4049 | Pandalian | 0.00 | N |  |

Content-first audit: top10 items by neural_sim (rank movement)

| anime_id | Title | neural_sim | hybrid_val | score_before | score_after | rank_before | rank_after |
|---:|---|---:|---:|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter | 0.7222 | 0.00000 | 1.00518 | 1.53103 | 61 | 5 |
| 4155 | One Piece Film: Strong World | 0.6178 | 0.07884 | 0.96464 | 0.96464 | 77 | 78 |
| 38234 | One Piece: Stampede | 0.6082 | 0.00000 | 0.95390 | 1.39807 | 82 | 14 |
| 5252 | One Piece: Romance Dawn Story | 0.6072 | -0.06775 | 0.93114 | 0.93114 | 93 | 93 |
| 464 | One Piece: Baron Omatsuri and the Secret Island | 0.6000 | -0.05454 | 0.93337 | 0.93337 | 92 | 92 |
| 12859 | One Piece Film: Z | 0.5993 | 0.51676 | 1.05432 | 1.05432 | 51 | 53 |
| 31490 | One Piece Film: Gold | 0.5806 | -0.03002 | 0.87969 | 0.87969 | 115 | 115 |
| 459 | One Piece: The Movie | 0.5802 | -0.04647 | 0.91683 | 0.91683 | 101 | 101 |
| 462 | One Piece: Dead End Adventure | 0.5461 | -0.01895 | 0.74768 | 0.74768 | 195 | 195 |
| 460 | One Piece: Clockwork Island Adventure | 0.5427 | 0.11849 | 0.77859 | 0.77859 | 178 | 178 |

Forced-neural top10 neighbors (by similarity):

| anime_id | Title | Type | sim | in_shortlist | rank@50 | in_top20 |
|---:|---|---|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter |  | 0.7222 | True | 5 | True |
| 4155 | One Piece Film: Strong World | Movie | 0.6178 | True |  | False |
| 38234 | One Piece: Stampede |  | 0.6082 | True | 14 | True |
| 5252 | One Piece: Romance Dawn Story | OVA | 0.6072 | True |  | False |
| 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 0.6000 | True |  | False |
| 12859 | One Piece Film: Z | Movie | 0.5993 | True |  | False |
| 31490 | One Piece Film: Gold | Movie | 0.5806 | True |  | False |
| 459 | One Piece: The Movie | Movie | 0.5802 | True |  | False |
| 462 | One Piece: Dead End Adventure | Movie | 0.5461 | True |  | False |
| 460 | One Piece: Clockwork Island Adventure | Movie | 0.5427 | True |  | False |

Stage 2 high-sim override audit (top10 neural neighbors):

| anime_id | sim | type | final_rank | score | Δ_to_top20_cutoff | hybrid | overlap | coverage | neural_bonus | penalty_before | penalty_after | stage2_override |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 60022 | 0.7222 |  | 5 | 1.53103 | -0.21075 | 0.00000 | 1.000 | 1.000 | 0.16527 | -0.01000 | 0.00000 | True |
| 4155 | 0.6178 | Movie | 78 | 0.96464 | 0.35565 | 0.07884 | 1.000 | 1.000 | 0.12874 | -0.01000 | 0.00000 | True |
| 38234 | 0.6082 |  | 14 | 1.39807 | -0.07778 | 0.00000 | 1.000 | 1.000 | 0.12538 | -0.01000 | 0.00000 | True |
| 5252 | 0.6072 | OVA | 93 | 0.93114 | 0.38914 | -0.06775 | 1.000 | 1.000 | 0.12503 | -0.01000 | 0.00000 | True |
| 464 | 0.6000 | Movie | 92 | 0.93337 | 0.38692 | -0.05454 | 1.000 | 1.000 | 0.12250 | -0.01000 | 0.00000 | True |
| 12859 | 0.5993 | Movie | 53 | 1.05432 | 0.26596 | 0.51676 | 1.000 | 1.000 | 0.12226 | -0.01000 | -0.01000 | False |
| 31490 | 0.5806 | Movie | 115 | 0.87969 | 0.44059 | -0.03002 | 1.000 | 1.000 | 0.11572 | -0.01000 | -0.01000 | False |
| 459 | 0.5802 | Movie | 101 | 0.91683 | 0.40345 | -0.04647 | 1.000 | 1.000 | 0.11557 | -0.01000 | -0.01000 | False |
| 462 | 0.5461 | Movie | 195 | 0.74768 | 0.57260 | -0.01895 | 1.000 | 1.000 | 0.00000 | -0.05389 | -0.05389 | False |
| 460 | 0.5427 | Movie | 178 | 0.77859 | 0.54170 | 0.11849 | 1.000 | 1.000 | 0.00000 | -0.05726 | -0.05726 | False |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 33 | 20 | Naruto |  | 0.00000 |
| 46 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 44 | 1482 | D.Gray-man |  | 0.00000 |
| 45 | 1818 | Claymore |  | 0.00000 |
| 19 | 2503 | Nangoku Shounen Papuwa-kun |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 2 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 3 | 30738 | Air Bound | Movie | 5.63 |  |  |
| 4 | 5071 | Croket! | TV | 6.90 |  |  |
| 5 | 60022 | One Piece Fan Letter |  | 9.03 |  |  |
| 6 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 7 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 8 | 15579 | Shinkai Densetsu Meremanoid | TV | 5.66 |  |  |
| 9 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 10 | 33484 | Shiroi Zou | Movie | 5.68 |  |  |
| 11 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 12 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 13 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 14 | 38234 | One Piece: Stampede |  | 8.18 |  |  |
| 15 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 16 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 17 | 19505 | Kaizoku Ouji | TV | 5.90 |  |  |
| 18 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 19 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 20 | 23015 | Chief Joker | TV |  |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=4612, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=972/2423/281/140, stage1_universe=3000, shortlist=600/600, scored=550, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=70.0%, top20_from_genre_or_theme=85.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.861, content_first_alpha=0.70, content_first_active(top20/top50/all)=1/1/1, avg_neural_sim_top20=0.3702, avg_hybrid_val_top20=3.4643, sem_top50_mean=0.471, sem_top50_p95=0.519, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.72, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.385/0.419/0.600, forced_in_top20/top50=12/29, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=1/1, top50_franchise_like(before/after)=1/1, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.600/0.600/0.600, high_sim_override_sim_min/mean/max(all)=0.600/0.600/0.600, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=154, top20_off_type=9, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=211, demo_override_top20=7, blocked_overlap=496, blocked_low_sim=460, bonus_fired=1, bonus_mean=0.00244, bonus_max=0.04880, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/9, theme_bonus_mean(top20/top50)=0.00020/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=11, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc | overlap | 1.00 | 0.600 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 2 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 3 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 4 | 30664 | Artificial Paradise | Movie | 4.55 |  |  |
| 5 | 19989 | Tatakae! Osper | TV |  |  |  |
| 6 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 7 | 31978 | Crayon Shin-chan: Fast Asleep! The Great Assault on the Dreaming World! | Movie | 7.18 |  |  |
| 8 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 9 | 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc |  | 8.17 |  |  |
| 10 | 7619 | Spooky Kitaro | TV | 6.79 |  |  |
| 11 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 12 | 23639 | Kappa Kawatarou | Movie | 5.37 |  |  |
| 13 | 6829 | Over a Drink | Movie | 5.06 |  |  |
| 14 | 2740 | Monkey Turn | TV | 6.43 |  |  |
| 15 | 27757 | Anisava | TV | 5.52 |  |  |
| 16 | 9349 | Shizukanaru Don: Yakuza Side Story | OVA | 5.81 |  |  |
| 17 | 9498 | Naniwa Yuukyouden | OVA | 5.90 |  |  |
| 18 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 19 | 17467 | Otoko Ippiki Gaki Daishou | TV | 6.46 |  |  |
| 20 | 23699 | Kumo ni Noru | OVA | 5.44 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=5045, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=963/2488/337/147, stage1_universe=3000, shortlist=600/600, scored=558, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=65.0%, top20_from_genre_or_theme=100.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.883, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/1, avg_neural_sim_top20=0.3416, avg_hybrid_val_top20=3.3388, sem_top50_mean=0.469, sem_top50_p95=0.531, sem_top50_overlap_mean=0.420, sem_top50_any_match=0.80, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.377/0.411/0.556, forced_in_top20/top50=10/19, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=0/0, top50_franchise_like(before/after)=0/0, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=137, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=93, theme_override=1, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=194, demo_override_top20=7, blocked_overlap=495, blocked_low_sim=503, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/5, theme_bonus_mean(top20/top50)=0.00020/0.00020, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=11, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 3 | 8685 | Ryuuichi Manga Gekijou Onbu Obake | TV |  |  |  |
| 4 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 5 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 6 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 7 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 8 | 19989 | Tatakae! Osper | TV |  |  |  |
| 9 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 10 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 11 | 12401 | The Chohjotai | OVA | 5.51 |  |  |
| 12 | 12833 | Ushiro no Hyakutarou | OVA |  |  |  |
| 13 | 9613 | Big X | TV | 6.07 |  |  |
| 14 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 15 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 16 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 17 | 29089 | Monster List | ONA | 6.80 |  |  |
| 18 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 19 | 3023 | Mami the Psychic | TV | 6.49 |  |  |
| 20 | 5760 | Dororo | TV | 7.27 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=4575, stage0_after_hygiene=3000, stage0_src(neural/genre/theme/pop)=971/2328/647/112, stage1_universe=3000, shortlist=600/600, scored=546, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=80.0%, top20_from_genre_or_theme=90.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.863, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/2/2, avg_neural_sim_top20=0.4065, avg_hybrid_val_top20=3.5576, sem_top50_mean=0.463, sem_top50_p95=0.532, sem_top50_overlap_mean=0.680, sem_top50_any_match=0.68, top20_pools(A/B/C)=20/0/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.409/0.652, forced_in_top20/top50=14/26, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=2/2, top50_franchise_like(before/after)=3/3, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.609/0.609/0.609, high_sim_override_sim_min/mean/max(all)=0.609/0.609/0.609, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=99, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=546, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=144, demo_override_top20=0, blocked_overlap=309, blocked_low_sim=505, bonus_fired=2, bonus_mean=0.00628, bonus_max=0.07760, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/12, theme_bonus_mean(top20/top50)=0.00050/0.00048, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=7, top50_moved_meta=13, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 38408 | My Hero Academia Season 4 | overlap | 1.00 | 0.652 |
| 44200 | My Hero Academia: World Heroes' Mission | overlap | 1.00 | 0.609 |
| 13161 | Aesthetica of a Rogue Hero | overlap | 0.50 | 0.472 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 3 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 4 | 21491 | Ninjaman Ippei | TV | 6.03 |  |  |
| 5 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 6 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 7 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 8 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 9 | 12401 | The Chohjotai | OVA | 5.51 |  |  |
| 10 | 24089 | High School Jingi | OVA | 5.85 |  |  |
| 11 | 16814 | Son O-gong gwa Byeoldeul-ui Jeonjaeng | Movie |  |  |  |
| 12 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 13 | 38408 | My Hero Academia Season 4 |  | 7.86 |  |  |
| 14 | 3846 | Microid S | TV | 6.00 |  |  |
| 15 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 16 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 17 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 18 | 44200 | My Hero Academia: World Heroes' Mission |  | 7.58 |  |  |
| 19 | 5760 | Dororo | TV | 7.27 |  |  |
| 20 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, stage0_pool_raw=2514, stage0_after_hygiene=2272, stage0_src(neural/genre/theme/pop)=962/447/1449/198, stage1_universe=2272, shortlist=600/600, scored=546, top20_in_stage0=20, top50_in_stage0=20, top20_from_neural=60.0%, top20_from_genre_or_theme=100.0%, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.933, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/0/0, avg_neural_sim_top20=0.3456, avg_hybrid_val_top20=3.8623, sem_top50_mean=0.493, sem_top50_p95=0.557, sem_top50_overlap_mean=0.900, sem_top50_any_match=0.90, top20_pools(A/B/C)=18/2/0, forced_neural_shortlist=300, forced_sim_min/mean/max=0.366/0.410/0.857, forced_in_top20/top50=8/25, seed_mode=completion, franchise_cap(thr/cap20/cap50)=0.50/6/15, top20_franchise_like(before/after)=0/0, top50_franchise_like(before/after)=1/1, dropped(top20/top50/all)=0/0/0, high_sim_override_fired(top20/top50/all)=0/1/1, high_sim_override_sim_min/mean/max(top50)=0.857/0.857/0.857, high_sim_override_sim_min/mean/max(all)=0.857/0.857/0.857, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=100, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=208, demo_override_top20=0, blocked_overlap=552, blocked_low_sim=434, bonus_fired=4, bonus_mean=0.00145, bonus_max=0.00980, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=11/28, theme_bonus_mean(top20/top50)=0.00110/0.00112, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=6, top50_moved_meta=10, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Franchise-like examples (top 10, pre-cap):

| anime_id | Title | reason | title_overlap | neural_sim |
|---:|---|---|---:|---:|
| 29755 | Haikyu!! the Movie: The End and the Beginning | overlap | 1.00 | 0.857 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 32870 | Winter Cup Highlights Episode 2 – Winter Cup Highlights -Beyond the Tears- | Movie | 7.77 |  |  |
| 2 | 32871 | Winter Cup Highlights Episode 3 – Winter Cup Highlights -Crossing the Door- | Movie | 7.83 |  |  |
| 3 | 11919 | Zoku Attacker You! Kin Medal e no Michi | TV | 6.25 |  |  |
| 4 | 9905 | Captain (TV) | TV | 6.45 |  |  |
| 5 | 10360 | Kinniku Banzuke: Kongou-kun no Daibouken! | TV | 4.99 |  |  |
| 6 | 16650 | Pro Golfer Saru (TV) | TV | 6.35 |  |  |
| 7 | 23011 | Otoko Doahou! Koushien | TV |  |  |  |
| 8 | 20237 | Anime Document: München e no Michi | TV |  |  |  |
| 9 | 10323 | Golden★Kids | ONA | 5.25 |  |  |
| 10 | 17893 | Cheonbangjichuk Hani | TV | 6.45 |  |  |
| 11 | 11857 | Judo Sanka | TV | 6.19 |  |  |
| 12 | 25967 | Bernard | TV | 5.81 |  |  |
| 13 | 7479 | Karate Master | TV | 6.64 |  |  |
| 14 | 17671 | Animal 1 | TV | 6.01 |  |  |
| 15 | 17092 | Dallyeola Hani | TV | 6.59 |  |  |
| 16 | 19887 | Shouri Toushu | Movie |  |  |  |
| 17 | 5834 | Kyojin no Hoshi | TV | 6.91 |  |  |
| 18 | 11593 | Hit and Run | TV Special |  |  |  |
| 19 | 16552 | Hungry Best 5 | Movie |  |  |  |
| 20 | 9665 | Bucchigiri | OVA | 5.89 |  |  |

