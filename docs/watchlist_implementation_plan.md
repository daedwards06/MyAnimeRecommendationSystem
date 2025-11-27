# Watchlist & Personalization Implementation Plan

## Project Goal
Enable users to import their MyAnimeList watch history to exclude already-watched anime from recommendations, with future support for personalized collaborative filtering based on their rating history.

---

## Phase A: MAL Import + Exclusion Filter (MVP - Quick Win)

**Timeline**: 1-2 days  
**Value**: Immediate elimination of already-watched anime from recommendations

### Checklist

#### 1. MAL XML Parser Module (`src/data/mal_parser.py`)
- [ ] Create parser function `parse_mal_export(xml_path) -> dict`
- [ ] Extract fields: `anime_title`, `series_animedb_id`, `my_score`, `my_status`
- [ ] Handle status types: Completed, Watching, On-Hold, Dropped, Plan to Watch
- [ ] Map MAL IDs to internal anime_ids (using metadata lookup)
- [ ] Return structure:
  ```python
  {
    "username": "...",
    "watched_ids": [1, 5, 6, ...],  # anime_ids
    "ratings": {1: 8.5, 5: 7.0, ...},  # anime_id: score
    "status_map": {1: "Completed", 5: "Watching", ...},
    "unmatched": [{"mal_id": 123, "title": "..."}]  # titles not in our DB
  }
  ```
- [ ] Add error handling for malformed XML
- [ ] Log unmatched titles (MAL IDs not in our metadata)

#### 2. User Profile Storage (`src/data/user_profiles.py`)
- [ ] Create `data/user_profiles/` directory structure
- [ ] Implement `save_profile(username, profile_data) -> Path`
  - Save as JSON: `data/user_profiles/{username}_profile.json`
- [ ] Implement `load_profile(username) -> dict | None`
- [ ] Implement `list_profiles() -> list[str]`
- [ ] Profile schema:
  ```json
  {
    "username": "your_name",
    "watched_ids": [1, 5, 6, ...],
    "ratings": {"1": 8.5, "5": 7.0},
    "status_map": {"1": "Completed", "5": "Watching"},
    "import_date": "2025-11-26T12:00:00Z",
    "mal_username": "mal_username",
    "stats": {
      "total_watched": 98,
      "rated_count": 52,
      "unrated_count": 46,
      "avg_rating": 7.8
    }
  }
  ```
- [ ] Add profile validation function

#### 3. Streamlit UI Integration (`app/main.py`)
- [ ] Add "👤 User Profile" expander in sidebar (below Performance section)
- [ ] **Profile Selector**:
  - [ ] Dropdown to select existing profile or "(none)"
  - [ ] Show profile stats when loaded (watched count, avg rating)
- [ ] **MAL Import UI**:
  - [ ] File uploader widget for XML (`st.file_uploader`)
  - [ ] "Parse & Preview" button
  - [ ] Show import summary: "Found X anime (Y rated, Z unrated)"
  - [ ] Display unmatched titles if any (warning)
  - [ ] Username text input
  - [ ] Import options checkboxes:
    - ☑️ Use ratings when available (default: on)
    - ☑️ Default unrated completed to 7.0 (default: on)
    - ☑️ Include "Plan to Watch" (default: off)
    - ☑️ Include "On Hold" (default: on)
  - [ ] "💾 Save Profile" button
- [ ] Store active profile in `st.session_state["active_profile"]`
- [ ] Show active profile indicator: "✓ Profile: {username} ({X} watched)"

#### 4. Recommendation Exclusion Filter
- [ ] **Browse Mode**: Filter out watched anime before adding to `browse_results`
- [ ] **Recommendation Mode**: 
  - [ ] Filter out watched anime from multi-seed scoring loop
  - [ ] Filter out watched anime from `recommender.get_top_n_for_user()` results
  - [ ] Adjust `filter_multiplier` to account for watched exclusions (increase from 5x to 10x?)
- [ ] Add exclusion counter: Display "Excluded {X} already-watched titles" below results
- [ ] Ensure exclusion happens BEFORE other filters (genre/type/year)

#### 5. Testing & Validation
- [ ] Unit test: MAL XML parser with sample export file
- [ ] Unit test: Profile save/load roundtrip
- [ ] Integration test: Import profile → load in app → verify exclusions
- [ ] Manual test: Import your personal MAL export
- [ ] Verify no watched anime appear in recommendations
- [ ] Test edge cases: empty watchlist, all anime watched, malformed XML

#### 6. Documentation Updates
- [ ] Update `README.md` with "Import Your Watchlist" section
- [ ] Add `docs/user_guide_watchlist.md` with screenshots
- [ ] Update `docs/running_context.md` with Phase A completion
- [ ] Document MAL export instructions (how to download from MAL)

---

## Phase B: Personalized Collaborative Filtering (Advanced Enhancement)

