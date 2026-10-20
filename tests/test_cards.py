"""Recommendation cards render the explanation, rank and badge label as class-styled HTML (UI redesign Task 2.4)."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

from src.app.components.cards import explanation_html, poster_html, score_badge_html

SCORES = [0.9, 0.7, 0.5, 0.3]
EXPLANATION = "You rate Drama and Mystery highly"


def _card_app(view: str, demo: bool) -> None:
    import pandas as pd
    import streamlit as st

    from src.app.components.cards import render_card, render_card_grid

    row = pd.Series(
        {
            "anime_id": 9253,
            "title_english": "Steins;Gate",
            "title_japanese": "\u30b7\u30e5\u30bf\u30a4\u30f3\u30ba",  # AppTest writes the script as cp1252
            "genres": "Drama|Sci-Fi",
            "poster_thumb_url": None,
            "poster_url": "https://cdn.myanimelist.net/images/anime/5/73199.jpg",
            "synopsis": "A self-proclaimed mad scientist.",
            "mal_score": 9.07,
            "type": "TV",
            "episodes": 24,
            "status": "Finished Airing",
            "aired_from": "2011-04-06",
        }
    )
    rec = {"anime_id": 9253, "score": 0.9, "explanation": "You rate Drama and Mystery highly"}
    st.session_state["active_profile"] = {"username": "demo", "demo": demo, "ratings": {}}
    render = render_card_grid if view == "grid" else render_card
    render(row, rec, 50.0, is_in_training=True, all_raw_scores=[0.9, 0.7, 0.5, 0.3])


def _run(view: str, demo: bool = True) -> AppTest:
    at = AppTest.from_function(_card_app, kwargs={"view": view, "demo": demo})
    at.run(timeout=30)
    assert not at.exception, at.exception
    return at


def _markdown(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def test_list_card_html_has_explanation_rank_badge_and_poster_alt():
    html = _markdown(_run("list"))
    assert "mars-card-marker" in html
    assert explanation_html(EXPLANATION) in html
    assert "<span class='mars-rank'>#1</span>Top match" in html
    assert "<img class='mars-poster'" in html and "alt='Steins;Gate'" in html
    assert "style=" not in html


def test_grid_card_html_has_explanation_rank_and_badge():
    html = _markdown(_run("grid"))
    assert "mars-card-marker" in html
    assert explanation_html(EXPLANATION, compact=True) in html
    assert "#1</span>Top match" in html
    assert "style=" not in html


def test_explanation_sits_directly_under_the_title():
    texts = [m.value for m in _run("list").markdown]
    title = next(i for i, t in enumerate(texts) if "mars-card-title" in t)
    assert "mars-explanation" in texts[title + 1]


def test_demo_profile_rating_buttons_are_disabled():
    for view in ("list", "grid"):
        buttons = [b for b in _run(view, demo=True).button if b.key and b.key.startswith("quick_")]
        assert len(buttons) == 3 and all(b.disabled for b in buttons), view
    buttons = [b for b in _run("grid", demo=False).button if b.key and b.key.startswith("quick_")]
    assert buttons and not any(b.disabled for b in buttons)


def test_badge_tooltip_text_is_unchanged():
    assert "title='Rank 1 of 4 in this run, raw score 0.900 (relative, not a probability)'" in score_badge_html(
        0.9, SCORES
    )


def test_poster_alt_is_the_escaped_title():
    html = poster_html("https://example.com/p.jpg", "Kaguya-sama: 'Love' & War")
    assert "alt='Kaguya-sama: &#x27;Love&#x27; &amp; War'" in html
    assert html.count("<img ") == 1
