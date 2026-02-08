# Simple task runner (works in Git Bash; on Windows PowerShell, prefer the explicit commands shown in README)

.PHONY: setup test app fetch-jikan features discover-new lint fmt venv-minimal venv-kernel venv-all phase4-artifacts

# Create .venv and install full project requirements
setup:
	python -m venv .venv
	. .venv/Scripts/activate && python -m pip install --upgrade pip wheel && pip install -r requirements.txt

# Minimal deps for notebooks/EDA only (fast): numpy/pandas/pyarrow/matplotlib/seaborn/ipykernel
venv-minimal:
	python -m venv .venv
	. .venv/Scripts/activate && python -m pip install --upgrade pip wheel && \
		pip install numpy pandas pyarrow matplotlib seaborn ipykernel

# Register Jupyter kernel for this venv
venv-kernel:
	. .venv/Scripts/activate && python -m ipykernel install --user --name mars-venv --display-name "Python 3 (.venv MARS)"

# Convenience: minimal deps + kernel
venv-all: venv-minimal venv-kernel

test:
	. .venv/Scripts/activate && pytest -q

# Run tests with CI configuration (mirrors GitHub Actions)
ci:
	. .venv/Scripts/activate && APP_IMPORT_LIGHT=1 pytest -x -q --tb=short

app:
	. .venv/Scripts/activate && streamlit run app/app.py

fetch-jikan:
	. .venv/Scripts/activate && python scripts/fetch_jikan.py --ids 1 20 1735 --snapshot-suffix $$(date +%Y%m)

features:
	. .venv/Scripts/activate && python scripts/build_features.py

discover-new:
	. .venv/Scripts/activate && python scripts/discover_new_ids.py --baseline data/raw/anime.csv --out data/raw/new_anime_ids_$$(date +%Y%m%d).txt --sources seasons_now seasons_upcoming top --top-pages 5

lint:
	ruff check src/ tests/

fmt:
	ruff format src/ tests/

fmt-check:
	ruff format --check src/ tests/

# Regenerate Phase 4 evaluation artifacts (metrics curves, ablation, explanations, diversity/novelty)
phase4-artifacts:
	. .venv/Scripts/activate && python scripts/plot_phase4_metrics.py --metrics-path data/processed/phase4/metrics_by_k.parquet || echo "(Skip if metrics_by_k not yet built)"
	. .venv/Scripts/activate && python scripts/generate_phase4_ablation.py
	. .venv/Scripts/activate && python scripts/explain_hybrid_examples.py --k 10 --sample-users 500 --max-users 3
	. .venv/Scripts/activate && python scripts/generate_recommendations_sample.py --k 10 --sample-users 500
	. .venv/Scripts/activate && python scripts/genre_exposure_scan.py --recommendations data/processed/recommendations_sample.parquet --items data/processed/anime_metadata_normalized.parquet --model hybrid
	. .venv/Scripts/activate && python scripts/novelty_bias_plot.py --recommendations data/processed/recommendations_sample.parquet --popularity data/processed/popularity.parquet
	. .venv/Scripts/activate && python scripts/explain_hybrid_examples.py --k 10 --sample-users 500 --max-users 3 --w-mf 0.7 --w-knn 0.2 --w-pop 0.1 --out-suffix alt
	@echo "Phase 4 artifacts regenerated. See reports/ and experiments/metrics."