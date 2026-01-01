

# Phase 4 Implementation Plan

## 1. Step-by-Step Actions

### Metrics & Diversity
1. Load cached evaluation artifacts (per model per K) from existing experiment JSON/CSV (fallback: recompute via `run_unified_eval.py`).
2. Normalize schema: columns -> `model`, `k`, `ndcg`, `map`, `coverage`, `gini`.
3. Plot:
   - Accuracy: NDCG@K, MAP@K (lines per model; shared x-axis).
   - Diversity: Coverage@K, Gini@K.
4. Save plots under `reports/figures/phase4/` as PNG + optionally interactive HTML (Plotly).

### Ablation
5. Filter K=10 rows for Popularity, MF, Hybrid, TF-IDF.
6. Compute relative lifts: `(metric_model - metric_popularity) / metric_popularity * 100`.
7. Emit CSV (`reports/phase4_ablation.csv`) + Markdown table (embedded in evaluation report).

### Hybrid Explanations
8. For a selected user/item seed set (e.g., first 3 users with stable histories):
   - Retrieve hybrid recommendation score components (mf_score, knn_score, pop_score, content_score, weights).
   - Compute normalized contribution percentages.
9. Store examples as JSON snippet or inline Markdown table for report.

### Temporal Split
10. Implement time-based partition logic: earliest X% interactions for training, remaining for validation.
11. Retrain MF + recompute metrics at K (same evaluation pipeline).
12. Compare unified vs temporal metrics; flag drift or leakage suspicion.

### Cold-Start Recap
13. Identify items flagged as new/cold-start (no historical ratings).
14. Evaluate content-only ranking performance (e.g., average NDCG/MAP where possible, or qualitative top genres).
15. Include 2–3 example new items with content feature rationale.

### Infrastructure / Quality
16. Add `.github/workflows/ci.yml` running: setup Python, install deps from requirements.txt, cache pip, run `ruff`, `black --check`, `pytest`.
17. Add `.pre-commit-config.yaml` with hooks: ruff, black, end-of-file-fixer, trailing-whitespace.
18. Document instructions in README.md for enabling pre-commit: `pre-commit install`.

### Reporting
19. Create `reports/phase4_evaluation.md`:
    - Sections: Overview, Metric Curves, Diversity Curves, Ablation, Hybrid Explanations, Temporal Robustness, Cold-Start, Interpretation.
20. Update running_context.md with Phase 4 summary.
21. Link report in main README.md.

### Stretch (Optional)
22. Genre exposure: aggregate recommended items’ genre distribution vs catalog; plot KL-divergence or ratio bars.
23. Novelty/popularity: plot average popularity rank vs model type.

### Final Integration Prep
24. Design JSON payload structure for app usage: curves data, explanation components, ablation metrics.
25. Define functions to load Phase 4 artifacts in Streamlit app (Phase 5 preview).

---

## 2. Code Snippets

### Script: plot_phase4_metrics.py
```python
#!/usr/bin/env python
"""
Phase 4 metric & diversity plotting.

Reads experiment metric artifacts (JSON/CSV) and produces:
- NDCG@K vs K
- MAP@K vs K
- Coverage@K vs K
- Gini@K vs K

Outputs PNG (and optional HTML) to reports/figures/phase4/.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

FIG_DIR = Path("reports/figures/phase4")
FIG_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DISPLAY = {
    "popularity": "Popularity",
    "mf": "Matrix Factorization",
    "hybrid": "Hybrid (Balanced)",
    "content_tfidf": "Content TF-IDF",
}

def load_metrics(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for p in paths:
        if p.suffix == ".json":
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            frames.append(pd.DataFrame(data))
        else:
            frames.append(pd.read_csv(p))
    df = pd.concat(frames, ignore_index=True)
    return df

def standardize(df: pd.DataFrame) -> pd.DataFrame:
    # Expect columns: model, k, ndcg, map, coverage, gini (rename if needed)
    rename_map = {
        "NDCG": "ndcg",
        "MAP": "map",
        "coverage": "coverage",
        "gini": "gini",
        "K": "k",
        "model_name": "model",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
    keep_cols = ["model", "k", "ndcg", "map", "coverage", "gini"]
    return df[keep_cols].dropna()

def plot_line(df: pd.DataFrame, metric: str, ylabel: str, fname: str) -> None:
    plt.figure(figsize=(7, 4.5))
    sns.lineplot(
        data=df,
        x="k",
        y=metric,
        hue="model",
        hue_order=list(MODEL_DISPLAY.keys()),
        palette="tab10"
    )
    plt.ylabel(ylabel)
    plt.xlabel("K")
    plt.title(f"{ylabel} vs K")
    handles, labels = plt.gca().get_legend_handles_labels()
    new_labels = [MODEL_DISPLAY.get(l, l) for l in labels]
    plt.legend(handles, new_labels, title="Model")
    out = FIG_DIR / fname
    plt.tight_layout()
    plt.savefig(out)
    plt.close()

def main(args: argparse.Namespace) -> None:
    metric_paths = [Path(p) for p in args.inputs]
    raw = load_metrics(metric_paths)
    df = standardize(raw)
    # Filter to desired models only
    df = df[df["model"].isin(MODEL_DISPLAY.keys())]

    plot_line(df, "ndcg", "NDCG@K", "ndcg_vs_k.png")
    plot_line(df, "map", "MAP@K", "map_vs_k.png")
    plot_line(df, "coverage", "Coverage@K", "coverage_vs_k.png")
    plot_line(df, "gini", "Gini@K", "gini_vs_k.png")

    print(f"Saved plots to {FIG_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="List of metric artifact JSON/CSV paths."
    )
    main(parser.parse_args())
```

