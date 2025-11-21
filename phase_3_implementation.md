

## Phase 3 Implementation Plan (Structured)

### 1. Step‑by‑Step Actions (High-Level Rationale)
1. Metrics utilities: implement NDCG@K, MAP@K, Precision/Recall/F1@K for consistent evaluation.
2. Baselines first (popularity, genre similarity) to anchor performance.
3. Content similarity (TF‑IDF + embeddings) for cold‑start coverage.
4. Collaborative filtering suite: KNNBasic → SVD → LightFM WARP → implicit ALS (increasing sophistication).
5. Unified data loader to read Phase 2 artifacts (parquet + feature matrices).
6. Standard evaluation harness producing metric JSON/CSV per run.
7. Model serialization utilities (versioned naming + manifest update).
8. Hybrid layer (weighted score blending + rank fusion) leveraging previously serialized component scores.
9. Optuna studies: define objective (NDCG@K primary, MAP@K tie-break) and run reproducible sweeps; store study artifacts.
10. Final orchestration scripts and README snippet for model registry usage.

Global constants: RANDOM_SEED, DEFAULT_TOP_K, ARTIFACT_DIR paths.

---

### 2. Code Snippets (Production-Ready Examples)

#### 2.1 Constants and Paths (`src/models/constants.py`)
```python
from pathlib import Path

RANDOM_SEED: int = 42
TOP_K_DEFAULT: int = 10

DATA_PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
EXPERIMENTS_DIR = Path("experiments")
METRICS_DIR = EXPERIMENTS_DIR / "metrics"
OPTUNA_DIR = EXPERIMENTS_DIR / "optuna_studies"

for p in (MODELS_DIR, METRICS_DIR, OPTUNA_DIR):
    p.mkdir(parents=True, exist_ok=True)
```

#### 2.2 Metrics (`src/eval/metrics.py`)
```python
from __future__ import annotations
import numpy as np
from typing import Sequence, Iterable, Dict, List

def precision_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    top = recommended[:k]
    hit_count = sum(1 for i in top if i in relevant)
    return hit_count / max(k, 1)

def recall_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    if not relevant:
        return 0.0
    top = recommended[:k]
    hit_count = sum(1 for i in top if i in relevant)
    return hit_count / len(relevant)

def f1_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    p = precision_at_k(recommended, relevant, k)
    r = recall_at_k(recommended, relevant, k)
    return 0.0 if (p + r) == 0 else 2 * p * r / (p + r)

def dcg(scores: Sequence[float]) -> float:
    return sum(score / np.log2(idx + 2) for idx, score in enumerate(scores))

def ndcg_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    top = recommended[:k]
    gains = [1.0 if i in relevant else 0.0 for i in top]
    ideal = sorted(gains, reverse=True)
    denom = dcg(ideal)
    return 0.0 if denom == 0 else dcg(gains) / denom

def average_precision_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    ap = 0.0
    hit = 0
    for idx, item in enumerate(recommended[:k], start=1):
        if item in relevant:
            hit += 1
            ap += hit / idx
    return 0.0 if not relevant else ap / min(len(relevant), k)

def evaluate_ranking(
    recommended: Sequence[int],
    relevant: set[int],
    k_values: Iterable[int]
) -> Dict[str, Dict[int, float]]:
    out: Dict[str, Dict[int, float]] = {"precision": {}, "recall": {}, "f1": {}, "ndcg": {}, "map": {}}
    for k in k_values:
        out["precision"][k] = precision_at_k(recommended, relevant, k)
        out["recall"][k] = recall_at_k(recommended, relevant, k)
        out["f1"][k] = f1_at_k(recommended, relevant, k)
        out["ndcg"][k] = ndcg_at_k(recommended, relevant, k)
        out["map"][k] = average_precision_at_k(recommended, relevant, k)
    return out
```

#### 2.3 Data Loader (`src/models/data_loader.py`)
```python
from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict

def load_interactions(base_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(base_dir / "interactions.parquet")

def load_items(base_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(base_dir / "items.parquet")

def load_users(base_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(base_dir / "users.parquet")

def load_feature_matrix(path: Path) -> pd.DataFrame | pd.Series:
    # Accepts parquet or numpy .npy persisted matrix; adapt as needed
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported feature artifact: {path}")

def build_id_maps(interactions: pd.DataFrame) -> Tuple[Dict[int, int], Dict[int, int]]:
    user_ids = interactions["user_id"].unique()
    item_ids = interactions["anime_id"].unique()
    user_map = {uid: idx for idx, uid in enumerate(user_ids)}
    item_map = {iid: idx for idx, iid in enumerate(item_ids)}
    return user_map, item_map
```

