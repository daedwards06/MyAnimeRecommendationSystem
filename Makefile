# Simple task runner (works in Git Bash; on Windows PowerShell, prefer the explicit commands shown in README)

.PHONY: setup test app fetch-jikan features discover-new lint fmt venv-minimal venv-kernel venv-all

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

app:
	. .venv/Scripts/activate && streamlit run app/app.py

fetch-jikan:
	. .venv/Scripts/activate && python scripts/fetch_jikan.py --ids 1 20 1735 --snapshot-suffix $$(date +%Y%m)

features:
	. .venv/Scripts/activate && python scripts/build_features.py

discover-new:
	. .venv/Scripts/activate && python scripts/discover_new_ids.py --baseline data/raw/anime.csv --out data/raw/new_anime_ids_$$(date +%Y%m%d).txt --sources seasons_now seasons_upcoming top --top-pages 5

lint:
	@echo "Add ruff/black later"

fmt:
	@echo "Add ruff/black later"