### Script: generate_phase4_ablation.py
```python
#!/usr/bin/env python
"""
Generate Phase 4 ablation (K=10) comparing Popularity, MF, Hybrid, Content TF-IDF.

Outputs:
- reports/phase4_ablation.csv
- Markdown table snippet for embedding
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import pandas as pd

OUT_CSV = Path("reports/phase4_ablation.csv")
MODELS = ["popularity", "mf", "hybrid", "content_tfidf"]

def load(paths: list[str]) -> pd.DataFrame:
    frames = []
    for p in paths:
        path = Path(p)
        if path.suffix == ".json":
            with path.open("r", encoding="utf-8") as f:
                frames.append(pd.DataFrame(json.load(f)))
        else:
            frames.append(pd.read_csv(path))
    df = pd.concat(frames, ignore_index=True)
    return df

def standardize(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {"NDCG": "ndcg", "MAP": "map", "K": "k", "model_name": "model"}
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
    return df

def compute_lifts(sub: pd.DataFrame) -> pd.DataFrame:
    base = sub[sub["model"] == "popularity"].iloc[0]
    for metric in ["ndcg", "map", "coverage"]:
        lift_col = f"{metric}_lift_pct"
        sub[lift_col] = (sub[metric] - base[metric]) / base[metric] * 100
    return sub

def to_markdown(df: pd.DataFrame) -> str:
    cols = [
        "model", "ndcg", "map", "coverage",
        "ndcg_lift_pct", "map_lift_pct", "coverage_lift_pct"
    ]
    md = ["| Model | NDCG@10 | MAP@10 | Coverage@10 | NDCG Lift% | MAP Lift% | Coverage Lift% |",
          "|-------|---------|--------|-------------|------------|-----------|----------------|"]
    for _, r in df[cols].iterrows():
        md.append(
            f"| {r['model']} | {r['ndcg']:.5f} | {r['map']:.5f} | {r['coverage']:.3f} | "
            f"{r['ndcg_lift_pct']:.2f}% | {r['map_lift_pct']:.2f}% | {r['coverage_lift_pct']:.2f}% |"
        )
    return "\n".join(md)

def main(args: argparse.Namespace) -> None:
    df = load(args.inputs)
    df = standardize(df)
    sub = df[(df["k"] == 10) & (df["model"].isin(MODELS))].copy()
    sub = compute_lifts(sub)
    sub.to_csv(OUT_CSV, index=False)
    md = to_markdown(sub)
    print(md)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    main(parser.parse_args())
```

