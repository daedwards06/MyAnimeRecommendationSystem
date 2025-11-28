# User Guide: Personalized Recommendations

## Overview

The MARS (My Anime Recommendation System) now includes **personalized collaborative filtering** to generate recommendations tailored to your unique taste profile. Instead of relying solely on seed-based similarity, the system learns from your rating history to predict which anime you'll enjoy most.

---

## Getting Started

### Prerequisites

1. **Import your MAL watchlist** (see [`user_guide_watchlist.md`](user_guide_watchlist.md))
2. **Ensure your watchlist includes ratings** (1-10 scale from MyAnimeList)

### Step 1: Load Your Profile

1. Launch the app: `streamlit run app/main.py`
2. In the sidebar, go to **👤 User Profile**
3. Select your profile from the dropdown (e.g., "Relentless649")
4. You should see your stats:
   ```
   ✓ Relentless649 – 93 watched
   ⭐ 91 ratings • Avg: 7.3/10
   ```

### Step 2: Enable Personalization

1. Scroll down in the **👤 User Profile** section
2. Check the box: **🎯 Personalized Recommendations**
3. Wait for the system to generate your taste profile (~1-2 seconds)
4. You'll see: `✓ Taste profile generated from 91 ratings`

### Step 3: Adjust Personalization Strength

Use the **Personalization Strength** slider to blend seed-based and personalized recommendations:

- **0%**: Pure seed-based (original behavior)
  - Recommendations based only on similarity to selected seeds
  - Best for discovering anime similar to a specific title

- **50%**: Balanced blend
  - Mix of personalized predictions and seed similarity
  - Good for exploring within your comfort zone

- **100%**: Fully personalized (default)
  - Recommendations based entirely on your rating history
  - Best for discovering new favorites aligned with your taste

### Step 4: View Recommendations

Browse recommendations as usual. With personalization enabled:
- Recommendations reflect **your** preferences, not just seed similarity
- Scores are higher for anime you're likely to enjoy based on collaborative filtering
- Watched anime are still automatically excluded

---

## Features

### 🎯 Personalized Explanations (NEW!)

When personalization is enabled, each recommendation includes an explanation showing **why** it's being recommended:

**Example explanations:**
- `🎯 Match: 8.5/10 • You rate Action (8.3★), Adventure (8.1★) & Drama (7.9★)`
- `🎯 Match: 9.2/10 • You rate Psychological (8.7★) highly • Similar to: Death Note, Code Geass`
- `🎯 Match: 7.8/10 • Based on your taste profile`

**What the explanations show:**
1. **Match Score**: Predicted rating based on your taste (0-10)
2. **Genre Preferences**: Your top-rated genres that match this anime
3. **Similar Titles**: Highly-rated anime (8+) you've watched that share genres

**How it works:**
- Analyzes your rating history to find genre patterns
- Identifies anime you rated 8+ that share 2+ genres with the recommendation
- Shows your average rating for matching genres (minimum 2 ratings per genre)

**Grid view**: Compact one-line explanation  
**List view**: Full explanation in highlighted box

### 🎨 Taste Profile Visualization

Click **🎨 View Taste Profile** in the sidebar to see:

#### **Genre Preferences Tab**
- **Radar chart**: Visual representation of your top 8 genres by average rating
- **Genre list**: All genres you've rated, sorted by average rating
- Example:
  ```
  Adventure         7.5/10
  Horror            7.5/10
  Drama             7.5/10
  Award Winning     7.4/10
  Fantasy           7.4/10
  ```

#### **Rating Patterns Tab**
- **Bar chart**: Distribution of your ratings (9-10, 7-8, 5-6, 1-4)
- **Breakdown**: Percentage of ratings in each bucket
- Example:
  ```
  9-10 stars: 10 (11.0%)
  7-8 stars:  81 (89.0%)
  ```

#### **Statistics Tab**
- **Total Ratings**: How many anime you've rated
- **Avg Rating**: Your overall average (e.g., 7.33/10)
- **Generosity**: % of ratings 7 or higher
- **Genre Diversity**: Number of different genres you've rated
- **Rating Style**: Personality analysis
  - 🌟 **Enthusiast** (avg ≥ 8.0)
  - 👍 **Balanced** (avg ≥ 7.0)
  - 🤔 **Critical** (avg ≥ 6.0)
  - 😐 **Tough Critic** (avg < 6.0)

### ⭐ In-App Rating

Rate anime directly from recommendation cards!

