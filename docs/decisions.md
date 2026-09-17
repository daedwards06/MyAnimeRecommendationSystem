# Decision Log

A dated record of project decisions that are not derivable from the code: what was decided, why,
and what would change the answer. Newest first.

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
