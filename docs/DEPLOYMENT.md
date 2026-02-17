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
├── models/
│   ├── mf_sgd_v*.joblib            (~23 MB)
│   ├── item_knn_sklearn_v*.joblib  (~181 MB)
│   └── [other model files]
├── src/
│   └── app/
│       ├── artifacts_loader.py
│       ├── scoring_pipeline.py
│       ├── constants.py
│       └── [other modules]
├── requirements.txt         # Production dependencies only
└── README.md
```

**Important:** Total repository size must be < 1 GB for Streamlit Cloud.

## File Size Summary

Based on current artifacts:
- **Models folder:** ~440 MB
- **Data folder:** ~88 MB  
- **Total:** ~528 MB ✓ (under 1 GB limit)

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

### 5. Test the Deployed App

Once live, test all critical paths:

- ✅ Homepage loads
- ✅ Seed-Based recommendations work
- ✅ Personalized mode accepts ratings
- ✅ Quick Explore shows results
- ✅ Filters work (genre, type, year)
- ✅ Diversity panel displays correctly
- ✅ No console errors

### 6. Update README with Live URL

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

### 1. Model Loading Time
- **Symptom:** App shows "Please wait..." for 30-60 seconds on first load
- **Cause:** Loading ~440 MB of models from disk
- **Solution:** Normal behavior. Models are cached after first load.

### 2. Memory Limits
- **Limit:** Streamlit Cloud free tier has 1 GB RAM
- **Current usage:** ~600-800 MB with all models loaded
- **If exceeded:** Consider:
  - Using smaller models
  - Lazy loading (load models only when needed)
  - Upgrading to paid tier

### 3. Session State Resets
- **Symptom:** User ratings disappear on page reload
- **Cause:** Streamlit session state is in-memory only
- **Solution:** Expected behavior. For persistence, add database backend (future enhancement).

### 4. Cold Starts
- **Symptom:** App is slow after 5+ minutes of inactivity
- **Cause:** Streamlit Cloud spins down idle apps
- **Solution:** Normal for free tier. First request wakes the app (~10 seconds).

### 5. Path Issues
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
- **Current largest:** `item_knn_sklearn_v*.joblib` (~181 MB)
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

## Cost & Limits (Free Tier)

Streamlit Community Cloud free tier includes:
- ✅ 1 private app (or unlimited public apps)
- ✅ 1 GB RAM
- ✅ 1 CPU core
- ✅ 1 GB storage
- ✅ Auto-sleep after inactivity
- ✅ Community support

**Current MARS usage:**
- Storage: ~528 MB ✓
- RAM: ~600-800 MB ✓
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
