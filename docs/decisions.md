# Decision Log

A dated record of project decisions that are not derivable from the code: what was decided, why,
and what would change the answer. Newest first.

---

## 2026-10-20 — UI redesign closed: what shipped, what was deferred

**Status:** Closed. Source: Task 4.2 of [MARS_UI_REDESIGN_PLAN.md](plans/MARS_UI_REDESIGN_PLAN.md);
summary page [ui_design.md](ui_design.md).

**Scope that shipped.** The Subtle / Signal OVA direction (entry below) across the header, cards
and sidebar. Every color, font, spacing and radius comes from `src/app/theme_tokens.py`; the
Streamlit theme and `app/styles/tokens.css` are generated from it, and
`tests/test_theme_tokens.py` fails on drift or on any text pair under 4.5:1 (the pre-redesign
muted text was 2.18:1). All CSS moved to `app/styles/`, with no `st-emotion-cache-*` selectors.
Loading, empty and error states (Task 3.1), phone width (3.2), an accessibility pass (3.3,
[A11Y_PASS.md](redesign/A11Y_PASS.md)) and the audit fixes F1, F2, F6, F7, F8, F12 and F18
(3.4, [UX_PLAN.md](redesign/UX_PLAN.md)). The ranking pipeline, models, evaluation and every
published number were out of scope and untouched. The deployed warm time to first card stayed
within 1 s of the pre-redesign median ([DEPLOYMENT.md](DEPLOYMENT.md) § Performance). The README
GIF and still were re-recorded on the final UI.

**Deferred.**
- **Texture and motion (Task 2.6 scanlines, VHS hover).** Ruled out by the Subtle pick; only the
  reduced-motion rule shipped.
- **Framework migration** (Reflex, or React over a FastAPI wrapper). Streamlit's limits did not
  block any high-impact audit item.
- **A light "daytime broadcast" theme**, **sound**, and **visual regression in CI** (needs a
  pinned browser and font set). All in the plan's Phase 5.
- **F14, Browse starts empty**, and **F15, the explanation repeats the seed title.** The first is
  a product decision (a preselected genre), the second belongs to the explanation text, not the
  visual layer.

**Known gap.** `scripts/capture_ui_baseline.py` no longer completes its phone-width For me step
(the demo-profile button is outside the viewport in the collapsed-then-opened sidebar), and its
full-page height probe now stops seed mode after the first two cards. The Task 4.2 desktop
set in `docs/redesign/after_4_2/` was captured before the phone step failed.

**What would change this.** A reviewer reading the app as a generic dark theme: add the
episode-style section headers first (the cheapest Title-card piece, per the entry below). A
Streamlit upgrade past 1.38 that breaks the `data-testid` selectors: the live check and the
capture script are the first things to rerun.

---

## 2026-10-19 — Redesign direction: Subtle, Signal OVA palette, Mincho titles, subtitle line

**Status:** Adopted (owner pick). Source: Task 1.3 of
[MARS_UI_REDESIGN_PLAN.md](plans/MARS_UI_REDESIGN_PLAN.md); mockups in
[redesign/mockups/index.html](redesign/mockups/index.html), view
`#palette=ova&font=mincho&explain=subtitle`, Subtle frames.

**Context.** Task 1.1 had settled on direction A (cel title card at night). Task 1.3 drew the
header, a real card (Serial Experiments Lain, the first result for the Steins;Gate seed) and
the top of the sidebar at three intensities. Subtle has palette and type only. Title card adds
an outlined wordmark, episode-style headers and hard offset shadows. Full broadcast adds
scanlines, a VHS hover and katakana. A second round added toggles for three dark palettes,
two display faces and two explanation-line styles.

**Decision.**
- **Intensity: Subtle.** No hard shadows, outlined display type, episode headers, scanlines,
  VHS motion or decorative katakana.
- **Palette: Signal OVA.** Plum-black background `#110D14`, panel `#1E1823`, signal red
  `#FF4A4A`, cyan `#4FD3E6`, fansub yellow `#FFD84A`. It replaces Sunset night (navy, sunset,
  magenta, sakura, teal).
- **Display face: Shippori Mincho B1 (800)** in place of Dela Gothic One.
- **Explanation line: subtitle style.** Yellow, bold, with a 1 px ink outline, like a 90s VHS
  fansub. It's the only stylized text on the card.

Tokens (`src/app/theme_tokens.py`), the generated `app/styles/tokens.css` and
`design-system/mars/MASTER.md` were updated in the same change. The color roles were renamed
to fit the palette: `sunset` → `signal`, `sakura` → `subtitle`, `teal` → `cyan`. `magenta` is
gone. The shape and texture tokens for hard shadows, the 3 px border and scanlines were removed.