**Timeline**: 2-3 days  
**Value**: True personalization based on user's rating history  
**Prerequisite**: Phase A complete & tested

### Checklist

#### 1. User Embedding Generation (`src/models/user_embedding.py`)
- [ ] Create function `generate_user_embedding(ratings_dict, mf_model) -> np.ndarray`
- [ ] Map user ratings to item factors using MF model
- [ ] Handle missing items (not in training set)
- [ ] Options for unrated watched anime:
  - [ ] Default rating (7.0)
  - [ ] Exclude from embedding
  - [ ] Weighted average based on status
- [ ] Return user factor vector (matches MF latent dimensions)

#### 2. Personalized Scoring Integration
- [ ] Extend `HybridRecommender` class:
  - [ ] Add `set_user_embedding(user_vec)` method
  - [ ] Modify scoring to use custom user embedding vs default user_index
- [ ] Create `PersonalizedRecommender` wrapper:
  - [ ] Compute personalized MF scores: `user_vec @ item_factors.T`
  - [ ] Blend with seed similarity scores
  - [ ] Blend with kNN and popularity as before
- [ ] Add "Personalization Strength" slider (0-100%):
  - 0% = pure seed-based (current behavior)
  - 100% = pure CF personalization
  - 50% = balanced blend

#### 3. UI Enhancements
- [ ] Add "🎯 Personalization" toggle in sidebar
  - [ ] Only enabled when profile loaded with ratings
  - [ ] Show personalization strength slider when enabled
- [ ] Add "Why this recommendation?" explanation:
  - [ ] Show % from personal taste vs seed similarity
  - [ ] Highlight genres user typically rates high
- [ ] Display personalization metrics:
  - [ ] "Based on your {X} ratings"
  - [ ] "Your avg rating for {genre}: {score}"

#### 4. Rating Management
- [ ] Add "⭐ Rate" button on recommendation cards
- [ ] Rating widget: 1-10 scale or unrated
- [ ] Update profile JSON with new ratings
- [ ] Trigger embedding regeneration on rating change
- [ ] Optional: "Mark as Watched" without rating

#### 5. Advanced Features (Stretch)
- [ ] "Similar to my favorites": Recommend based on your top-rated anime
- [ ] "Discover new genres": Recommend outside your usual genres
- [ ] Rating prediction: Show predicted rating for each recommendation
- [ ] Taste profile visualization: Chart of preferred genres/themes
- [ ] Export recommendations list (CSV/Markdown)

#### 6. Testing & Validation
- [ ] Unit test: User embedding generation
- [ ] Compare personalized vs non-personalized recommendations
- [ ] Validate embedding quality (similarity to known preferences)
- [ ] A/B test: Personalized vs seed-only recommendations
- [ ] Performance test: Embedding generation latency (<100ms target)

#### 7. Documentation
- [ ] Update `README.md` with personalization features
- [ ] Add technical doc: How personalization works
- [ ] Update `docs/running_context.md` with Phase B completion
- [ ] Create user guide for rating management

---

## Success Metrics

### Phase A (MVP)
- ✅ Successfully import MAL export (100+ anime)
- ✅ Zero already-watched anime in recommendations
- ✅ Profile persists across sessions
- ✅ Import takes <5 seconds
- ✅ No errors on malformed/incomplete data

### Phase B (Advanced)
- ✅ Personalized recommendations differ from generic
- ✅ Recommendations align with user's rating patterns
- ✅ Embedding generation <100ms
- ✅ User can add/update ratings seamlessly
- ✅ Positive user feedback on recommendation quality

---

## Technical Notes

### MAL ID Mapping Strategy
- MAL IDs may not match our internal anime_ids (Jikan IDs)
- Use title fuzzy matching as fallback
- Log unmatched titles for manual review
- Store both MAL ID and internal ID in profile

