# Phase 4 — Golden Queries Report

Generated: 2026-02-01T21:42:21.412851+00:00
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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.923, content_first_alpha=0.70, content_first_active(top20/top50/all)=1/14/155, avg_neural_sim_top20=0.3875, avg_hybrid_val_top20=3.1959, sem_top50_mean=0.484, sem_top50_p95=0.550, sem_top50_overlap_mean=0.510, sem_top50_any_match=0.98, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.398/0.429/0.577, forced_in_top20/top50=11/31, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=150, top20_off_type=5, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=313, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[seinen], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=1709, blocked_low_sim=2533, bonus_fired=1, bonus_mean=0.00049, bonus_max=0.00990, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/18, theme_bonus_mean(top20/top50)=0.00030/0.00053, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=7, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=14, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 41 | 22535 | Parasyte: The Maxim | 0.667 | 0.00200 |
| 19 | 27899 | Tokyo Ghoul √A | 1.000 | 0.00200 |
| 28 | 30458 | Tokyo Ghoul: Jack | 1.000 | 0.00200 |
| 40 | 34055 | Berserk: Season II | 0.667 | 0.00200 |
| 45 | 1818 | Claymore | 0.333 | 0.00133 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30463 | Horror News | ONA | 5.43 |  |  |
| 2 | 31339 | Drifters | TV | 7.88 |  |  |
| 3 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 4 | 30412 | Zombie Brother | ONA | 6.51 |  |  |
| 5 | 29089 | Monster List | ONA | 6.80 |  |  |
| 6 | 23723 | Teppen | OVA |  |  |  |
| 7 | 19533 | Fujiko Fujio A no Mumako | TV Special | 5.47 |  |  |
| 8 | 27495 | Sore Ike! Anpanman: Kaiketsu Naganegiman to Yakisobapanman | Movie | 6.04 |  |  |
| 9 | 25815 | Yokohama Bakkure-tai | OVA |  |  |  |
| 10 | 5760 | Dororo | TV | 7.27 |  |  |
| 11 | 29687 | Duel Masters VSR | TV | 5.45 |  |  |
| 12 | 13125 | From the New World | TV | 8.25 |  |  |
| 13 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 14 | 13769 | Kamen no Ninja Akakage | TV | 6.46 |  |  |
| 15 | 21999 | Duel Masters Victory V3 | TV | 5.66 |  |  |
| 16 | 43690 | High-Rise Invasion |  | 6.68 |  |  |
| 17 | 9882 | High School Mystery: Gakuen Nanafushigi | TV | 6.39 |  |  |
| 18 | 20083 | Doteraman | TV | 5.77 |  |  |
| 19 | 27899 | Tokyo Ghoul √A | TV | 7.03 |  |  |
| 20 | 10237 | Ki Fighter | TV |  |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.828, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/6/104, avg_neural_sim_top20=0.3422, avg_hybrid_val_top20=3.5373, sem_top50_mean=0.432, sem_top50_p95=0.520, sem_top50_overlap_mean=0.355, sem_top50_any_match=0.84, top20_pools(A/B/C)=18/2/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.307/0.354/0.611, forced_in_top20/top50=18/34, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=145, top20_off_type=8, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=133, demo_override_top20=0, blocked_overlap=289, blocked_low_sim=4086, bonus_fired=4, bonus_mean=0.00794, bonus_max=0.07680, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=6/12, theme_bonus_mean(top20/top50)=0.00053/0.00044, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=9, top50_moved_meta=16, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 12 | 35760 | Attack on Titan Season 3 |  | 8.64 |  |  |
| 13 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 14 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 15 | 3846 | Microid S | TV | 6.00 |  |  |
| 16 | 16822 | Captain of Cosmos | Movie | 3.52 |  |  |
| 17 | 17621 | Ultraman Super Fighter Legend | OVA | 5.92 |  |  |
| 18 | 32071 | Gantz:O | Movie | 7.40 |  |  |
| 19 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 20 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.906, content_first_alpha=0.70, content_first_active(top20/top50/all)=4/9/137, avg_neural_sim_top20=0.3802, avg_hybrid_val_top20=3.1278, sem_top50_mean=0.488, sem_top50_p95=0.546, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.66, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.417/0.703, forced_in_top20/top50=12/29, high_sim_override_fired(top20/top50/all)=0/1/1, high_sim_override_sim_min/mean/max(top50)=0.703/0.703/0.703, high_sim_override_sim_min/mean/max(all)=0.703/0.703/0.703, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=122, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=417, demo_override_top20=0, blocked_overlap=1039, blocked_low_sim=2761, bonus_fired=2, bonus_mean=0.00248, bonus_max=0.04400, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=7/17, theme_bonus_mean(top20/top50)=0.00070/0.00068, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=8, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30463 | Horror News | ONA | 5.43 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 4 | 24663 | Dororonpa! | TV | 6.18 |  |  |
| 5 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 6 | 33144 | The Hell (Two Kinds of Life) | Movie | 5.73 |  |  |
| 7 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 8 | 28991 | Ninja & Soldier | Movie | 5.72 |  |  |
| 9 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 10 | 19533 | Fujiko Fujio A no Mumako | TV Special | 5.47 |  |  |
| 11 | 32071 | Gantz:O | Movie | 7.40 |  |  |
| 12 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 13 | 9345 | Gakkou no Kowai Uwasa Shin: Hanako-san ga Kita!! | TV | 6.14 |  |  |
| 14 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 15 | 30485 | ChäoS;Child | TV | 6.30 |  |  |
| 16 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 17 | 2246 | Mononoke | TV | 8.41 |  |  |
| 18 | 47194 | Summer Time Rendering |  | 8.47 |  |  |
| 19 | 33339 | Zhongguo Jingqi Xiansheng | ONA | 6.05 |  |  |
| 20 | 37451 | Boogiepop and Others |  | 7.06 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.794, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/1/70, avg_neural_sim_top20=0.3632, avg_hybrid_val_top20=5.0554, sem_top50_mean=0.410, sem_top50_p95=0.514, sem_top50_overlap_mean=0.693, sem_top50_any_match=1.00, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.321/0.353/0.683, forced_in_top20/top50=19/41, high_sim_override_fired(top20/top50/all)=0/0/1, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.612/0.612/0.612, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=146, top20_off_type=13, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=871, blocked_low_sim=3636, bonus_fired=1, bonus_mean=0.00029, bonus_max=0.00580, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/9, theme_bonus_mean(top20/top50)=0.00020/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 18 | 13125 | From the New World | TV | 8.25 |  |  |
| 19 | 29800 | Urameshi Denwa | Movie | 5.07 |  |  |
| 20 | 29793 | The Strong Bridge | Movie | 5.45 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.793, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/2/35, avg_neural_sim_top20=0.3176, avg_hybrid_val_top20=3.4539, sem_top50_mean=0.423, sem_top50_p95=0.499, sem_top50_overlap_mean=0.673, sem_top50_any_match=1.00, top20_pools(A/B/C)=17/3/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.311/0.355/0.522, forced_in_top20/top50=13/31, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=172, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=95, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=400, blocked_low_sim=4074, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/10, theme_bonus_mean(top20/top50)=0.00030/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=6, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.712, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/5/108, avg_neural_sim_top20=0.2797, avg_hybrid_val_top20=3.4207, sem_top50_mean=0.377, sem_top50_p95=0.476, sem_top50_overlap_mean=0.535, sem_top50_any_match=0.94, top20_pools(A/B/C)=17/3/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.253/0.294/0.828, forced_in_top20/top50=12/31, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.741/0.741/0.741, high_sim_override_sim_min/mean/max(all)=0.741/0.741/0.741, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=162, top20_off_type=8, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=79, demo_override_top20=4, blocked_overlap=62, blocked_low_sim=4347, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00610, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/4, theme_bonus_mean(top20/top50)=0.00020/0.00016, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 13 | 18321 | Kkomaeosa Ttori | Movie |  |  |  |
| 14 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 15 | 9613 | Big X | TV | 6.07 |  |  |
| 16 | 22613 | Keroppi in the Adventures of the Coward Prince | OVA | 5.74 |  |  |
| 17 | 5581 | Kaitei Daisensou: Ai no 20,000 Miles | TV Special | 5.20 |  |  |
| 18 | 20 | Naruto | TV | 8.01 |  |  |
| 19 | 2314 | Fly! Peek the Whale | Movie | 6.16 |  |  |
| 20 | 4597 | Kouya no Shounen Isamu | TV | 6.30 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.991, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/18/150, avg_neural_sim_top20=0.4442, avg_hybrid_val_top20=3.5408, sem_top50_mean=0.542, sem_top50_p95=0.616, sem_top50_overlap_mean=0.607, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.431/0.470/0.672, forced_in_top20/top50=11/26, high_sim_override_fired(top20/top50/all)=0/0/3, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.603/0.623/0.638, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=130, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=578, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=502, demo_override_top20=3, blocked_overlap=1631, blocked_low_sim=1858, bonus_fired=1, bonus_mean=0.00240, bonus_max=0.04800, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/8, theme_bonus_mean(top20/top50)=0.00020/0.00032, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=4, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 30463 | Horror News | ONA | 5.43 |  |  |
| 4 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 5 | 9768 | Shima Shima Tora no Shimajirou | TV | 5.93 |  |  |
| 6 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 7 | 1735 | Naruto Shippuden | TV | 8.28 |  |  |
| 8 | 5923 | Utsunomiko: Heaven Chapter | OVA | 6.06 |  |  |
| 9 | 5760 | Dororo | TV | 7.27 |  |  |
| 10 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 11 | 28991 | Ninja & Soldier | Movie | 5.72 |  |  |
| 12 | 7479 | Karate Master | TV | 6.64 |  |  |
| 13 | 9691 | Kyomu Senshi Miroku | OVA | 5.66 |  |  |
| 14 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 15 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 16 | 15479 | Hey Yo Yorang | TV | 6.13 |  |  |
| 17 | 29089 | Monster List | ONA | 6.80 |  |  |
| 18 | 45560 | Orient |  | 6.61 |  |  |
| 19 | 5274 | Magical★Taruruuto-kun | TV | 6.87 |  |  |
| 20 | 23723 | Teppen | OVA |  |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.902, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/2/74, avg_neural_sim_top20=0.3431, avg_hybrid_val_top20=3.4472, sem_top50_mean=0.466, sem_top50_p95=0.608, sem_top50_overlap_mean=0.713, sem_top50_any_match=0.94, top20_pools(A/B/C)=19/1/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.279/0.335/0.722, forced_in_top20/top50=13/30, high_sim_override_fired(top20/top50/all)=2/2/5, high_sim_override_sim_min/mean/max(top50)=0.608/0.665/0.722, high_sim_override_sim_min/mean/max(all)=0.600/0.631/0.722, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=186, top20_off_type=5, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=86, demo_override_top20=2, blocked_overlap=117, blocked_low_sim=4266, bonus_fired=4, bonus_mean=0.00762, bonus_max=0.06769, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=10, top50_moved_meta=15, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Content-first audit: top10 items by neural_sim (rank movement)

