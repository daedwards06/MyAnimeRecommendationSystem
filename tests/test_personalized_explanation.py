import pandas as pd

from src.app.components.explanations import generate_explanation

METADATA = pd.DataFrame(
    {
        "anime_id": [1, 2, 3, 4],
        "title_display": ["Rated A", "Rated B", "Rated C", "Candidate"],
        "genres": ["Drama|Mystery", "Drama|Mystery", "Drama", "Drama|Mystery"],
    }
)


def test_explanation_has_no_raw_score_or_markdown():
    profile = {"ratings": {1: 9, 2: 8, 3: 9}}
    text = generate_explanation(4, 1.083, profile, METADATA)
    assert text is not None
    assert "**" not in text
    assert "1.083" not in text
    assert "Match score" not in text
    assert text.startswith("You rate Drama")


def test_explanation_falls_back_without_genre_or_similar_match():
    profile = {"ratings": {1: 3}}
    assert generate_explanation(4, 0.5, profile, METADATA) == "Based on your taste profile"
