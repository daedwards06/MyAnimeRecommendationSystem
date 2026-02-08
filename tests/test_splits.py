import pandas as pd

from src.eval.splits import build_validation, sample_user_ids


def test_build_validation_basic():
    df = pd.DataFrame({
        'user_id': [1,1,2,2],
        'anime_id': [10,11,10,12],
        'rating': [5,4,3,2],
    })
    train, val = build_validation(df)
    assert not train.empty
    assert not val.empty
    assert set(train.columns) == set(df.columns)


def test_sample_user_ids_deterministic():
    users = list(range(100))
    a = sample_user_ids(users, 10, seed=123)
    b = sample_user_ids(users, 10, seed=123)
    assert a == b
    assert len(a) == 10