| anime_id | Title | neural_sim | hybrid_val | score_before | score_after | rank_before | rank_after |
|---:|---|---:|---:|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter | 0.7222 | 0.00000 | 1.00518 | 1.53103 | 54 | 5 |
| 4155 | One Piece Film: Strong World | 0.6178 | 0.07884 | 0.96464 | 0.96464 | 70 | 73 |
| 38234 | One Piece: Stampede | 0.6082 | 0.00000 | 0.95390 | 1.39807 | 75 | 12 |
| 5252 | One Piece: Romance Dawn Story | 0.6072 | -0.06775 | 0.93114 | 0.93114 | 86 | 94 |
| 464 | One Piece: Baron Omatsuri and the Secret Island | 0.6000 | -0.05454 | 0.93337 | 0.93337 | 85 | 93 |
| 12859 | One Piece Film: Z | 0.5993 | 0.51676 | 1.05432 | 1.05432 | 45 | 47 |
| 31490 | One Piece Film: Gold | 0.5806 | -0.03002 | 0.87969 | 0.87969 | 108 | 124 |
| 459 | One Piece: The Movie | 0.5802 | -0.04647 | 0.91683 | 0.91683 | 93 | 105 |
| 462 | One Piece: Dead End Adventure | 0.5461 | -0.01895 | 0.74768 | 0.74768 | 181 | 210 |
| 460 | One Piece: Clockwork Island Adventure | 0.5427 | 0.11849 | 0.77859 | 0.77859 | 167 | 188 |

