# Watchlist & Personalization Implementation Plan

## Project Goal
Enable users to import their MyAnimeList watch history to exclude already-watched anime from recommendations, with future support for personalized collaborative filtering based on their rating history.

---

## Phase A: MAL Import + Exclusion Filter (MVP - Quick Win)

**Timeline**: 1-2 days  
**Value**: Immediate elimination of already-watched anime from recommendations

### Checklist

#### 1. MAL XML Parser Module (`src/data/mal_parser.py`)
- [x] Create parser function `parse_mal_export(xml_path) -> dict`
- [x] Extract fields: `anime_title`, `series_animedb_id`, `my_score`, `my_status`
- [x] Handle status types: Completed, Watching, On-Hold, Dropped, Plan to Watch
- [x] Map MAL IDs to internal anime_ids (using metadata lookup)
- [x] Return structure:
  ```python
  {
    "username": "...",
    "watched_ids": [1, 5, 6, ...],  # anime_ids
    "ratings": {1: 8.5, 5: 7.0, ...},  # anime_id: score
    "status_map": {1: "Completed", 5: "Watching", ...},
    "unmatched": [{"mal_id": 123, "title": "..."}]  # titles not in our DB
  }
  ```
- [x] Add error handling for malformed XML
- [x] Log unmatched titles (MAL IDs not in our metadata)

#### 2. User Profile Storage (`src/data/user_profiles.py`)
- [x] Create `data/user_profiles/` directory structure
- [x] Implement `save_profile(username, profile_data) -> Path`
  - Save as JSON: `data/user_profiles/{username}_profile.json`
- [x] Implement `load_profile(username) -> dict | None`
- [x] Implement `list_profiles() -> list[str]`
- [x] Profile schema:
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
- [x] Add profile validation function

#### 3. Streamlit UI Integration (`app/main.py`)
- [x] Add "👤 User Profile" expander in sidebar (below Performance section)
- [x] **Profile Selector**:
  - [x] Dropdown to select existing profile or "(none)"
  - [x] Show profile stats when loaded (watched count, avg rating)
- [x] **MAL Import UI**:
  - [x] File uploader widget for XML (`st.file_uploader`)
  - [x] "Parse & Preview" button
  - [x] Show import summary: "Found X anime (Y rated, Z unrated)"
  - [x] Display unmatched titles if any (warning)
  - [x] Username text input
  - [x] Import options (hardcoded defaults - configurable in future):
    - ☑️ Use ratings when available (default: on)
    - ☑️ Default unrated completed to 7.0 (default: on)
    - ☑️ Include "Plan to Watch" (default: off)
    - ☑️ Include "On Hold" (default: on)
  - [x] "💾 Save Profile" button
- [x] Store active profile in `st.session_state["active_profile"]`
- [x] Show active profile indicator: "✓ Profile: {username} ({X} watched)"

#### 4. Recommendation Exclusion Filter
- [x] **Browse Mode**: Filter out watched anime before adding to `browse_results`
- [x] **Recommendation Mode**: 
  - [x] Filter out watched anime from multi-seed scoring loop
  - [x] Filter out watched anime from multi-seed scoring (not using get_top_n_for_user in current implementation)
  - [x] Adjust `filter_multiplier` to account for watched exclusions (increased to 10x)
- [x] Add exclusion counter: Display "Excluded {X} already-watched titles" below results
- [x] Ensure exclusion happens BEFORE other filters (genre/type/year)

#### 5. Testing & Validation
- [x] Unit test: MAL XML parser with sample export file
- [x] Unit test: Profile save/load roundtrip
- [x] Integration test: Import profile → load in app → verify exclusions
- [x] Manual test: Import your personal MAL export
- [x] Verify no watched anime appear in recommendations
- [x] Test edge cases: empty watchlist, all anime watched, malformed XML

#### 6. Documentation Updates
- [x] Update `README.md` with "Import Your Watchlist" section
- [x] Add `docs/user_guide_watchlist.md` with detailed instructions
- [x] Update `docs/running_context.md` with Phase A completion
- [x] Document MAL export instructions (how to download from MAL)

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
- [x] Add `data/user_profiles/*.json` to `.gitignore`
- [x] Keep directory structure tracked with `.gitkeep`
- [x] Document: "Profiles stay local, never committed to git"
- [x] Provide `data/user_profiles/example_profile.json` (sample structure, not real data)

#### First-Run Experience
- [x] **Default state**: App launches with no profile selected
  - All features work normally (browse, seed recommendations)
  - No exclusions applied (shows all anime)
  - No personalization (uses default collaborative filtering)
- [x] **Profile indicator**: Sidebar shows "👤 User Profile" (collapsed) when none selected
- [x] **Soft prompt** (non-intrusive):
  - Info box in sidebar: "💡 Import your MAL watchlist to hide anime you've already watched"
  - No modal/blocking dialog (user can ignore and use app normally)

#### Documentation for Fork Users
- [x] Update `README.md` with "Getting Started" section:
  - Clone repo → install deps → run app (works immediately)
  - Optional: Import MAL for personalization
  - Link to MAL export instructions
- [x] Add `docs/user_guide_watchlist.md`:
  - How to export from MAL (step-by-step)
  - How to import in app
  - Privacy note (profiles are local only)
  - How to switch profiles
- [x] Add FAQ:
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
- [x] Profile selector defaults to "(none)"
- [x] When no profile: Show info message "💡 Import your MAL watchlist to hide anime you've already watched"
- [x] When profile loaded: Show "✓ Profile: {username} ({X} watched)"
- [x] Profile UI is collapsed by default (user expands if interested)

#### Add to "6. Documentation Updates"
- [x] README: "Quick Start" section (no profile required)
- [x] README: "Import Your Watchlist (Optional)" section
- [x] Create `.gitignore` rules for profiles
- [x] Add `data/user_profiles/.gitkeep` to track directory
- [x] Create example profile JSON (structure reference)

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

**Status**: ✅ **Phase A (MVP) Complete** - November 27, 2025

**Completed:**
- MAL XML parser with full error handling and metadata matching
- Profile management system (save/load/list/validate)
- Streamlit UI integration (profile selector, import UI, stats display)
- Exclusion filter in both browse and recommendation modes
- Comprehensive testing (unit tests, integration tests, manual testing)
- Full documentation (README, user guide, running context, implementation plan)

**Results:**
- 93/104 anime matched from real MAL export (89% success rate)
- Zero watched anime appearing in filtered results
- <5 second import time for 100+ anime
- Profile persistence across sessions working correctly
- Multi-user support confirmed functional
- Privacy-by-default (profiles local-only, git-ignored)

**Next Phase**: Phase B - Personalized Collaborative Filtering (user embeddings, personalized scoring, rating management)