### Performance Considerations
- Profile loading: Cache in session state (don't reload every interaction)
- Large watchlists (1000+ anime): Test exclusion filter performance
- Embedding generation: Precompute on profile load, not per recommendation

### Error Handling
- Missing XML tags: Use defaults, don't crash
- Duplicate anime: Keep highest rating
- Invalid ratings: Skip entry, log warning
- Corrupted profile JSON: Backup + recovery flow

---

## Phase A Implementation Order (Suggested)

1. **Day 1 Morning**: MAL parser + profile storage (backend)
2. **Day 1 Afternoon**: Profile storage tests + sample data
3. **Day 2 Morning**: Streamlit UI (upload + preview)
4. **Day 2 Afternoon**: Exclusion filter integration + testing
5. **Day 2 Evening**: Documentation + manual testing with real MAL export

## Phase B Implementation Order (Suggested)

1. **Day 3**: User embedding generation + tests
2. **Day 4 Morning**: Personalized scoring integration
3. **Day 4 Afternoon**: UI enhancements (toggle, strength slider)
4. **Day 5**: Rating management + advanced features
5. **Day 5 Evening**: Testing, validation, documentation

---

## Git Workflow

**Phase A Branches:**
- `feature/mal-parser` (parser + profile storage)
- `feature/watchlist-ui` (Streamlit integration)
- `feature/exclusion-filter` (recommendation filtering)

**Phase B Branches:**
- `feature/user-embedding` (CF personalization)
- `feature/rating-management` (interactive ratings)

**Tags:**
- `phase5-watchlist-mvp` (after Phase A complete)
- `phase5-personalization` (after Phase B complete)

---

## Multi-User & Fork-Friendly Design

### Philosophy
**Profiles are optional**: The app works perfectly without any profile. Users only create profiles if they want personalized exclusions. This ensures anyone can clone the repo and use it immediately.

### Multi-User Support (Built-In)

**How it works:**
- File-based storage: `data/user_profiles/{username}_profile.json`
- Profile selector dropdown in UI (defaults to "(none)")
- Multiple people can use the same installation with separate profiles
- No authentication/login required (local file system separation)

**Use Cases:**
- **Solo user**: Create one profile, keep it selected
- **Family/shared computer**: Each person has their own profile
- **Fork users**: Import their own MAL, profile stays local

### Fork-Friendly Setup (Phase A)

#### Privacy & Git Ignore
- [ ] Add `data/user_profiles/*.json` to `.gitignore`
- [ ] Keep directory structure tracked with `.gitkeep`
- [ ] Document: "Profiles stay local, never committed to git"
- [ ] Provide `data/user_profiles/example_profile.json` (sample structure, not real data)

#### First-Run Experience
- [ ] **Default state**: App launches with no profile selected
  - All features work normally (browse, seed recommendations)
  - No exclusions applied (shows all anime)
  - No personalization (uses default collaborative filtering)
- [ ] **Profile indicator**: Sidebar shows "👤 No Profile" when none selected
- [ ] **Soft prompt** (non-intrusive):
  - Info box in sidebar: "💡 Import your MAL watchlist to hide anime you've already watched"
  - No modal/blocking dialog (user can ignore and use app normally)

#### Documentation for Fork Users
- [ ] Update `README.md` with "Getting Started" section:
  - Clone repo → install deps → run app (works immediately)
  - Optional: Import MAL for personalization
  - Link to MAL export instructions
- [ ] Add `docs/user_guide_watchlist.md`:
  - How to export from MAL (screenshots)
  - How to import in app
  - Privacy note (profiles are local only)
  - How to switch profiles
- [ ] Add FAQ:
  - Q: "Do I need a MAL account?" A: "No, profiles are optional"
  - Q: "Will my watchlist be public?" A: "No, stays on your computer"
  - Q: "Can multiple people use this?" A: "Yes, each person creates their own profile"

#### Sample Data (Testing/Demo)
- [ ] Provide `data/user_profiles/demo_profile.json`:
  - Fictional watchlist (10-20 popular anime)
  - Allows users to test profile feature without importing
  - Clearly labeled as example data
- [ ] Add note in UI: "Using demo profile" if `demo_profile` selected

### Phase A Checklist Updates

#### Add to "3. Streamlit UI Integration"
- [ ] Profile selector defaults to "(none)"
- [ ] When no profile: Show info message "Using app without profile (all anime visible)"
- [ ] When profile loaded: Show "✓ Profile: {username} ({X} watched)"
- [ ] Profile UI is collapsed by default (user expands if interested)

#### Add to "6. Documentation Updates"
- [ ] README: "Quick Start" section (no profile required)
- [ ] README: "Import Your Watchlist (Optional)" section
- [ ] Create `.gitignore` rules for profiles
- [ ] Add `data/user_profiles/.gitkeep` to track directory
- [ ] Create example profile JSON (structure reference)

---

## Open Questions / Decisions Needed

1. **Profile naming**: Use MAL username or custom name?
2. **Dropped anime**: Treat as negative rating or just exclude?
3. **Plan to Watch**: Include in exclusions or keep as recommendations?
4. **Default rating**: 7.0, 8.0, or no default (binary only)?

---

## Dependencies

**New Python Libraries:**
- None required (use stdlib `xml.etree.ElementTree` for XML parsing)
- Optional: `fuzzywuzzy` for better title matching (if needed)

**Files to Create:**
- `src/data/mal_parser.py`
- `src/data/user_profiles.py`
- `src/models/user_embedding.py` (Phase B)
- `data/user_profiles/` directory
- `docs/user_guide_watchlist.md`

**Files to Modify:**
- `app/main.py` (UI + filtering)
- `src/app/recommender.py` (personalization, Phase B)
- `docs/running_context.md`
- `README.md`

---

**Status**: Planning phase complete. Ready to begin Phase A implementation.

**Next Action**: Review plan, confirm approach, then start with MAL parser implementation.
