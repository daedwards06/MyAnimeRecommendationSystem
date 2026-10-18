# Deployment Guide: Streamlit Community Cloud

This guide covers deploying the MARS Anime Recommendation System to Streamlit Community Cloud.

## Prerequisites

- GitHub account
- Streamlit Community Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- Repository pushed to GitHub with all required files

## Repository Structure for Deployment

Ensure the following files/folders are in your repository:

```
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── .python-version          # Python 3.11.9 (preference for Streamlit Cloud)
├── app/
│   ├── main.py              # Entry point
│   ├── sidebar.py
│   ├── state.py
│   ├── display.py
│   └── pipeline_runner.py
├── data/
│   └── processed/
│       ├── anime_metadata.parquet  (~6 MB)
│       ├── interactions.parquet    (~17 MB)
│       └── [other data files]
├── models/                      # one artifact per family, all Git LFS
│   ├── mf_sgd_v2025.11.21_202756.joblib               (~23 MB)
│   ├── item_knn_sklearn_v2025.11.21_202756.joblib     (~181 MB)
│   ├── synopsis_tfidf_v2026.03.14_001647.joblib       (~5 MB)
│   ├── synopsis_embeddings_v2026.03.14_001718.joblib  (~12 MB)
│   └── synopsis_neural_embeddings_v2026.01.31_235728.joblib (~17 MB)
├── src/
│   └── app/
│       ├── artifacts_loader.py
│       ├── scoring_pipeline.py
│       ├── constants.py
│       └── [other modules]
├── requirements.txt         # Production dependencies only
└── README.md
```

**Important:** 
- Total repository size must be < 1 GB for Streamlit Cloud.
- Using FastParquet instead of PyArrow for Python 3.13 compatibility.
- `.python-version` specifies Python 3.11.9 as preference (fallback to 3.13 works with FastParquet).

## File Size Summary

Based on current artifacts:
- **Models folder:** ~250 MB (5 LFS artifacts; was ~650 MB before the duplicate stems were
  pruned in Task 0.3)
- **Data folder:** ~88 MB
- **Total:** ~338 MB ✓ (under 1 GB limit)

### One stem per model family

`models/` holds exactly one artifact per family, and `MF_MODEL_STEM` / `KNN_MODEL_STEM` in
`src/models/constants.py` name the MF and kNN ones (re-exported by `src/app/constants.py` as
`DEFAULT_MF_MODEL_STEM` / `DEFAULT_KNN_MODEL_STEM`). Offline evaluation scripts and the app read
those constants, so the metrics describe the model that is served.

Adding a second artifact for a family without updating the constant makes `_select_model_stem`
ambiguous: MF selection then fails the app at startup, and the kNN and synopsis families are
dropped. A dropped family is logged at warning level, recorded in `bundle["load_report"]`, and
shown as a notice under the app header (reason under Scoring details, in the footer); the app keeps running. Replace the artifact and update the constant in the same change, or set
`APP_MF_MODEL_STEM` / `APP_KNN_MODEL_STEM` / `APP_SYNOPSIS_TFIDF_STEM` /
`APP_SYNOPSIS_EMBEDDINGS_STEM` / `APP_SYNOPSIS_NEURAL_EMBEDDINGS_STEM` to disambiguate.

Offline evaluation does **not** use these artifacts: it fits its own on the train split, under
`experiments/artifacts/` (git-ignored, never deployed). Keep them there — a `*_trainsplit.joblib`
in `models/` would make selection ambiguous and fail the app at startup.

Verify with:

```powershell
git lfs ls-files -s   # expect 5 entries, one per family
```

### Artifact smoke check

CI runs with `APP_IMPORT_LIGHT=1` and does not fetch LFS objects, so it never loads the real
models. That is how two synopsis families went unloaded in the deployed app unnoticed. The smoke
check covers that gap:

```powershell
python scripts/smoke_artifacts.py   # or: make smoke
```

It loads the real bundle, prints one line per model family (loaded / stem / size, or the reason
it is missing), and runs a seed-based query (Steins;Gate) and a personalized query (the example
profile) through the scoring-pipeline functions. It exits non-zero when a family in
`EXPECTED_MODEL_FAMILIES` (`src/app/constants.py`) did not load or either query returns fewer
than 10 results. Run it after replacing any artifact, before pushing. It takes about a minute.