#### 2.4 Popularity Baseline (`src/models/baselines.py`)
```python
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List

def popularity_scores(interactions: pd.DataFrame) -> pd.Series:
    grouped = interactions.groupby("anime_id").agg(
        num_ratings=("rating", "count"),
        mean_rating=("rating", "mean")
    )
    grouped["pop_score"] = np.log1p(grouped["num_ratings"]) * grouped["mean_rating"]
    return grouped["pop_score"].sort_values(ascending=False)

def recommend_popularity(
    interactions: pd.DataFrame,
    top_k: int = 10,
    exclude_watched: set[int] | None = None
) -> List[int]:
    scores = popularity_scores(interactions)
    ranked = scores.index.tolist()
    if exclude_watched:
        ranked = [i for i in ranked if i not in exclude_watched]
    return ranked[:top_k]
```

#### 2.5 Genre / TF-IDF Similarity Baseline (`src/models/content_similarity.py`)
```python
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List
from sklearn.metrics.pairwise import cosine_similarity

def recommend_by_tfidf(
    item_features: pd.DataFrame,
    seed_item_id: int,
    top_k: int = 10,
    exclude_seed: bool = True
) -> List[int]:
    if seed_item_id not in item_features.index:
        raise ValueError("Seed item missing from feature index.")
    seed_vec = item_features.loc[[seed_item_id]].values
    sims = cosine_similarity(seed_vec, item_features.values)[0]
    order = np.argsort(-sims)
    candidate_ids = item_features.index[order].tolist()
    if exclude_seed:
        candidate_ids = [cid for cid in candidate_ids if cid != seed_item_id]
    return candidate_ids[:top_k]
```

#### 2.6 Embedding Similarity (`src/models/embeddings_similarity.py`)
```python
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List
from sklearn.metrics.pairwise import cosine_similarity

def recommend_by_embedding(
    embeddings: pd.DataFrame,
    seed_item_id: int,
    top_k: int = 10
) -> List[int]:
    if seed_item_id not in embeddings.index:
        raise ValueError("Seed item missing from embeddings.")
    seed = embeddings.loc[[seed_item_id]].values
    sims = cosine_similarity(seed, embeddings.values)[0]
    order = np.argsort(-sims)
    ranked = embeddings.index[order].tolist()
    ranked = [rid for rid in ranked if rid != seed_item_id]
    return ranked[:top_k]
```

#### 2.7 Surprise KNNBasic & SVD (`scripts/train_knn.py`, `scripts/train_svd.py`)
```python
# scripts/train_knn.py
import pandas as pd
from surprise import Dataset, Reader, KNNBasic
from joblib import dump
from pathlib import Path
from src.eval.metrics import evaluate_ranking
from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED

def load_surprise(interactions: pd.DataFrame):
    reader = Reader(rating_scale=(interactions["rating"].min(), interactions["rating"].max()))
    return Dataset.load_from_df(interactions[["user_id", "anime_id", "rating"]], reader)

def train_knn(k: int = 40, sim: str = "cosine"):
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    data = load_surprise(interactions)
    trainset = data.build_full_trainset()
    algo = KNNBasic(k=k, sim_options={"name": sim, "user_based": True})
    algo.fit(trainset)
    dump(algo, MODELS_DIR / f"knn_user_v1.0.joblib")

if __name__ == "__main__":
    train_knn()
```

```python
# scripts/train_svd.py
import pandas as pd
from surprise import Dataset, Reader, SVD
from joblib import dump
from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED

def train_svd(n_factors: int = 100, reg_all: float = 0.02, lr_all: float = 0.005):
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    reader = Reader(rating_scale=(inter["rating"].min(), inter["rating"].max()))
    data = Dataset.load_from_df(inter[["user_id", "anime_id", "rating"]], reader)
    trainset = data.build_full_trainset()
    algo = SVD(n_factors=n_factors, reg_all=reg_all, lr_all=lr_all, random_state=RANDOM_SEED)
    algo.fit(trainset)
    dump(algo, MODELS_DIR / f"svd_v1.0.joblib")

if __name__ == "__main__":
    train_svd()
```

#### 2.8 Implicit ALS (`scripts/train_als_implicit.py`)
```python
import pandas as pd
import numpy as np
from implicit.als import AlternatingLeastSquares
from scipy.sparse import coo_matrix
from joblib import dump
from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED

def build_sparse(interactions: pd.DataFrame):
    user_ids = interactions["user_id"].astype("category")
    item_ids = interactions["anime_id"].astype("category")
    rows = user_ids.cat.codes.values
    cols = item_ids.cat.codes.values
    data = interactions["rating"].values
    mat = coo_matrix((data, (rows, cols)))
    return mat, user_ids, item_ids

def train_als(factors: int = 64, regularization: float = 0.01, iterations: int = 15):
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    mat, user_codes, item_codes = build_sparse(inter)
    model = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=iterations,
        random_state=RANDOM_SEED
    )
    model.fit(mat)
    artifact = {
        "model": model,
        "user_index": dict(zip(user_codes.cat.codes, user_codes.cat.categories)),
        "item_index": dict(zip(item_codes.cat.codes, item_codes.cat.categories))
    }
    dump(artifact, MODELS_DIR / "als_implicit_v1.0.joblib")

if __name__ == "__main__":
    train_als()
```

