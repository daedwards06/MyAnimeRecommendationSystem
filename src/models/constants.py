from pathlib import Path

RANDOM_SEED: int = 42
TOP_K_DEFAULT: int = 10
DEFAULT_SAMPLE_USERS: int = 300
# The cohort the ablation and README report on; blend tuning draws its users from outside it.
REPORTING_COHORT_USERS: int = 1000

# Served weighted hybrid blend: the Task 0.6 Optuna re-tune on users disjoint from the
# reporting cohort (experiments/optuna_studies/hybrid_weights_best.json, weights_normalized).
DEFAULT_HYBRID_WEIGHTS = {
    "mf": 0.047506697349330884,
    "knn": 0.9521858800432561,
    "pop": 0.0003074226074129113,
}

# Single surviving artifact stem per model family (Task 0.3). Scripts and the app must
# reference these instead of literals so offline evaluation scores the model the app serves.
MF_MODEL_STEM = "mf_sgd_v2025.11.21_202756"
KNN_MODEL_STEM = "item_knn_sklearn_v2025.11.21_202756"

DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
EXPERIMENTS_DIR = Path("experiments")
METRICS_DIR = EXPERIMENTS_DIR / "metrics"
OPTUNA_DIR = EXPERIMENTS_DIR / "optuna_studies"

# Offline evaluation fits its own CF artifacts on the train split only; the artifacts in
# MODELS_DIR are fit on all interactions and would be scored against rows they trained on.
# Created on demand, git-ignored, and never loaded by the app.
EVAL_ARTIFACTS_DIR = EXPERIMENTS_DIR / "artifacts"
MF_EVAL_ARTIFACT = "mf_sgd_trainsplit"
KNN_EVAL_ARTIFACT = "item_knn_sklearn_trainsplit"
ALS_EVAL_ARTIFACT = "implicit_als_trainsplit"

# Ensure directories exist when imported in scripts
for p in (MODELS_DIR, METRICS_DIR, OPTUNA_DIR):
    p.mkdir(parents=True, exist_ok=True)