`.github/workflows/smoke.yml` runs the same check on GitHub: on demand (Actions → Artifact
smoke → Run workflow), and on pushes to `main` that touch `models/**`, the artifact loader, or
the stem / expected-family constants. It is not on a schedule: the artifacts rarely change, so a
periodic run would mostly re-check the same files.

**LFS bandwidth cost:** a run that misses the cache downloads ~250 MB of LFS objects, which
counts against the account's Git LFS bandwidth quota (Streamlit Cloud's clones use the same
quota). The workflow caches `.git/lfs` keyed on the LFS object IDs, so the full download happens
when an artifact changes (exactly when the check is worth running) or when the cache has been
evicted (GitHub evicts caches unused for 7 days). A code-only push reuses the cache only if
another run happened within the last 7 days. Expect a full download on most runs, but only a
handful of runs a year; check the quota under GitHub → Settings → Billing if that changes.

The workflow runs alongside the Streamlit Cloud redeploy triggered by the same push, so it
reports a broken artifact minutes after deploy rather than blocking it. Run the script locally
before pushing an artifact change.

## Step-by-Step Deployment

### 1. Verify Local Deployment Works

Before deploying to the cloud, test locally in a clean environment:

```powershell
# Create fresh virtual environment
python -m venv .venv-deploy-test
.venv-deploy-test\Scripts\Activate.ps1

# Install only production dependencies
pip install -r requirements.txt

# Run the app
streamlit run app/main.py
```

**Expected behavior:**
- App loads in browser at http://localhost:8501
- No import errors
- Models load successfully
- All three recommendation modes work (Seed-Based, Personalized, Quick Explore)

If there are issues, fix them before proceeding to cloud deployment.

### 2. Push to GitHub

Ensure all necessary files are committed and pushed:

```powershell
git add .streamlit/ requirements.txt requirements-dev.txt
git add data/processed/*.parquet models/*.joblib
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

**Note:** If your model files are in `.gitignore`, you'll need to either:
- Remove them from `.gitignore` (for files < 100 MB)
- Use Git LFS for larger files
- Host models externally and download them at runtime

### 3. Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repository: `daedwards06/MyAnimeRecommendationSystem`
4. Set the following:
   - **Branch:** `main`
   - **Main file path:** `app/main.py`
   - **App URL:** Choose a custom URL (e.g., `mars-anime-rec`)
5. Click "Deploy"

### 4. Monitor Deployment

The deployment process takes 2-5 minutes. You'll see:

1. **Installing dependencies** - reads `requirements.txt`
2. **Building app** - imports modules, loads artifacts
3. **App is running** - success! App is live

**Watch for errors:**
- Import errors → missing dependencies in `requirements.txt`
- File not found → check paths are relative, not absolute
- Memory errors → models too large (1 GB RAM limit)

### 5. Sharing Setting (public vs. private)

The free tier allows **1 private app or unlimited public apps** (see "Cost & Limits" below), so a
public demo costs nothing. A private app is visible only to the owner and invited viewers;
everyone else ends on a Streamlit sign-in page.

**Where it is:** [share.streamlit.io](https://share.streamlit.io) → the app's "..." menu →
**Settings** → **Sharing**. Public shows as *"This app is public and searchable."*

### 6. Verify From Outside

Do not trust your own browser — you are signed in, so a private app renders normally for you.

**A bare `curl` is not a valid check.** Every Streamlit Cloud app, public ones included, answers
the first request with `303` to `https://share.streamlit.io/-/auth/app?redirect_uri=...`. That is
the anonymous-session cookie handshake, not an auth wall. Checking only the first hop makes a
healthy public app look private. Following redirects *without* storing cookies is equally
misleading: the handshake never completes and curl gives up after 50 redirects.

Follow the redirects **with a cookie jar** and look at where the chain ends:

```powershell
curl.exe -sL -c "$env:TEMP\st.txt" -b "$env:TEMP\st.txt" -o NUL -w "%{http_code} %{url_effective}`n" https://myanimerecommendationsystem-x6rqm6vqjmbr2ij8i8yk3b.streamlit.app/
```

- **Public (expected):** `200` and a final URL back on `...streamlit.app/` — three hops:
  `/-/auth/app` → `/-/login?payload=...` → the app. A sleeping app also ends `200`, serving a
  "wake up" page first.
- **Private:** the chain ends on `share.streamlit.io` with a sign-in page instead of returning to
  the app host — go back to step 5.

A logged-out browser window (private/incognito) is the second check, and the one that also tells
you whether the app is awake.

### 7. Test the Deployed App

Once live, test all critical paths:

- ✅ Homepage loads
- ✅ Seed-Based recommendations work
- ✅ Personalized mode accepts ratings
- ✅ Quick Explore shows results
- ✅ Filters work (genre, type, year)
- ✅ Diversity panel displays correctly
- ✅ No console errors

### 8. Update README with Live URL

After successful deployment, update your README.md:

```markdown
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP-URL.streamlit.app)
```

Example:
```markdown
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://mars-anime-rec.streamlit.app)
```

## Environment Variables (Optional)

If you need to override model selection, set these in Streamlit Cloud settings:

- `MF_MODEL_STEM` - Override default MF model (e.g., `mf_sgd_v2025.11.21_202756`)
- `KNN_MODEL_STEM` - Override default kNN model

**How to set:**
1. In Streamlit Cloud dashboard, click your app
2. Click "⋮" → "Settings"
3. Go to "Secrets" tab
4. Add environment variables as TOML:

```toml
MF_MODEL_STEM = "mf_sgd_v2025.11.21_202756"
```

## Known Deployment Gotchas

### 1. Python Version & Parquet Library (CRITICAL)
- **Symptom:** Deployment fails with `ModuleNotFoundError: No module named 'pkg_resources'` when installing PyArrow
- **Cause:** Streamlit Cloud may default to Python 3.13, but PyArrow < 18 has build issues on Python 3.13
- **Solution:** 
  - **Switched to FastParquet** instead of PyArrow for parquet file support
  - FastParquet has pre-built wheels for all Python versions and doesn't require compilation
  - Created `.python-version` file with `3.11.9` as preference (Streamlit Cloud support varies)
  - Added `packages.txt` with system dependencies as fallback
  - **This fix is already applied in the repository**

### 2. Model Loading Time
- **Symptom:** The first visitor after a boot waits while ~250 MB of models load
- **Cause:** `build_artifacts()` loads every model family eagerly; `st.cache_resource` keeps
  them for later sessions
- **Measured:** see [Performance](#performance). Locally the first card takes ~28 s on a fresh
  server and ~9 s after that.

### 3. Memory Limits
- **Limit:** Streamlit Cloud free tier has 1 GB RAM
- **Current usage:** 519 MB peak RSS with all models loaded plus one seed-based and one
  personalized query (measured locally, see [Performance](#performance))
- **If exceeded:** Consider:
  - Using smaller models
  - Lazy loading (load models only when needed)
  - Upgrading to paid tier

### 4. Session State Resets
- **Symptom:** User ratings disappear on page reload
- **Cause:** Streamlit session state is in-memory only
- **Solution:** Expected behavior. For persistence, add database backend (future enhancement).

### 5. Cold Starts
- **Symptom:** A visitor lands on a "This app has gone to sleep" page
- **Cause:** Streamlit Cloud spins down idle apps
- **Solution:** Normal for free tier. Waking reboots the container, which then pays the model
  load above. Timings are under [Performance](#performance). A scheduled job keeps the demo
  from sleeping; see [Keeping the demo awake](#keeping-the-demo-awake).

### 6. Path Issues
- **Symptom:** FileNotFoundError for data/models
- **Cause:** Using absolute paths or `os.getcwd()`
- **Solution:** Use relative paths from project root:
  ```python
  # ✓ Correct
  Path("data/processed/anime_metadata.parquet")
  
  # ✗ Wrong
  Path("C:/Users/...")  # absolute path
  Path(os.getcwd()) / "data/..."  # unreliable
  ```

### 6. GitHub File Size Limits
- **Limit:** 100 MB per file
- **Current largest:** `item_knn_sklearn_v2025.11.21_202756.joblib` (~181 MB)
- **Solution:** Use Git LFS:
  ```powershell
  git lfs install
  git lfs track "models/*.joblib"
  git add .gitattributes
  git commit -m "Track model files with Git LFS"
  ```

## Updating the Deployed App

After making code changes:

```powershell
git add .
git commit -m "Fix: your changes"
git push origin main
```

Streamlit Cloud auto-deploys on every push to `main`. 
You can also manually trigger a reboot from the app dashboard.

## Refreshing Data & Models

To add newly released anime to the deployed app:

1. **Run the refresh pipeline locally:**
   ```powershell
   python scripts/refresh_catalog.py            # full refresh
   python scripts/refresh_catalog.py --season 2026 winter  # specific season
   ```
2. **Commit updated artifacts:**
   ```powershell
   git add data/processed/ models/
   git commit -m "Refresh catalog: YYYY-MM"
   git push origin main
   ```
3. Streamlit Cloud auto-deploys on push.

> **Note:** The `sentence-transformers` package is only needed for offline neural embedding builds (WSL2). The production `requirements.txt` excludes it — `build_features.py` skips embeddings gracefully when it's not installed.

## Rollback on Errors

If a deployment breaks the app:

1. Go to Streamlit Cloud dashboard
2. Click your app → "⋮" → "Reboot app"
3. If error persists, revert your Git commit:
   ```powershell
   git revert HEAD
   git push origin main
   ```

## Performance Monitoring

Monitor app health via Streamlit Cloud dashboard:
- **Viewer count** - current active users
- **Memory usage** - track if approaching 1 GB limit
- **Errors** - console logs for debugging

## Performance

*Measured 2026-10-18 (Task 1.8).*

**Time to first card on the deployed app.** This is a first-time visitor's view: a fresh
browser context (no cookies) per run, timed from navigation until the default "Similar to
Fullmetal Alchemist: Brotherhood" results show their header and first poster. Playwright drove
Edge from a home connection.

| Load | Runs | Median | Range |
|:---|---:|---:|---:|
| Warm (app awake, models cached) | 3 | 10.9 s | 10.9–11.2 s |
| Cold (app asleep, woken by the visitor) | 0 | not yet measured | |

About 2 s of the warm figure is the pipeline itself: the results heading appears at ~9 s and the
first poster ~2 s later. The rest is Streamlit Cloud's auth redirect handshake, the frontend
bundle and the websocket session.

Cold start is still open. The one run that found the app asleep (the sleep page appeared 7.1 s
after navigation) recorded the wake, but its first-card detector failed, so it has no number. A
cold run needs the app to have slept first (Community Cloud sleeps an app after a period with no
traffic), so three runs take three idle periods. To time one: open the app in a private window
after it has slept, click the wake button, and stop the clock at the first poster. Add the
median and range to the table above and to the README note under the badge.
Decided 2026-10-18 without the cold runs: rather than measure the wake, keep the app from
sleeping with a scheduled headless-browser visit (`docs/decisions.md`; plan Task 1.9). That
job records a cold reading whenever it finds the app asleep (see
[Keeping the demo awake](#keeping-the-demo-awake)); add any such reading to the Cold row above.

The same detector, run locally with `scripts/check_live_app.py` on the awake app, read 10.1,
10.5 and 12.6 s (Playwright's Chromium and Edge, 2026-10-18), in line with the warm row. A
fourth run, the first after installing the browser, read 20.8 s and is not counted. The first
manual run of the workflow on GitHub's runner read 9.8 s (app awake).

Locally (Windows, Python 3.12, same machine as the deployed-app timings), `streamlit run` takes
28.5 s to the first card on a fresh server and 8.7 s on the next session. The difference is the
eager model load in `build_artifacts()`, which the deployed app also pays on every wake.

**Memory.** Measured with `python scripts/smoke_artifacts.py --profile-memory`, which samples
the process RSS every 20 ms while loading the real bundle and running one seed-based and one
personalized query:

| Stage | RSS |
|:---|---:|
| Imports done | 155 MB |
| Bundle loaded | 512 MB |
| Engine built | 512 MB |
| Seed-based query | 515 MB |
| Personalized query | 515 MB |
| **Peak** | **519 MB** |

As a cross-check, a local `streamlit run` process peaked at 501 MB (Windows peak working set)
after serving two sessions. Both figures are under half the 1 GB limit, so none of the
memory-reduction options (lazy-loading the neural model, memory-mapping artifacts, a Hugging
Face mirror) is needed now. These are Windows numbers. Community Cloud runs Linux, where RSS for
the same arrays should be close but is not guaranteed equal, and the Cloud dashboard's memory
graph is the authoritative reading.

**Python version.** Cloud and CI run Python 3.11.9 (`.python-version`); the published ablation was
produced in the local 3.12.3 venv. Re-run under 3.11.9 with the same library versions (numpy
2.4.3, pandas 2.2.2, scikit-learn 1.5.2, scipy 1.16.3, joblib 1.4.2), with the train-split kNN
and MF refit from scratch, then `evaluate_knn_mf`, `evaluate_hybrid` and
`evaluate_content_only` (`--k 10 --sample-users 1000`), `aggregate_phase4_metrics.py --cohort
1000` and `generate_phase4_ablation.py`: `phase4_ablation.md` came out byte-identical, and the
largest difference in any `phase4_ablation.csv` column was 1.8e-13. The Python version does not
move the published numbers. `requirements.txt` uses `>=` floors, not pins, so the library
versions Cloud resolves can drift from the ones the evaluation used; this check does not cover
that.

## Keeping the demo awake

Community Cloud puts an app to sleep after a period with no traffic, and waking it reboots the
container and reloads every model before the first card. `.github/workflows/keep-awake.yml`
visits the app so that a reviewer does not have to wait for that (decision: `docs/decisions.md`,
2026-10-18).

**What the job does.** It runs `scripts/check_live_app.py`, which opens the app in headless
Chromium with a fresh browser context, clicks the wake button if the sleep page shows, and waits
for the first card: the "N recommendations" header plus a loaded poster image. A plain `curl`
does not count as a visit (a sleeping app still answers `200`; see
[Verify From Outside](#6-verify-from-outside)). The job runs:

- every 6 hours (`17 */6 * * *`, UTC);
- on demand: Actions → **Keep demo awake** → **Run workflow**;
- after every push to `main`, which redeploys and reboots the app. It waits 5 minutes for the
  redeploy first, so the job, not the next visitor, pays the model load.

It checks out only the script (no LFS objects, so no LFS bandwidth) and installs Playwright
itself. Playwright is not in `requirements.txt`. The time to first card and `was_asleep` go to
the run's job summary.

**Run it locally.**

```powershell
pip install playwright; python -m playwright install chromium
python scripts/check_live_app.py                    # or --channel msedge to use installed Edge
```

It prints `time_to_first_card_s` and `was_asleep`, and exits 1 after `--timeout` seconds
(default 300; the workflow uses 420) with a screenshot at `--screenshot`.

**Reading a failure.** A red run means no card appeared within the timeout. Download the
`live-app-failure` artifact from the run and look at the screenshot:

- *Sleep page still showing:* the wake button's text no longer matches `WAKE_BUTTON_RE` in the
  script (it looks for "get this app back up"; that text has not been checked against a real
  sleep page yet). Update the pattern.
- *App error or "in the oven":* the app itself is broken or still redeploying. Check the Cloud
  dashboard logs; re-run the job once it is up.
- *App rendered, cards visible:* the detector is stale (the header text or the
  `stImageContainer` test id changed). Fix the script, and check it both ways before trusting a
  reading: it must fire on the rendered page and time out on a page without cards.

**Cold-start readings.** A run with `was_asleep: yes` found the app asleep. Its time to first
card is a cold-start reading for the table under [Performance](#performance). If those runs
become common, the app is sleeping between visits and the schedule should be tightened.

**The 60-day disable.** GitHub disables scheduled workflows in a public repository after 60 days
with no commits, and emails the owner first. Re-enable it from Actions → **Keep demo awake** →
**Enable workflow**, or push any commit. Until then the app goes back to sleeping.

## Cost & Limits (Free Tier)

Streamlit Community Cloud free tier includes:
- ✅ 1 private app (or unlimited public apps)
- ✅ 1 GB RAM
- ✅ 1 CPU core
- ✅ 1 GB storage
- ✅ Auto-sleep after inactivity
- ✅ Community support

**Current MARS usage:**
- Storage: ~338 MB ✓
- RAM: 519 MB peak, measured locally ✓
- Public repository ✓

## Troubleshooting

### App won't start
1. Check logs in Streamlit Cloud dashboard
2. Verify `app/main.py` exists and is executable
3. Test locally with `streamlit run app/main.py`

### Import errors
1. Ensure all imports in `requirements.txt`
2. Check for typos in package names
3. Verify versions are compatible

### Models not loading
1. Confirm `.joblib` files are committed to Git
2. Check file paths are relative
3. Verify `METADATA_PARQUET` constant matches actual filename

### Out of memory
1. Monitor memory usage in dashboard
2. Consider lazy loading models
3. Reduce data/model sizes
4. Upgrade to paid tier if needed

## Support Resources

- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io)
- **Status Page:** [streamlit.statuspage.io](https://streamlit.statuspage.io)

## Next Steps After Deployment

1. ✅ Add live URL badge to README.md
2. ✅ Test all features on the deployed app
3. ✅ Share the link in your portfolio/resume
4. 🔄 Monitor performance and user feedback
5. 🔄 Iterate based on real-world usage

---

**Deployment Status:** Ready for production  
**Last Updated:** February 16, 2026
