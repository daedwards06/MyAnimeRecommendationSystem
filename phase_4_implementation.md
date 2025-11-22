

## Phase 4 Implementation Plan

### 1. Step-by-Step Action Plan

1. Metrics & Data Access
   - Gather per-model metric-by-K logs (ensure each model exposes: K, ndcg, map, coverage, gini).
   - Standardize schema: columns = ['model','K','ndcg','map','coverage','gini'].
   - Persist aggregated frame for reuse: `data/processed/phase4/metrics_by_k.parquet`.

2. Plotting
   - Implement `scripts/plot_phase4_metrics.py`:
     - Load metrics frame.
     - Produce:
       - ndcg_vs_k.png / map_vs_k.png
       - coverage_vs_k.png / gini_vs_k.png
     - Save under `reports/figures/phase4/`.
     - Optionally produce interactive Plotly HTML copies.

3. Ablation Table
   - Implement `scripts/generate_phase4_ablation.py`:
     - Filter K=10 rows for required models.
     - Compute relative lifts vs Popularity for ndcg, map, coverage.
     - Output:
       - `reports/phase4_ablation.csv`
       - `reports/phase4_ablation.md` (Markdown table).

4. Hybrid Explanation Examples
   - Add utility in script (or `src/eval/explanations.py`): given user_id & top-N hybrid ranking + component scores, produce per-item contribution percentages.
   - Serialize example snippet to `reports/artifacts/phase4_hybrid_examples.json`.
   - Inject Markdown into report.

5. Temporal Split Sanity Check
   - Implement function:
     - Create earlier_time vs later_time splits (e.g., based on interaction timestamp quantile 0.75).
     - Train MF + Hybrid on early, evaluate on late.
     - Compare ndcg@10 deltas vs unified slice metrics.
   - Save summary JSON: `reports/artifacts/phase4_temporal_check.json`.

6. Cold-Start Recap
   - Identify items flagged as new (no historical ratings).
   - Evaluate content-only recommender (TF-IDF + embedding blend).
   - Produce qualitative examples: recommended list + driving feature similarities.
   - Save to `reports/artifacts/phase4_cold_start_examples.json`.

7. CI & Quality Gates
   - Add `.github/workflows/ci.yml`:
     - Setup Python.
     - Cache pip.
     - Install deps from requirements.txt.
     - Run: `ruff check .`, `black --check .`, `pytest -q`.
   - Add `.pre-commit-config.yaml` & instructions for install.

8. Documentation & Reporting
   - Create `reports/phase4_evaluation.md` consolidating:
     - Plots (embed relative paths).
     - Ablation table.
     - Explanation examples.
     - Temporal split summary.
     - Cold-start analysis.
     - Diversity interpretation.
   - Update running_context.md with Phase 4 artifacts.
   - Link report in README.md.

9. Optional Stretch (defer unless time remains)
   - Genre exposure histogram vs catalog.
   - Novelty (inverse popularity) distribution chart.
   - Implicit ALS / LightFM comparative curves if adds narrative value.

10. Phase 5 Readiness
   - Expose explanation function and artifact loader for Streamlit.
   - Define simplified API contract for app layer (`get_recommendations`, `explain_hybrid_item`).

### 2. Code Snippets

#### `scripts/plot_phase4_metrics.py`
```python
#!/usr/bin/env python
"""
Plot Phase 4 evaluation curves:
- Ranking metrics (NDCG@K, MAP@K)
- Diversity metrics (Coverage@K, Gini@K)
Saves PNG (and optional HTML) under reports/figures/phase4/.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

MODELS_DISPLAY_ORDER = ["popularity", "mf", "hybrid", "content_tfidf"]
PALETTE = {
    "popularity": "#D95F02",
    "mf": "#1B9E77",
    "hybrid": "#7570B3",
    "content_tfidf": "#E7298A",
}

def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    required = {"model", "K", "ndcg", "map", "coverage", "gini"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in metrics file: {missing}")
    return df

def plot_curve(df: pd.DataFrame, metric: str, out_dir: Path) -> None:
    plt.figure(figsize=(7, 5))
    sns.lineplot(
        data=df[df["model"].isin(MODELS_DISPLAY_ORDER)],
        x="K",
        y=metric,
        hue="model",
        palette=PALETTE,
        marker="o",
    )
    plt.title(f"{metric.upper()} vs K")
    plt.xlabel("K")
    plt.ylabel(metric.upper())
    plt.legend(title="Model")
    out_path = out_dir / f"{metric}_vs_k.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def main(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = load_metrics(Path(args.metrics_path))

    for metric in ["ndcg", "map", "coverage", "gini"]:
        plot_curve(df, metric, out_dir)

    print(f"Saved plots to {out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics-path",
        default="data/processed/phase4/metrics_by_k.parquet",
        help="Parquet file containing evaluation metrics per K & model.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/figures/phase4",
        help="Directory for output figures."
    )
    main(parser.parse_args())
```

