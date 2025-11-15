import pandas as pd

from src.data.cleaning import clean_interactions


def test_clean_interactions_dedup():
    df = pd.DataFrame({"user_id": [1, 1], "anime_id": [10, 10], "rating": [7.0, 8.0]})
    out = clean_interactions(df)
    assert len(out) == 1
    assert out.iloc[0]["rating"] == 8.0
