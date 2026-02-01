# Phase 4 — Golden Queries Report

Generated: 2026-02-01T02:14:40.470020+00:00
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.923, sem_top50_mean=0.484, sem_top50_p95=0.550, sem_top50_overlap_mean=0.510, sem_top50_any_match=0.98, top20_pools(A/B/C)=13/7/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=313, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[seinen], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=1709, blocked_low_sim=2533, bonus_fired=3, bonus_mean=0.00093, bonus_max=0.00990, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/22, theme_bonus_mean(top20/top50)=0.00040/0.00075, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=10, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=6, top50_moved_meta=17, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.828, sem_top50_mean=0.432, sem_top50_p95=0.520, sem_top50_overlap_mean=0.355, sem_top50_any_match=0.84, top20_pools(A/B/C)=5/6/9, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=58, demo_override_top20=3, blocked_overlap=289, blocked_low_sim=4161, bonus_fired=1, bonus_mean=0.00016, bonus_max=0.00313, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/15, theme_bonus_mean(top20/top50)=0.00037/0.00048, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=19, top20_overlap_meta=1.000, top50_overlap_meta=0.960, top20_moved_meta=0, top50_moved_meta=21, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 7960 | Pachislo Kizoku Gin | TV | 5.90 |  |  |
| 2 | 2740 | Monkey Turn | TV | 6.43 |  |  |
| 3 | 17467 | Otoko Ippiki Gaki Daishou | TV | 6.46 |  |  |
| 4 | 6087 | Jetter Mars | TV | 6.24 |  |  |
| 5 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 6 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 7 | 6230 | The Fleet of the Rising Sun | OVA | 6.33 |  |  |
| 8 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 9 | 2741 | Monkey Turn V | TV | 6.46 |  |  |
| 10 | 5763 | Space Carrier Blue Noah | TV | 6.48 |  |  |
| 11 | 15227 | In This Corner of the World | Movie | 8.23 |  |  |
| 12 | 30 | Neon Genesis Evangelion | TV | 8.36 |  |  |
| 13 | 13125 | From the New World | TV | 8.25 |  |  |
| 14 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 15 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 16 | 3235 | Ambassador Magma | OVA | 5.67 |  |  |
| 17 | 2904 | Code Geass: Lelouch of the Rebellion R2 | TV | 8.91 |  |  |
| 18 | 3675 | Andromeda Stories | TV Special | 5.69 |  |  |
| 19 | 11857 | Judo Sanka | TV | 6.19 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.906, sem_top50_mean=0.488, sem_top50_p95=0.546, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.66, top20_pools(A/B/C)=14/6/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=6, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=341, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=248, demo_override_top20=1, blocked_overlap=1039, blocked_low_sim=2930, bonus_fired=1, bonus_mean=0.00032, bonus_max=0.00640, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=7/18, theme_bonus_mean(top20/top50)=0.00070/0.00072, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=12, top20_overlap_meta=1.000, top50_overlap_meta=0.960, top20_moved_meta=0, top50_moved_meta=12, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 30463 | Horror News | ONA | 5.43 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 33154 | Osiris no Tenbin: Season 2 | ONA |  |  |  |
| 4 | 23351 | Cat Eyed Boy | TV | 5.93 |  |  |
| 5 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 6 | 31362 | Osiris no Tenbin | ONA | 5.68 |  |  |
| 7 | 30947 | Kurayami Santa | TV | 5.16 |  |  |
| 8 | 9345 | Gakkou no Kowai Uwasa Shin: Hanako-san ga Kita!! | TV | 6.14 |  |  |
| 9 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 10 | 6730 | Tonde Mon Pe | TV | 6.37 |  |  |
| 11 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 12 | 6124 | Toshishun | TV Special | 5.56 |  |  |
| 13 | 2246 | Mononoke | TV | 8.41 |  |  |
| 14 | 5930 | Hayou no Tsurugi: Shikkoku no Mashou | OVA | 5.34 |  |  |
| 15 | 3064 | Wounded Man | OVA | 4.01 |  |  |
| 16 | 2994 | Death Note: Relight | TV Special | 7.72 |  |  |
| 17 | 10721 | Penguindrum | TV | 7.92 |  |  |
| 18 | 7724 | Shiki | TV | 7.71 |  |  |
| 19 | 9811 | Hanasaka Tenshi Tenten-kun | TV |  |  |  |
| 20 | 13125 | From the New World | TV | 8.25 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.794, sem_top50_mean=0.410, sem_top50_p95=0.514, sem_top50_overlap_mean=0.693, sem_top50_any_match=1.00, top20_pools(A/B/C)=3/7/10, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=4, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=53, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=871, blocked_low_sim=3636, bonus_fired=1, bonus_mean=0.00029, bonus_max=0.00580, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=5/17, theme_bonus_mean(top20/top50)=0.00050/0.00068, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.793, sem_top50_mean=0.423, sem_top50_p95=0.499, sem_top50_overlap_mean=0.673, sem_top50_any_match=1.00, top20_pools(A/B/C)=4/2/14, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=95, theme_override=0, seed_has_shounen_demo=False, seed_demo_tokens=[], demo_override_admitted=0, demo_override_top20=0, blocked_overlap=400, blocked_low_sim=4074, bonus_fired=1, bonus_mean=0.00042, bonus_max=0.00846, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/12, theme_bonus_mean(top20/top50)=0.00030/0.00048, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=4, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.712, sem_top50_mean=0.377, sem_top50_p95=0.476, sem_top50_overlap_mean=0.535, sem_top50_any_match=0.94, top20_pools(A/B/C)=5/3/12, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=80, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=17, demo_override_top20=1, blocked_overlap=62, blocked_low_sim=4409, bonus_fired=2, bonus_mean=0.00060, bonus_max=0.00610, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=2/4, theme_bonus_mean(top20/top50)=0.00020/0.00016, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=13, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 2 | 5071 | Croket! | TV | 6.90 |  |  |
| 3 | 8777 | Julie the Wild Rose | TV | 6.00 |  |  |
| 4 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 5 | 22065 | The Adventures of T-Rex | TV |  |  |  |
| 6 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 7 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |
| 8 | 5760 | Dororo | TV | 7.27 |  |  |
| 9 | 10236 | Kagee Grimm Douwa | TV |  |  |  |
| 10 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 11 | 23409 | Duel Masters VS | TV | 5.73 |  |  |
| 12 | 21999 | Duel Masters Victory V3 | TV | 5.66 |  |  |
| 13 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 14 | 6262 | Manga Fairy Tales of the World | TV | 7.00 |  |  |
| 15 | 21997 | Duel Masters Victory V | TV | 5.81 |  |  |
| 16 | 430 | Fullmetal Alchemist: The Movie - Conqueror of Shamballa | Movie | 7.50 |  |  |
| 17 | 18321 | Kkomaeosa Ttori | Movie |  |  |  |
| 18 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 19 | 9613 | Big X | TV | 6.07 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.991, sem_top50_mean=0.542, sem_top50_p95=0.616, sem_top50_overlap_mean=0.607, sem_top50_any_match=0.90, top20_pools(A/B/C)=7/13/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=578, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=382, demo_override_top20=1, blocked_overlap=1631, blocked_low_sim=1978, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/4, theme_bonus_mean(top20/top50)=0.00000/0.00016, theme_bonus_max(top20/top50)=0.00000/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=2, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 3 | 32269 | Saving Mother | Movie |  |  |  |
| 4 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 5 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 6 | 5071 | Croket! | TV | 6.90 |  |  |
| 7 | 9768 | Shima Shima Tora no Shimajirou | TV | 5.93 |  |  |
| 8 | 9061 | RPG Densetsu Hepoi | TV | 6.44 |  |  |
| 9 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 10 | 5923 | Utsunomiko: Heaven Chapter | OVA | 6.06 |  |  |
| 11 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 12 | 30155 | Hoshi no Kirby: Taose!! Koukaku Majuu Ebizou | ONA | 5.95 |  |  |
| 13 | 18313 | Dokkaebi Gamtu | Movie |  |  |  |
| 14 | 7752 | Lotus Lantern | Movie | 6.18 |  |  |
| 15 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |
| 16 | 5760 | Dororo | TV | 7.27 |  |  |
| 17 | 9228 | Wanwan Chuushingura | Movie | 5.73 |  |  |
| 18 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 19 | 18321 | Kkomaeosa Ttori | Movie |  |  |  |
| 20 | 19687 | Kuiba 2 | Movie | 6.44 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.902, sem_top50_mean=0.466, sem_top50_p95=0.608, sem_top50_overlap_mean=0.713, sem_top50_any_match=0.94, top20_pools(A/B/C)=11/4/5, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=88, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=18, demo_override_top20=1, blocked_overlap=117, blocked_low_sim=4334, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/0, theme_bonus_mean(top20/top50)=0.00000/0.00000, theme_bonus_max(top20/top50)=0.00000/0.00000, top20_theme_overlap_count=0, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

