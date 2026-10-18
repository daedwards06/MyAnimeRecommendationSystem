from __future__ import annotations

from src.app.explanations import explain_in_words
from src.app.scoring_pipeline import finalize_explanation_shares

SEED = "Steins;Gate"
SEED_GENRES = {SEED: {"Drama", "Sci-Fi", "Suspense"}}
ITEM_GENRES = ["Comedy", "Sci-Fi", "Suspense"]


def _contrib(**overrides):
    base = {
        "mf": 0.0,
        "knn": 0.0,
        "content": 1.0,
        "pop": 0.0,
        "_used": ["mf", "knn", "content", "pop"],
        "seed_genres": SEED_GENRES,
    }
    base.update(overrides)
    return base


def test_genre_clause_names_shared_genres_and_seed():
    s = explain_in_words(_contrib(), [SEED], ITEM_GENRES)
    assert s == "Shares Sci-Fi and Suspense with Steins;Gate"


def test_story_clause_fires_above_high_sim_threshold():
    s = explain_in_words(_contrib(seed_genres={}, synopsis_neural_sim=0.9), [SEED], ITEM_GENRES)
    assert s == "Very similar story"
    assert explain_in_words(_contrib(seed_genres={}, synopsis_neural_sim=0.1), [SEED], ITEM_GENRES) == ""


def test_knn_clause_when_knn_is_the_larger_cf_share():
    s = explain_in_words(_contrib(content=0.0, mf=0.1, knn=0.2), [SEED], ITEM_GENRES)
    assert s == "Fans of Steins;Gate also rate it highly"


def test_mf_clause_when_mf_is_the_larger_cf_share():
    s = explain_in_words(_contrib(content=0.0, mf=0.2, knn=0.1), [SEED], ITEM_GENRES)
    assert s == "Rated well by MAL viewers overall"
    s = explain_in_words(_contrib(content=0.0, mf=0.2, has_profile=True), [SEED], ITEM_GENRES)
    assert s == "Matches the taste of viewers who rate like you"


def test_popularity_clauses():
    well_known = explain_in_words(_contrib(content=0.0, pop=0.3, popularity_pct=0.02), [SEED], ITEM_GENRES)
    assert well_known == "A well-known pick"
    gem = explain_in_words(_contrib(content=0.0, popularity_pct=0.8), [SEED], ITEM_GENRES)
    assert gem == "A hidden gem"


def test_full_sentence_caps_at_three_clauses_in_priority_order():
    c = _contrib(content=0.7, knn=0.3, synopsis_neural_sim=0.9, popularity_pct=0.8)
    s = explain_in_words(c, [SEED], ITEM_GENRES)
    assert s == "Shares Sci-Fi and Suspense with Steins;Gate · very similar story · fans of Steins;Gate also rate it highly"


def test_zero_share_components_are_never_mentioned():
    # Content signals are present but the content share is zero; MF/kNN unused.
    c = _contrib(
        content=0.0,
        mf=0.9,
        knn=0.9,
        pop=0.5,
        _used=["content"],
        synopsis_neural_sim=0.9,
        popularity_pct=0.02,
    )
    assert explain_in_words(c, [SEED], ITEM_GENRES) == ""


def test_multi_seed_appends_seed_match_count():
    seeds = [SEED, "Erased", "Monster"]
    c = _contrib(
        seed_genres={SEED: {"Sci-Fi"}, "Erased": {"Mystery", "Suspense", "Sci-Fi"}, "Monster": {"Drama"}},
        knn=0.2,
        seeds_matched=2,
    )
    s = explain_in_words(c, seeds, ["Mystery", "Sci-Fi", "Suspense"])
    assert s == "Shares Mystery and Sci-Fi with Erased · fans of your seeds also rate it highly · Matches 2 of 3 seeds"


def test_finalize_puts_sentence_on_card_and_shares_in_breakdown():
    recs = [
        {
            "anime_id": 1,
            "explanation": {"mf": 0.0},
            "_raw_components": {"mf": 0.0, "knn": 1.0, "content": 3.0, "pop": 0.0},
            "_used_components": ["knn", "content", "pop"],
            "_explanation_meta": {
                "seed_titles": [SEED],
                "seeds_matched": 1,
                "seed_genres": SEED_GENRES,
                "item_genres": ITEM_GENRES,
                "synopsis_neural_sim": 0.0,
                "synopsis_tfidf_sim": 0.0,
            },
        }
    ]
    out = finalize_explanation_shares(recs, pop_pct_fn=lambda _aid: 0.3)
    assert out[0]["explanation"] == "Shares Sci-Fi and Suspense with Steins;Gate · fans of Steins;Gate also rate it highly"
    assert out[0]["signal_breakdown"] == "Similar-item CF 25.0% | Content 75.0% | Popularity 0.0%"