### Hybrid Explanation Extraction: `scripts/extract_hybrid_explanations.py`
```python
#!/usr/bin/env python
"""
Extract top-3 hybrid recommendation score component contributions for selected users.

Expects a unified scorer interface providing:
get_hybrid_components(user_id, top_n) -> list[dict]:
  dict keys: item_id, final_score, mf_score, knn_score, pop_score, content_score, weights
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

# Placeholder imports; adjust to actual project structure
# from src.models.hybrid import HybridRecommender

OUT_PATH = Path("reports/artifacts/hybrid_explanations.json")

def normalize(entry: dict[str, Any]) -> dict[str, Any]:
    total = (
        entry["mf_score"]
        + entry["knn_score"]
        + entry["pop_score"]
        + entry["content_score"]
    )
    if total == 0:
        total = 1e-12
    return {
        "item_id": entry["item_id"],
        "final_score": entry["final_score"],
        "component_breakdown": {
            "mf_pct": entry["mf_score"] / total,
            "knn_pct": entry["knn_score"] / total,
            "pop_pct": entry["pop_score"] / total,
            "content_pct": entry["content_score"] / total,
        },
        "weights": entry.get("weights", {}),
    }

def main(args: argparse.Namespace) -> None:
    # recommender = HybridRecommender.load_from_artifacts()
    results: dict[str, Any] = {}
    for uid in args.user_ids:
        # comps = recommender.get_hybrid_components(uid, top_n=args.top_n)
        comps = []  # Replace with actual call
        processed = [normalize(c) for c in comps][: args.top_n]
        results[str(uid)] = processed

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved explanations to {OUT_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-ids", nargs="+", required=True, help="User IDs for extraction.")
    parser.add_argument("--top-n", type=int, default=3)
    main(parser.parse_args())
```

### Temporal Split Evaluation: `scripts/evaluate_temporal_split.py`
```python
#!/usr/bin/env python
"""
Temporal split sanity check.

Procedure:
1. Load interactions with timestamp.
2. Sort by timestamp; take earliest fraction for train, remainder for validation.
3. Train MF model on train; evaluate metrics on validation.
4. Compare against pre-existing unified slice metrics (provided via input file).
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import pandas as pd
from typing import Dict, Any

# Placeholder for actual MF training/evaluation utilities
# from src.models.mf import train_mf, evaluate_ranking

def temporal_split(df: pd.DataFrame, frac: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_sorted = df.sort_values("timestamp")
    cutoff = int(len(df_sorted) * frac)
    return df_sorted.iloc[:cutoff], df_sorted.iloc[cutoff:]

def main(args: argparse.Namespace) -> None:
    interactions = pd.read_parquet(args.interactions)
    train_df, val_df = temporal_split(interactions, args.train_frac)

    # mf_model = train_mf(train_df)
    # metrics_temporal = evaluate_ranking(mf_model, val_df, k_values=[5,10,20])
    metrics_temporal: Dict[str, Any] = {
        "placeholder": True,
        "ndcg@10": 0.0,
        "map@10": 0.0
    }

    unified = {}
    if args.unified_metrics:
        with Path(args.unified_metrics).open("r", encoding="utf-8") as f:
            unified = json.load(f)

    comparison = {
        "temporal": metrics_temporal,
        "unified": unified,
        "train_frac": args.train_frac,
        "interpretation": "Replace placeholder with actual delta analysis."
    }

    out_path = Path("reports/artifacts/temporal_split_comparison.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
    print(f"Wrote temporal comparison to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactions", required=True, help="Parquet with user-item-timestamp interactions.")
    parser.add_argument("--train-frac", type=float, default=0.7)
    parser.add_argument("--unified-metrics", help="JSON file with unified slice metrics.")
    main(parser.parse_args())
```

### Genre Exposure (Stretch): `scripts/genre_exposure_scan.py`
```python
#!/usr/bin/env python
"""
Compute genre exposure ratios in recommendations vs catalog distribution.
"""
from __future__ import annotations
import argparse
import pandas as pd
from pathlib import Path
import json

OUT = Path("reports/artifacts/genre_exposure.json")

def main(args: argparse.Namespace) -> None:
    recs = pd.read_parquet(args.recommendations)  # columns: user_id, item_id
    items = pd.read_parquet(args.items)           # columns: item_id, genres (list|str)

    # Explode genres
    items["genres"] = items["genres"].apply(lambda g: g if isinstance(g, list) else g.split("|"))
    genres_catalog = items.explode("genres")["genres"].value_counts(normalize=True)

    # Join to recommendations
    merged = recs.merge(items[["item_id", "genres"]], on="item_id", how="left")
    merged = merged.explode("genres")
    genres_recs = merged["genres"].value_counts(normalize=True)

    result = {
        "catalog_distribution": genres_catalog.to_dict(),
        "recommendation_distribution": genres_recs.to_dict()
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Saved genre exposure scan to {OUT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recommendations", required=True)
    parser.add_argument("--items", required=True)
    main(parser.parse_args())
```

