# Phase 4 — Golden Queries Report

Generated: 2026-02-01T01:35:41.921121+00:00
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.396, emb_top50_p95=0.455, emb_top50_overlap_mean=0.425, emb_top50_any_match=0.96, top20_pools(A/B/C)=17/3/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=20, embed_blocked%=63.6%, tfidf_blocked%=69.7%, laneA=11, laneB=284, theme_override=0, blocked_overlap=1635, blocked_low_sim=7116, bonus_fired=5, bonus_mean=0.00367, bonus_max=0.05040, tfidf_fired=16, tfidf_mean=0.02430, theme_bonus_fired(top20/top50)=12/28, theme_bonus_mean(top20/top50)=0.00090/0.00088, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=17, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=20, top20_overlap_tfidf=0.800, top50_overlap_tfidf=0.840, top20_moved_tfidf=13, top50_moved_tfidf=39

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 22 | 33 | Berserk | 0.667 | 0.00200 |
| 42 | 226 | Elfen Lied | 0.667 | 0.00200 |
| 32 | 384 | Gantz | 0.667 | 0.00200 |
| 31 | 395 | Gantz: Second Stage | 0.667 | 0.00200 |
| 13 | 10620 | The Future Diary | 0.667 | 0.00200 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 33508 | Order Designer | ONA | 5.25 |  |  |
| 3 | 30412 | Zombie Brother | ONA | 6.51 |  |  |
| 4 | 32751 | The Guardian Brothers | Movie | 6.37 |  |  |
| 5 | 17291 | Jinzou Konchuu Kabutoborg VxV | TV | 6.08 |  |  |
| 6 | 13125 | From the New World | TV | 8.25 |  |  |
| 7 | 5760 | Dororo | TV | 7.27 |  |  |
| 8 | 27899 | Tokyo Ghoul √A | TV | 7.03 |  |  |
| 9 | 28623 | Kabaneri of the Iron Fortress | TV | 7.28 |  |  |
| 10 | 16498 | Attack on Titan | TV | 8.57 |  |  |
| 11 | 20 | Naruto | TV | 8.01 |  |  |
| 12 | 8074 | High School of the Dead | TV | 7.06 |  |  |
| 13 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 14 | 34176 | Grimoire of Zero | TV | 7.06 |  |  |
| 15 | 1482 | D.Gray-man | TV | 8.00 |  |  |
| 16 | 22535 | Parasyte: The Maxim | TV | 8.32 |  |  |
| 17 | 2246 | Mononoke | TV | 8.41 |  |  |
| 18 | 1818 | Claymore | TV | 7.73 |  |  |
| 19 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 20 | 32105 | Twin Star Exorcists | TV | 7.29 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.464, emb_top50_p95=0.587, emb_top50_overlap_mean=0.295, emb_top50_any_match=0.96, top20_pools(A/B/C)=9/8/3, shortlist=600/600, stage1_off_type_allowed=2, top20_off_type=0, off_type_sim_min=0.20878, off_type_sim_mean=0.24258, off_type_sim_max=0.27638, top20_tfidf_nonzero=14, embed_blocked%=69.3%, tfidf_blocked%=86.1%, laneA=50, laneB=142, theme_override=3, blocked_overlap=1553, blocked_low_sim=7305, bonus_fired=5, bonus_mean=0.01076, bonus_max=0.07680, tfidf_fired=9, tfidf_mean=0.10501, theme_bonus_fired(top20/top50)=10/22, theme_bonus_mean(top20/top50)=0.00083/0.00073, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=19, top20_overlap_meta=0.950, top50_overlap_meta=0.980, top20_moved_meta=7, top50_moved_meta=25, top20_overlap_tfidf=0.650, top50_overlap_tfidf=0.480, top20_moved_tfidf=12, top50_moved_tfidf=23

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 35760 | Attack on Titan Season 3 |  | 8.64 |  |  |
| 2 | 7960 | Pachislo Kizoku Gin | TV | 5.90 |  |  |
| 3 | 25777 | Attack on Titan Season 2 | TV | 8.53 |  |  |
| 4 | 2740 | Monkey Turn | TV | 6.43 |  |  |
| 5 | 17467 | Otoko Ippiki Gaki Daishou | TV | 6.46 |  |  |
| 6 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 7 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 8 | 48583 | Attack on Titan: Final Season Part 2 |  | 8.77 |  |  |
| 9 | 6230 | The Fleet of the Rising Sun | OVA | 6.33 |  |  |
| 10 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 11 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 12 | 2741 | Monkey Turn V | TV | 6.46 |  |  |
| 13 | 40028 | Attack on Titan: Final Season |  | 8.78 |  |  |
| 14 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 15 | 13125 | From the New World | TV | 8.25 |  |  |
| 16 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 17 | 2904 | Code Geass: Lelouch of the Rebellion R2 | TV | 8.91 |  |  |
| 18 | 6229 | Konpeki no Kantai | OVA | 6.56 |  |  |
| 19 | 9756 | Puella Magi Madoka Magica | TV | 8.38 |  |  |
| 20 | 10620 | The Future Diary | TV | 7.38 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.421, emb_top50_p95=0.484, emb_top50_overlap_mean=0.510, emb_top50_any_match=0.90, top20_pools(A/B/C)=14/6/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=2, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=18, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=4, laneB=298, theme_override=4, blocked_overlap=1840, blocked_low_sim=6829, bonus_fired=1, bonus_mean=0.00032, bonus_max=0.00640, tfidf_fired=12, tfidf_mean=0.04350, theme_bonus_fired(top20/top50)=9/21, theme_bonus_mean(top20/top50)=0.00090/0.00084, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=15, top20_overlap_tfidf=0.750, top50_overlap_tfidf=0.820, top20_moved_tfidf=13, top50_moved_tfidf=38

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 28673 | Die Now | ONA | 6.37 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |
| 4 | 1547 | Obake no Q-tarou | TV | 6.09 |  |  |
| 5 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 6 | 9345 | Gakkou no Kowai Uwasa Shin: Hanako-san ga Kita!! | TV | 6.14 |  |  |
| 7 | 6730 | Tonde Mon Pe | TV | 6.37 |  |  |
| 8 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 9 | 7307 | Gegege no Kitarou (1985) | TV | 6.58 |  |  |
| 10 | 3023 | Mami the Psychic | TV | 6.49 |  |  |
| 11 | 2246 | Mononoke | TV | 8.41 |  |  |
| 12 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 13 | 2366 | Touma Kishinden Oni | TV | 6.28 |  |  |
| 14 | 10721 | Penguindrum | TV | 7.92 |  |  |
| 15 | 7724 | Shiki | TV | 7.71 |  |  |
| 16 | 339 | Serial Experiments Lain | TV | 8.10 |  |  |
| 17 | 269 | Bleach | TV | 7.98 |  |  |
| 18 | 12133 | Sekaikei Sekai Ron | OVA | 5.81 |  |  |
| 19 | 3077 | Laughing Salesman | TV | 6.88 |  |  |
| 20 | 1601 | Red Garden | TV | 7.02 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.437, emb_top50_p95=0.518, emb_top50_overlap_mean=0.407, emb_top50_any_match=0.98, top20_pools(A/B/C)=12/6/2, shortlist=600/600, stage1_off_type_allowed=2, top20_off_type=1, off_type_sim_min=0.17606, off_type_sim_mean=0.20026, off_type_sim_max=0.22445, top20_tfidf_nonzero=17, embed_blocked%=64.4%, tfidf_blocked%=81.1%, laneA=41, laneB=119, theme_override=1, blocked_overlap=1370, blocked_low_sim=7562, bonus_fired=2, bonus_mean=0.00077, bonus_max=0.00954, tfidf_fired=8, tfidf_mean=0.03133, theme_bonus_fired(top20/top50)=5/18, theme_bonus_mean(top20/top50)=0.00050/0.00072, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=16, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=0.650, top50_overlap_tfidf=0.580, top20_moved_tfidf=11, top50_moved_tfidf=27

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30484 | Steins;Gate 0 | TV | 8.55 |  |  |
| 2 | 28673 | Die Now | ONA | 6.37 |  |  |
| 3 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 4 | 27957 | Steins;Gate: The Sagacious Wisdom of Cognitive Computing | ONA | 7.44 |  |  |
| 5 | 13125 | From the New World | TV | 8.25 |  |  |
| 6 | 11307 | Ginga Patrol PJ | TV | 6.73 |  |  |
| 7 | 5052 | 8 Man | TV | 5.88 |  |  |
| 8 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 9 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 10 | 10793 | Guilty Crown | TV | 7.39 |  |  |
| 11 | 2904 | Code Geass: Lelouch of the Rebellion R2 | TV | 8.91 |  |  |
| 12 | 3176 | Gandalla: The King of Burning Desert | TV | 5.68 |  |  |
| 13 | 10869 | Scan2Go | TV | 6.19 |  |  |
| 14 | 2613 | Future Boy Conan 2: River Adventure | TV | 6.42 |  |  |
| 15 | 1575 | Code Geass: Lelouch of the Rebellion | TV | 8.71 |  |  |
| 16 | 16498 | Attack on Titan | TV | 8.57 |  |  |
| 17 | 6114 | Rainbow | TV | 8.46 |  |  |
| 18 | 1737 | Space Warrior Baldios | TV | 6.46 |  |  |
| 19 | 26 | Texhnolyze | TV | 7.75 |  |  |
| 20 | 395 | Gantz: Second Stage | TV | 7.01 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.448, emb_top50_p95=0.561, emb_top50_overlap_mean=0.440, emb_top50_any_match=1.00, top20_pools(A/B/C)=11/3/6, shortlist=600/600, stage1_off_type_allowed=1, top20_off_type=0, off_type_sim_min=0.26122, off_type_sim_mean=0.26122, off_type_sim_max=0.26122, top20_tfidf_nonzero=15, embed_blocked%=70.6%, tfidf_blocked%=87.6%, laneA=46, laneB=195, theme_override=0, blocked_overlap=1961, blocked_low_sim=6836, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=8, tfidf_mean=0.00619, theme_bonus_fired(top20/top50)=3/8, theme_bonus_mean(top20/top50)=0.00030/0.00032, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=7, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=4, top20_overlap_tfidf=0.950, top50_overlap_tfidf=0.680, top20_moved_tfidf=12, top50_moved_tfidf=27

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 12951 | AWOL | TV | 5.32 |  |  |
| 2 | 6989 | Space Ace | TV | 5.84 |  |  |
| 3 | 2697 | High Speed Jessie | OVA | 6.10 |  |  |
| 4 | 9438 | Rainbow Sentai Robin | TV | 5.93 |  |  |
| 5 | 8799 | Okawari-Boy Starzan-S | TV | 6.09 |  |  |
| 6 | 4933 | The White Whale of Mu | TV | 6.32 |  |  |
| 7 | 8879 | Dolphin Ouji | TV |  |  |  |
| 8 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 9 | 6448 | Prince Planet | TV | 5.37 |  |  |
| 10 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 11 | 28145 | Johnny Cypher in Dimension Zero | TV |  |  |  |
| 12 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 13 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 14 | 9613 | Big X | TV | 6.07 |  |  |
| 15 | 3846 | Microid S | TV | 6.00 |  |  |
| 16 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 17 | 8553 | Time Bokan Series: Time Patroltai Otasukeman | TV | 6.27 |  |  |
| 18 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 19 | 4083 | Wonder Beat Scramble | TV | 6.57 |  |  |
| 20 | 4088 | The Amazing 3 | TV | 6.16 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.369, emb_top50_p95=0.449, emb_top50_overlap_mean=0.515, emb_top50_any_match=0.98, top20_pools(A/B/C)=17/3/0, shortlist=600/600, stage1_off_type_allowed=3, top20_off_type=0, off_type_sim_min=0.20991, off_type_sim_mean=0.22310, off_type_sim_max=0.23917, top20_tfidf_nonzero=18, embed_blocked%=55.3%, tfidf_blocked%=54.2%, laneA=9, laneB=432, theme_override=1, blocked_overlap=1072, blocked_low_sim=7484, bonus_fired=1, bonus_mean=0.00030, bonus_max=0.00590, tfidf_fired=13, tfidf_mean=0.02043, theme_bonus_fired(top20/top50)=1/7, theme_bonus_mean(top20/top50)=0.00010/0.00028, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=2, top20_overlap_tfidf=0.800, top50_overlap_tfidf=0.840, top20_moved_tfidf=15, top50_moved_tfidf=41

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 2 | 5071 | Croket! | TV | 6.90 |  |  |
| 3 | 32613 | Elsword: El-ui Yeoin | ONA | 5.93 |  |  |
| 4 | 6989 | Space Ace | TV | 5.84 |  |  |
| 5 | 27965 | Maboroshi Mabo-chan | TV |  |  |  |
| 6 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 7 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 8 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 9 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 10 | 5923 | Utsunomiko: Heaven Chapter | OVA | 6.06 |  |  |
| 11 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 12 | 22065 | The Adventures of T-Rex | TV |  |  |  |
| 13 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 14 | 5760 | Dororo | TV | 7.27 |  |  |
| 15 | 21999 | Duel Masters Victory V3 | TV | 5.66 |  |  |
| 16 | 21997 | Duel Masters Victory V | TV | 5.81 |  |  |
| 17 | 3176 | Gandalla: The King of Burning Desert | TV | 5.68 |  |  |
| 18 | 2806 | Yadamon: Magical Dreamer | TV | 6.42 |  |  |
| 19 | 6547 | Angel Beats! | TV | 8.05 |  |  |
| 20 | 11757 | Sword Art Online | TV | 7.22 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.467, emb_top50_p95=0.588, emb_top50_overlap_mean=0.587, emb_top50_any_match=1.00, top20_pools(A/B/C)=10/10/0, shortlist=600/600, stage1_off_type_allowed=13, top20_off_type=1, off_type_sim_min=0.12701, off_type_sim_mean=0.18014, off_type_sim_max=0.23967, top20_tfidf_nonzero=18, embed_blocked%=38.5%, tfidf_blocked%=60.5%, laneA=38, laneB=439, theme_override=0, blocked_overlap=1259, blocked_low_sim=7212, bonus_fired=2, bonus_mean=0.00282, bonus_max=0.04800, tfidf_fired=5, tfidf_mean=0.02357, theme_bonus_fired(top20/top50)=2/5, theme_bonus_mean(top20/top50)=0.00020/0.00020, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=5, top50_moved_meta=5, top20_overlap_tfidf=0.750, top50_overlap_tfidf=0.640, top20_moved_tfidf=15, top50_moved_tfidf=32

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 2 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 3 | 5071 | Croket! | TV | 6.90 |  |  |
| 4 | 17687 | Bemubemu Hunter Kotengu Tenmaru | TV | 6.17 |  |  |
| 5 | 32890 | Legend of a Rabbit: The Martial of Fire | Movie | 6.08 |  |  |
| 6 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 7 | 1735 | Naruto Shippuden | TV | 8.28 |  |  |
| 8 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 9 | 20173 | Mori no Senshi Bonolon | TV |  |  |  |
| 10 | 27943 | Nano Invaders | TV |  |  |  |
| 11 | 4933 | The White Whale of Mu | TV | 6.32 |  |  |
| 12 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 13 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 14 | 6583 | Super Bikkuriman | TV | 6.22 |  |  |
| 15 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |
| 16 | 29687 | Duel Masters VSR | TV | 5.45 |  |  |
| 17 | 23409 | Duel Masters VS | TV | 5.73 |  |  |
| 18 | 5760 | Dororo | TV | 7.27 |  |  |
| 19 | 21999 | Duel Masters Victory V3 | TV | 5.66 |  |  |
| 20 | 21997 | Duel Masters Victory V | TV | 5.81 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.438, emb_top50_p95=0.638, emb_top50_overlap_mean=0.707, emb_top50_any_match=0.98, top20_pools(A/B/C)=18/2/0, shortlist=600/600, stage1_off_type_allowed=3, top20_off_type=7, off_type_sim_min=0.13615, off_type_sim_mean=0.18077, off_type_sim_max=0.25035, top20_tfidf_nonzero=19, embed_blocked%=47.3%, tfidf_blocked%=50.7%, laneA=11, laneB=356, theme_override=0, blocked_overlap=923, blocked_low_sim=7742, bonus_fired=8, bonus_mean=0.00945, bonus_max=0.06769, tfidf_fired=16, tfidf_mean=0.12254, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=9, top50_moved_meta=23, top20_overlap_tfidf=0.650, top50_overlap_tfidf=0.760, top20_moved_tfidf=9, top50_moved_tfidf=33

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 33 | 20 | Naruto |  | 0.00000 |
| 39 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 45 | 249 | InuYasha |  | 0.00000 |
| 6 | 460 | One Piece: Clockwork Island Adventure |  | 0.00000 |
| 24 | 462 | One Piece: Dead End Adventure |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 3 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 4 | 1237 | One Piece: Open Upon the Great Sea! A Father's Huge, HUGE Dream! | TV Special | 7.17 |  |  |
| 5 | 4155 | One Piece Film: Strong World | Movie | 8.04 |  |  |
| 6 | 460 | One Piece: Clockwork Island Adventure | Movie | 7.08 |  |  |
| 7 | 38234 | One Piece: Stampede |  | 8.18 |  |  |
| 8 | 5071 | Croket! | TV | 6.90 |  |  |
| 9 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 10 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 11 | 12859 | One Piece Film: Z | Movie | 8.10 |  |  |
| 12 | 20173 | Mori no Senshi Bonolon | TV |  |  |  |
| 13 | 17619 | Souya Monogatari | TV |  |  |  |
| 14 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 15 | 5252 | One Piece: Romance Dawn Story | OVA | 7.32 |  |  |
| 16 | 15913 | Happy☆Lucky Bikkuriman | TV | 6.28 |  |  |
| 17 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 18 | 50410 | One Piece Film: Red |  | 7.82 |  |  |
| 19 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 20 | 15905 | Qin's Moon: The Great Wall | TV | 7.06 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 0.992, emb_top50_mean=0.490, emb_top50_p95=0.608, emb_top50_overlap_mean=0.287, emb_top50_any_match=0.74, top20_pools(A/B/C)=12/8/0, shortlist=600/600, stage1_off_type_allowed=5, top20_off_type=0, off_type_sim_min=0.17550, off_type_sim_mean=0.21919, off_type_sim_max=0.26737, top20_tfidf_nonzero=18, embed_blocked%=75.5%, tfidf_blocked%=88.4%, laneA=45, laneB=91, theme_override=13, blocked_overlap=1965, blocked_low_sim=6563, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=9, tfidf_mean=0.01149, theme_bonus_fired(top20/top50)=4/8, theme_bonus_mean(top20/top50)=0.00040/0.00032, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=0.550, top50_overlap_tfidf=0.660, top20_moved_tfidf=8, top50_moved_tfidf=30

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 18919 | The Midnight★Animal | ONA |  |  |  |
| 3 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 4 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 5 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 6 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 7 | 3235 | Ambassador Magma | OVA | 5.67 |  |  |
| 8 | 269 | Bleach | TV | 7.98 |  |  |
| 9 | 49387 | Vinland Saga Season 2 |  | 8.82 |  |  |
| 10 | 4068 | Shin Megami Tensei Devil Children: Light & Dark | TV | 6.43 |  |  |
| 11 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 12 | 16498 | Attack on Titan | TV | 8.57 |  |  |
| 13 | 1708 | Beast Fighter: The Apocalypse | TV | 5.29 |  |  |
| 14 | 2251 | Baccano! | TV | 8.35 |  |  |
| 15 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 16 | 6746 | Durarara!! | TV | 8.09 |  |  |
| 17 | 4067 | Shin Megami Tensei Devil Children | TV | 6.51 |  |  |
| 18 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 19 | 150 | Blood+ | TV | 7.60 |  |  |
| 20 | 1667 | Barom 1 | TV | 5.08 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 0.887, emb_top50_mean=0.463, emb_top50_p95=0.574, emb_top50_overlap_mean=0.140, emb_top50_any_match=0.36, top20_pools(A/B/C)=9/11/0, shortlist=600/600, stage1_off_type_allowed=2, top20_off_type=1, off_type_sim_min=0.13643, off_type_sim_mean=0.15636, off_type_sim_max=0.17628, top20_tfidf_nonzero=18, embed_blocked%=76.9%, tfidf_blocked%=88.3%, laneA=51, laneB=81, theme_override=36, blocked_overlap=1661, blocked_low_sim=6873, bonus_fired=2, bonus_mean=0.00484, bonus_max=0.04960, tfidf_fired=9, tfidf_mean=0.04875, theme_bonus_fired(top20/top50)=3/9, theme_bonus_mean(top20/top50)=0.00030/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=12, top50_moved_meta=12, top20_overlap_tfidf=0.650, top50_overlap_tfidf=0.680, top20_moved_tfidf=10, top50_moved_tfidf=31

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 18919 | The Midnight★Animal | ONA |  |  |  |
| 3 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 4 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 5 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 6 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 7 | 269 | Bleach | TV | 7.98 |  |  |
| 8 | 51009 | Jujutsu Kaisen Season 2 |  | 8.72 |  |  |
| 9 | 1708 | Beast Fighter: The Apocalypse | TV | 5.29 |  |  |
| 10 | 16498 | Attack on Titan | TV | 8.57 |  |  |
| 11 | 4068 | Shin Megami Tensei Devil Children: Light & Dark | TV | 6.43 |  |  |
| 12 | 41467 | Bleach: Thousand-Year Blood War |  | 8.99 |  |  |
| 13 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 14 | 57658 | Jujutsu Kaisen: The Culling Game Part 1 |  |  |  |  |
| 15 | 2251 | Baccano! | TV | 8.35 |  |  |
| 16 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 17 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 18 | 15451 | High School DxD New | TV | 7.46 |  |  |
| 19 | 6746 | Durarara!! | TV | 8.09 |  |  |
| 20 | 4067 | Shin Megami Tensei Devil Children | TV | 6.51 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.368, emb_top50_p95=0.475, emb_top50_overlap_mean=0.940, emb_top50_any_match=0.94, top20_pools(A/B/C)=16/4/0, shortlist=600/600, stage1_off_type_allowed=3, top20_off_type=3, off_type_sim_min=0.14393, off_type_sim_mean=0.16716, off_type_sim_max=0.20237, top20_tfidf_nonzero=19, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=3, laneB=556, theme_override=3, blocked_overlap=1366, blocked_low_sim=6940, bonus_fired=2, bonus_mean=0.00425, bonus_max=0.07920, tfidf_fired=8, tfidf_mean=0.03894, theme_bonus_fired(top20/top50)=8/17, theme_bonus_mean(top20/top50)=0.00080/0.00068, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=0.950, top50_overlap_meta=0.960, top20_moved_meta=3, top50_moved_meta=27, top20_overlap_tfidf=0.950, top50_overlap_tfidf=0.940, top20_moved_tfidf=18, top50_moved_tfidf=44

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 2 | 6989 | Space Ace | TV | 5.84 |  |  |
| 3 | 19989 | Tatakae! Osper | TV |  |  |  |
| 4 | 22065 | The Adventures of T-Rex | TV |  |  |  |
| 5 | 5071 | Croket! | TV | 6.90 |  |  |
| 6 | 3104 | Geisters: Fractions of the Earth | TV | 5.69 |  |  |
| 7 | 16399 | Jeonja Ingan 337 | Movie |  |  |  |
| 8 | 3235 | Ambassador Magma | OVA | 5.67 |  |  |
| 9 | 33486 | My Hero Academia Season 2 | TV | 8.05 |  |  |
| 10 | 34449 | The Reflection | TV | 5.12 |  |  |
| 11 | 918 | Gintama | TV | 8.93 |  |  |
| 12 | 16820 | Lightning Atom | Movie |  |  |  |
| 13 | 9799 | Shin-Men | TV | 6.16 |  |  |
| 14 | 20 | Naruto | TV | 8.01 |  |  |
| 15 | 269 | Bleach | TV | 7.98 |  |  |
| 16 | 988 | Shinshaku Sengoku Eiyuu Densetsu: Sanada Juu Yuushi The Animation | TV | 6.01 |  |  |
| 17 | 1057 | Ippatsu Kiki Musume | TV | 6.18 |  |  |
| 18 | 11695 | Ultraman Graffiti | OVA | 5.54 |  |  |
| 19 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 20 | 3588 | Soul Eater | TV | 7.85 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(embeddings/high) 1.000, emb_top50_mean=0.391, emb_top50_p95=0.478, emb_top50_overlap_mean=0.860, emb_top50_any_match=0.86, top20_pools(A/B/C)=4/16/0, shortlist=600/600, stage1_off_type_allowed=5, top20_off_type=1, off_type_sim_min=0.15516, off_type_sim_mean=0.20266, off_type_sim_max=0.30590, top20_tfidf_nonzero=10, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=7, laneB=145, theme_override=7, blocked_overlap=1419, blocked_low_sim=7548, bonus_fired=1, bonus_mean=0.00049, bonus_max=0.00990, tfidf_fired=4, tfidf_mean=0.04029, theme_bonus_fired(top20/top50)=9/31, theme_bonus_mean(top20/top50)=0.00090/0.00124, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=11, top20_overlap_tfidf=0.850, top50_overlap_tfidf=0.820, top20_moved_tfidf=10, top50_moved_tfidf=34

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31237 | Ganbare-bu Next! | TV |  |  |  |
| 2 | 31464 | Pichiko Dakyuubu | TV |  |  |  |
| 3 | 11919 | Zoku Attacker You! Kin Medal e no Michi | TV | 6.25 |  |  |
| 4 | 8179 | Eagle Sam | TV |  |  |  |
| 5 | 10360 | Kinniku Banzuke: Kongou-kun no Daibouken! | TV | 4.99 |  |  |
| 6 | 22215 | Pretty Rhythm: All Star Selection | TV | 6.55 |  |  |
| 7 | 29755 | Haikyu!! the Movie: The End and the Beginning | Movie | 8.10 |  |  |
| 8 | 16650 | Pro Golfer Saru (TV) | TV | 6.35 |  |  |
| 9 | 18983 | Yuuto-kun ga Iku | TV |  |  |  |
| 10 | 17893 | Cheonbangjichuk Hani | TV | 6.45 |  |  |
| 11 | 9905 | Captain (TV) | TV | 6.45 |  |  |
| 12 | 25967 | Bernard | TV | 5.81 |  |  |
| 13 | 11857 | Judo Sanka | TV | 6.19 |  |  |
| 14 | 17671 | Animal 1 | TV | 6.01 |  |  |
| 15 | 23011 | Otoko Doahou! Koushien | TV |  |  |  |
| 16 | 7525 | Kick Off (2002) | TV |  |  |  |
| 17 | 20237 | Anime Document: München e no Michi | TV |  |  |  |
| 18 | 17315 | Shin Pro Golfer Saru | TV |  |  |  |
| 19 | 23737 | Neko Pitcher | TV | 6.04 |  |  |
| 20 | 9284 | Bakuhatsu Gorou | TV | 5.60 |  |  |

