
# Phase 5 Implementation Plan

## 1. Strategy & Sequencing
1. Loader & Core Utilities (artifacts_loader, search, recommender, badges, explanations).
2. Persona & Sample Data (personas.json).
3. Hybrid + Similarity Paths (MF/kNN/pop blend, TF‑IDF embedding fallback).
4. UI Scaffold (sidebar controls + main recommendation panel + diversity summary + help).
5. Performance & Profiling (latency hooks, caching, pruning).
6. Tests & CI (unit helpers, smoke import, workflow).
7. Deployment (requirements pruning, config, deploy, README updates).
8. Post‑Deployment polish (screenshots, latency validation, optional blog/video scaffolding).

## 2. UI Wireframe (Conceptual)
Sidebar:
- Persona selector (select box)
- Search bar (fuzzy title → seed selection)
- Hybrid weight preset toggle (radio: Balanced | Diversity+)
- Method selector (Similarity: Embeddings | TF-IDF fallback)
- N (slider for top-N)
Main:
- Recommendations tab:
  - Loading skeleton → list of cards (Title | Genres | Badges | Explanation dropdown)
- Diversity Summary tab:
  - Coverage %, Genre exposure ratio, Popularity distribution bands
  - Mini bar charts (accessible palette)
- Help / FAQ tab:
  - Accordion: Metrics, Hybrid logic, Cold-start explanation
Footer:
- Latency display (last inference ms), memory usage (approx), version/manifest hash

## 3. Rationale Highlights
- Deterministic randomness ensures reproducible persona sample & tie-breaking.
- Pruned metadata keeps memory low (<512MB target).
- Caching isolates model/artifact initialization cost—interactive updates remain sub‑500ms.
- Hybrid toggle encourages user understanding of diversity/accuracy trade‑offs.
- Explanation shares (mf/knn/pop %) bridge algorithm internals to UX clarity.

---

# Code Snippets

## constants.py
```python
# src/app/constants.py
RANDOM_SEED: int = 42
DEFAULT_TOP_N: int = 10

# Weights (normalized)
BALANCED_WEIGHTS = {"mf": 0.93078, "knn": 0.06625, "pop": 0.00297}
DIVERSITY_EMPHASIZED_WEIGHTS = {"mf": 0.80, "knn": 0.18, "pop": 0.02}  # illustrative

EMBEDDING_TTL_SECONDS: int = 24 * 3600
MAX_INFERENCE_LATENCY_MS: int = 250
```

## artifacts_loader.py
```python
# src/app/artifacts_loader.py
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import joblib
import random
import numpy as np

from .constants import RANDOM_SEED

class ArtifactBundle(Dict[str, Any]):
    """Container mapping artifact names to loaded objects."""

def set_determinism(seed: int = RANDOM_SEED) -> None:
    """Configure deterministic state for Python, NumPy, and random."""
    random.seed(seed)
    np.random.seed(seed)

def prune_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Keep minimal columns required for UI."""
    keep = ["anime_id", "title_display", "genres", "synopsis_snippet"]
    return df.loc[:, [c for c in keep if c in df.columns]]

def safe_read_parquet(path: str | Path) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Missing parquet: {path}")
    return pd.read_parquet(path)

def load_models(models_dir: str | Path) -> Dict[str, Any]:
    """Load serialized model artifacts (joblib)."""
    models = {}
    for fname in Path(models_dir).glob("*.joblib"):
        key = fname.stem
        models[key] = joblib.load(fname)
    if not models:
        raise RuntimeError(f"No models found in {models_dir}")
    return models

def load_explanations(reports_dir: str | Path) -> Dict[str, Any]:
    """Load explanation artifacts if present."""
    payload = {}
    for fname in Path(reports_dir).glob("**/*explanations*.json"):
        with open(fname, "r", encoding="utf-8") as f:
            payload[fname.stem] = json.load(f)
    return payload

def load_diversity_metrics(reports_dir: str | Path) -> Dict[str, Any]:
    """Load diversity/novelty metrics (flexible naming)."""
    metrics = {}
    for fname in Path(reports_dir).glob("**/*diversity*.json"):
        with open(fname, "r", encoding="utf-8") as f:
            metrics[fname.stem] = json.load(f)
    return metrics

def build_artifacts(
    data_dir: str | Path = "data/processed",
    models_dir: str | Path = "models",
    reports_dir: str | Path = "reports",
) -> ArtifactBundle:
    """Assemble artifacts needed for app inference."""
    set_determinism()
    bundle: ArtifactBundle = ArtifactBundle()

    metadata_path = Path(data_dir) / "anime_metadata.parquet"
    metadata_df = prune_metadata(safe_read_parquet(metadata_path))
    bundle["metadata"] = metadata_df

    bundle["models"] = load_models(models_dir)
    bundle["explanations"] = load_explanations(reports_dir)
    bundle["diversity"] = load_diversity_metrics(reports_dir)

    return bundle
```