#### `scripts/generate_phase4_ablation.py`
```python
#!/usr/bin/env python
"""
Generate Phase 4 ablation table comparing models at K=10.
Outputs CSV + Markdown with relative lifts vs popularity baseline.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

TARGET_K = 10
BASELINE_MODEL = "popularity"
MODELS = ["popularity", "mf", "hybrid", "content_tfidf"]
METRICS = ["ndcg", "map", "coverage"]

def compute_lifts(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["model"] == BASELINE_MODEL].iloc[0]
    rows = []
    for _, row in df.iterrows():
        data = {
            "model": row["model"],
            "ndcg@10": row["ndcg"],
            "map@10": row["map"],
            "coverage@10": row["coverage"],
        }
        # Relative lifts vs baseline (percentage)
        for m in METRICS:
            if base[m] == 0:
                lift = None
            else:
                lift = (row[m] - base[m]) / base[m] * 100.0
            data[f"{m}_lift_vs_{BASELINE_MODEL}_pct"] = lift
        rows.append(data)
    return pd.DataFrame(rows)

def to_markdown_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False, floatfmt=".4f")

def main(args: argparse.Namespace) -> None:
    metrics = pd.read_parquet(args.metrics_path)
    subset = metrics[(metrics["K"] == TARGET_K) & (metrics["model"].isin(MODELS))]
    if subset.empty:
        raise ValueError("No rows found for target K and models.")
    ablation = compute_lifts(subset)

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    ablation.to_csv(out_csv, index=False)
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Phase 4 Ablation (K=10)\n\n")
        f.write(to_markdown_table(ablation))
        f.write("\n")

    print(f"Wrote ablation CSV: {out_csv}")
    print(f"Wrote ablation Markdown: {out_md}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics-path",
        default="data/processed/phase4/metrics_by_k.parquet",
        help="Input metrics parquet path."
    )
    parser.add_argument(
        "--output-csv",
        default="reports/phase4_ablation.csv",
        help="CSV output file."
    )
    parser.add_argument(
        "--output-md",
        default="reports/phase4_ablation.md",
        help="Markdown output file."
    )
    main(parser.parse_args())
```

#### Hybrid Explanation Utility (example `src/eval/explanations.py`)
```python
from __future__ import annotations
from typing import Dict, List, Tuple
import pandas as pd

def compute_hybrid_contributions(
    component_scores: Dict[str, float],
    weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Convert component scores and weights into normalized contribution shares.

    component_scores: raw scores from each source (e.g., mf, knn, pop, content)
    weights: blending weights (same keys as component_scores subset)

    Returns dict of component -> percentage share of final hybrid score.
    """
    weighted = {k: component_scores.get(k, 0.0) * weights.get(k, 0.0) for k in component_scores}
    total = sum(weighted.values())
    if total == 0:
        return {k: 0.0 for k in weighted}
    return {k: v / total for k, v in weighted.items()}

def format_explanation(item_id: int, contributions: Dict[str, float]) -> str:
    """
    Human-readable summary of component shares.
    """
    parts = [f"{src}: {pct:.1%}" for src, pct in sorted(contributions.items(), key=lambda x: -x[1])]
    return f"Item {item_id} hybrid contribution breakdown -> " + ", ".join(parts)

def build_examples(
    recommendations: List[Tuple[int, Dict[str, float]]],
    weights: Dict[str, float],
    top_n: int = 3
) -> List[Dict[str, str]]:
    """
    recommendations: list of (item_id, component_scores_dict)
    Returns list of explanation dicts for top N items.
    """
    examples = []
    for item_id, comp_scores in recommendations[:top_n]:
        shares = compute_hybrid_contributions(comp_scores, weights)
        examples.append(
            {
                "item_id": str(item_id),
                "shares": {k: round(v, 4) for k, v in shares.items()},
                "text": format_explanation(item_id, shares),
            }
        )
    return examples
```

