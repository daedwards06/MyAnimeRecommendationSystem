# Phase 4 — Golden Queries Report

Generated: 2026-02-01T16:56:37.532575+00:00
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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.923, sem_top50_mean=0.484, sem_top50_p95=0.550, sem_top50_overlap_mean=0.510, sem_top50_any_match=0.98, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.398/0.429/0.577, forced_in_top20/top50=11/26, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=150, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=313, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[seinen], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=1709, blocked_low_sim=2533, bonus_fired=2, bonus_mean=0.00077, bonus_max=0.00990, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/13, theme_bonus_mean(top20/top50)=0.00023/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=7, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=16, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 47 | 384 | Gantz | 0.667 | 0.00200 |
| 33 | 22535 | Parasyte: The Maxim | 0.667 | 0.00200 |
| 18 | 27899 | Tokyo Ghoul √A | 1.000 | 0.00200 |
| 27 | 30458 | Tokyo Ghoul: Jack | 1.000 | 0.00200 |
| 36 | 1818 | Claymore | 0.333 | 0.00133 |

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
| 16 | 9882 | High School Mystery: Gakuen Nanafushigi | TV | 6.39 |  |  |
| 17 | 20083 | Doteraman | TV | 5.77 |  |  |
| 18 | 27899 | Tokyo Ghoul √A | TV | 7.03 |  |  |
| 19 | 10237 | Ki Fighter | TV |  |  |  |
| 20 | 4923 | Akai Hayate | OVA | 5.31 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.828, sem_top50_mean=0.432, sem_top50_p95=0.520, sem_top50_overlap_mean=0.355, sem_top50_any_match=0.84, top20_pools(A/B/C)=18/2/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.307/0.354/0.611, forced_in_top20/top50=18/32, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=145, top20_off_type=9, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=133, demo_override_top20=0, blocked_overlap=289, blocked_low_sim=4086, bonus_fired=2, bonus_mean=0.00030, bonus_max=0.00303, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/11, theme_bonus_mean(top20/top50)=0.00033/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=0.960, top20_moved_meta=2, top50_moved_meta=14, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 4 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 5 | 4933 | The White Whale of Mu | TV | 6.32 |  |  |
| 6 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 7 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 8 | 33220 | Summer's Puke is Winter's Delight | Movie | 3.84 |  |  |
| 9 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 10 | 33266 | NANOCORE | ONA | 5.97 |  |  |
| 11 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 12 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 13 | 3846 | Microid S | TV | 6.00 |  |  |
| 14 | 16822 | Captain of Cosmos | Movie | 3.52 |  |  |
| 15 | 17621 | Ultraman Super Fighter Legend | OVA | 5.92 |  |  |
| 16 | 32071 | Gantz:O | Movie | 7.40 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.906, sem_top50_mean=0.488, sem_top50_p95=0.546, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.66, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.417/0.703, forced_in_top20/top50=12/26, high_sim_override_fired(top20/top50)=1/1, high_sim_override_sim_min/mean/max=0.703/0.703/0.703, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=122, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=417, demo_override_top20=0, blocked_overlap=1039, blocked_low_sim=2761, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00640, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=7/18, theme_bonus_mean(top20/top50)=0.00070/0.00072, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=11, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=9, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 15 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 16 | 2246 | Mononoke | TV | 8.41 |  |  |
| 17 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |
| 18 | 3372 | RGB Adventure | TV |  |  |  |
| 19 | 10533 | Fujilog | TV | 5.57 |  |  |
| 20 | 10721 | Penguindrum | TV | 7.92 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.794, sem_top50_mean=0.410, sem_top50_p95=0.514, sem_top50_overlap_mean=0.693, sem_top50_any_match=1.00, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.321/0.353/0.683, forced_in_top20/top50=19/40, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=146, top20_off_type=13, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=871, blocked_low_sim=3636, bonus_fired=1, bonus_mean=0.00029, bonus_max=0.00580, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/10, theme_bonus_mean(top20/top50)=0.00020/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.793, sem_top50_mean=0.423, sem_top50_p95=0.499, sem_top50_overlap_mean=0.673, sem_top50_any_match=1.00, top20_pools(A/B/C)=17/3/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.311/0.355/0.522, forced_in_top20/top50=13/30, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=172, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=95, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=400, blocked_low_sim=4074, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/9, theme_bonus_mean(top20/top50)=0.00030/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=6, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.712, sem_top50_mean=0.377, sem_top50_p95=0.476, sem_top50_overlap_mean=0.535, sem_top50_any_match=0.94, top20_pools(A/B/C)=17/3/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.253/0.294/0.828, forced_in_top20/top50=12/28, high_sim_override_fired(top20/top50)=1/1, high_sim_override_sim_min/mean/max=0.741/0.741/0.741, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=162, top20_off_type=8, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=79, demo_override_top20=4, blocked_overlap=62, blocked_low_sim=4347, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00610, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/5, theme_bonus_mean(top20/top50)=0.00020/0.00020, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.991, sem_top50_mean=0.542, sem_top50_p95=0.616, sem_top50_overlap_mean=0.607, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.431/0.470/0.672, forced_in_top20/top50=11/28, high_sim_override_fired(top20/top50)=0/3, high_sim_override_sim_min/mean/max=0.603/0.623/0.638, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=130, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=578, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=502, demo_override_top20=3, blocked_overlap=1631, blocked_low_sim=1858, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/10, theme_bonus_mean(top20/top50)=0.00020/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=9, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 30463 | Horror News | ONA | 5.43 |  |  |
| 4 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 5 | 9768 | Shima Shima Tora no Shimajirou | TV | 5.93 |  |  |
| 6 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 7 | 5923 | Utsunomiko: Heaven Chapter | OVA | 6.06 |  |  |
| 8 | 5760 | Dororo | TV | 7.27 |  |  |
| 9 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 10 | 28991 | Ninja & Soldier | Movie | 5.72 |  |  |
| 11 | 7479 | Karate Master | TV | 6.64 |  |  |
| 12 | 9691 | Kyomu Senshi Miroku | OVA | 5.66 |  |  |
| 13 | 2463 | Bomber Bikers of Shonan | OVA | 7.60 |  |  |
| 14 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 15 | 15479 | Hey Yo Yorang | TV | 6.13 |  |  |
| 16 | 29089 | Monster List | ONA | 6.80 |  |  |
| 17 | 5274 | Magical★Taruruuto-kun | TV | 6.87 |  |  |
| 18 | 23723 | Teppen | OVA |  |  |  |
| 19 | 5192 | Kiku-chan to Ookami | TV Special | 6.17 |  |  |
| 20 | 12795 | Yajikita Gakuen Douchuuki | OVA | 5.49 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.902, sem_top50_mean=0.466, sem_top50_p95=0.608, sem_top50_overlap_mean=0.713, sem_top50_any_match=0.94, top20_pools(A/B/C)=19/1/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.279/0.335/0.722, forced_in_top20/top50=13/30, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=186, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=86, demo_override_top20=2, blocked_overlap=117, blocked_low_sim=4266, bonus_fired=2, bonus_mean=0.00085, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=7, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Forced-neural top10 neighbors (by similarity):