## search.py
```python
# src/app/search.py
from __future__ import annotations
from typing import List, Tuple
from rapidfuzz import process, fuzz

def normalize_query(q: str) -> str:
    return q.strip().lower()

def fuzzy_search(
    query: str,
    choices: List[Tuple[str, int]],
    limit: int = 10,
    min_score: int = 60
) -> List[Tuple[int, float, str]]:
    """
    Fuzzy match titles.
    choices: list of (title_string, anime_id)
    Returns: list of (anime_id, score, matched_title)
    """
    q = normalize_query(query)
    results = process.extract(
        q,
        [c[0] for c in choices],
        scorer=fuzz.WRatio,
        limit=limit
    )
    output = []
    for title, score, idx in results:
        if score >= min_score:
            anime_id = choices[idx][1]
            output.append((anime_id, score, title))
    # Fallback substring if empty
    if not output:
        for title, aid in choices:
            if q in title.lower():
                output.append((aid, 100.0, title))
    return output[:limit]
```

## recommender.py
```python
# src/app/recommender.py
from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from functools import lru_cache
import time

from .constants import BALANCED_WEIGHTS, DIVERSITY_EMPHASIZED_WEIGHTS

class HybridRecommender:
    """Hybrid blending of MF, kNN, popularity scores with explanation output."""

    def __init__(
        self,
        mf_scores: np.ndarray,
        knn_scores: np.ndarray,
        pop_scores: np.ndarray,
        item_ids: np.ndarray,
    ) -> None:
        """
        All arrays shape: (num_users, num_items) except pop_scores (num_items,).
        item_ids: mapping indices -> anime_id.
        """
        self.mf = mf_scores
        self.knn = knn_scores
        self.pop = pop_scores
        self.item_ids = item_ids

    def _blend(self, user_index: int, weights: Dict[str, float]) -> np.ndarray:
        return (
            weights["mf"] * self.mf[user_index] +
            weights["knn"] * self.knn[user_index] +
            weights["pop"] * self.pop
        )

    def explain_item(self, user_index: int, item_index: int, weights: Dict[str, float]) -> Dict[str, float]:
        """Return per-source contributions (raw) and normalized shares."""
        mf_val = weights["mf"] * self.mf[user_index, item_index]
        knn_val = weights["knn"] * self.knn[user_index, item_index]
        pop_val = weights["pop"] * self.pop[item_index]
        total = mf_val + knn_val + pop_val
        if total <= 0:
            return {"mf": 0.0, "knn": 0.0, "pop": 0.0}
        return {
            "mf": mf_val / total,
            "knn": knn_val / total,
            "pop": pop_val / total,
        }

    def get_top_n_for_user(
        self,
        user_index: int,
        n: int = 10,
        weights: Optional[Dict[str, float]] = None,
        exclude: Optional[List[int]] = None,
    ) -> List[Dict[str, float]]:
        w = weights or BALANCED_WEIGHTS
        scores = self._blend(user_index, w)
        if exclude:
            mask = np.isin(self.item_ids, exclude)
            scores = scores.copy()
            scores[mask] = -np.inf
        top_idx = np.argpartition(scores, -n)[-n:]
        # Sort final slice
        ordered = top_idx[np.argsort(scores[top_idx])[::-1]]
        return [
            {
                "anime_id": int(self.item_ids[i]),
                "score": float(scores[i]),
                "explanation": self.explain_item(user_index, i, w),
            }
            for i in ordered
        ]

@lru_cache(maxsize=8)
def compute_tfidf_similarity(matrix_hash: str, seed_index: int, tfidf_matrix: np.ndarray, top_k: int) -> List[int]:
    """Cached similarity: return top_k item indices similar to seed (excluding self)."""
    seed_vec = tfidf_matrix[seed_index]
    sims = tfidf_matrix @ seed_vec
    sims[seed_index] = -np.inf
    top = np.argpartition(sims, -top_k)[-top_k:]
    return top[np.argsort(sims[top])[::-1]].tolist()

def get_content_only_recs_for_new_item(
    item_index: int,
    tfidf_matrix: np.ndarray,
    top_k: int = 10
) -> List[int]:
    """Content-only path: pure TF-IDF similarity used for cold-start items."""
    seed_vec = tfidf_matrix[item_index]
    sims = tfidf_matrix @ seed_vec
    sims[item_index] = -np.inf
    top = np.argpartition(sims, -top_k)[-top_k:]
    return top[np.argsort(sims[top])[::-1]].tolist()
```