Top 5 items by theme_stage2_bonus (within top50):

| Rank@50 | anime_id | Title | theme_overlap | theme_stage2_bonus |
|---:|---:|---|---:|---:|
| 25 | 20 | Naruto |  | 0.00000 |
| 37 | 121 | Fullmetal Alchemist |  | 0.00000 |
| 48 | 249 | InuYasha |  | 0.00000 |
| 34 | 1482 | D.Gray-man |  | 0.00000 |
| 36 | 1818 | Claymore |  | 0.00000 |

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 3 | 32269 | Saving Mother | Movie |  |  |  |
| 4 | 31838 | Ze Tian Ji | ONA | 6.82 |  |  |
| 5 | 7109 | Captain Fatz and the Seamorphs | TV | 6.44 |  |  |
| 6 | 5071 | Croket! | TV | 6.90 |  |  |
| 7 | 15915 | Magical Hat | TV | 5.68 |  |  |
| 8 | 4470 | Gene Diver | TV | 6.33 |  |  |
| 9 | 15579 | Shinkai Densetsu Meremanoid | TV | 5.66 |  |  |
| 10 | 8897 | Marine Boy | TV | 5.60 |  |  |
| 11 | 31892 | The Legend of Huainanzi | TV |  |  |  |
| 12 | 5440 | The Brave of Gold Goldran | TV | 6.99 |  |  |
| 13 | 7419 | Wrestler Gundan Seisenshi Robin Jr. | TV |  |  |  |
| 14 | 9106 | Hamos: The Green Chariot | TV | 6.25 |  |  |
| 15 | 10194 | The Legend of Blue | TV | 6.04 |  |  |
| 16 | 29687 | Duel Masters VSR | TV | 5.45 |  |  |
| 17 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 18 | 5760 | Dororo | TV | 7.27 |  |  |
| 19 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 20 | 23409 | Duel Masters VS | TV | 5.73 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.861, sem_top50_mean=0.471, sem_top50_p95=0.519, sem_top50_overlap_mean=0.380, sem_top50_any_match=0.72, top20_pools(A/B/C)=8/12/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=8, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=101, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=306, demo_override_top20=5, blocked_overlap=1233, blocked_low_sim=2701, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=4/9, theme_bonus_mean(top20/top50)=0.00040/0.00036, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=9, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=0, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31966 | Sword Gai | ONA | 5.61 |  |  |
| 2 | 30278 | Ghost Messenger Movie | Movie | 5.90 |  |  |
| 3 | 18919 | The Midnight★Animal | ONA |  |  |  |
| 4 | 27811 | Shaolin Wuzang | TV | 6.13 |  |  |
| 5 | 6067 | The Burning Wild Man | TV | 6.44 |  |  |
| 6 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 7 | 28685 | Tough Guy! | Movie | 5.21 |  |  |
| 8 | 4427 | Fight!! Ramenman | TV | 6.27 |  |  |
| 9 | 9691 | Kyomu Senshi Miroku | OVA | 5.66 |  |  |
| 10 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 11 | 25591 | Tokyo Juushouden: Fuuma Gogyou Denshou | OVA | 5.14 |  |  |
| 12 | 8146 | Spooky Kitaro: Giant Sea Monster | Movie | 6.17 |  |  |
| 13 | 5760 | Dororo | TV | 7.27 |  |  |
| 14 | 269 | Bleach | TV | 7.98 |  |  |
| 15 | 12061 | Twin Angels (2) | OVA | 5.50 |  |  |
| 16 | 8745 | Seikima II Humane Society: Jinrui Ai ni Michita Shakai | OVA | 5.82 |  |  |
| 17 | 1708 | Beast Fighter: The Apocalypse | TV | 5.29 |  |  |
| 18 | 2503 | Nangoku Shounen Papuwa-kun | TV | 6.32 |  |  |
| 19 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 20 | 2251 | Baccano! | TV | 8.35 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.883, sem_top50_mean=0.469, sem_top50_p95=0.531, sem_top50_overlap_mean=0.420, sem_top50_any_match=0.80, top20_pools(A/B/C)=11/9/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=7, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=1, laneB=110, theme_override=1, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=283, demo_override_top20=4, blocked_overlap=1143, blocked_low_sim=2803, bonus_fired=0, bonus_mean=0.00000, bonus_max=0.00000, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=0/5, theme_bonus_mean(top20/top50)=0.00000/0.00020, theme_bonus_max(top20/top50)=0.00000/0.00200, top20_theme_overlap_count=8, top20_overlap_meta=1.000, top50_overlap_meta=1.000, top20_moved_meta=0, top50_moved_meta=3, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 33309 | The Devil Ring | ONA | 6.02 |  |  |
| 2 | 31966 | Sword Gai | ONA | 5.61 |  |  |
| 3 | 30278 | Ghost Messenger Movie | Movie | 5.90 |  |  |
| 4 | 18919 | The Midnight★Animal | ONA |  |  |  |
| 5 | 6971 | Gegege no Kitarou (1971) | TV | 6.54 |  |  |
| 6 | 28685 | Tough Guy! | Movie | 5.21 |  |  |
| 7 | 33350 | Rakshasa Street | ONA | 7.54 |  |  |
| 8 | 19989 | Tatakae! Osper | TV |  |  |  |
| 9 | 18325 | The Silver Twilight | Movie | 5.51 |  |  |
| 10 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 11 | 25591 | Tokyo Juushouden: Fuuma Gogyou Denshou | OVA | 5.14 |  |  |
| 12 | 2694 | Tree in the Sun | TV | 7.14 |  |  |
| 13 | 5760 | Dororo | TV | 7.27 |  |  |
| 14 | 8745 | Seikima II Humane Society: Jinrui Ai ni Michita Shakai | OVA | 5.82 |  |  |
| 15 | 269 | Bleach | TV | 7.98 |  |  |
| 16 | 12061 | Twin Angels (2) | OVA | 5.50 |  |  |
| 17 | 9811 | Hanasaka Tenshi Tenten-kun | TV |  |  |  |
| 18 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 19 | 16498 | Attack on Titan | TV | 8.57 |  |  |
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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.863, sem_top50_mean=0.463, sem_top50_p95=0.532, sem_top50_overlap_mean=0.680, sem_top50_any_match=0.68, top20_pools(A/B/C)=15/5/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=1, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=581, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=245, demo_override_top20=0, blocked_overlap=1163, blocked_low_sim=2543, bonus_fired=3, bonus_mean=0.00074, bonus_max=0.00570, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=3/14, theme_bonus_mean(top20/top50)=0.00030/0.00056, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=15, top20_overlap_meta=1.000, top50_overlap_meta=0.980, top20_moved_meta=2, top50_moved_meta=13, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

