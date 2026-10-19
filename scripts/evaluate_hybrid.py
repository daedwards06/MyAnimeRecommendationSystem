import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
import numpy as np

from src.models.constants import (
    DATA_PROCESSED_DIR,
    METRICS_DIR,
    OPTUNA_DIR,
    TOP_K_DEFAULT,
    DEFAULT_SAMPLE_USERS,
)
from src.eval.splits import build_validation, reporting_and_tuning_users
from src.eval.eval_artifacts import knn_eval_scores, load_eval_als, load_eval_models, run_metadata
from src.eval.metrics import ndcg_at_k, average_precision_at_k
from src.models.hybrid import weighted_blend, reciprocal_rank_fusion
from src.models.baselines import popularity_scores
from src.eval.metrics_extra import item_coverage, gini_index


# The blend served before Task 0.9, tuned while item-kNN could not score. It stays the default
# `hybrid_weighted` row so the published labels keep their meaning: `hybrid_weighted` is this
# legacy blend and `hybrid_weighted_tuned` is the re-tune the app now serves (DEFAULT_HYBRID_WEIGHTS).
LEGACY_HYBRID_WEIGHTS = {"mf": 0.9307796791956574, "knn": 0.06624663364738044, "pop": 0.0029736871569621902}


def _tuned_weights(path: Path) -> dict[str, float] | None:
    """Normalized weights from the latest Optuna sweep, or None if no sweep has run."""
    try:
        w = json.loads(path.read_text(encoding="utf-8"))["weights_normalized"]
    except (OSError, KeyError, TypeError, ValueError):
        return None
    return {"mf": float(w["w_mf"]), "knn": float(w["w_knn"]), "pop": float(w["w_pop"])}


def _build_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Backward compat shim; delegate to shared util
    return build_validation(df)


# JSON serializer that handles NumPy types and arrays
def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)


def _evaluate(model_name: str, recommendations: dict[int, list[int]], relevant: dict[int, set[int]], k: int) -> dict:
    ndcgs, maps = [], []
    for u, recs in recommendations.items():
        rel = relevant.get(u, set())
        ndcgs.append(ndcg_at_k(recs, rel, k))
        maps.append(average_precision_at_k(recs, rel, k))
    return {
        "model": model_name,
        "k": k,
        "users_evaluated": len(recommendations),
        "ndcg@k_mean": float(sum(ndcgs) / max(1, len(ndcgs))),
        "map@k_mean": float(sum(maps) / max(1, len(maps))),
        "per_user": {"user_id": [int(u) for u in recommendations], "ndcg": ndcgs, "map": maps},
    }


def _truncate(recs: dict[int, list[int]], k: int) -> dict[int, list[int]]:
    return {u: r[:k] for u, r in recs.items()}


def _without_pop(weights: dict[str, float]) -> dict[str, float]:
    """The blend with its popularity term removed, renormalized: the "no pop" ablation."""
    total = weights["mf"] + weights["knn"]
    return {"mf": weights["mf"] / total, "knn": weights["knn"] / total, "pop": 0.0}