## badges.py
```python
# src/app/badges.py
from __future__ import annotations
from typing import Dict, Any

def cold_start_flag(is_in_training: bool) -> bool:
    return not is_in_training

def popularity_band(pop_percentile: float) -> str:
    """
    Map popularity percentile to band label.
    0.0 = most popular, 1.0 = least popular.
    """
    if pop_percentile < 0.10:
        return "Top 10%"
    if pop_percentile < 0.25:
        return "Top 25%"
    if pop_percentile < 0.50:
        return "Mid"
    return "Long Tail"

def novelty_ratio(user_genre_hist: Dict[str, int], item_genres: list[str]) -> float:
    """Compute fraction of item genres not previously seen (novelty)."""
    unseen = sum(1 for g in item_genres if g not in user_genre_hist)
    return unseen / max(len(item_genres) or 1, 1)

def badge_payload(
    is_in_training: bool,
    pop_percentile: float,
    user_genre_hist: Dict[str, int],
    item_genres: list[str]
) -> Dict[str, Any]:
    return {
        "cold_start": cold_start_flag(is_in_training),
        "popularity_band": popularity_band(pop_percentile),
        "novelty_ratio": novelty_ratio(user_genre_hist, item_genres),
    }
```

## explanations.py
```python
# src/app/explanations.py
from __future__ import annotations
from typing import Dict

def format_explanation(contributions: Dict[str, float]) -> str:
    """
    Format explanation shares as a concise string.
    e.g. 'mf 76.2% | knn 18.4% | pop 5.4%'
    """
    parts = []
    for key in ("mf", "knn", "pop"):
        val = contributions.get(key, 0.0) * 100
        parts.append(f"{key} {val:.1f}%")
    return " | ".join(parts)
```

## profiling.py
```python
# src/app/profiling.py
from __future__ import annotations
import time
import tracemalloc
from contextlib import contextmanager
from typing import Callable, Any, Dict

@contextmanager
def latency_timer(label: str):
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[LATENCY] {label}: {elapsed_ms:.2f} ms")

def profile_memory(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start = time.perf_counter()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[PROFILE] {func.__name__} latency={elapsed_ms:.2f}ms current={current/1024:.1f}KB peak={peak/1024:.1f}KB")
        return result
    return wrapper
```