#### Quick Rating Buttons
Each anime card now includes:
- **👍 8**: Good (8/10)
- **❤️ 10**: Love it! (10/10)
- **👎 4**: Meh (4/10)

#### Current Rating Display
If you've already rated an anime, your rating is shown:
```
Your rating: 8/10
```

#### What Happens When You Rate:
1. ✅ Rating saved to your profile
2. 🗑️ User embedding cache invalidated (will regenerate on next use)
3. 📊 Stats updated (total ratings, avg rating)
4. 🔔 Toast notification: "Added rating: Anime Title (8/10)"

### 📊 Rating Distribution (Sidebar)

Expand **📊 Rating Distribution** in your profile section to see a histogram:
```
10/10: ████ (4)
9/10:  ██ (2)
8/10:  ████████████████ (16)
7/10:  ████████████████████████████████ (32)
6/10:  ██ (2)
```

---

## How It Works

### The Science Behind Personalization

1. **Matrix Factorization (MF) Model**
   - Trained on 73,515 users × 11,200 anime
   - Each anime has a 64-dimensional "factor vector" representing its latent features
   - These features capture genre, themes, style, and other attributes

2. **User Embedding Generation**
   - Your ratings are used to compute a custom 64-dimensional "user vector"
   - **Weighted averaging**: Higher-rated anime contribute more to your profile
   - **L2 normalization**: Ensures consistent scale

   ```
   For each anime i you rated with score r_i:
     1. Normalize rating: r'_i = (r_i - min) / (max - min)
     2. Weight item factor: weighted_i = r'_i * Q[i]
     3. Sum all weighted factors
     4. Normalize: user_embedding /= ||user_embedding||
   ```

3. **Personalized Scoring**
   - **Dot product**: `score = user_embedding · anime_factor`
   - Higher score = anime is more aligned with your taste profile
   - Blended with popularity scores for diversity

4. **Collaborative Filtering Magic**
   - Your embedding is in the same space as 73,515 other users
   - The model learns patterns like: "Users who rated X highly also liked Y"
   - Even if you haven't rated anime similar to Y, the model can predict you'll enjoy it

### Example Walkthrough

**Your Ratings:**
- Attack on Titan: 10/10
- Fullmetal Alchemist: 9/10
- Steins;Gate: 9/10
- Cowboy Bebop: 8/10

**Embedding Generation:**
1. Normalize ratings to 0-1: [1.0, 0.67, 0.67, 0.33]
2. Weight each anime's factor vector by normalized rating
3. Sum and normalize to unit vector

**Personalized Recommendation:**
1. Compute dot product with all 11,200 anime factors
2. Highest scores: Hunter x Hunter (2.847), Code Geass R2 (2.673), Death Note (2.501)
3. These anime share latent features with your highly-rated anime
4. You likely enjoy: dark themes, complex plots, action, psychological elements

---

## Tips for Best Results

### Minimum Ratings Needed
- **3 ratings**: Basic taste profile available
- **10 ratings**: Decent personalization
- **30+ ratings**: High-quality recommendations
- **100+ ratings**: Excellent personalization

### Rating Strategy
1. **Rate diverse genres**: Helps system understand your preferences across styles
2. **Rate both favorites and meh anime**: Teaches system what you DON'T like
3. **Be honest**: Don't inflate ratings—accurate data = better recommendations
4. **Update regularly**: Rate new anime as you watch them

### When to Use 100% Personalization
- Discovering new favorites outside your usual seeds
- "Surprise me with something I'll love"
- Cold start (no specific seed in mind)

### When to Use Blended (50%)
- Want recommendations similar to a seed BUT aligned with your taste
- Exploring a new genre with personalized safety net

### When to Use 0% (Seed-Only)
- Specifically want "more like this exact anime"
- Exploring outside your comfort zone intentionally
- Testing recommendations for a friend's taste

---

## Troubleshooting

### "No personalization toggle showing"
- **Cause**: Profile has no ratings
- **Fix**: Import MAL watchlist with ratings, or rate anime in-app

### "Taste profile takes forever to generate"
- **Cause**: Large number of ratings (100+)
- **Expected**: ~1-2 seconds for 100 ratings, ~3-5 seconds for 300+
- **Fix**: Wait patiently; profile is cached after first generation

### "Recommendations don't change when I adjust strength"
- **Cause**: Must click outside slider or hit Enter to trigger update
- **Fix**: Click elsewhere, then scroll to recommendations

### "Rated anime still showing in recommendations"
- **Cause**: Cache issue or rating not saved
- **Fix**: Refresh page, verify profile has rating in distribution

