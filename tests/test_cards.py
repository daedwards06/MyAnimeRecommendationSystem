"""Recommendation cards render the explanation, rank and badge label as class-styled HTML (UI redesign Task 2.4)."""

from __future__ import annotations

from streamlit.testing.v1 import AppTest

from src.app.components.cards import (
    GENRE_ROW_MARKER_HTML,
    GRID_MARKER_HTML,
    explanation_html,
    poster_html,
    score_badge_html,
)
from src.app.score_semantics import MATCH_TIERS, SCORE_LABEL_SHORT

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
    assert "<span class='mars-rank'>#1</span> Top match" in html
    assert "<img class='mars-poster'" in html and "alt='Steins;Gate'" in html
    assert "style=" not in html


def test_grid_card_html_has_explanation_rank_and_badge():
    html = _markdown(_run("grid"))
    assert "mars-card-marker" in html
    assert explanation_html(EXPLANATION, compact=True) in html
    assert "#1</span> Top match" in html
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


def test_badge_meaning_is_in_text_not_only_color():
    labels = [label for label, _ in MATCH_TIERS]
    scores = [i / 20 for i in range(20)]
    for score in scores:
        for compact in (False, True):
            html = score_badge_html(score, scores, compact=compact)
            assert sum(f"</span> {label}</span>" in html for label in labels) == 1, html
    assert f"{SCORE_LABEL_SHORT}: " in score_badge_html(0.42, None)


def test_poster_alt_is_the_escaped_title():
    html = poster_html("https://example.com/p.jpg", "Kaguya-sama: 'Love' & War")
    assert "alt='Kaguya-sama: &#x27;Love&#x27; &amp; War'" in html
    assert html.count("<img ") == 1


LONG_TITLE = "That Time I Got Reincarnated as a Slime Season 3"


def _grid_app(view: str) -> None:
    import pandas as pd
    import streamlit as st

    from app.display import _render_cards

    titles = ["Steins;Gate", "That Time I Got Reincarnated as a Slime Season 3", "Cowboy Bebop", "Mushishi", "Monster"]
    metadata = pd.DataFrame(
        [{"anime_id": i, "title_english": t, "genres": "Drama", "poster_url": None} for i, t in enumerate(titles, 1)]
    )
    st.session_state["view_mode"] = view
    recs = [{"anime_id": i, "score": 1.0 - i / 10} for i in (3, 1, 5, 2, 4)]
    _render_cards(recs, metadata, pop_pct_fn=lambda _: 50.0, is_in_training_fn=lambda _: True)


def test_grid_view_is_one_marked_block_in_rank_order():
    at = AppTest.from_function(_grid_app, kwargs={"view": "grid"})
    at.run(timeout=30)
    assert not at.exception, at.exception
    texts = [m.value for m in at.markdown]
    assert texts.count(GRID_MARKER_HTML) == 1
    assert texts.index(GRID_MARKER_HTML) < next(i for i, t in enumerate(texts) if "mars-card-marker" in t)
    titles = [t for t in texts if "mars-card-title-compact" in t]
    expected = ["Cowboy Bebop", "Steins;Gate", "Monster", LONG_TITLE, "Mushishi"]
    assert titles == [f"<p class='mars-card-title-compact'>{t}</p>" for t in expected]


def test_list_view_has_no_grid_marker():
    at = AppTest.from_function(_grid_app, kwargs={"view": "list"})
    at.run(timeout=30)
    assert not at.exception, at.exception
    assert GRID_MARKER_HTML not in [m.value for m in at.markdown]


def test_local_poster_is_a_data_uri_and_missing_files_fall_back(tmp_path):
    from src.app.components.cards import _local_poster_url

    thumb = tmp_path / "1_thumb.webp"
    thumb.write_bytes(b"RIFF0000WEBP")
    assert _local_poster_url(str(thumb)) == "data:image/webp;base64,UklGRjAwMDBXRUJQ"
    assert _local_poster_url(str(tmp_path / "missing_thumb.webp")) is None


def test_app_code_does_not_import_private_streamlit_modules():
    # Cloud installs a newer Streamlit than the local 1.38 (requirements.txt floors the version);
    # streamlit.elements.image.image_to_url moved and took the deployed app down. The style loader's
    # get_script_run_ctx is the one allowed exception: it is still exported by current releases.
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    offenders = {
        p.relative_to(root).as_posix()
        for p in [*root.glob("app/**/*.py"), *root.glob("src/**/*.py")]
        if any(m in p.read_text(encoding="utf-8") for m in ("streamlit.elements", "streamlit.runtime"))
    }
    assert offenders <= {"app/styles/__init__.py"}


def test_genre_buttons_follow_the_genre_row_marker():
    # The pill style is scoped to the row right after this marker (audit F6).
    for view in ("list", "grid"):
        at = _run(view)
        assert GENRE_ROW_MARKER_HTML in _markdown(at), view
        assert {b.label for b in at.button} >= {"Drama", "Sci-Fi"}, view
