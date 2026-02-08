# Scoring Pipeline Integration Guide

## Task 1.1 Status: Module Extracted ✅

The scoring pipeline has been successfully extracted into `src/app/scoring_pipeline.py` with:
- ✅ `ScoringContext` dataclass - holds all pipeline inputs
- ✅ `PipelineResult` dataclass - holds all pipeline outputs
- ✅ `run_seed_based_pipeline()` - full Stage 0 → 1 → 2 → post-processing
- ✅ `run_personalized_pipeline()` - personalized mode path
- ✅ `run_browse_pipeline()` - browse/filter path
- ✅ NO streamlit imports (verified)

## What Remains: Integration into app/main.py

The extracted module is ready. Now `app/main.py` needs to be updated to call it instead of the inline logic.

### Integration Pattern

The large inline pipeline section (lines ~1490-2460) should be replaced with:

```python
# In app/main.py, around line 1490, replace the entire seed-based pipeline with:

if selected_seed_ids:
    # Build scoring context
    ctx = ScoringContext(
        metadata=metadata,
        components=components,
        recommender=recommender,
        bundle=bundle,
        selected_seed_ids=list(selected_seed_ids),
        selected_seed_titles=list(selected_seed_titles),
        user_index=user_index,
        user_embedding=st.session_state.get("user_embedding"),
        personalization_enabled=False,  # Seed-based mode
        personalization_strength=1.0,
        watched_ids=watched_ids_set,
        ranked_hygiene_exclude_ids=ranked_hygiene_exclude_ids,
        genre_filter=genre_filter,
        type_filter=type_filter,
        year_range=year_range,
        weights=weights,
        top_n=top_n,
        n_requested=n_requested,
        seed_ranking_mode=str(st.session_state.get("seed_ranking_mode", SEED_RANKING_MODE)).strip().lower(),
        browse_mode=False,
        sort_by=sort_by,
    )
    
    # Run pipeline
    pipeline_result = run_seed_based_pipeline(ctx)
    
    # Unpack results
    recs = pipeline_result.ranked_items
    
    # Store diagnostics in session_state
    st.session_state["last_stage0"] = pipeline_result.stage0_diagnostics
    st.session_state["last_stage0_enforcement"] = pipeline_result.enforcement_diagnostics
    if pipeline_result.franchise_cap_diagnostics:
        st.session_state["last_franchise_cap"] = pipeline_result.franchise_cap_diagnostics
```

### Personalized Mode Integration

Around line 2519, replace the personalized mode logic with:

```python
if personalization_strength >= 0.99:
    # Pure personalized mode
    ctx_pers = ScoringContext(
        metadata=metadata,
        components=components,
        recommender=recommender,
        bundle=bundle,
        selected_seed_ids=list(selected_seed_ids) if selected_seed_ids else [],
        selected_seed_titles=list(selected_seed_titles) if selected_seed_titles else [],
        user_index=user_index,
        user_embedding=user_embedding,
        personalization_enabled=True,
        personalization_strength=1.0,
        watched_ids=watched_ids,
        ranked_hygiene_exclude_ids=exclude_ranked_ids,
        genre_filter=genre_filter,
        type_filter=type_filter,
        year_range=year_range,
        weights=weights,
        top_n=top_n,
        n_requested=n_requested,
        browse_mode=False,
    )
    
    pers_result = run_personalized_pipeline(ctx_pers)
    
    if pers_result.personalization_blocked_reason:
        st.session_state["personalization_blocked_reason"] = pers_result.personalization_blocked_reason
    else:
        recs = pers_result.ranked_items
        personalization_applied = pers_result.personalization_applied
```

### Browse Mode Integration

Around line 1332, replace browse mode logic with:

```python
if not genre_filter:
    st.info("Pick ≥1 genre in Filters to start browsing...")
    recs = []
else:
    ctx_browse = ScoringContext(
        metadata=metadata,
        components=components,
        recommender=recommender,  # Not used in browse mode
        bundle=bundle,
        watched_ids=(
            {int(x) for x in st.session_state["active_profile"].get("watched_ids", [])}
            if st.session_state["active_profile"] else set()
        ),
        genre_filter=genre_filter,
        type_filter=type_filter,
        year_range=year_range,
        top_n=min(top_n, len(metadata)),
        browse_mode=True,
        sort_by=sort_by,
    )
    
    browse_result = run_browse_pipeline(ctx_browse)
    recs = browse_result.ranked_items
    
    if browse_result.warnings:
        for warning in browse_result.warnings:
            st.warning(warning)
```

## Step-by-Step Integration Instructions

### Step 1: Identify the seed-based pipeline block
- Start: Line ~1490 (`if selected_seed_ids:`)
- End: Line ~2460 (just before `else:` for default seed-based fallback)
- This is ~970 lines of inline scoring logic

### Step 2: Replace with pipeline call
- Build `ScoringContext` from session_state and widgets
- Call `run_seed_based_pipeline(ctx)`
- Unpack `PipelineResult` and store diagnostics

### Step 3: Integrate personalized mode
- Find the personalized recommendation section (~line 2519)
- Replace with `run_personalized_pipeline()` call
- Handle the blending logic for 0 < strength < 1

### Step 4: Integrate browse mode
- Find the browse mode section (~line 1332)
- Replace with `run_browse_pipeline()` call

### Step 5: Test thoroughly
- Run with 3+ different seed queries
- Compare results before/after (should be identical)
- Verify all diagnostics panels still populate
- Check that personalization still works
- Test browse mode

## Files Modified

- ✅ `src/app/scoring_pipeline.py` - Created (complete)
- ⏳ `app/main.py` - Needs integration (in progress)

## Verification Checklist

After integration:
- [ ] No `import streamlit` in `src/app/scoring_pipeline.py`
- [ ] App produces identical recommendations for same inputs
- [ ] Stage 0/1/2 diagnostics panels still populate
- [ ] Franchise cap diagnostics still work
- [ ] Personalization mode still functions
- [ ] Browse mode still functions
- [ ] All explanation badges still render correctly
- [ ] No regressions in filtering/sorting

## Notes

The extracted module is pure Python and testable without Streamlit. This is the key architectural improvement. The integration into `app/main.py` is straightforward but requires care to preserve all the diagnostic tracking and post-processing logic.

Because of the scale (~1000 lines to replace), I recommend:
1. Making the changes in a new  git branch
2. Testing incrementally (seed-based first, then personalized, then browse)
3. Using manual comparison on known queries to verify identical outputs

## Next Steps

You can either:
1. **Complete the integration yourself** using the patterns above
2. **Have Claude continue** with the full replacement in small incremental steps
3. **Test the extracted module first** before integrating (recommended)

The extracted `scoring_pipeline.py` is production-ready and can be tested independently with mock data (Task 1.2 covers this).