#### Temporal Split Check (snippet)
```python
def temporal_split_sanity(
    interactions: pd.DataFrame,
    time_col: str,
    cutoff_quantile: float = 0.75
) -> Dict[str, float]:
    """
    Perform temporal split: earlier vs later partitions.
    Returns dict of metric deltas and raw metrics.

    interactions: columns include user_id, item_id, rating, timestamp
    """
    cutoff = interactions[time_col].quantile(cutoff_quantile)
    early = interactions[interactions[time_col] <= cutoff]
    late = interactions[interactions[time_col] > cutoff]

    # Train models on early; evaluate on late (pseudo-code).
    # mf_model = train_mf(early)
    # hybrid_model = train_hybrid(early)
    # metrics_late_mf = evaluate(mf_model, late)
    # metrics_late_hybrid = evaluate(hybrid_model, late)
    # unified_metrics = evaluate(hybrid_model, interactions)  # or precomputed

    # Return placeholder structure to be populated.
    return {
        "cutoff_ts": cutoff,
        "early_count": len(early),
        "late_count": len(late),
        "mf_ndcg_late": None,
        "hybrid_ndcg_late": None,
        "hybrid_ndcg_unified": None,
        "hybrid_ndcg_delta_late_vs_unified": None,
    }
```

#### GitHub Actions CI (`.github/workflows/ci.yml`)
```yaml
name: CI

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  build-test-lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
            python-version: "3.11"

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff black

      - name: Lint (ruff)
        run: ruff check .

      - name: Format check (black)
        run: black --check .

      - name: Run tests
        run: pytest -q
```

#### Pre-commit Config (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.4
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

#### Report Skeleton (`reports/phase4_evaluation.md`)
```markdown
# Phase 4 Evaluation & Analysis

## 1. Metric Curves
![NDCG vs K](figures/phase4/ndcg_vs_k.png)
![MAP vs K](figures/phase4/map_vs_k.png)

## 2. Diversity Curves
![Coverage vs K](figures/phase4/coverage_vs_k.png)
![Gini vs K](figures/phase4/gini_vs_k.png)

## 3. Ablation (K=10)
(Embedded from `reports/phase4_ablation.md`)

## 4. Hybrid Explanation Examples
```json
<insert contents of artifacts/phase4_hybrid_examples.json>
```

## 5. Temporal Split Robustness
Summary table & interpretation.

## 6. Cold-Start Performance
Qualitative examples + metric snapshot.

## 7. Diversity & Exposure Narrative
Interpret trade-offs (accuracy vs coverage vs inequality).

## 8. Summary & Next Steps (Transition to Phase 5)
- Artifacts ready for app integration.
```

### 3. File / Module Layout

```
scripts/
  plot_phase4_metrics.py
  generate_phase4_ablation.py
  build_temporal_split.py          # (optional if separated)
src/
  eval/
    explanations.py                # hybrid explanation logic
reports/
  figures/
    phase4/
      ndcg_vs_k.png
      map_vs_k.png
      coverage_vs_k.png
      gini_vs_k.png
  artifacts/
    phase4_hybrid_examples.json
    phase4_temporal_check.json
    phase4_cold_start_examples.json
  phase4_ablation.csv
  phase4_ablation.md
  phase4_evaluation.md
.github/
  workflows/
    ci.yml
.pre-commit-config.yaml
```

### 4. Milestone Checklist (Definition of Done)

Core:
- [ ] Metrics parquet aggregated
- [ ] Curves generated (4 PNGs)
- [ ] Ablation CSV + Markdown
- [ ] Hybrid explanation JSON (top 3 items, per-source shares)

Rigor:
- [ ] Temporal split JSON + interpretation
- [ ] Cold-start examples JSON + summary

Infrastructure:
- [ ] CI workflow green on PR
- [ ] Pre-commit installed (`pre-commit install`)
- [ ] Report compiled & linked from README.md
- [ ] running_context.md updated

Optional:
- [ ] Genre exposure plot
- [ ] Novelty/popularity bias chart

Final:
- [ ] All artifacts committed
- [ ] Proposal references Phase 4 outputs
- [ ] Phase 5 readiness section created

### 5. Phase 5 Preview (App Integration Path)

Artifacts feeding Streamlit:
- Plot images → About/Performance tabs.
- Ablation table → Performance comparison expandable section.
- Explanation function (`compute_hybrid_contributions`) → “Why recommended?” component.
- Temporal robustness & cold-start summary → Info panels clarifying limitations.
- Hybrid weights constants → Reused for real-time scoring.
- Genre exposure (if added) → Diversity insights panel.

Minimal API Contract for App:
```python
def get_recommendations(user_id: int, k: int = 10) -> list[int]:
    """Return top-k item IDs for user using frozen hybrid weights."""

def explain_hybrid_item(user_id: int, item_id: int) -> dict:
    """Return component score breakdown & contribution percentages."""
```

### Try-It (Local Execution Examples)
```powershell
# Generate plots
python scripts/plot_phase4_metrics.py

# Build ablation
python scripts/generate_phase4_ablation.py

# Install pre-commit
pip install pre-commit ruff black
pre-commit install
```