def main(ks: list[int], sample_users: int, w_mf: float, w_knn: float, w_pop: float, save_examples: int = 2):
    ks = sorted(set(ks))
    k_max = ks[-1]
    interactions = pd.read_parquet(DATA_PROCESSED_DIR / "interactions.parquet")
    train_df, val_df = _build_validation(interactions)
    users, _ = reporting_and_tuning_users(val_df["user_id"].unique().tolist(), sample_users, 0)

    # Train-split artifacts: the served models in models/ trained on the val rows.
    knn_model, mf_model = load_eval_models(train_df)
    als_model = load_eval_als(train_df)

    # Build histories and popularity scores
    train_hist = train_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    val_hist = val_df.groupby("user_id")["anime_id"].apply(set).to_dict()
    pop_series = popularity_scores(train_df)  # pandas Series item_id -> score
    pop_scores_global = {int(i): float(s) for i, s in pop_series.items()}

    # Every list is ranked once at the largest K; a score-ranked top-K is a prefix of it.
    recs_knn: dict[int, list[int]] = {}
    recs_mf: dict[int, list[int]] = {}
    recs_pop: dict[int, list[int]] = {}
    recs_als: dict[int, list[int]] = {}
    blend_variants = {"hybrid_weighted": {"mf": w_mf, "knn": w_knn, "pop": w_pop}}
    if blend_variants["hybrid_weighted"] != LEGACY_HYBRID_WEIGHTS:
        blend_variants["hybrid_weighted_legacy"] = LEGACY_HYBRID_WEIGHTS
    tuned = _tuned_weights(OPTUNA_DIR / "hybrid_weights_best.json")
    if tuned is not None and tuned not in blend_variants.values():
        blend_variants["hybrid_weighted_tuned"] = tuned
    if tuned is not None:
        blend_variants["hybrid_mf_knn"] = _without_pop(tuned)
    recs_blend: dict[str, dict[int, list[int]]] = {name: {} for name in blend_variants}

    examples: dict[str, dict] = {}

    for u in users:
        seen = train_hist.get(u, set())

        # KNN scores and recs
        knn_scores = knn_eval_scores(knn_model, u, seen)
        knn_top = sorted(knn_scores.items(), key=lambda x: x[1], reverse=True)[:k_max]
        recs_knn[u] = [i for i, _ in knn_top]

        # MF scores and recs
        mf_scores_arr = mf_model.predict_user(u)
        # mask seen
        for it in seen:
            if it in mf_model.item_to_index:
                mf_scores_arr[mf_model.item_to_index[it]] = -np.inf
        # map to dict; a user MF never saw has no MF scores, as with kNN
        known = u in mf_model.user_to_index
        mf_scores = {mf_model.index_to_item[i]: float(s) for i, s in enumerate(mf_scores_arr) if np.isfinite(s)} if known else {}
        recs_mf[u] = mf_model.recommend(u, top_k=k_max, exclude=seen)
        recs_als[u] = als_model.recommend(u, top_k=k_max, exclude=seen)

        # Popularity recs (mask seen)
        pop_scores = {i: s for i, s in pop_scores_global.items() if i not in seen}
        pop_top = sorted(pop_scores.items(), key=lambda x: x[1], reverse=True)[:k_max]
        recs_pop[u] = [i for i, _ in pop_top]

        # Weighted blend (scores)
        sources = {
            "mf": mf_scores,
            "knn": knn_scores,
            "pop": pop_scores,
        }
        for name, weights in blend_variants.items():
            recs_blend[name][u] = weighted_blend(sources, weights, top_k=k_max)

        # Capture a few examples
        if len(examples) < save_examples:
            examples[str(u)] = {
                "knn": recs_knn[u][:5],
                "mf": recs_mf[u][:5],
                "pop": recs_pop[u][:5],
                "blend": recs_blend["hybrid_weighted"][u][:5],
                "rrf": reciprocal_rank_fusion({"mf": recs_mf[u], "knn": recs_knn[u], "pop": recs_pop[u]}, top_k=5),
            }

    total_items = int(train_df["anime_id"].nunique())
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    summary = []
    for k in ks:
        # RRF fuses each source's top-K, so it is rebuilt per K rather than truncated.
        recs_rrf = {
            u: reciprocal_rank_fusion({"mf": recs_mf[u][:k], "knn": recs_knn[u][:k], "pop": recs_pop[u][:k]}, top_k=k)
            for u in users
        }
        # (model label, JSON file stem, recommendations)
        runs = [
            ("item_knn_sklearn", "item_knn_sklearn", _truncate(recs_knn, k)),
            ("mf_sgd", "mf_sgd", _truncate(recs_mf, k)),
            ("popularity", "popularity_baseline", _truncate(recs_pop, k)),
            ("implicit_als", "implicit_als", _truncate(recs_als, k)),
            *[(name, name, _truncate(recs_blend[name], k)) for name in blend_variants],
            ("hybrid_rrf", "hybrid_rrf", recs_rrf),
        ]
        meta = run_metadata(k=k, sample_users=sample_users)
        for label, stem, recs in runs:
            m = _evaluate(label, recs, val_hist, k)
            m["item_coverage@k"] = item_coverage(recs, total_items)
            m["gini_index@k"] = gini_index(recs)
            if label in blend_variants:
                m["weights"] = blend_variants[label]
            m.update(meta)
            (METRICS_DIR / f"{stem}_k{k}_{ts}.json").write_text(json.dumps(m, indent=2, default=_json_default))
            summary.append({key: v for key, v in m.items() if key != "per_user"})

    (METRICS_DIR / f"hybrid_examples_{ts}.json").write_text(json.dumps(examples, indent=2, default=_json_default))

    # Append combined CSV rows
    out_csv = METRICS_DIR / "summary.csv"
    pd.DataFrame(summary).to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False)

    print(pd.DataFrame(summary)[["model", "k", "ndcg@k_mean", "map@k_mean", "item_coverage@k", "gini_index@k"]].to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate hybrid blends of MF, KNN, and Popularity")
    parser.add_argument("--k", type=int, nargs="+", default=[TOP_K_DEFAULT], help="One or more K values")
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    parser.add_argument("--w-mf", type=float, default=LEGACY_HYBRID_WEIGHTS["mf"])
    parser.add_argument("--w-knn", type=float, default=LEGACY_HYBRID_WEIGHTS["knn"])
    parser.add_argument("--w-pop", type=float, default=LEGACY_HYBRID_WEIGHTS["pop"])
    args = parser.parse_args()
    main(ks=args.k, sample_users=args.sample_users, w_mf=args.w_mf, w_knn=args.w_knn, w_pop=args.w_pop)