**Why.** The era comes through palette, the serif title face and one signature detail. Texture
and heavy framing don't add much on top of that. Subtle is also the cheapest and safest of the
three: no texture or motion to fit within the first-card budget or reduced-motion rules, and
nothing to break when Streamlit reflows columns at phone width. The subtitle line makes the
plain-language explanation the second thing a visitor reads on each card, which is what Task 2.4
asks for. Signal OVA is the darkest of the three palettes and the most specific to late-90s
OVAs. Its yellow doubles as the subtitle color. All its text pairs pass 4.5:1 (weakest: signal
red on panel, 5.2). The tiers avoid red, so "Good match" doesn't read as an error. Mincho reads
as a title card; Dela Gothic One reads as more playful and more recent.

**Ruled out for later tasks.** Task 2.3: the outlined wordmark with an offset shadow, and the
episode-style title cards. Task 2.4: the 3 px border and hard-shadow card. All of Task 2.6
(scanlines, VHS hover). The plan's checklists were amended to match.

**What would change this.** At real size the app reads as a generic dark theme rather than 90s
anime. Then add back the episode-style section headers first, since they're the cheapest piece
of Title card with no motion or texture. Or the subtitle line tests poorly for readability over
a long result list; then fall back to a plain `text` sentence with a yellow left rule.

## 2026-10-19 — UI UX Pro Max skill files are not committed; its design-system output is

**Status:** Adopted. Source: Task 0.1 of
[MARS_UI_REDESIGN_PLAN.md](plans/MARS_UI_REDESIGN_PLAN.md).

**Context.** The redesign takes its design decisions from the UI UX Pro Max Claude Code skill.
`npx ui-ux-pro-max-cli init --ai claude` installs it project-locally under `.claude/skills/`,
together with six sibling skills from the same package (`banner-design`, `brand`, `design`,
`design-system`, `slides`, `ui-styling`). When asked to persist a design system, the skill writes
`design-system/<project>/MASTER.md` and per-page overrides at the repo root.

**Decision.** `.gitignore` excludes all seven installer-created skill directories. The root
`design-system/` directory is tracked.

**Why.** The skill directories are third-party code and data, reinstallable with one command;
committing them would vendor someone else's package into the repo and make its diffs look like
project work. `design-system/` holds the decisions made *for this project* (palette, type,
page rules); the tokens module and CSS are derived from them, so they need history and review
like any other source file. The ignore patterns are anchored (`/.claude/skills/design-system/`)
so the skill named `design-system` does not hide the project's `design-system/` folder.

**What would change this.** The skill is modified locally (then the modified copy is project code
and gets tracked), or the CLI stops being installable at a working version (then vendor a pinned
copy).

---

## 2026-10-19 — A learned reranker beats the hand-weighted blend; served behind `RERANKER_MODE=learned`

**Status:** Adopted behind a flag (default `hand`). Source: Task 2.3, `reports/learned_reranker.md`
(`scripts/train_learned_reranker.py --sample-users 1000 --k 10`).

**Context.** Stage 2 blends hand-set signals; the CF part is the Task 0.6 Optuna re-tune
(mf 0.048 / knn 0.952 / pop 0.0003), NDCG@10 0.0658 on the reporting cohort. The question was
whether learning the combination beats it.

