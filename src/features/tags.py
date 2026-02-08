from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def _to_token_list(x: Any) -> list[str]:
    """Coerce various container/string types to a clean list[str] tokens.
    Accepts list/tuple/set/np.ndarray/pd.Series or delimited strings ("," or "|")."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return []
    # Containers
    if isinstance(x, (list, tuple, set)):
        return [str(t).strip() for t in x if str(t).strip()]
    if isinstance(x, np.ndarray):
        return [str(t).strip() for t in x.tolist() if str(t).strip()]
    if isinstance(x, pd.Series):
        return [str(t).strip() for t in x.dropna().tolist() if str(t).strip()]
    # Delimited string
    if isinstance(x, str):
        s = x.replace("|", ",")
        return [t.strip() for t in s.split(",") if t.strip()]
    return []


def build_multi_hot(
    meta: pd.DataFrame,
    id_col: str = "anime_id",
    genres_col: str = "genres_list",
    themes_col: str = "themes_list",
) -> pd.DataFrame:
    """Create multi-hot columns for genres and themes; columns named genre_* and theme_*."""
    meta = meta[[id_col, genres_col, themes_col]].copy()
    meta[genres_col] = meta[genres_col].apply(_to_token_list)
    meta[themes_col] = meta[themes_col].apply(_to_token_list)

    genres = sorted({g for lst in meta[genres_col] for g in lst})
    themes = sorted({t for lst in meta[themes_col] for t in lst})

    def to_hot(lst: list[str], vocab: list[str]) -> list[int]:
        s = set(lst)
        return [1 if v in s else 0 for v in vocab]

    genre_hot = meta[genres_col].apply(
        lambda lst: pd.Series(to_hot(lst, genres), index=[f"genre_{g}" for g in genres])
    )
    theme_hot = meta[themes_col].apply(
        lambda lst: pd.Series(to_hot(lst, themes), index=[f"theme_{t}" for t in themes])
    )
    return pd.concat([meta[[id_col]], genre_hot, theme_hot], axis=1)


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def build_tfidf_from_tags(
    meta: pd.DataFrame,
    id_col: str = "anime_id",
    tag_cols: Iterable[str] = ("genres_list", "themes_list"),
    max_features: int = 10000,
    ngram_range: tuple[int, int] = (1, 2),
) -> pd.DataFrame:
    """
    Join list-like tag columns into a token string and fit TF-IDF.
    Returns DataFrame with [id_col] + tfidf_* columns.
    """

    def as_str(row: pd.Series) -> str:
        tokens: list[str] = []
        for c in tag_cols:
            val = row.get(c, [])
            tokens.extend(_to_token_list(val))
        return " ".join(sorted(set(tokens)))

    tmp = meta[[id_col, *tag_cols]].copy()
    tmp["tags_str"] = tmp.apply(as_str, axis=1)

    # If all documents are empty, return id-only DataFrame to avoid empty vocabulary errors
    tags_series = tmp["tags_str"].fillna("")
    if not tags_series.str.len().gt(0).any():
        return tmp[[id_col]].reset_index(drop=True)

    vec = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        token_pattern=r"(?u)\b\w+\b",
    )
    try:
        X = vec.fit_transform(tags_series)
    except ValueError as e:
        # Handle "empty vocabulary" gracefully by returning id-only DataFrame
        if "empty vocabulary" in str(e).lower():
            return tmp[[id_col]].reset_index(drop=True)
        raise
    feature_names = [f"tfidf_{t}" for t in vec.get_feature_names_out()]
    X_df = pd.DataFrame.sparse.from_spmatrix(
        X, index=tmp.index, columns=feature_names
    )

    return pd.concat(
        [tmp[[id_col]].reset_index(drop=True), X_df.reset_index(drop=True)], axis=1
    )


def build_tfidf_and_vectorizer(
    meta: pd.DataFrame,
    id_col: str = "anime_id",
    tag_cols: Iterable[str] = ("genres_list", "themes_list"),
    max_features: int = 10000,
    ngram_range: tuple[int, int] = (1, 2),
) -> tuple[pd.DataFrame, TfidfVectorizer]:
    """Build TF-IDF matrix and return both DataFrame and fitted vectorizer."""
    df = build_tfidf_from_tags(
        meta, id_col=id_col, tag_cols=tag_cols, max_features=max_features, ngram_range=ngram_range
    )
    # If no features, fit a dummy vectorizer with empty vocab to keep interface consistent
    def as_str(row: pd.Series) -> str:
        tokens: list[str] = []
        for c in tag_cols:
            tokens.extend(_to_token_list(row.get(c, [])))
        return " ".join(sorted(set(tokens)))

    tmp = meta[[id_col, *tag_cols]].copy()
    tmp["tags_str"] = tmp.apply(as_str, axis=1).fillna("")
    vec = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        token_pattern=r"(?u)\b\w+\b",
    )
    try:
        vec.fit(tmp["tags_str"])  # fit even if df ended up id-only previously
    except ValueError:
        # empty vocabulary is acceptable; consumer can handle no tfidf_* columns
        pass
    return df, vec


def save_tfidf_vectorizer(vec: TfidfVectorizer, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(vec, path)


def load_tfidf_vectorizer(path: Path) -> TfidfVectorizer:
    return joblib.load(path)
