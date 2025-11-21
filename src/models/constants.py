from pathlib import Path

RANDOM_SEED: int = 42
TOP_K_DEFAULT: int = 10
DEFAULT_SAMPLE_USERS: int = 300

# Default weighted hybrid blend (balanced: accuracy + coverage; normalized Optuna diversity-aware weights)
DEFAULT_HYBRID_WEIGHTS = {
    "mf": 0.9307796791956574,
    "knn": 0.06624663364738044,
    "pop": 0.0029736871569621902,
}

DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
EXPERIMENTS_DIR = Path("experiments")
METRICS_DIR = EXPERIMENTS_DIR / "metrics"
OPTUNA_DIR = EXPERIMENTS_DIR / "optuna_studies"

# Ensure directories exist when imported in scripts
for p in (MODELS_DIR, METRICS_DIR, OPTUNA_DIR):
    p.mkdir(parents=True, exist_ok=True)