Forced-neural top10 neighbors (by similarity):

| anime_id | Title | Type | sim | in_shortlist | rank@50 | in_top20 |
|---:|---|---|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter |  | 0.7222 | True | 5 | True |
| 4155 | One Piece Film: Strong World | Movie | 0.6178 | True |  | False |
| 38234 | One Piece: Stampede |  | 0.6082 | True | 12 | True |
| 5252 | One Piece: Romance Dawn Story | OVA | 0.6072 | True |  | False |
| 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 0.6000 | True |  | False |
| 12859 | One Piece Film: Z | Movie | 0.5993 | True | 47 | False |
| 31490 | One Piece Film: Gold | Movie | 0.5806 | True |  | False |
| 459 | One Piece: The Movie | Movie | 0.5802 | True |  | False |
| 462 | One Piece: Dead End Adventure | Movie | 0.5461 | True |  | False |
| 460 | One Piece: Clockwork Island Adventure | Movie | 0.5427 | True |  | False |

Stage 2 high-sim override audit (top10 neural neighbors):

| anime_id | sim | type | final_rank | score | Δ_to_top20_cutoff | hybrid | overlap | coverage | neural_bonus | penalty_before | penalty_after | stage2_override |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 60022 | 0.7222 |  | 5 | 1.53103 | -0.22356 | 0.00000 | 1.000 | 1.000 | 0.16527 | -0.01000 | 0.00000 | True |
| 4155 | 0.6178 | Movie | 73 | 0.96464 | 0.34283 | 0.07884 | 1.000 | 1.000 | 0.12874 | -0.01000 | 0.00000 | True |
| 38234 | 0.6082 |  | 12 | 1.39807 | -0.09059 | 0.00000 | 1.000 | 1.000 | 0.12538 | -0.01000 | 0.00000 | True |
| 5252 | 0.6072 | OVA | 94 | 0.93114 | 0.37633 | -0.06775 | 1.000 | 1.000 | 0.12503 | -0.01000 | 0.00000 | True |
| 464 | 0.6000 | Movie | 93 | 0.93337 | 0.37410 | -0.05454 | 1.000 | 1.000 | 0.12250 | -0.01000 | 0.00000 | True |
| 12859 | 0.5993 | Movie | 47 | 1.05432 | 0.25315 | 0.51676 | 1.000 | 1.000 | 0.12226 | -0.01000 | -0.01000 | False |
| 31490 | 0.5806 | Movie | 124 | 0.87969 | 0.42778 | -0.03002 | 1.000 | 1.000 | 0.11572 | -0.01000 | -0.01000 | False |
| 459 | 0.5802 | Movie | 105 | 0.91683 | 0.39064 | -0.04647 | 1.000 | 1.000 | 0.11557 | -0.01000 | -0.01000 | False |
| 462 | 0.5461 | Movie | 210 | 0.74768 | 0.55979 | -0.01895 | 1.000 | 1.000 | 0.00000 | -0.05389 | -0.05389 | False |
| 460 | 0.5427 | Movie | 188 | 0.77859 | 0.52888 | 0.11849 | 1.000 | 1.000 | 0.00000 | -0.05726 | -0.05726 | False |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 30 | 20 | Naruto |  | 0.00000 |
| 42 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 46 | 249 | InuYasha |  | 0.00000 |
| 40 | 1482 | D.Gray-man |  | 0.00000 |
| 41 | 1818 | Claymore |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 2 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 3 | 30738 | Air Bound | Movie | 5.63 |  |  |
| 4 | 5071 | Croket! | TV | 6.90 |  |  |
| 5 | 60022 | One Piece Fan Letter |  | 9.03 |  |  |
| 6 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 7 | 15579 | Shinkai Densetsu Meremanoid | TV | 5.66 |  |  |
| 8 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 9 | 33484 | Shiroi Zou | Movie | 5.68 |  |  |
| 10 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 11 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 12 | 38234 | One Piece: Stampede |  | 8.18 |  |  |
| 13 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 14 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 15 | 19505 | Kaizoku Ouji | TV | 5.90 |  |  |
| 16 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 17 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 18 | 23015 | Chief Joker | TV |  |  |  |
| 19 | 8184 | Adventure on the Gaboten Island | TV | 5.93 |  |  |
| 20 | 5760 | Dororo | TV | 7.27 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.861, content_first_alpha=0.70, content_first_active(top20/top50/all)=2/7/134, avg_neural_sim_top20=0.4022, avg_hybrid_val_top20=3.4955, sem_top50_mean=0.471, sem_top50_p95=0.519, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.72, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.385/0.419/0.600, forced_in_top20/top50=16/33, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.600/0.600/0.600, high_sim_override_sim_min/mean/max(all)=0.600/0.600/0.600, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=154, top20_off_type=10, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=101, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=476, demo_override_top20=3, blocked_overlap=1233, blocked_low_sim=2531, bonus_fired=1, bonus_mean=0.00244, bonus_max=0.04880, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/10, theme_bonus_mean(top20/top50)=0.00030/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=10, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 3 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 4 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 5 | 30664 | Artificial Paradise | Movie | 4.55 |  |  |
| 6 | 31978 | Crayon Shin-chan: Fast Asleep! The Great Assault on the Dreaming World! | Movie | 7.18 |  |  |
| 7 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 8 | 51019 | Demon Slayer: Kimetsu no Yaiba Swordsmith Village Arc |  | 8.17 |  |  |
| 9 | 7619 | Spooky Kitaro | TV | 6.79 |  |  |
| 10 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 11 | 23639 | Kappa Kawatarou | Movie | 5.37 |  |  |
| 12 | 6829 | Over a Drink | Movie | 5.06 |  |  |
| 13 | 27757 | Anisava | TV | 5.52 |  |  |
| 14 | 9349 | Shizukanaru Don: Yakuza Side Story | OVA | 5.81 |  |  |
| 15 | 9498 | Naniwa Yuukyouden | OVA | 5.90 |  |  |
| 16 | 40748 | Jujutsu Kaisen |  | 8.53 |  |  |
| 17 | 23699 | Kumo ni Noru | OVA | 5.44 |  |  |
| 18 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 19 | 7307 | Gegege no Kitarou (1985) | TV | 6.58 |  |  |
| 20 | 31235 | Hikawa Maru Monogatari | Movie |  |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.883, content_first_alpha=0.70, content_first_active(top20/top50/all)=1/18/147, avg_neural_sim_top20=0.3733, avg_hybrid_val_top20=3.0271, sem_top50_mean=0.469, sem_top50_p95=0.531, sem_top50_overlap_mean=0.420, sem_top50_any_match=0.80, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.377/0.411/0.556, forced_in_top20/top50=13/24, high_sim_override_fired(top20/top50/all)=0/0/0, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=137, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=110, theme_override=1, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=431, demo_override_top20=4, blocked_overlap=1143, blocked_low_sim=2655, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=1/10, theme_bonus_mean(top20/top50)=0.00010/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=12, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 8685 | Ryuuichi Manga Gekijou Onbu Obake | TV |  |  |  |
| 3 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 4 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 5 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 6 | 19989 | Tatakae! Osper | TV |  |  |  |
| 7 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 8 | 12401 | The Chohjotai | OVA | 5.51 |  |  |
| 9 | 12833 | Ushiro no Hyakutarou | OVA |  |  |  |
| 10 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 11 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 12 | 38000 | Demon Slayer: Kimetsu no Yaiba |  | 8.42 |  |  |
| 13 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 14 | 29089 | Monster List | ONA | 6.80 |  |  |
| 15 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 16 | 5760 | Dororo | TV | 7.27 |  |  |
| 17 | 17687 | Bemubemu Hunter Kotengu Tenmaru | TV | 6.17 |  |  |
| 18 | 269 | Bleach | TV | 7.98 |  |  |
| 19 | 9811 | Hanasaka Tenshi Tenten-kun | TV |  |  |  |
| 20 | 10620 | The Future Diary | TV | 7.38 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.863, content_first_alpha=0.70, content_first_active(top20/top50/all)=3/22/158, avg_neural_sim_top20=0.4149, avg_hybrid_val_top20=3.2768, sem_top50_mean=0.463, sem_top50_p95=0.532, sem_top50_overlap_mean=0.680, sem_top50_any_match=0.68, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.409/0.652, forced_in_top20/top50=15/39, high_sim_override_fired(top20/top50/all)=1/1/1, high_sim_override_sim_min/mean/max(top50)=0.609/0.609/0.609, high_sim_override_sim_min/mean/max(all)=0.609/0.609/0.609, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=99, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=581, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=398, demo_override_top20=0, blocked_overlap=1163, blocked_low_sim=2390, bonus_fired=3, bonus_mean=0.01024, bonus_max=0.07920, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=6/17, theme_bonus_mean(top20/top50)=0.00060/0.00068, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=0.950, top50_overlap_meta=0.980, top20_moved_meta=7, top50_moved_meta=31, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 3 | 21491 | Ninjaman Ippei | TV | 6.03 |  |  |
| 4 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 5 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 6 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 7 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 8 | 12401 | The Chohjotai | OVA | 5.51 |  |  |
| 9 | 24089 | High School Jingi | OVA | 5.85 |  |  |
| 10 | 16814 | Son O-gong gwa Byeoldeul-ui Jeonjaeng | Movie |  |  |  |
| 11 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 12 | 38408 | My Hero Academia Season 4 |  | 7.86 |  |  |
| 13 | 3846 | Microid S | TV | 6.00 |  |  |
| 14 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 15 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 16 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 17 | 44200 | My Hero Academia: World Heroes' Mission |  | 7.58 |  |  |
| 18 | 5760 | Dororo | TV | 7.27 |  |  |
| 19 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 20 | 33486 | My Hero Academia Season 2 | TV | 8.05 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.933, content_first_alpha=0.70, content_first_active(top20/top50/all)=0/13/134, avg_neural_sim_top20=0.3552, avg_hybrid_val_top20=3.6310, sem_top50_mean=0.493, sem_top50_p95=0.557, sem_top50_overlap_mean=0.900, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.366/0.410/0.857, forced_in_top20/top50=10/33, high_sim_override_fired(top20/top50/all)=0/0/1, high_sim_override_sim_min/mean/max(top50)=0.000/0.000/0.000, high_sim_override_sim_min/mean/max(all)=0.857/0.857/0.857, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=100, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=383, demo_override_top20=0, blocked_overlap=897, blocked_low_sim=3122, bonus_fired=3, bonus_mean=0.00097, bonus_max=0.00950, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=12/32, theme_bonus_mean(top20/top50)=0.00120/0.00128, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=16, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 32871 | Winter Cup Highlights Episode 3 – Winter Cup Highlights -Crossing the Door- | Movie | 7.83 |  |  |
| 2 | 11919 | Zoku Attacker You! Kin Medal e no Michi | TV | 6.25 |  |  |
| 3 | 9905 | Captain (TV) | TV | 6.45 |  |  |
| 4 | 16650 | Pro Golfer Saru (TV) | TV | 6.35 |  |  |
| 5 | 23011 | Otoko Doahou! Koushien | TV |  |  |  |
| 6 | 20237 | Anime Document: München e no Michi | TV |  |  |  |
| 7 | 17893 | Cheonbangjichuk Hani | TV | 6.45 |  |  |
| 8 | 11857 | Judo Sanka | TV | 6.19 |  |  |
| 9 | 25967 | Bernard | TV | 5.81 |  |  |
| 10 | 7479 | Karate Master | TV | 6.64 |  |  |
| 11 | 17671 | Animal 1 | TV | 6.01 |  |  |
| 12 | 17092 | Dallyeola Hani | TV | 6.59 |  |  |
| 13 | 19887 | Shouri Toushu | Movie |  |  |  |
| 14 | 5834 | Kyojin no Hoshi | TV | 6.91 |  |  |
| 15 | 11593 | Hit and Run | TV Special |  |  |  |
| 16 | 16552 | Hungry Best 5 | Movie |  |  |  |
| 17 | 9665 | Bucchigiri | OVA | 5.89 |  |  |
| 18 | 12899 | Ucchare Goshogawara | OVA |  |  |  |
| 19 | 18005 | Forza! Hidemaru | TV | 6.06 |  |  |
| 20 | 7092 | Shoujo Fight: Norainu-tachi no Odekake | OVA | 5.77 |  |  |