#### 2.9 LightFM WARP (train_lightfm_baseline.py)
```python
import pandas as pd
import numpy as np
from scipy.sparse import coo_matrix
from lightfm import LightFM
from joblib import dump
from src.models.constants import DATA_PROCESSED_DIR, MODELS_DIR, RANDOM_SEED

def build_interaction_matrix(df: pd.DataFrame):
    users = df["user_id"].astype("category")
    items = df["anime_id"].astype("category")
    row = users.cat.codes.values
    col = items.cat.codes.values
    data = np.ones(len(df), dtype=np.float32)  # implicit presence
    mat = coo_matrix((data, (row, col)))
    return mat.tocsr(), users, items

def train_lightfm(no_components: int = 64, epochs: int = 30, num_threads: int = 4):
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    mat, users, items = build_interaction_matrix(inter)
    model = LightFM(loss="warp", no_components=no_components, random_state=RANDOM_SEED)
    model.fit(mat, epochs=epochs, num_threads=num_threads)
    dump({
        "model": model,
        "user_index": dict(enumerate(users.cat.categories)),
        "item_index": dict(enumerate(items.cat.categories))
    }, MODELS_DIR / "lightfm_warp_v1.0.joblib")

if __name__ == "__main__":
    train_lightfm()
```

#### 2.10 Hybrid Strategies (`src/models/hybrid.py`)
```python
from __future__ import annotations
import numpy as np
from typing import List, Dict, Sequence

def weighted_blend(
    score_dicts: Dict[str, Dict[int, float]],
    weights: Dict[str, float],
    top_k: int
) -> List[int]:
    agg: Dict[int, float] = {}
    for source, scores in score_dicts.items():
        w = weights.get(source, 0.0)
        for item, sc in scores.items():
            agg[item] = agg.get(item, 0.0) + w * sc
    ranked = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]

def reciprocal_rank_fusion(rankings: Dict[str, Sequence[int]], top_k: int, k: int = 60) -> List[int]:
    # RRF score: sum 1 / (k + rank)
    scores: Dict[int, float] = {}
    for _, ranking in rankings.items():
        for r, item in enumerate(ranking):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + r + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]

def borda_count(rankings: Dict[str, Sequence[int]], top_k: int) -> List[int]:
    scores: Dict[int, int] = {}
    for _, ranking in rankings.items():
        n = len(ranking)
        for r, item in enumerate(ranking):
            scores[item] = scores.get(item, 0) + (n - r)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [i for i, _ in ranked[:top_k]]
```

#### 2.11 Optuna Study (`scripts/tune_svd_optuna.py`)
```python
import optuna
import pandas as pd
from surprise import SVD, Dataset, Reader
from src.models.constants import DATA_PROCESSED_DIR, OPTUNA_DIR, RANDOM_SEED
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from pathlib import Path

def load_data():
    inter = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    reader = Reader(rating_scale=(inter["rating"].min(), inter["rating"].max()))
    return Dataset.load_from_df(inter[["user_id", "anime_id", "rating"]], reader)

def objective(trial: optuna.Trial) -> float:
    data = load_data()
    trainset = data.build_full_trainset()
    algo = SVD(
        n_factors=trial.suggest_int("n_factors", 50, 200),
        reg_all=trial.suggest_float("reg_all", 0.002, 0.08, log=True),
        lr_all=trial.suggest_float("lr_all", 0.001, 0.02, log=True),
        random_state=RANDOM_SEED
    )
    algo.fit(trainset)

    # Simple validation using subset of users (sample) for ranking on top items
    item_ids = list(trainset.all_items())
    item_raw_ids = [trainset.to_raw_iid(i) for i in item_ids]

    ndcg_scores = []
    map_scores = []
    sampled_users = list(trainset.all_users())[:200]
    for u in sampled_users:
        u_raw = trainset.to_raw_uid(u)
        # Skip users without known ratings
        relevant = {trainset.to_raw_iid(i) for (i, _) in trainset.ur[u]}
        preds = [(iid, algo.predict(u_raw, iid).est) for iid in item_raw_ids]
        ranked = [iid for iid, est in sorted(preds, key=lambda x: x[1], reverse=True)]
        ndcg_scores.append(ndcg_at_k(ranked, relevant, 10))
        map_scores.append(average_precision_at_k(ranked, relevant, 10))
    return float(sum(ndcg_scores) / len(ndcg_scores))

if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)
    out = OPTUNA_DIR / "svd_ndcg_study_v1.0.pkl"
    study.trials_dataframe().to_csv(OPTUNA_DIR / "svd_trials_v1.0.csv", index=False)
    print("Best params:", study.best_params, "Best value:", study.best_value)
```

