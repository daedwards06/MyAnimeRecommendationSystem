# Decision Log

A dated record of project decisions that are not derivable from the code: what was decided, why,
and what would change the answer. Newest first.

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