| Rank | anime_id | Title | Type | MAL | Members | Flag |
|---:|---:|---|---|---:|---:|---|
| 1 | 31339 | Drifters | TV | 7.88 |  |  |
| 2 | 32543 | Lu Shidai 2nd Season | ONA | 6.69 |  |  |
| 3 | 21491 | Ninjaman Ippei | TV | 6.03 |  |  |
| 4 | 12887 | Uchuu Shounen Soran | TV | 5.87 |  |  |
| 5 | 8999 | Origami Warriors | TV | 6.40 |  |  |
| 6 | 31233 | Lu Shidai | ONA | 6.43 |  |  |
| 7 | 33605 | Spiritpact | ONA | 7.20 |  |  |
| 8 | 5760 | Dororo | TV | 7.27 |  |  |
| 9 | 5997 | Sabu & Ichi's Arrest Warrant | TV | 6.56 |  |  |
| 10 | 20 | Naruto | TV | 8.01 |  |  |
| 11 | 988 | Shinshaku Sengoku Eiyuu Densetsu: Sanada Juu Yuushi The Animation | TV | 6.01 |  |  |
| 12 | 10620 | The Future Diary | TV | 7.38 |  |  |
| 13 | 1 | Cowboy Bebop | TV | 8.75 |  |  |
| 14 | 8215 | Genji Tsuushin Agedama | TV | 6.52 |  |  |
| 15 | 3021 | Wingman | TV | 6.54 |  |  |
| 16 | 6056 | Sasuke | TV | 6.74 |  |  |
| 17 | 7522 | Tai Chi Chasers | TV | 6.36 |  |  |
| 18 | 3588 | Soul Eater | TV | 7.85 |  |  |
| 19 | 121 | Fullmetal Alchemist | TV | 8.11 |  |  |
| 20 | 1355 | Dark Warrior | OVA | 4.83 |  |  |

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
Diagnostics: K_sem=300, K_meta=300, sem_conf=(neural/high) 0.933, sem_top50_mean=0.493, sem_top50_p95=0.557, sem_top50_overlap_mean=0.900, sem_top50_any_match=0.90, top20_pools(A/B/C)=3/17/0, shortlist=600/600, stage1_off_type_allowed=0, top20_off_type=3, off_type_sim_min=0.00000, off_type_sim_mean=0.00000, off_type_sim_max=0.00000, top20_tfidf_nonzero=0, embed_blocked%=0.0%, tfidf_blocked%=0.0%, laneA=0, laneB=163, theme_override=0, seed_has_shounen_demo=True, seed_demo_tokens=[shounen], demo_override_admitted=243, demo_override_top20=0, blocked_overlap=897, blocked_low_sim=3262, bonus_fired=4, bonus_mean=0.00145, bonus_max=0.00980, tfidf_fired=0, tfidf_mean=0.00000, theme_bonus_fired(top20/top50)=15/30, theme_bonus_mean(top20/top50)=0.00150/0.00120, theme_bonus_max(top20/top50)=0.00200/0.00200, top20_theme_overlap_count=16, top20_overlap_meta=0.950, top50_overlap_meta=1.000, top20_moved_meta=2, top50_moved_meta=7, top20_overlap_tfidf=1.000, top50_overlap_tfidf=1.000, top20_moved_tfidf=0, top50_moved_tfidf=0

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
| 15 | 17315 | Shin Pro Golfer Saru | TV |  |  |  |
| 16 | 2758 | Shippuu! Iron Leaguer | TV | 7.15 |  |  |
| 17 | 23737 | Neko Pitcher | TV | 6.04 |  |  |
| 18 | 9284 | Bakuhatsu Gorou | TV | 5.60 |  |  |
| 19 | 23011 | Otoko Doahou! Koushien | TV |  |  |  |
| 20 | 10323 | Golden★Kids | ONA | 5.25 |  |  |