### "Personalized recs seem worse than seed-based"
- **Cause**: Not enough ratings, or ratings don't reflect true preferences
- **Fix**: 
  - Rate at least 20 anime
  - Ensure ratings are accurate (don't inflate)
  - Try 50% blend instead of 100%

---

## Privacy & Data

### What Gets Stored
- Your ratings: `data/user_profiles/{username}.json`
- No data uploaded to external servers
- All processing happens locally

### What Gets Cached
- User embedding: Session state (cleared when you close browser)
- Taste profile: Generated on-demand (not persisted)

### Deleting Your Data
```powershell
# Remove your profile
rm data/user_profiles/Relentless649.json

# Remove all profiles
rm data/user_profiles/*.json
```

---

## Advanced Usage

### Export Your Taste Profile

Want to see the raw data? Your profile JSON includes:

```json
{
  "username": "Relentless649",
  "watched_ids": [1, 5, 6, ...],
  "ratings": {
    "1": 8,
    "5": 9,
    "6": 7,
    ...
  },
  "stats": {
    "total_ratings": 91,
    "avg_rating": 7.33
  }
}
```

### Scripting Personalized Recommendations

```python
from src.app.artifacts_loader import build_artifacts
from src.data.user_profiles import load_profile
from src.models.user_embedding import generate_user_embedding
from src.app.recommender import HybridRecommender, HybridComponents

# Load
bundle = build_artifacts()
profile = load_profile("Relentless649")
ratings = profile["ratings"]

# Generate embedding
mf_model = bundle["models"]["mf"]
embedding = generate_user_embedding(ratings, mf_model)

# Get recommendations
recommender = HybridRecommender(HybridComponents(...))
recs = recommender.get_personalized_recommendations(
    user_embedding=embedding,
    mf_model=mf_model,
    n=20,
    weights={"mf": 0.7, "pop": 0.3},
    exclude_item_ids=profile["watched_ids"]
)

print(recs[:5])  # Top 5
```

---

## Comparison: Seed vs Personalized

| Feature | Seed-Based | Personalized |
|---------|-----------|--------------|
| **Basis** | Similarity to selected anime | Your rating history |
| **Best For** | "More like X" | "What will I love?" |
| **Coverage** | Narrow (similar to seed) | Broad (all genres) |
| **Surprise Factor** | Low (similar items) | Medium-High |
| **Cold Start** | Requires seed selection | Works without seeds |
| **Diversity** | Depends on seed | Higher (collaborative filtering) |
| **Accuracy** | High (for seed-like items) | High (for your taste) |

---

## FAQ

**Q: Can I use personalization without a seed?**  
A: Yes! Set personalization to 100% and leave seed selection empty. You'll get pure CF recommendations.

**Q: What should I do if I update my ratings on MAL?**  
A: Simply re-export your list from MAL and re-import it:
1. Go to MyAnimeList → Export → Download XML
2. In MARS sidebar, go to **👤 User Profile**
3. Expand **📥 Import from MAL**
4. Upload the new XML file
5. Click **Parse** then **Save Profile** (use the same profile name to overwrite)
6. Your ratings, watched list, and stats will update automatically
7. User embedding will regenerate on next use with personalization

**Q: How often should I update my ratings?**  
A: After watching any anime you feel strongly about. 1-2 new ratings per week is ideal.

**Q: Can I import ratings from AniList/Kitsu?**  
A: Not yet. Currently only MAL XML export is supported. Export from those services and manually import to MAL, then export from MAL.

**Q: Do I need to rate everything I've watched?**  
A: No! Quality > quantity. Rate anime you have strong opinions about (loved or hated). The system learns from contrast.

**Q: What if I rate an anime I haven't finished?**  
A: That's fine! Rate based on episodes you've seen. You can update later.

**Q: Can I see which anime influenced a recommendation?**  
A: Yes! When personalization is enabled, each recommendation shows an explanation including your genre preferences and similar anime you've rated highly. Look for the explanation text below the match score.

**Q: Does rating an anime automatically mark it as watched?**  
A: No. Ratings and watched status are separate. Add to watched list during import or manually.

---

## Next Steps

- 📖 [**Technical Details**](phase_b_implementation.md): Deep dive into embedding generation
- 🧪 [**Testing Guide**](../tests/test_personalization.py): Run tests to verify your setup
- 🔧 [**API Documentation**](phase_b_implementation.md#usage-examples): Programmatic access

**Enjoy personalized anime discovery! 🎬✨**
