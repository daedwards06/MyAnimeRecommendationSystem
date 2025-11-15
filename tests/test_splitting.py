import pandas as pd

from src.data.cleaning import SplitConfig, user_based_split


def test_user_split_ratios():
    df = pd.DataFrame(
        {
            "user_id": [1] * 10 + [2] * 10,
            "anime_id": list(range(10)) * 2,
            "rating": [5.0] * 20,
        }
    )
    tr, va, te = user_based_split(df, SplitConfig(val_ratio=0.15, test_ratio=0.15))
    assert len(tr) + len(va) + len(te) == len(df)
    assert len(va) > 0 and len(te) > 0