### GitHub Actions Workflow: `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

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

### Pre-Commit Config: `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.5
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

### Markdown Table Embedding Example (for `reports/phase4_evaluation.md`)
```markdown
#### Ablation (K=10)

| Model | NDCG@10 | MAP@10 | Coverage@10 | NDCG Lift% | MAP Lift% | Coverage Lift% |
|-------|---------|--------|-------------|------------|-----------|----------------|
| popularity | 0.04120 | 0.02785 | 0.006 | 0.00% | 0.00% | 0.00% |
| mf | 0.05036 | 0.03900 | 0.071 | 22.26% | 40.00% | 1083.33% |
| hybrid | 0.04973 | 0.03844 | 0.066 | 20.66% | 38.00% | 1000.00% |
| content_tfidf | (fill) | (fill) | (fill) | (calc) | (calc) | (calc) |
```

---

## 3. File / Module Layout

```
scripts/
  plot_phase4_metrics.py
  generate_phase4_ablation.py
  extract_hybrid_explanations.py
  evaluate_temporal_split.py
  genre_exposure_scan.py          # (optional)
reports/
  phase4_evaluation.md
  phase4_ablation.csv
  figures/
    phase4/
      ndcg_vs_k.png
      map_vs_k.png
      coverage_vs_k.png
      gini_vs_k.png
  artifacts/
    hybrid_explanations.json
    temporal_split_comparison.json
    genre_exposure.json (optional)
.github/
  workflows/
    ci.yml
.pre-commit-config.yaml
docs/
  running_context.md  (updated Phase 4 section)
```

---

## 4. Milestone Checklist (Definition of Done)

Core:
- [ ] Plots generated and saved (accuracy & diversity).
- [ ] Ablation CSV + Markdown table committed.
- [ ] Hybrid explanation JSON + report section.
- [ ] Temporal split comparison artifact + interpretation.
- [ ] Cold-start examples documented.

Infrastructure:
- [ ] CI workflow passes (pytest + ruff + black).
- [ ] Pre-commit installed and active.
- [ ] `reports/phase4_evaluation.md` finalized and linked in README.md.
- [ ] running_context.md updated with Phase 4 summary.

Stretch (optional):
- [ ] Genre exposure scan plot/data.
- [ ] Novelty/popularity bias plot.

Sign-off:
- [ ] Exit criteria matched (metrics narrative, robustness noted, artifacts organized).

---

## 5. Phase 5 Preview (App Integration)

Data/Artifacts to Surface in Streamlit:
- Curves data: Load `reports/figures/phase4/*.png` (or underlying aggregated DataFrame for interactive plots).
- Ablation summary: Parse `reports/phase4_ablation.csv` → display with styled lift columns.
- Explanations: Serve `hybrid_explanations.json` in a “Why recommended?” modal (component contributions bar chart).
- Temporal robustness: Small info panel summarizing stability vs unified evaluation.
- Cold-start handling: Badge logic referencing content-only rationale (e.g., top genres / embedding similarity sources).
- Genre exposure (if implemented): Diversity insights panel for advanced users.

Proposed App Utility Module (`src/app/artifacts_loader.py`):
- `load_metric_curves() -> pd.DataFrame`
- `load_ablation() -> pd.DataFrame`
- `load_hybrid_explanations(user_id: str) -> list[dict]`
- `load_temporal_summary() -> dict`
- `load_genre_exposure() -> dict | None`

These functions enable rapid Phase 5 UI development without recomputation.

---

## Recommended Run Commands

```powershell
# Generate plots
python scripts/plot_phase4_metrics.py --inputs experiments/metrics/content_tfidf.json experiments/metrics/mf.json experiments/metrics/hybrid.json experiments/metrics/popularity.json

# Generate ablation
python scripts/generate_phase4_ablation.py --inputs experiments/metrics/*.json > reports/phase4_ablation_table.md

# Temporal split
python scripts/evaluate_temporal_split.py --interactions data/processed/interactions.parquet --unified-metrics experiments/metrics/unified_mf.json

# Hybrid explanations (replace user IDs)
python scripts/extract_hybrid_explanations.py --user-ids 1001 1002 1003 --top-n 3
```

---