| anime_id | Title | Type | sim | in_shortlist | rank@50 | in_top20 |
|---:|---|---|---:|---:|---:|---:|
| 60022 | One Piece Fan Letter |  | 0.7222 | True |  | False |
| 4155 | One Piece Film: Strong World | Movie | 0.6178 | True |  | False |
| 38234 | One Piece: Stampede |  | 0.6082 | True |  | False |
| 5252 | One Piece: Romance Dawn Story | OVA | 0.6072 | True |  | False |
| 464 | One Piece: Baron Omatsuri and the Secret Island | Movie | 0.6000 | True |  | False |
| 12859 | One Piece Film: Z | Movie | 0.5993 | True | 45 | False |
| 31490 | One Piece Film: Gold | Movie | 0.5806 | True |  | False |
| 459 | One Piece: The Movie | Movie | 0.5802 | True |  | False |
| 462 | One Piece: Dead End Adventure | Movie | 0.5461 | True |  | False |
| 460 | One Piece: Clockwork Island Adventure | Movie | 0.5427 | True |  | False |

Stage 2 high-sim override audit (top10 neural neighbors):

| anime_id | sim | type | was_off_type | penalty_before | penalty_after | stage2_override | final_rank |
|---:|---:|---|---:|---:|---:|---:|---:|
| 60022 | 0.7222 |  | True | -0.01000 | 0.00000 | True | 54 |
| 4155 | 0.6178 | Movie | True | -0.01000 | 0.00000 | True | 70 |
| 38234 | 0.6082 |  | True | -0.01000 | 0.00000 | True | 75 |
| 5252 | 0.6072 | OVA | True | -0.01000 | 0.00000 | True | 86 |
| 464 | 0.6000 | Movie | True | -0.01000 | 0.00000 | True | 85 |
| 12859 | 0.5993 | Movie | True | -0.01000 | -0.01000 | False | 45 |
| 31490 | 0.5806 | Movie | True | -0.01000 | -0.01000 | False | 108 |
| 459 | 0.5802 | Movie | True | -0.01000 | -0.01000 | False | 93 |
| 462 | 0.5461 | Movie | True | -0.05389 | -0.05389 | False | 181 |
| 460 | 0.5427 | Movie | True | -0.05726 | -0.05726 | False | 167 |

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 28 | 20 | Naruto |  | 0.00000 |
| 40 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 44 | 249 | InuYasha |  | 0.00000 |
| 38 | 1482 | D.Gray-man |  | 0.00000 |
| 39 | 1818 | Claymore |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 2 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 3 | 30738 | Air Bound | Movie | 5.63 |  |  |
| 4 | 5071 | Croket! | TV | 6.90 |  |  |
| 5 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 6 | 15579 | Shinkai Densetsu Meremanoid | TV | 5.66 |  |  |
| 7 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 8 | 33484 | Shiroi Zou | Movie | 5.68 |  |  |
| 9 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 10 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 11 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 12 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 13 | 19505 | Kaizoku Ouji | TV | 5.90 |  |  |
| 14 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 15 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 16 | 23015 | Chief Joker | TV |  |  |  |
| 17 | 8184 | Adventure on the Gaboten Island | TV | 5.93 |  |  |
| 18 | 5760 | Dororo | TV | 7.27 |  |  |
| 19 | 21019 | Noonbory & the Super 7 | TV |  |  |  |
| 20 | 16814 | Son O-gong gwa Byeoldeul-ui Jeonjaeng | Movie |  |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.861, sem_top50_mean=0.471, sem_top50_p95=0.519, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.72, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.385/0.419/0.600, forced_in_top20/top50=16/30, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=154, top20_off_type=10, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=101, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=476, demo_override_top20=4, blocked_overlap=1233, blocked_low_sim=2531, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/10, theme_bonus_mean(top20/top50)=0.00030/0.00040, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 3 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 4 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 5 | 30664 | Artificial Paradise | Movie | 4.55 |  |  |
| 6 | 31978 | Crayon Shin-chan: Fast Asleep! The Great Assault on the Dreaming World! | Movie | 7.18 |  |  |
| 7 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 8 | 7619 | Spooky Kitaro | TV | 6.79 |  |  |
| 9 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 10 | 23639 | Kappa Kawatarou | Movie | 5.37 |  |  |
| 11 | 6829 | Over a Drink | Movie | 5.06 |  |  |
| 12 | 27757 | Anisava | TV | 5.52 |  |  |
| 13 | 9349 | Shizukanaru Don: Yakuza Side Story | OVA | 5.81 |  |  |
| 14 | 9498 | Naniwa Yuukyouden | OVA | 5.90 |  |  |
| 15 | 23699 | Kumo ni Noru | OVA | 5.44 |  |  |
| 16 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 17 | 7307 | Gegege no Kitarou (1985) | TV | 6.58 |  |  |
| 18 | 31235 | Hikawa Maru Monogatari | Movie |  |  |  |
| 19 | 5760 | Dororo | TV | 7.27 |  |  |
| 20 | 27653 | Crayon Shin-chan: My Moving Story - The Great Cactus Attack! | Movie | 7.19 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.883, sem_top50_mean=0.469, sem_top50_p95=0.531, sem_top50_overlap_mean=0.420, sem_top50_any_match=0.80, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.377/0.411/0.556, forced_in_top20/top50=12/29, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=137, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=110, theme_override=1, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=431, demo_override_top20=4, blocked_overlap=1143, blocked_low_sim=2655, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=1/7, theme_bonus_mean(top20/top50)=0.00010/0.00028, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 12 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 13 | 29089 | Monster List | ONA | 6.80 |  |  |
| 14 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 15 | 5760 | Dororo | TV | 7.27 |  |  |
| 16 | 17687 | Bemubemu Hunter Kotengu Tenmaru | TV | 6.17 |  |  |
| 17 | 269 | Bleach | TV | 7.98 |  |  |
| 18 | 9811 | Hanasaka Tenshi Tenten-kun | TV |  |  |  |
| 19 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 20 | 4068 | Shin Megami Tensei Devil Children: Light & Dark | TV | 6.43 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.863, sem_top50_mean=0.463, sem_top50_p95=0.532, sem_top50_overlap_mean=0.680, sem_top50_any_match=0.68, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.378/0.409/0.652, forced_in_top20/top50=14/27, high_sim_override_fired(top20/top50)=0/0, high_sim_override_sim_min/mean/max=0.000/0.000/0.000, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=99, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=581, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=398, demo_override_top20=0, blocked_overlap=1163, blocked_low_sim=2390, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/12, theme_bonus_mean(top20/top50)=0.00030/0.00048, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=13, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 12 | 3846 | Microid S | TV | 6.00 |  |  |
| 13 | 33674 | No Game, No Life: Zero | Movie | 8.16 |  |  |
| 14 | 30923 | Colorful Ninja Iromaki | Movie | 5.88 |  |  |
| 15 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 16 | 5760 | Dororo | TV | 7.27 |  |  |
| 17 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 18 | 13307 | Samurai Kid | TV | 5.88 |  |  |
| 19 | 32871 | Winter Cup Highlights Episode 3 – Winter Cup Highlights -Crossing the Door- | Movie | 7.83 |  |  |
| 20 | 30870 | Ajin: Demi-Human Movie 3: Collide | Movie | 7.23 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, force_neural=True, force_topk=300, force_min_sim=0.200, sem_conf=(neural/high) 0.933, sem_top50_mean=0.493, sem_top50_p95=0.557, sem_top50_overlap_mean=0.900, sem_top50_any_match=0.90, top20_pools(A/B/C)=20/0/0, shortlist=600/600, forced_neural_shortlist=300, forced_sim_min/mean/max=0.366/0.410/0.857, forced_in_top20/top50=10/26, high_sim_override_fired(top20/top50)=0/1, high_sim_override_sim_min/mean/max=0.857/0.857/0.857, stage1_off_type_allowed=0, stage1_off_type_allowed_neural=100, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=383, demo_override_top20=0, blocked_overlap=897, blocked_low_sim=3122, bonus_fired=3, bonus_mean=0.00097, bonus_max=0.00950, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=12/27, theme_bonus_mean(top20/top50)=0.00120/0.00108, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=6, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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

