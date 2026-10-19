# MARS Documentation

Start with the [README](../README.md) for the pitch and quick start, then the
[model card](MODEL_CARD.md) for what the recommender does and how well.

## Results

| Page | What it covers |
|------|----------------|
| [Phase 4 ablation](../reports/phase4_ablation.md) ([CSV](../reports/phase4_ablation.csv), [by K](../reports/phase4_ablation_by_k.csv)) | The evaluation table: every variant on one cohort, K=10, plus K=5 and 20; [trade-off chart](../reports/figures/ablation_accuracy_vs_coverage.png) |
| [Phase 4 evaluation](../reports/phase4_evaluation.md) | Protocol, metrics by K, coverage and novelty, open items |
| [Phase 3 summary](../reports/phase3_summary.md) | Earlier modeling phase, closed 2025-11-21 |
| [Model card](MODEL_CARD.md) | Intended use, data, metrics, limitations |

## How it works

| Page | What it covers |
|------|----------------|
| [Scoring pipeline](scoring_pipeline_integration_guide.md) | Candidate generation → shortlist → hybrid reranking → post-processing |
| [Project structure](project_structure.md) | Directory layout and tech stack |
| [Features](features.md) | Content, metadata, and CF features |
| [Decision log](decisions.md) | Why things are the way they are |
| [UI design](ui_design.md) | Layout, design tokens, imagery, UX backlog |
| [Project proposal](PROJECT_PROPOSAL.md) | Original scope and goals |

## Data

| Page | What it covers |
|------|----------------|
| [Data sources](DATA_SOURCES.md) | Kaggle and Jikan sources, attribution, licensing |
| [Data catalog](data_catalog.md) | Every dataset, its lineage, and [updating the catalog](data_catalog.md#updating-the-catalog) |

## Using and running it

| Page | What it covers |
|------|----------------|
| [Personalization guide](user_guide_personalization.md) | Recommendations from your own ratings |
| [Watchlist import](user_guide_watchlist.md) | Importing a MyAnimeList export |
| [Deployment](DEPLOYMENT.md) | Streamlit Community Cloud setup and limits |
| [Running plan tasks](HOW_TO_RUN_TASKS.md) | How plan tasks are executed and validated |
| [Portfolio product plan](plans/MARS_PORTFOLIO_PRODUCT_PLAN.md) | Current roadmap |

## Notebooks

- [01 — EDA and data quality](../notebooks/01_eda_data_quality.ipynb)
- [02 — Pipeline walkthrough](../notebooks/02_pipeline_walkthrough.ipynb)
- [03 — Segment and error analysis](../notebooks/03_segment_and_error_analysis.ipynb): who the
  recommender works for, where its hits come from, cold-start users, and sampled misses
