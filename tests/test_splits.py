import pandas as pd

from src.eval.splits import build_validation, reporting_and_tuning_users, sample_user_ids


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


def test_tuning_users_are_disjoint_from_reporting_cohort():
    users = list(range(5000))
    report, tune = reporting_and_tuning_users(users, 1000, 1000, seed=42)
    assert len(report) == 1000
    assert len(tune) == 1000
    assert not set(report) & set(tune)


def test_reporting_cohort_is_the_cohort_eval_scripts_score():
    users = list(range(5000))
    report, _ = reporting_and_tuning_users(users, 1000, 500, seed=42)
    assert report == sample_user_ids(users, 1000, seed=42)
