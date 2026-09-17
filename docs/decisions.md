# Decision Log

A dated record of project decisions that are not derivable from the code: what was decided, why,
and what would change the answer. Newest first.

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