**Experiment.** LightGBM LambdaRank reorders each user's top 200 blend candidates, so both
rankings see identical candidates (the hand-weighted row reproduces the ablation's 0.0658 exactly).
Training users are 4,000 validation users outside the reporting cohort, split 80 / 20 for early
stopping; three seeds vary that split and LightGBM's bagging. All features come from the train
split: the CF scores, plus content and metadata affinities to the user's train history.

**Result.**
- *CF signals alone:* 0.0683 mean, a tie (every seed's paired CI spans 0). The Optuna weights
  already get what three CF scores can give.
- *All signals:* **0.0931** mean (0.0963 / 0.0926 / 0.0904), +0.0273 over the blend, against a
  seed spread of 0.0059. Every seed's paired CI clears zero; the narrowest is
  [+0.0147, +0.0366]. Coverage@10 is unchanged (0.099–0.103 vs. 0.103). The gain comes from
  the content signals the CF blend never sees: synopsis TF-IDF affinity has the largest gain
  share (0.17), then blend rank and kNN rank.
- *Ceiling:* the held-out item is among the 200 candidates for only 37% of users. Reordering
  cannot reach the rest, and the implicit ALS (0.1890 alone, previous entry) is the larger
  lever.

**Decision.** The plan's rule (gain > seed spread *and* paired CI excludes 0) is met, so the
seed-42 model is served in the personalized pipeline only, behind `RERANKER_MODE=learned`.
The default stays `hand`, so the deployed demo is unchanged until the owner flips it. Seed
mode, Browse and the seedless baseline are untouched. `lightgbm` moves into `requirements.txt`
because the loader unpickles every `models/*.joblib`.

**Train / serve differences, accepted.** The ranker was trained on train-split artifacts; the app
scores with the full-fit artifacts and a profile's folded-in MF embedding, not a trained user row.
`ServedReranker` carries the train-split popularity table, and MF gets `global_mean` back, so
both features stay on their training scales. A test pins serve-time scores to training-frame
predictions. The MF embedding's distribution is the one difference no artifact can remove. MF
features have 7% of the gain between them, so the offline number is the best estimate there is
but not a measurement of the served path.

**What would change this.** Swapping the first stage to implicit ALS (the previous entry) changes
the candidates and the features, so the ranker would have to be retrained and re-measured; the
flag stays until then. A drop in the live path's quality on the golden-query or demo profiles
would argue for leaving the default at `hand`.

---

## 2026-10-18 — Implicit ALS is a candidate to replace FunkSVD; two eval exclusion faults fixed

**Status:** Candidate (not served). Source: Task 2.1, `reports/mf_diagnostic.md`
(`scripts/diagnose_mf.py --sample-users 1000`).

**Context.** On the corrected protocol FunkSVD sat below popularity, after falling from the
0.0504 first published. MF still drives the *For me* user vector (`src/models/user_embedding.py`)
and is 4.8% of the Balanced CF blend.

**Findings.**
- *Snapshot.* The parquet from before the 2026-03-14 refresh (`9813b02d`) holds the same 7.8M rows
  in the same order as today's. Only the dtypes changed (int64 → int32), so the refresh moved
  nothing.
- *The drop was the leak.* Crossing the old and new holdout samplers with the old protocol
  (full-data fit) and the new one (train split) gives four cells. The old setup reproduces the
  published 0.0504 exactly, and popularity's 0.0412 too. Moving to the train split costs
  −0.0230 / −0.0191 (both CIs clear of zero), while the sampler change is a tie (+0.0008). This
  **reverses the 2026-09-16 entry's measurement** (mean −0.0018 on a 120K-row slice): at full
  scale, a FunkSVD fit on the held-out rows does lift them into the top 10.
- *Objective.* FunkSVD treats the 1.48M "watched, not rated" interactions (Kaggle −1, clipped to
  0 by `clean_interactions`) as the worst possible score. It ranks such a holdout at a median 9,463
  of 11,200. Refitting without those rows hurts it (−0.0178 [−0.0266, −0.0099]). A popularity prior
  helps (+0.0171), but only by turning the list into popularity.
- *Implicit ALS* (`src/models/als_implicit.py`: Hu–Koren–Volinsky with uniform confidence 1 + α,
  64 factors, α = 5 tuned on users disjoint from the cohort) scores **0.1890 [0.1687, 0.2086]**.
  That beats FunkSVD by +0.1608, CI [+0.1408, +0.1801], and item-kNN by +0.1258, CI
  [+0.1032, +0.1468]. It is also the best model on liked holdouts (≥ 8) alone.

**Eval faults fixed in the same change.** Both moved published numbers, and both are now pinned
by tests in `tests/test_eval_artifacts.py`:
- `FunkSVDRecommender.recommend` scored an unknown user all-zero and returned items in index order.
  That order is first appearance in the file, so it worked as a popularity fallback. 33 cohort
  users have no train history; five got hits this way, worth +0.0044. It now returns `[]`, as kNN
  does. MF goes 0.0326 → 0.0282 and RRF 0.0586 → 0.0547.
- kNN eval used the model's own seen-mask, and `getcol().nonzero()` drops explicit zeros, so 0-rated
  train items stayed eligible: 139 of 10,000 top-10 slots. `knn_eval_scores` now excludes by train
  history, as MF and popularity already did. kNN goes 0.0628 → 0.0632. This is the Task 0.4 lesson
  again: an exclusion set must come from the eval split, never the model.

**Decision.** Record ALS as the serving candidate for the MF role and do not swap it here. The swap
touches `user_embedding.py`, the personalized gate and the artifact loader, and it needs its own
task.

**What would change this.** This protocol holds out one random *watched* item, which is exactly
what an implicit objective is trained to predict, so part of ALS's lead is the protocol's choice of
target. The liked-only bucket is the first check and it holds. Before serving, confirm on a graded
or liked-only holdout. Also check that ALS's user vector can be built from a profile the way
`generate_user_embedding` builds FunkSVD's: ALS needs a least-squares solve against fixed item
factors, not a weighted average.

---

## 2026-10-18 — Keep the demo awake with a scheduled browser visit; no Hugging Face mirror

**Status:** Adopted (owner decision; implementation is Task 1.9). Answers the "what would change
this" of the 2026-09-16 hosting entry: hosting stays on Community Cloud.

**Context.** Task 1.8 measured the deployed app awake: first card at a median of 10.9 s (range
10.9–11.2 s, three runs). Waking it reboots the container, which reloads every model before the
first card (locally that load is ~20 s of a 28.5 s first card). The cold start itself was not
measured: the one run that found the app asleep lost its reading. The owner already knew the
wake was slow enough to lose visitors and decided not to spend three sleep cycles confirming it.
Memory is not a constraint (519 MB peak against the 1 GB limit). The goal is that a visitor
does not wait for a wake, without paying for hosting.

**Options considered.**
- *Hugging Face Spaces mirror (free tier).* The 2026-09-16 entry named it as the first
  alternative, but free `cpu-basic` Spaces also pause after 48 hours of inactivity, so it would
  sleep less often, not never. Hugging Face's Spaces overview now also says compute Spaces
  (Gradio or Docker) need a paid plan; not confirmed against the pricing page. Either way it adds
  a second host that can break or serve a stale build.
- *Paid always-on hardware (Spaces or elsewhere).* Removes sleep entirely; ruled out on cost.
- *Lazy-load or memory-map the artifacts.* Shortens a wake but does not prevent it, and since the
  app serves item-kNN (2026-10-18 entry below) the largest artifact (189 MB) is needed for the
  first card anyway. Deferring it would move the wait, not remove it.
- *Keep it awake with a scheduled visit.* A GitHub Actions job opens the app in a headless
  browser every few hours, well inside the sleep window. A plain HTTP request does not count:
  `curl` gets a `200` from a sleeping app (DEPLOYMENT.md, "Verify From Outside"), and only a
  browser session wakes it.

**Decision.** Keep the app awake with a scheduled headless-browser visit that waits for the first
card. The Hugging Face mirror stays deferred.

**Why.** It costs nothing, changes nothing in the app, and keeps one host. It also answers the
objection that ruled out the mirror, "a second thing that can break silently": the visit fails
the job when no card appears, and GitHub emails the owner, so a broken demo surfaces within
hours rather than when a reviewer finds it. Each run logs time to first card, and a run that
finds the app asleep is a cold-start reading for free.

**Known limits.** A push to `main` redeploys and reboots the app, so the first visitor after a
push pays the model load unless the job also runs after pushes. GitHub disables scheduled
workflows in a repository with no commits for 60 days (it emails first; re-enabling is one
click). Community Cloud's exact sleep window is not pinned down here; the schedule starts at
every 6 hours and is tightened if the job's logs show it finding the app asleep.

**What would change this.** Community Cloud's terms or behavior stop treating scheduled visits as
traffic (the app sleeps despite the job); the app outgrows 1 GB; or paid hosting becomes
acceptable. A Spaces deployment on upgraded hardware is then the next option.

---

## 2026-10-18 — The app serves item-kNN: Balanced is the re-tuned blend, Diversity is kNN alone

**Status:** Adopted (supersedes the "served weights stay" decision of 2026-10-17)

**Context.** The 2026-10-17 entry left the app on its old weights because it had no kNN
component. `ItemKNNRecommender.score_all` only scores a *training* user, and an app visitor is
never one. `knn_scores_from_ratings` (`src/app/recommender.py`) builds the same profile from any
`{anime_id: rating}` dict. It applies the same centring, rating power, shrinkage and popularity
prior, and matches `score_all` to ~1e-7 on real training users, at ~40 ms per request. The app
builds one vector per request and leaves the shared engine untouched:

| Path | kNN profile from |
|:---|:---|
| Seed-based | the seed titles, each counted as one liked item (no centring: equal weights would centre to zero) |
| Personalized | the profile's ratings, mean-centred like the training users |
| Seeds + personalization | seeds rank the pool; the profile's kNN re-ranks it, mixed by the strength slider like personal MF |
| Seedless (no seeds, no profile) | nothing to build from: ranks by MF with the old popularity prior (`COMMUNITY_BASELINE_WEIGHTS`), whatever preset is selected |

**Decision.** Balanced serves the re-tuned blend (mf 0.0475 / knn 0.9522 / pop 0.0003, now
`DEFAULT_HYBRID_WEIGHTS`). Diversity serves item-kNN alone. `STAGE2_HYBRID_CF_WEIGHT` goes from
0.15 to 0.42.

**Why the blend and not kNN alone for Balanced.** The plan preferred the simpler option, and
offline the two are tied (+0.0031, CI [−0.0033, +0.0097]). The app has one path the table does
not have, though: a seedless run has no kNN profile. With kNN alone, every candidate there would
score 0. The blend keeps the same code path meaningful wherever a profile exists, and the MF term
is a tiebreak where one doesn't. Item-kNN alone is still served, as Diversity. It is the measured
choice for that label: higher coverage (0.116 vs 0.103) and lower Gini (0.728 vs 0.760) at tied
NDCG. It replaces an "illustrative" 0.80/0.18/0.02 preset that was never measured, and that
before this change was *more* popularity-weighted, not less.

**Popularity scale.** The tuned `pop` weight was fit on the offline popularity score
(log-count × mean rating, max ~82). The app's popularity vector is kNN's normalised log-count
(max 1), so the served `pop` term is about 80× smaller than the one tuned. Checked on the
reporting cohort with the train-split artifacts: the tuned blend reproduces at 0.0658; with
app-scale popularity it scores 0.0696 (paired +0.0038, CI [+0.0009, +0.0068]), with no
popularity term 0.0697. The served form is therefore no worse than the measured one. 0.0696 is
not published as a result: it was read off the reporting cohort after the fact, and the gain is
small.

**Stage-2 coefficient.** 0.15 was set against an MF-dominated CF score: mean-user MF, ~6.2 ± 0.3
across a shortlist. The served CF score is ~0.5 ± 0.1. Across 12 popular seeds, the spread of CF
scores among CF-covered candidates fell by a median factor of 2.8, so 0.15 × 2.8 ≈ 0.42 keeps CF's
influence within the shortlist where it was. One effect is intended and visible: items with no CF
data (titles newer than the ratings snapshot) used to trail CF-covered ones by ~0.9 in score,
because MF scores *everything* near 6. They now trail by ~0.2. At 0.15, *Demon Lord 2099* reached
#3 for an FMA:B seed; at 0.42 it sits at #5, and the CF-covered *Steins;Gate* movie and *The
Future Diary* return to the Steins;Gate top 10.

**Limits.** The ablation scores the CF blend on its own. In the app it is one Stage-2 signal
next to genre, synopsis and metadata signals, so the end-to-end ranking is unmeasured. The "kNN"
share on cards still mixes real kNN with content signals (`STAGE2_RAW_KNN_*`); that is a display
question for the card-explanation task. `scripts/evaluate_phase4_golden.py` keeps its own copy of
the old 0.93/0.07 `hybrid_cf_score`. The ablation is not regenerated, and `evaluate_hybrid.py`
keeps `hybrid_weighted` pinned to the legacy weights, so its labels keep their published meaning.

**What would change this.** An end-to-end offline evaluation of the Stage-2 ranking, which would
let the 0.42 coefficient be tuned rather than matched. Or a seedless path that is itself
personal, which would remove the reason to keep MF in the Balanced blend.

---

## 2026-10-17 — Blend re-tuned offline on disjoint users; the app keeps its weights until it can serve kNN

**Status:** Superseded 2026-10-18 (the app now serves kNN; see the entry above)

**Context.** `BALANCED_WEIGHTS` / `DEFAULT_HYBRID_WEIGHTS` (mf 0.931 / knn 0.066 / pop 0.003)
came from an Optuna sweep run while item-kNN could not score, and that sweep drew its users with
the same seed from the same population as the 1,000-user reporting cohort. Task 0.6 re-ran the
sweep on 1,000 validation users drawn from **outside** the reporting cohort
(`reporting_and_tuning_users` in `src/eval/splits.py`; overlap 0, recorded in
`experiments/optuna_studies/hybrid_weights_best.json`), 100 TPE trials, seed 42. The weights are
searched log-uniformly because the three sources are summed raw and their scales differ by orders
of magnitude (kNN similarity about ±0.5, MF predicted rating 2–10, popularity 0–80).

**Result** (reporting cohort, NDCG@10, 95% paired bootstrap CIs, 1,000 resamples):

| Comparison | Difference | 95% CI |
|:---|---:|:---|
| Re-tuned blend (mf 0.048 / knn 0.952 / pop 0.0003) − popularity | +0.0312 | [+0.0175, +0.0454] |
| Re-tuned blend − MF | +0.0332 | [+0.0222, +0.0448] |
| Re-tuned blend − item-kNN alone | +0.0031 | [−0.0033, +0.0097] |
| RRF − item-kNN alone | −0.0042 | [−0.0141, +0.0056] |
| Shipped blend − MF | −0.0002 | [−0.0053, +0.0041] |
| MF − popularity | −0.0021 | [−0.0139, +0.0102] |

The re-tuned blend scores 0.0658 [0.0535, 0.0795], against 0.0324 for the shipped weights. It is
effectively item-kNN with a small MF tiebreak, and it is **not distinguishable from item-kNN
alone** (0.0628) or from RRF (0.0586). All three clearly beat popularity, MF and the shipped
blend. Separately, "MF is below popularity", as stated after Task 0.4, is not supported: the
interval spans zero.

**Decision.** The served weights stay as they are. The re-tuned weights are recorded as the offline
result (`hybrid_weighted_tuned` in the ablation) and not written to `src/app/constants.py` or
`src/models/constants.py`.

**Why.** The app cannot serve this blend by changing constants. `app/pipeline_runner.py` builds
`HybridComponents(mf=..., knn=None, ...)`; the kNN artifact is read only for its item-popularity
vector. The app's CF signal is therefore `w_mf·MF + w_pop·pop`, and the "kNN" share on cards is
made up of content signals (genre overlap, seed coverage, synopsis similarity). Setting
`w_mf = 0.048` would shrink the MF term about 20× beneath Stage-2 coefficients hand-tuned around
its current magnitude, while adding no kNN. The app would get a different and unmeasured ranking,
not the one measured offline. This is the stop condition the plan sets for RRF ("if serving it
would change the pipeline contract, ship the best weighted blend and record the rest as a
follow-up"). Here the condition applies to the weighted blend itself, because its winning
ingredient is not wired in.

**What would change this.** A follow-up task wires per-user item-kNN scores into the app
(from the seeds in seed mode, from profile ratings when personalized), populates
`components.knn`, and re-checks the Stage-2 coefficients. Then the re-tuned weights, or kNN alone,
can be served. Because the two are tied, the simpler kNN-alone option is a legitimate choice.
README, model card and `reports/phase4_evaluation.md` §8 say plainly that the app does not yet
serve the best offline ranker.

---

## 2026-09-16 — The evaluation table is one cohort from one run; metric collisions fail the build

**Status:** Adopted

**Context.** The published ablation (`reports/phase4_ablation.{csv,md}`) was ten rows all labeled
`popularity`, spanning three different cohort sizes, and the README's headline `+43% NDCG / +61%
MAP` was popularity@500 measured against popularity@300 — the baseline against itself. Three
faults compounded: `aggregate_phase4_metrics.py` only read a `metrics_by_k` array that no file in
`experiments/metrics/` has ever contained, so it could not run at all and the committed parquet
came from some other route with no dedupe; `generate_phase4_ablation.py` filtered on the model
names `mf` and `hybrid`, which do not exist (`mf_sgd` and `hybrid_weighted` do), dropping every
CF row; and `compute_lifts` took `iloc[0]` as the baseline, silently picking one of the duplicate
`popularity` rows.

The parquet also held three conflicting `hybrid_weighted@1000` rows, one of them bit-identical to
`popularity@1000` on NDCG and MAP. **That is not a mislabeled run or a silent fallback.** The
three rows are three different weight vectors written under one model label:
`{mf 0.309, knn 0.022, pop 0.6}`, `{mf 0.0004, knn 0.039, pop 0.4}`, and the shipped
`DEFAULT_HYBRID_WEIGHTS`. In the second, the MF weight is effectively zero and popularity
dominates, so the blend degenerates to a popularity ranking — the top-10s coincide and the
metrics match, with Gini differing only in the fifth decimal. The defect is that the parquet
recorded no run configuration, so three experiments were indistinguishable after the fact.

**Decision.** Every published number comes from one cohort of one run. `aggregate_phase4_metrics.py`
reads the flat schema the eval scripts actually emit, keeps the latest run per
`(model, K, users_evaluated)`, carries `seed`, `generated_at` and `source` into the parquet, and
takes `--cohort` to select a single `users_evaluated`. `generate_phase4_ablation.py` refuses a
frame spanning more than one cohort, and `compute_lifts` raises rather than choosing among
duplicate baseline rows. Two differently-labeled models sharing an identical `(ndcg, map)` pair
in one cohort fails the aggregator, overridable with `--allow-metric-collisions` once understood.

**Why.** Each guard is placed where the specific published error would have been caught. A
degenerate blend that scores exactly like popularity is worth stopping on even when explainable:
it means a weight vector is doing nothing, which is a result, not a rounding artifact.

**What would change this.** A deliberate multi-cohort study (a sample-size sensitivity curve, for
example) would need the ablation's single-cohort rule relaxed to an explicit "compare within
cohort" grouping rather than an error. Recording the weight vector as a parquet column would let
several hybrid configurations coexist under one label, which is the cleaner fix if hybrid weight
variants ever need to appear in the same table.

---

## 2026-09-16 — One CF trainer; offline evaluation gets its own train-split artifacts

**Status:** Adopted

**Context.** Task 0.3 left a gap: `scripts/train_mf_sgd.py` and `scripts/train_knn_sklearn.py`
wrote `*_v1.0.joblib`, a stem nothing read any more. Looking at why they existed turned up two
findings.

First, they held nothing worth keeping. Their "tuned" hyperparameters — `n_factors=64, lr=0.005,
reg=0.05, n_epochs=10` for MF; `normalize_items/center_ratings/popularity_weight=0.02` for kNN —
are byte-for-byte the class defaults, so `save_artifacts.py`'s bare `FunkSVDRecommender()`
already produced the same recipe. (This also explains the difference between `mf_sgd_v1.0` and
the served stem recorded in the entry below: same recipe, a catalog six days apart, not a
configuration change.)

Second, and the reason this is not a cleanup: **`save_artifacts.py` fits on the full
`interactions.parquet`, and the eval scripts then scored those artifacts against a holdout
carved out of the same table.** `build_validation` finds no `split` or `timestamp` column, so it
takes the random per-user holdout branch; MF and kNN had therefore trained on every validation
pair they were scored on. Popularity is computed from `train_df` inside the eval script, so it
was scored honestly. The `_v1.0` path had the same leak, so this predates Task 0.3.

**How much it actually moved the numbers: not measurably.** The first draft of this entry assumed
the leak inflated the published figures. It was measured instead — same 120K-row slice, same
holdout, same 300 users, MF fit with and without the validation rows, three seeds:

| Seed | Fit on train+val | Fit on train only | Delta |
|---|---|---|---|
| 42 | 0.029901 | 0.031274 | −0.001373 |
| 7 | 0.026845 | 0.030940 | −0.004094 |
| 1234 | 0.031765 | 0.031834 | −0.000069 |

NDCG@10; mean delta −0.0018 against a between-seed spread of 0.0040. The model that saw the
validation rows was never the better one, and the difference sits below SGD seed noise. That is
what a single held-out rating per user should do: one extra observation among ~100 per user, with
`lr=0.005`, ten epochs and L2 regularization, is not enough to surface that item in a top-10 out
of 5,397. Leakage bites when a model can memorize; this configuration cannot.

Limits of that measurement: MF only, a 1.5% slice, one held-out item per user. kNN is unmeasured.

**Decision.** One trainer, two splits, two destinations:

| Command | Fits on | Writes to | Used by |
|---|---|---|---|
| `python scripts/save_artifacts.py` | all interactions | `models/`, timestamped | the app |
| `python scripts/save_artifacts.py --split train` | train split only | `experiments/artifacts/` (git-ignored) | offline evaluation |

`src/eval/eval_artifacts.py` owns fitting and caching; the seven eval scripts call
`load_eval_models(train_df)` and no longer touch `models/` at all. The cache carries a
fingerprint sidecar (`n_rows`, `n_users`, `n_items` of the split it was fit from) and refits on a
mismatch, so a stale artifact cannot be scored silently. `train_mf_sgd.py` and
`train_knn_sklearn.py` are deleted.

**Why these shapes.** Serving a model trained on everything is correct; measuring it that way is
not — the two needs genuinely want different artifacts, so the fix is two outputs, not one
compromise. Refitting per eval run would be honest but slow enough to discourage running the
evaluation, hence the cache; a fingerprint is what keeps the cache from reintroducing a quieter
version of the same bug.

The eval artifacts must live outside `models/`. The loader globs `startswith("mf_")`, so an
`mf_sgd_trainsplit_*.joblib` sitting beside the served one would make MF selection ambiguous and
fail the app at startup — the failure Task 0.3 just removed. `test_eval_artifacts.py` asserts the
two directories stay distinct.

A `--split full` run prints the `MF_MODEL_STEM` / `KNN_MODEL_STEM` lines to paste rather than
rewriting `src/models/constants.py`, so repointing the served model stays a reviewed one-line
diff instead of a side effect of retraining.

**Consequence for Task 0.4.** Run `save_artifacts.py --split train` before the cohort run, and
expect the numbers to land close to where they are. The reason to do it is not that the old
figures are inflated — measured, they are not — but that "the model trained on the rows it was
scored against" is a question a reviewer can ask about a portfolio project and the answer has to
be "it didn't". Task 0.4 is regenerating every number anyway, so the correct-by-construction
version costs one command.

**What would change this.** A real temporal split (a `timestamp` column in
`interactions.parquet`) would let train/val be defined once in the data rather than reconstructed
per run, and the fingerprint cache could key on the split label instead of its shape.

---

## 2026-09-16 — One artifact stem per model family; six duplicate/stale `.joblib` files pruned

**Status:** Adopted

**Context.** `models/` carried 11 LFS artifacts, ~650 MB. `git lfs ls-files -s` showed all three
`item_knn_sklearn` files sharing one object id (`14808c1048`) — three pointers to identical
bytes. The MF family was not a duplication problem but a correctness one: `mf_sgd_v1.0`
(`e31310c952`) is a *different model* from `mf_sgd_v2025.11.21_202756` / `v2026.03.14_002417`
(both `1358863976`), and every evaluation script hard-coded `_v1.0` while the app loaded
`v2025.11.21_202756`. The published metrics therefore described a model the app does not serve.

A second, quieter failure came from the same cause. With two candidates and no preferred stem,
`_select_model_stem` raises "ambiguous"; the loader catches that for the optional families. No
env var set `APP_SYNOPSIS_TFIDF_STEM` or `APP_SYNOPSIS_EMBEDDINGS_STEM` anywhere in the repo, so
both synopsis TF-IDF and synopsis embeddings were silently **not loading** in the app.

**Decision.** One artifact per family, named by one constant:

| Family | Surviving stem | Why |
|---|---|---|
| MF | `mf_sgd_v2025.11.21_202756` | Byte-identical to the 2026.03 copy; already what the app prefers |
| kNN | `item_knn_sklearn_v2025.11.21_202756` | Byte-identical to both other copies |
| Synopsis TF-IDF | `synopsis_tfidf_v2026.03.14_001647` | Latest catalog build |
| Synopsis embeddings | `synopsis_embeddings_v2026.03.14_001718` | Latest catalog build |
| Synopsis neural | `synopsis_neural_embeddings_v2026.01.31_235728` | Only build; unchanged |

The other six files are removed from the tree. `MF_MODEL_STEM` / `KNN_MODEL_STEM` live in
`src/models/constants.py` and are re-exported by `src/app/constants.py`, so scripts do not import
from `src.app`.

**Why.** LFS storage is billed and cloned; three pointers to one 189 MB blob buy nothing. More
importantly, a single stem per family is what makes Task 0.4's evaluation table honest — the
`_v1.0` literal is exactly how the published metrics came to describe the wrong MF model, and a
literal that can drift from the app is the bug, not the particular wrong value. Pruning to one
candidate also restores the synopsis families without introducing env vars.

**Cost accepted.** `mf_sgd_v1.0` is genuinely different bytes, so the pre-Task-0.4 metrics are no
longer reproducible from the working tree. That is intended: those numbers are being regenerated,
and the file remains in git history and in LFS if it is ever needed.

**Known gap.** `scripts/train_mf_sgd.py` and `scripts/train_knn_sklearn.py` still write
`*_v1.0.joblib`, a stem nothing now reads. A retrain must be saved under the stem in
`src/models/constants.py` (and the constant updated) or it will not be picked up.

**What would change this.** A retrain that supersedes an artifact: replace the file and update
the constant in the same change. Keeping two builds of one family side by side requires setting
the matching `APP_*_STEM` env var, or the optional families drop out silently again.

---

## 2026-09-16 — Demo hosting stays on Streamlit Community Cloud; Hugging Face Spaces mirror deferred

**Status:** Deferred (revisit in Phase 3). Revisited 2026-10-18: hosting stays; the cold start is
handled by keeping the app awake (newest entry)

**Context.** The README badge is the first click a reviewer makes, and the portfolio plan opened
with a finding that the link was broken for anonymous visitors: `curl` on it returns `303` to
`share.streamlit.io/-/auth/app`. That finding was wrong. The dashboard sharing setting was
already *"This app is public and searchable"*, and the `303` is the anonymous-session cookie
handshake that **every** Streamlit Cloud app performs; followed with a cookie jar it completes in
three hops and serves the app with `200`. The diagnosis came from inspecting only the first hop.
See [DEPLOYMENT.md](DEPLOYMENT.md), "Verify From Outside", for the check that actually
distinguishes public from private.

The real weaknesses of Community Cloud are cold starts (~10–20 s to wake after inactivity) and a
1 GB RAM ceiling that the ~600–800 MB artifact load sits close to.

**Decision.** Keep Community Cloud as the single public demo. Do not add a Hugging Face Spaces
mirror now.

**Why.** The demo was never actually blocked, so the motivating problem for a second host does
not exist. A mirror is a second thing that can break silently and a second place a stale build
can be served — worse for a reviewer than one slow-to-wake app. The cold start is addressed with
a one-line note under the README badge rather than with more infrastructure. Nothing about the
app is Streamlit-Cloud-specific, so the option stays open.

**What would change this.** Any of: the app exceeds the 1 GB RAM limit after model changes;
Community Cloud downtime or sign-in regressions appear; or the cold start proves to be the thing
reviewers actually bounce on. A Spaces mirror (persistent hardware, no cookie handshake) is then
the first alternative to evaluate, and it is listed in Phase 3 of
[MARS_PORTFOLIO_PRODUCT_PLAN.md](plans/MARS_PORTFOLIO_PRODUCT_PLAN.md).
