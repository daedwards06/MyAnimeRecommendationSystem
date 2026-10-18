"""The README and model card quote the ablation table; these tests hold them to it.

The original headline lift was copied by hand and was wrong. Every number published in the
README Results section and the model card Metrics section is recomputed here from
`reports/phase4_ablation.csv` at the precision the document shows, so a regenerated table and a
stale README can't both be committed.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MODEL_CARD = ROOT / "docs" / "MODEL_CARD.md"
ABLATION_CSV = ROOT / "reports" / "phase4_ablation.csv"

README_LABELS = {
    "Hybrid (weighted, re-tuned; served)": "hybrid_weighted_tuned",
    "Item-kNN": "item_knn_sklearn",
    "Hybrid (RRF rank fusion)": "hybrid_rrf",
    "Popularity baseline": "popularity",
    "MF (FunkSVD)": "mf_sgd",
    "Hybrid (weighted, previous config weights)": "hybrid_weighted",
    "Content-only (TF-IDF)": "content_tfidf",
    "Content-only (embeddings)": "content_embeddings",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("−", "-").replace("**", ""))


def _section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^## )", text, flags=re.M | re.S)
    assert match, f"{path.name}: section {heading!r} not found"
    return match.group(1)


def _table(section: str) -> list[dict[str, str]]:
    lines = [ln for ln in section.splitlines() if ln.startswith("|")]
    assert len(lines) > 2, "no Markdown table in section"

    def split(line: str) -> list[str]:
        return [_normalize(c).strip() for c in line.strip().strip("|").split("|")]

    header = split(lines[0])
    return [dict(zip(header, split(ln))) for ln in lines[2:]]


def _f4(x: float) -> str:
    return f"{x:.4f}"


def _ci(low: float, high: float, fmt: str = "{:.4f}") -> str:
    return f"[{fmt.format(low)}, {fmt.format(high)}]"


def _paired_ci(r: pd.Series, ref: str) -> str:
    if r.name == ref:
        return "—"
    return _ci(r[f"ndcg_diff_vs_{ref}_ci_low"], r[f"ndcg_diff_vs_{ref}_ci_high"], "{:+.4f}")


@pytest.fixture(scope="module")
def ablation() -> pd.DataFrame:
    return pd.read_csv(ABLATION_CSV).set_index("model")


@pytest.fixture(scope="module")
def readme_results() -> str:
    return _section(README, "## Results")


@pytest.fixture(scope="module")
def card_metrics() -> str:
    return _section(MODEL_CARD, "## Metrics")


def test_readme_rows_are_exactly_the_mapped_models(readme_results):
    labels = [row["Model"] for row in _table(readme_results)]
    unmapped = [label for label in labels if label not in README_LABELS]
    assert not unmapped, f"README rows with no ablation id in README_LABELS: {unmapped}"
    assert sorted(labels) == sorted(README_LABELS), "README_LABELS names a row the README no longer has"


def test_readme_table_matches_ablation(readme_results, ablation):
    for row in _table(readme_results):
        r = ablation.loc[README_LABELS[row["Model"]]]
        lift = "(baseline)" if r.name == "popularity" else f"{r['ndcg_lift_vs_popularity_pct']:+.0f}%"
        expected = {
            "NDCG@10": _f4(r["ndcg@10"]),
            "NDCG@10 95% CI": _ci(r["ndcg@10_ci_low"], r["ndcg@10_ci_high"]),
            "MAP@10": _f4(r["map@10"]),
            "Coverage@10": _f4(r["coverage@10"]),
            "Gini@10": _f4(r["gini@10"]),
            "NDCG vs. popularity": lift,
        }
        actual = {col: row[col] for col in expected}
        assert actual == expected, row["Model"]


def test_model_card_table_matches_ablation(card_metrics, ablation):
    rows = _table(card_metrics)
    assert sorted(row["Model"] for row in rows) == sorted(ablation.index)
    for row in rows:
        r = ablation.loc[row["Model"]]
        expected = {
            "NDCG@10": _f4(r["ndcg@10"]),
            "NDCG@10 95% CI": _ci(r["ndcg@10_ci_low"], r["ndcg@10_ci_high"]),
            "MAP@10": _f4(r["map@10"]),
            "Coverage@10": _f4(r["coverage@10"]),
            "Gini@10": _f4(r["gini@10"]),
            "ΔNDCG vs. popularity, paired 95% CI": _paired_ci(r, "popularity"),
            "ΔNDCG vs. item-kNN, paired 95% CI": _paired_ci(r, "item_knn_sklearn"),
        }
        actual = {col: row[col] for col in expected}
        assert actual == expected, row["Model"]


def _paired_claim(ablation: pd.DataFrame, model: str, ref: str) -> str:
    r = ablation.loc[model]
    col = f"ndcg_diff_vs_{ref}"
    return f"{r[col]:+.3f}, CI {_ci(r[f'{col}_ci_low'], r[f'{col}_ci_high'], '{:+.3f}')}"


def test_readme_prose_numbers_match_ablation(readme_results, ablation):
    prose = _normalize(readme_results)
    claims = [
        _paired_claim(ablation, "hybrid_weighted_tuned", "popularity"),
        _paired_claim(ablation, "mf_sgd", "popularity"),
        _paired_claim(ablation, "hybrid_weighted_tuned", "item_knn_sklearn"),
        f"({_f4(ablation.loc['hybrid_weighted', 'ndcg@10'])} → {_f4(ablation.loc['hybrid_weighted_tuned', 'ndcg@10'])})",
    ]
    missing = [c for c in claims if c not in prose]
    assert not missing, f"README Results prose does not state: {missing}"


def test_model_card_prose_numbers_match_ablation(card_metrics, ablation):
    prose = _normalize(card_metrics)
    coverage_ratio = ablation.loc["mf_sgd", "coverage@10"] / ablation.loc["popularity", "coverage@10"]
    claims = [f"coverage ({coverage_ratio:.1f}× popularity)"]
    missing = [c for c in claims if c not in prose]
    assert not missing, f"Model card Metrics prose does not state: {missing}"
