# Phase 4 — Golden Queries Report

Generated: 2026-02-01T00:38:58.516400+00:00
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.923, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=13/7/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=313, theme_override=0, blocked_overlap=1709, blocked_low_sim=2533, bonus_fired=3, bonus_mean=0.00093, bonus_max=0.00990, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/22, theme_bonus_mean(top20/top50)=0.00040/0.00075, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=10, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=6, top50_moved_meta=17, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 41 | 33 | Berserk | 0.667 | 0.00200 |
| 45 | 226 | Elfen Lied | 0.667 | 0.00200 |
| 46 | 384 | Gantz | 0.667 | 0.00200 |
| 39 | 395 | Gantz: Second Stage | 0.667 | 0.00200 |
| 25 | 10620 | The Future Diary | 0.667 | 0.00200 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30463 | Horror News | ONA | 5.43 |  |  |
| 2 | 31339 | Drifters | TV | 7.88 |  |  |
| 3 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 4 | 30412 | Zombie Brother | ONA | 6.51 |  |  |
| 5 | 29089 | Monster List | ONA | 6.80 |  |  |
| 6 | 5760 | Dororo | TV | 7.27 |  |  |
| 7 | 32071 | Gantz:O | Movie | 7.40 |  |  |
| 8 | 29687 | Duel Masters VSR | TV | 5.45 |  |  |
| 9 | 3064 | Wounded Man | OVA | 4.01 |  |  |
| 10 | 13125 | From the New World | TV | 8.25 |  |  |
| 11 | 13769 | Kamen no Ninja Akakage | TV | 6.46 |  |  |
| 12 | 21999 | Duel Masters Victory V3 | TV | 5.66 |  |  |
| 13 | 3553 | Legend of Lyon Flare | OVA | 5.07 |  |  |
| 14 | 25591 | Tokyo Juushouden: Fuuma Gogyou Denshou | OVA | 5.14 |  |  |
| 15 | 8145 | Spooky Kitaro: Japan Explodes!! | Movie | 6.49 |  |  |
| 16 | 27899 | Tokyo Ghoul √A | TV | 7.03 |  |  |
| 17 | 8146 | Spooky Kitaro: Giant Sea Monster | Movie | 6.17 |  |  |
| 18 | 20 | Naruto | TV | 8.01 |  |  |
| 19 | 2342 | Urotsukidoji II: Legend of the Demon Womb | OVA | 5.66 |  |  |
| 20 | 8074 | High School of the Dead | TV | 7.06 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.828, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=2/5/13, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, blocked_overlap=347, blocked_low_sim=4161, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/17, theme_bonus_mean(top20/top50)=0.00027/0.00053, theme_bonus_max(top20/top50)=0.00133/0.00200, top20_theme_overlap_count=17, top20_overlap_meta=1.000, top50_overlap_meta=0.960, top20_moved_meta=0, top50_moved_meta=21, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30484 | Steins;Gate 0 | TV | 8.55 |  |  |
| 2 | 28685 | Tough Guy! | Movie | 5.21 |  |  |
| 3 | 7960 | Pachislo Kizoku Gin | TV | 5.90 |  |  |
| 4 | 2740 | Monkey Turn | TV | 6.43 |  |  |
| 5 | 17467 | Otoko Ippiki Gaki Daishou | TV | 6.46 |  |  |
| 6 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 7 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 8 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 9 | 33154 | Osiris no Tenbin: Season 2 | ONA |  |  |  |
| 10 | 6230 | The Fleet of the Rising Sun | OVA | 6.33 |  |  |
| 11 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 12 | 33348 | Kushimitama Samurai | Movie | 5.77 |  |  |
| 13 | 2741 | Monkey Turn V | TV | 6.46 |  |  |
| 14 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 15 | 15227 | In This Corner of the World | Movie | 8.23 |  |  |
| 16 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 17 | 13125 | From the New World | TV | 8.25 |  |  |
| 18 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 19 | 2904 | Code Geass: Lelouch of the Rebellion R2 | TV | 8.91 |  |  |
| 20 | 3675 | Andromeda Stories | TV Special | 5.69 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.924, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=14/6/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, blocked_overlap=1287, blocked_low_sim=2930, bonus_fired=1, bonus_mean=0.00032, bonus_max=0.00640, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/20, theme_bonus_mean(top20/top50)=0.00050/0.00080, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=9, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30463 | Horror News | ONA | 5.43 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 4 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 5 | 24663 | Dororonpa! | TV | 6.18 |  |  |
| 6 | 33154 | Osiris no Tenbin: Season 2 | ONA |  |  |  |
| 7 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 8 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 9 | 31362 | Osiris no Tenbin | ONA | 5.68 |  |  |
| 10 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 11 | 9345 | Gakkou no Kowai Uwasa Shin: Hanako-san ga Kita!! | TV | 6.14 |  |  |
| 12 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 13 | 6730 | Tonde Mon Pe | TV | 6.37 |  |  |
| 14 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 15 | 6124 | Toshishun | TV Special | 5.56 |  |  |
| 16 | 2246 | Mononoke | TV | 8.41 |  |  |
| 17 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 18 | 3064 | Wounded Man | OVA | 4.01 |  |  |
| 19 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.794, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=3/7/10, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, blocked_overlap=871, blocked_low_sim=3636, bonus_fired=1, bonus_mean=0.00029, bonus_max=0.00580, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/17, theme_bonus_mean(top20/top50)=0.00050/0.00068, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30484 | Steins;Gate 0 | TV | 8.55 |  |  |
| 2 | 28673 | Die Now | ONA | 6.37 |  |  |
| 3 | 30481 | Ginga Tetsudou 999 for Planetarium | Movie | 6.41 |  |  |
| 4 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 5 | 13125 | From the New World | TV | 8.25 |  |  |
| 6 | 33154 | Osiris no Tenbin: Season 2 | ONA |  |  |  |
| 7 | 11307 | Ginga Patrol PJ | TV | 6.73 |  |  |
| 8 | 5052 | 8 Man | TV | 5.88 |  |  |
| 9 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 10 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 11 | 2904 | Code Geass: Lelouch of the Rebellion R2 | TV | 8.91 |  |  |
| 12 | 17959 | Tetsuwan Atom: Atom Tanjou no Himitsu | Movie | 6.16 |  |  |
| 13 | 10793 | Guilty Crown | TV | 7.39 |  |  |
| 14 | 34136 | Orange: Mirai | Movie | 7.46 |  |  |
| 15 | 3176 | Gandalla: The King of Burning Desert | TV | 5.68 |  |  |
| 16 | 16498 | Attack on Titan | TV | 8.57 |  |  |
| 17 | 2613 | Future Boy Conan 2: River Adventure | TV | 6.42 |  |  |
| 18 | 1737 | Space Warrior Baldios | TV | 6.46 |  |  |
| 19 | 395 | Gantz: Second Stage | TV | 7.01 |  |  |
| 20 | 1575 | Code Geass: Lelouch of the Rebellion | TV | 8.71 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.793, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=4/2/14, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=95, theme_override=0, blocked_overlap=400, blocked_low_sim=4074, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/12, theme_bonus_mean(top20/top50)=0.00030/0.00048, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=4, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 12951 | AWOL | TV | 5.32 |  |  |
| 2 | 2697 | High Speed Jessie | OVA | 6.10 |  |  |
| 3 | 6989 | Space Ace | TV | 5.84 |  |  |
| 4 | 9438 | Rainbow Sentai Robin | TV | 5.93 |  |  |
| 5 | 8799 | Okawari-Boy Starzan-S | TV | 6.09 |  |  |
| 6 | 11405 | Skyers 5 | TV | 5.92 |  |  |
| 7 | 14623 | Do it Kororin Earth SOS | TV |  |  |  |
| 8 | 4933 | The White Whale of Mu | TV | 6.32 |  |  |
| 9 | 19997 | Fight Da!! Pyuta | TV | 6.01 |  |  |
| 10 | 19989 | Tatakae! Osper | TV |  |  |  |
| 11 | 22997 | Shin Skyers 5 | TV |  |  |  |
| 12 | 8879 | Dolphin Ouji | TV |  |  |  |
| 13 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 14 | 6448 | Prince Planet | TV | 5.37 |  |  |
| 15 | 16159 | Mirai Kara Kita Shounen Super Jetter | TV | 5.86 |  |  |
| 16 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 17 | 9978 | Dinosaur Expedition Born Free | TV | 5.90 |  |  |
| 18 | 7900 | Super Child | Movie | 2.92 |  |  |
| 19 | 9488 | Cencoroll Connect | Movie | 7.19 |  |  |
| 20 | 16822 | Captain of Cosmos | Movie | 3.52 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.712, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=4/3/13, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, blocked_overlap=79, blocked_low_sim=4409, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00610, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/4, theme_bonus_mean(top20/top50)=0.00020/0.00016, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 2 | 5071 | Croket! | TV | 6.90 |  |  |
| 3 | 8777 | Julie the Wild Rose | TV | 6.00 |  |  |
| 4 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 5 | 22065 | The Adventures of T-Rex | TV |  |  |  |
| 6 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 7 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |
| 8 | 29687 | Duel Masters VSR | TV | 5.45 |  |  |
| 9 | 5760 | Dororo | TV | 7.27 |  |  |
| 10 | 10236 | Kagee Grimm Douwa | TV |  |  |  |
| 11 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 12 | 23409 | Duel Masters VS | TV | 5.73 |  |  |
| 13 | 21999 | Duel Masters Victory V3 | TV | 5.66 |  |  |
| 14 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 15 | 6262 | Manga Fairy Tales of the World | TV | 7.00 |  |  |
| 16 | 21997 | Duel Masters Victory V | TV | 5.81 |  |  |
| 17 | 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | Movie | 7.50 |  |  |
| 18 | 18321 | Kkomaeosa Ttori | Movie |  |  |  |
| 19 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.991, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=10/10/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=578, theme_override=0, blocked_overlap=2013, blocked_low_sim=1978, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=1/2, theme_bonus_mean(top20/top50)=0.00010/0.00008, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=3, top50_moved_meta=5, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 4 | 32269 | Saving Mother | Movie |  |  |  |
| 5 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 6 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 7 | 5071 | Croket! | TV | 6.90 |  |  |
| 8 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 9 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 10 | 17687 | Bemubemu Hunter Kotengu Tenmaru | TV | 6.17 |  |  |
| 11 | 9768 | Shima Shima Tora no Shimajirou | TV | 5.93 |  |  |
| 12 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 13 | 16027 | Greek Roman Sinhwa: Olympus Guardian | TV | 6.17 |  |  |
| 14 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 15 | 5923 | Utsunomiko: Heaven Chapter | OVA | 6.06 |  |  |
| 16 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 17 | 30155 | Hoshi no Kirby: Taose!! Koukaku Majuu Ebizou | ONA | 5.95 |  |  |
| 18 | 18313 | Dokkaebi Gamtu | Movie |  |  |  |
| 19 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 20 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.902, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=10/4/6, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, blocked_overlap=135, blocked_low_sim=4334, bonus_fired=2, bonus_mean=0.00089, bonus_max=0.00892, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=4, top50_moved_meta=7, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 26 | 20 | Naruto |  | 0.00000 |
| 38 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 49 | 249 | InuYasha |  | 0.00000 |
| 35 | 1482 | D.Gray-man |  | 0.00000 |
| 37 | 1818 | Claymore |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 3 | 32269 | Saving Mother | Movie |  |  |  |
| 4 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 5 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 6 | 5071 | Croket! | TV | 6.90 |  |  |
| 7 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 8 | 15913 | Happy☆Lucky Bikkuriman | TV | 6.28 |  |  |
| 9 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 10 | 6583 | Super Bikkuriman | TV | 6.22 |  |  |
| 11 | 15579 | Shinkai Densetsu Meremanoid | TV | 5.66 |  |  |
| 12 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 13 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 14 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 15 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 16 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |
| 17 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 18 | 29687 | Duel Masters VSR | TV | 5.45 |  |  |
| 19 | 8999 | Origami Warriors | TV | 6.40 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.871, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=7/13/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=8, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=101, theme_override=0, blocked_overlap=1539, blocked_low_sim=2701, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/9, theme_bonus_mean(top20/top50)=0.00040/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 31966 | Sword Gai | ONA | 5.61 |  |  |
| 3 | 30278 | Ghost Messenger Movie | Movie | 5.90 |  |  |
| 4 | 18919 | The Midnight★Animal | ONA |  |  |  |
| 5 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 6 | 28685 | Tough Guy! | Movie | 5.21 |  |  |
| 7 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 8 | 9691 | Kyomu Senshi Miroku | OVA | 5.66 |  |  |
| 9 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 10 | 25591 | Tokyo Juushouden: Fuuma Gogyou Denshou | OVA | 5.14 |  |  |
| 11 | 8146 | Spooky Kitaro: Giant Sea Monster | Movie | 6.17 |  |  |
| 12 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 13 | 269 | Bleach | TV | 7.98 |  |  |
| 14 | 12061 | Twin Angels (2) | OVA | 5.50 |  |  |
| 15 | 8745 | Seikima II Humane Society: Jinrui Ai ni Michita Shakai | OVA | 5.82 |  |  |
| 16 | 1708 | Beast Fighter: The Apocalypse | TV | 5.29 |  |  |
| 17 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 18 | 2251 | Baccano! | TV | 8.35 |  |  |
| 19 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 20 | 16498 | Attack on Titan | TV | 8.57 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.883, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=9/11/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=110, theme_override=1, blocked_overlap=1426, blocked_low_sim=2803, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/7, theme_bonus_mean(top20/top50)=0.00000/0.00028, theme_bonus_max(top20/top50)=0.00000/0.00200, top20_theme_overlap_count=10, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 31966 | Sword Gai | ONA | 5.61 |  |  |
| 3 | 30278 | Ghost Messenger Movie | Movie | 5.90 |  |  |
| 4 | 18919 | The Midnight★Animal | ONA |  |  |  |
| 5 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 6 | 28685 | Tough Guy! | Movie | 5.21 |  |  |
| 7 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 8 | 18325 | The Silver Twilight | Movie | 5.51 |  |  |
| 9 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 10 | 25591 | Tokyo Juushouden: Fuuma Gogyou Denshou | OVA | 5.14 |  |  |
| 11 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 12 | 8745 | Seikima II Humane Society: Jinrui Ai ni Michita Shakai | OVA | 5.82 |  |  |
| 13 | 269 | Bleach | TV | 7.98 |  |  |
| 14 | 12061 | Twin Angels (2) | OVA | 5.50 |  |  |
| 15 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 16 | 16498 | Attack on Titan | TV | 8.57 |  |  |
| 17 | 1708 | Beast Fighter: The Apocalypse | TV | 5.29 |  |  |
| 18 | 4068 | Shin Megami Tensei Devil Children: Light & Dark | TV | 6.43 |  |  |
| 19 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 20 | 2251 | Baccano! | TV | 8.35 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.878, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=18/2/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=0, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=581, theme_override=0, blocked_overlap=1408, blocked_low_sim=2543, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=1/11, theme_bonus_mean(top20/top50)=0.00010/0.00044, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=0, top50_moved_meta=9, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 9 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 10 | 3846 | Microid S | TV | 6.00 |  |  |
| 11 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 12 | 5760 | Dororo | TV | 7.27 |  |  |
| 13 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 14 | 13307 | Samurai Kid | TV | 5.88 |  |  |
| 15 | 20 | Naruto | TV | 8.01 |  |  |
| 16 | 6374 | Eagle Riders | TV | 6.44 |  |  |
| 17 | 988 | Shinshaku Sengoku Eiyuu Densetsu: Sanada Juu Yuushi The Animation | TV | 6.01 |  |  |
| 18 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 19 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 20 | 8215 | Genji Tsuushin Agedama | TV | 6.52 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.933, emb_top50_mean=0.000, emb_top50_p95=0.000, emb_top50_overlap_mean=0.000, emb_top50_any_match=0.00, top20_pools(A/B/C)=4/16/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=2, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, blocked_overlap=1140, blocked_low_sim=3262, bonus_fired=3, bonus_mean=0.00098, bonus_max=0.00980, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=13/29, theme_bonus_mean(top20/top50)=0.00130/0.00116, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=14, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=8, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31237 | Ganbare-bu Next! | TV |  |  |  |
| 2 | 31464 | Pichiko Dakyuubu | TV |  |  |  |
| 3 | 32870 | Winter Cup Highlights Episode 2 – Winter Cup Highlights -Beyond the Tears- | Movie | 7.77 |  |  |
| 4 | 32871 | Winter Cup Highlights Episode 3 – Winter Cup Highlights -Crossing the Door- | Movie | 7.83 |  |  |
| 5 | 11919 | Zoku Attacker You! Kin Medal e no Michi | TV | 6.25 |  |  |
| 6 | 8179 | Eagle Sam | TV |  |  |  |
| 7 | 9905 | Captain (TV) | TV | 6.45 |  |  |
| 8 | 17669 | Kunimatsu-sama no Otoridai | TV | 6.27 |  |  |
| 9 | 22215 | Pretty Rhythm: All Star Selection | TV | 6.55 |  |  |
| 10 | 10554 | Yakyuukyou no Uta | TV | 6.52 |  |  |
| 11 | 18983 | Yuuto-kun ga Iku | TV |  |  |  |
| 12 | 15875 | Shin Kyojin no Hoshi | TV | 6.24 |  |  |
| 13 | 16486 | Shin Kyojin no Hoshi II | TV | 6.21 |  |  |
| 14 | 7525 | Kick Off (2002) | TV |  |  |  |
| 15 | 10360 | Kinniku Banzuke: Kongou-kun no Daibouken! | TV | 4.99 |  |  |
| 16 | 17315 | Shin Pro Golfer Saru | TV |  |  |  |
| 17 | 2758 | Shippuu! Iron Leaguer | TV | 7.15 |  |  |
| 18 | 23737 | Neko Pitcher | TV | 6.04 |  |  |
| 19 | 16650 | Pro Golfer Saru (TV) | TV | 6.35 |  |  |
| 20 | 9284 | Bakuhatsu Gorou | TV | 5.60 |  |  |