#### 2.12 Serialization Utilities (`src/models/serialization.py`)
```python
from __future__ import annotations
from joblib import dump, load
from pathlib import Path
from typing import Any

def save_model(model: Any, name: str, version: str = "1.0", models_dir: Path = Path("models")) -> Path:
    filename = f"{name}_v{version}.joblib"
    path = models_dir / filename
    models_dir.mkdir(parents=True, exist_ok=True)
    dump(model, path)
    return path

def load_model(name: str, version: str = "1.0", models_dir: Path = Path("models")) -> Any:
    path = models_dir / f"{name}_v{version}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")
    return load(path)
```

#### 2.13 Metrics Logging (`src/eval/logging.py`)
```python
from __future__ import annotations
import json
import csv
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

def write_json_metrics(metrics: Dict[str, Any], out_dir: Path, tag: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{tag}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    with path.open("w") as f:
        json.dump(metrics, f, indent=2)
    return path

def append_csv_row(row: Dict[str, Any], out_file: Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    write_header = not out_file.exists()
    with out_file.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)
```

---

### 3. Proposed File / Module Layout

`src/models/`
- `__init__.py`
- `constants.py` — paths, seeds
- `data_loader.py` — parquet + ID maps
- `baselines.py` — popularity
- `content_similarity.py` — TF‑IDF / genre similarity
- `embeddings_similarity.py` — synopsis embedding similarity
- `hybrid.py` — weighted blend, RRF, Borda
- `serialization.py` — save/load helpers
- `utils.py` — small helpers (optional)

`src/eval/`
- `metrics.py` — ranking metrics
- `logging.py` — JSON/CSV metrics logging

`scripts/`
- `train_knn.py` — Surprise KNNBasic (user/item)
- `train_svd.py` — Surprise SVD
- `train_als_implicit.py` — implicit ALS
- `train_lightfm_baseline.py` — LightFM WARP
- `tune_svd_optuna.py` — Optuna for SVD (extend to ALS/LightFM)
- `evaluate_model.py` — load model, score users, compute metrics, log
- `generate_hybrid.py` — blend/fuse rankings and evaluate

`experiments/`
- `metrics/` — CSV/JSON run outputs
- `optuna_studies/` — study CSVs/pickles

`models/`
- Versioned artifacts: `model_name_v{major}.{minor}.joblib`

---

### 4. Milestone Checklist (Phase 3 Completion Criteria)
- [ ] All baseline (popularity, genre similarity) functions implemented + evaluated
- [ ] CF models (KNNBasic, SVD, LightFM, ALS) trained with versioned artifacts in models
- [ ] Content-based similarity (TF-IDF & embeddings) operational for cold-start
- [ ] Ranking metrics module validated (unit tests added for edge cases)
- [ ] Optuna study completed for at least one CF model (SVD) — best params logged
- [ ] Hybrid recommender (weighted + rank fusion) producing improved validation NDCG@10 vs strongest single model
- [ ] Metrics and runs logged (JSON + consolidated CSV)
- [ ] Serialization utilities integrated into scripts (consistent version naming)
- [ ] README or docs update listing available models and usage
- [ ] Test coverage includes metrics, popularity baseline, one CF model, and hybrid logic

---

### 5. Phase 4 Preview (Integration into Streamlit App)
- Preload artifacts on app startup: popularity ranking, item feature matrices, embeddings, CF model factors.
- User flow:
  1. Select seed anime or enter user ID
  2. Generate candidate lists from multiple models (CF top-N, content similarity, popularity)
  3. Hybrid blending (weighted/RRF) to produce final recommendation set
  4. Explanations panel: show contributing sources (e.g., weights, top similar items, genres matched)
- Caching: use `st.cache_data` for feature matrices and similarity indices; `st.cache_resource` for large models (ALS, LightFM).
- Cold-start path: if user lacks history → omit CF scores, emphasize content + popularity + embeddings.
- Future Phase 4 additions: latency profiling, optional ANN index for embedding search (FAISS/Annoy), quality visualization panels.

---

### 6. Next Immediate Actions (Execution Order)
1. Add modules (`constants.py`, `metrics.py`, `serialization.py`).
2. Implement baselines and content similarity.
3. Add CF training scripts; run quick smoke training to produce artifacts.
4. Implement evaluation script logging metrics.
5. Run Optuna on SVD; store study outputs.
6. Implement hybrid strategies and validate uplift.
7. Update documentation + tests.