## Streamlit Entrypoint (main)
```python
# app/main.py
import streamlit as st
from src.app.artifacts_loader import build_artifacts
from src.app.constants import BALANCED_WEIGHTS, DIVERSITY_EMPHASIZED_WEIGHTS, DEFAULT_TOP_N
from src.app.search import fuzzy_search
from src.app.explanations import format_explanation
from src.app.badges import badge_payload

@st.cache_resource(show_spinner=False)
def init_bundle():
    return build_artifacts()

bundle = init_bundle()
metadata = bundle["metadata"]

st.set_page_config(page_title="Anime Recommender", layout="wide")

st.sidebar.header("Controls")
persona = st.sidebar.selectbox("Persona", options=["SampleUser1", "SampleUser2"])
query = st.sidebar.text_input("Search Title")
weight_mode = st.sidebar.radio("Hybrid Weights", ["Balanced", "Diversity+"])
top_n = st.sidebar.slider("Top N", 5, 30, DEFAULT_TOP_N)

weights = BALANCED_WEIGHTS if weight_mode == "Balanced" else DIVERSITY_EMPHASIZED_WEIGHTS

st.title("Anime Recommendation System")

# Placeholder: perform search
if query:
    choices = [(t.lower(), int(aid)) for t, aid in zip(metadata["title_display"], metadata["anime_id"])]
    matches = fuzzy_search(query, choices, limit=8)
    st.sidebar.write("Matches:")
    for mid, score, title in matches:
        st.sidebar.write(f"{title} ({score:.0f})")

# Recommendations mock (replace with real recommender)
st.subheader("Recommendations")
placeholder_recs = metadata.head(top_n)
for _, row in placeholder_recs.iterrows():
    badges = badge_payload(
        is_in_training=True,
        pop_percentile=0.3,
        user_genre_hist={"action": 5, "drama": 7},
        item_genres=(row.get("genres") or "").split("|")
    )
    exp_str = format_explanation({"mf": 0.75, "knn": 0.20, "pop": 0.05})
    with st.container():
        st.markdown(f"**{row['title_display']}**")
        st.caption(f"Genres: {row.get('genres','')}")
        st.write(f"Badges: cold_start={badges['cold_start']} | {badges['popularity_band']} | novelty={badges['novelty_ratio']:.2f}")
        st.write(f"Explanation: {exp_str}")

with st.expander("Help / FAQ"):
    st.markdown("""
    **Hybrid Logic** blends MF, kNN, and popularity.
    **Metrics**: NDCG for ranking quality, Coverage for diversity.
    **Cold-Start** items rely on content similarity (no training interactions).
    """)

st.sidebar.caption("Latency & memory will appear in logs.")
```

---

# File / Module Layout

```
src/app/
  constants.py
  artifacts_loader.py
  recommender.py
  search.py
  badges.py
  explanations.py
  profiling.py
  personas_loader.py        # (optional: load personas.json)
app/
  main.py
data/samples/
  personas.json
tests/
  test_app_helpers.py       # search, badges, explanations
  test_app_import.py        # import & minimal render
scripts/
  run_unified_eval.py       # existing smoke artifact check
.github/workflows/
  ci.yml                    # extended for app tests & lint
.streamlit/
  config.toml
```

---

# Milestone Checklist (PR-Sized)

1. Loader + Constants + Personas (artifacts_loader.py, constants.py, personas.json).
2. Search + Badges + Explanations utilities with tests.
3. HybridRecommender implementation + similarity fallback + profiling hooks.
4. Streamlit UI scaffold (main.py basic layout).
5. Caching & performance tuning (TTL, memory check).
6. Diversity/novelty summary integration.
7. Alternate weight toggle & explanation panel refinement.
8. CI workflow extension (black, ruff, pytest).
9. Requirements pruning + Streamlit config.
10. Deployment + README update + screenshots.
11. Post-deploy metrics and optional blog/video outline.

---

# Post-Deployment Steps

- Smoke Test: `streamlit run app/main.py --server.headless true`
- Latency Logging: capture inference median latency (profiling decorator).
- Memory Audit: use `tracemalloc` peak; confirm <512MB.
- Screenshots: Landing, recommendation list (both weight modes), diversity tab, help tab.
- README Updates: Add install + `streamlit run app/main.py`, features list, architecture diagram reference.
- Public URL: Add to README + running_context.md.
- Optional Blog Outline: Problem framing, model blend, UX decisions, diversity trade-offs, performance constraints.
- Video Script (2–3 min): Intro, persona selection, search, explanation panel, diversity summary.

---

# Additional Notes

- TF-IDF fallback: compute similarity via matrix dot product; keep sparse to minimize RAM.
- Embeddings (optional): lazy load with separate cache & TTL; guard with try/except if not present.
- Determinism: Seed at artifact build; avoid nondeterministic sampling for top-N (stable sort tie-break).
- Accessibility: Color palette from Phase 4; ensure sufficient contrast for badges (test with colorblind-safe palette).
- Popularity percentile: Precompute once, cache with `st.cache_data`.

---

