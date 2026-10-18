# Decision Log

A dated record of project decisions that are not derivable from the code: what was decided, why,
and what would change the answer. Newest first.

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

**Status:** Deferred (revisit in Phase 3)

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
