# User Guide: Import Your MyAnimeList Watchlist

This guide shows you how to import your MyAnimeList (MAL) watchlist into the recommendation system to automatically hide anime you've already watched.

## Why Use This Feature?

If you have a MAL account with your watch history, importing it will:
- ✅ **Automatically exclude** anime you've already seen from recommendations
- ✅ **Save time** by showing only fresh suggestions you haven't watched
- ✅ **Store your ratings** for future personalization features (Phase B)
- ✅ **Keep your data private** - profiles are stored locally and never uploaded

## Quick Start (3 Steps)

### Step 1: Export Your MAL Watchlist

1. Go to [MyAnimeList.net](https://myanimelist.net) and log in
2. Click your username in the top-right corner
3. Select **"Export"** from the dropdown menu (or go directly to https://myanimelist.net/panel.php?go=export)
4. Click **"Export My List"** button
5. Save the XML file (named like `animelist_XXXXX_XXXXX.xml`) to your computer

**Note**: The export includes all anime on your list (Completed, Watching, On-Hold, Dropped, Plan to Watch).

### Step 2: Import in the App

1. **Open the Streamlit app** (run `streamlit run app/main.py` if not already running)
2. **Expand "👤 User Profile"** in the left sidebar (below the Performance section)
3. **Upload your XML file**:
   - Click the file uploader area
   - Select your MAL export XML file
4. **Preview (optional)**:
   - Click "📊 Preview" to see a quick summary
   - Shows username, total anime count, and rated count
5. **Parse the file**:
   - Click "🔄 Parse" to process your watchlist
   - Wait a few seconds for parsing to complete
6. **Review the import summary**:
   - See how many anime were matched to our database
   - Check for any unmatched titles (newer anime may not be in our dataset)
7. **Save your profile**:
   - Enter a profile name (defaults to your MAL username)
   - Click "💾 Save Profile"
   - Your profile will be automatically loaded

### Step 3: Enjoy Personalized Recommendations!

Once your profile is loaded:
- ✅ You'll see **"✓ Profile: {YourName} – {N} watched"** at the top of the Profile section
- ✅ Browse or get recommendations as usual
- ✅ All results will show **"✓ Excluded {N} already-watched anime"** in green
- ✅ No anime you've already watched will appear in results

## Using Your Profile

### Switching Profiles

Multiple people can use the same app with different profiles:

1. Expand "👤 User Profile" in sidebar
2. Select a different profile from the **"Active Profile"** dropdown
3. App will reload with that profile's exclusions

To disable exclusions temporarily:
- Select **(none)** from the dropdown
- All anime will be visible again

### Checking Profile Stats

When a profile is loaded, you'll see:
- **Total watched**: Number of anime on your list
- **Average rating**: Your mean rating across rated titles

### Deleting a Profile

Profiles are stored as JSON files in `data/user_profiles/`.

To delete a profile:
- Delete the file `data/user_profiles/{username}_profile.json`
- Or use your operating system's file manager to remove it

The app will automatically detect the change next time you reload.

## Import Details

### What Gets Imported?

**By default**, the app imports:
- ✅ **Completed** anime (all episodes watched)
- ✅ **Watching** anime (currently watching)
- ✅ **On-Hold** anime (paused)
- ❌ **Dropped** anime (not imported by default)
- ❌ **Plan to Watch** anime (not imported by default)

### How Ratings Are Handled

- **Explicit ratings** (1-10 scale): Imported as-is from your MAL scores
- **Unrated completed anime**: Assigned a default rating of **7.0/10**
  - This ensures all watched anime have a rating for future personalization features
  - You can adjust this behavior in future updates

### Unmatched Anime

Some anime may not match our database:
- **Reason**: Newer anime released after our dataset was built
- **Impact**: These titles won't be excluded (we don't have them anyway)
- **Display**: Shown in yellow warning during import with title names

Example: If you've watched 100 anime and 10 are unmatched, 90 will be excluded from recommendations.

## Privacy & Data Storage

### Your Data Stays Local

- ✅ Profiles are stored in `data/user_profiles/` on your computer
- ✅ Never uploaded to any server or cloud
- ✅ Excluded from git via `.gitignore` (won't be committed if you fork the repo)
- ✅ Only you have access to your profile data

### Profile File Format

Profiles are stored as JSON files with this structure:

```json
{
  "username": "your_name",
  "watched_ids": [1, 5, 6, ...],
  "ratings": {"1": 8.5, "5": 7.0, ...},
  "status_map": {"1": "Completed", "5": "Watching", ...},
  "import_date": "2025-11-27T12:00:00Z",
  "mal_username": "your_mal_username",
  "stats": {
    "total_watched": 98,
    "rated_count": 52,
    "unrated_count": 46,
    "avg_rating": 7.8
  }
}
```

You can manually edit this file if needed (use a text editor).

## Troubleshooting

### "No profiles found"
- Make sure you've completed Step 2 (import and save)
- Check that `data/user_profiles/` directory exists
- Verify the XML file uploaded correctly

### "Parsing failed"
- Ensure you uploaded a valid MAL XML export (not a different file type)
- Check that the XML isn't corrupted (try re-exporting from MAL)
- Look for error messages in the app

### "Not excluding watched anime"
- Verify a profile is selected in the dropdown (not "(none)")
- Check that the green "✓ Excluded N anime" message appears below results
- Try reloading the app (`Ctrl+R` in browser)

### "Too many unmatched anime"
- This is normal for newer anime (released 2024-2025)
- Our dataset was built in late 2024 and may not include latest releases
- Unmatched anime won't appear in recommendations anyway (not in database)

## FAQ

**Q: Do I need a MAL account to use the app?**  
A: No! Profiles are completely optional. The app works perfectly without any profile - you'll just see all anime in results.

**Q: Will my watchlist be public?**  
A: No. Profiles are stored locally on your computer and never shared or uploaded.

**Q: Can multiple people use the same installation?**  
A: Yes! Each person can create their own profile and switch between them using the dropdown.

**Q: What if I update my MAL list?**  
A: Re-import your XML file and save it with the same profile name. It will overwrite the old profile with your updated watchlist.

**Q: Can I export my profile?**  
A: Yes - just copy the JSON file from `data/user_profiles/{username}_profile.json` to another location.

**Q: Does this affect the recommendation algorithm?**  
A: Currently no - exclusion is a simple filter (Phase A). Future updates (Phase B) will use your ratings for personalized collaborative filtering.

## Next Steps: Personalization (Phase B - Coming Soon)

Future updates will add:
- 🎯 **Personalized CF scoring** using your ratings
- ⭐ **Rate anime** directly from recommendation cards
- 📊 **Taste profile visualization** (your favorite genres/themes)
- 🔍 **"Similar to my favorites"** recommendation mode
- 📈 **Rating predictions** for recommendations

Stay tuned!

## Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Review `docs/running_context.md` for technical details
3. Open an issue on GitHub with:
   - Steps to reproduce
   - Error messages (if any)
   - Your profile stats (without personal data)

---

**Last Updated**: November 27, 2025  
**Feature Status**: Phase A (MVP) - Complete ✅
