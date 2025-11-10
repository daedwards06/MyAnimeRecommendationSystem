# Simple task runner (optional on Windows)

.PHONY: setup test app fetch-jikan lint fmt

setup:
	python -m venv .venv
	. .venv/Scripts/activate && pip install --upgrade pip && pip install -r requirements.txt

test:
	. .venv/Scripts/activate && pytest -q

app:
	. .venv/Scripts/activate && streamlit run app/app.py

fetch-jikan:
	. .venv/Scripts/activate && python scripts/fetch_jikan.py --ids 1 20 1735 --snapshot-suffix $$(date +%Y%m)

lint:
	@echo "Add ruff/black later"

fmt:
	@echo "Add ruff/black later"