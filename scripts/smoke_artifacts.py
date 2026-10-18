"""Smoke check against the real model artifacts (not the CI light-import stubs).

Loads the real bundle, prints which model families loaded, then runs one seed-based query
and one personalized query through the scoring-pipeline functions (no Streamlit runtime),
with the per-request item-kNN vectors the app builds.

Run:
    python scripts/smoke_artifacts.py        (or: make smoke)

Exit code is non-zero when an expected family (EXPECTED_MODEL_FAMILIES) did not load, or
when either query returns fewer than TOP_N results.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.pipeline_runner import build_recommender_engine
from src.app.artifacts_loader import (
    FAMILY_LABELS,
    build_artifacts,
    missing_expected_families,
)
from src.app.constants import BALANCED_WEIGHTS, EXPECTED_MODEL_FAMILIES
from src.app.quality_filters import build_ranked_candidate_hygiene_exclude_ids
from src.app.scoring_pipeline import (
    ScoringContext,
    apply_post_filters,
    finalize_explanation_shares,
    run_personalized_pipeline,
    run_seed_based_pipeline,
)
from src.data.user_profiles import load_profile
from src.models.user_embedding import generate_user_embedding

TOP_N = 10
SEED_ANIME_ID = 9253  # Steins;Gate
PROFILE_USERNAME = "example"  # data/user_profiles/example_profile.json


def _print_top(title: str, recs: list[dict], titles: dict[int, str]) -> None:
    print(f"\n{title} ({len(recs)} results)")
    for i, rec in enumerate(recs, 1):
        aid = int(rec["anime_id"])
        print(f"  {i:2d}. {titles.get(aid, f'Anime {aid}')}  [{aid}]")


def _finish(recs: list[dict], ctx: ScoringContext) -> list[dict]:
    recs = finalize_explanation_shares(recs)
    recs = apply_post_filters(recs, ctx)
    return recs[: ctx.top_n]


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    failures: list[str] = []

    bundle = build_artifacts(
        data_dir=ROOT_DIR / "data" / "processed",
        models_dir=ROOT_DIR / "models",
        reports_dir=ROOT_DIR / "reports",
    )
    load_report = bundle["load_report"]

    print("Model families")
    for family in sorted(set(load_report) | set(EXPECTED_MODEL_FAMILIES)):
        entry = load_report.get(family) or {}
        label = FAMILY_LABELS.get(family, family)
        if entry.get("loaded"):
            print(f"  {label:<28} loaded   {entry['stem']}  ({entry['size_mb']} MB)")
        else:
            print(f"  {label:<28} MISSING  {entry.get('reason') or 'not in the load report'}")
    for family in missing_expected_families(load_report):
        failures.append(f"expected model family not loaded: {FAMILY_LABELS.get(family, family)}")

    metadata = bundle["metadata"]
    titles = dict(zip(metadata["anime_id"].astype(int), metadata["title_display"].astype(str), strict=False))
    engine = build_recommender_engine(bundle)
    if engine.recommender is None or engine.components is None:
        failures.append("recommender engine did not build")
        return _report(failures)

    hygiene = build_ranked_candidate_hygiene_exclude_ids(metadata)
    models = bundle["models"]
    if engine.knn_model is None:
        failures.append("kNN model has no item_user_matrix; item-kNN cannot be served")
    common = {
        "metadata": metadata,
        "bundle": bundle,
        "weights": dict(BALANCED_WEIGHTS),
        "top_n": TOP_N,
        "pop_pct_fn": engine.pop_pct_for_anime_id,
        "is_in_training_fn": engine.is_in_training,
        "mf_model": models.get("mf"),
        "mf_stem": models.get("_mf_stem"),
        "ranked_hygiene_exclude_ids": hygiene,
    }

    # Seed-based: same request size as the app with no profile and no filters.
    # Per-request kNN vectors, built the way app/pipeline_runner.py builds them.
    seed_title = titles.get(SEED_ANIME_ID, str(SEED_ANIME_ID))
    seed_knn = engine.knn_scores({SEED_ANIME_ID: 1.0}, center=False)
    if seed_knn is None:
        failures.append("seed has no item-kNN vector")
    seed_rec, seed_components = engine.for_request(seed_knn)
    seed_ctx = ScoringContext(
        **common,
        recommender=seed_rec,
        components=seed_components,
        seed_ids=[SEED_ANIME_ID],
        seed_titles=[seed_title],
        n_requested=TOP_N,
    )
    seed_result = run_seed_based_pipeline(seed_ctx)
    seed_recs = _finish(seed_result.ranked_items, seed_ctx)
    _print_top(f"Seed-based: {seed_title} ({seed_result.active_scoring_path})", seed_recs, titles)
    if len(seed_recs) < TOP_N:
        failures.append(f"seed query returned {len(seed_recs)} < {TOP_N} results")

    # Personalized: example profile, full strength, no seeds (app requests 10x when a profile is active).
    # load_profile converts the JSON's string keys to the int anime_ids the MF index uses.
    profile = load_profile(PROFILE_USERNAME)
    if profile is None:
        failures.append(f"profile '{PROFILE_USERNAME}' not found")
        return _report(failures)
    embedding = generate_user_embedding(
        ratings_dict=profile.get("ratings", {}),
        mf_model=models.get("mf"),
        method="weighted_average",
        normalize=True,
    )
    if float(np.linalg.norm(embedding)) <= 1e-8:
        failures.append("profile ratings do not overlap the MF training set (zero embedding)")
    profile_knn = engine.knn_scores(profile.get("ratings", {}), center=True)
    if profile_knn is None:
        failures.append("profile ratings do not overlap the kNN index (no item-kNN vector)")
    pers_rec, pers_components = engine.for_request(profile_knn)
    pers_ctx = ScoringContext(
        **common,
        recommender=pers_rec,
        components=pers_components,
        personal_knn_scores=profile_knn,
        user_embedding=embedding,
        user_embedding_meta={"mf_stem": models.get("_mf_stem")},
        personalization_enabled=True,
        personalization_strength=1.0,
        active_profile=profile,
        watched_ids={int(x) for x in profile.get("watched_ids", [])},
        n_requested=TOP_N * 10,
    )
    pers_result = run_personalized_pipeline(pers_ctx)
    if pers_result.personalization_blocked_reason:
        failures.append(f"personalized query blocked: {pers_result.personalization_blocked_reason}")
    pers_recs = _finish(pers_result.ranked_items, pers_ctx)
    _print_top(f"Personalized: {profile.get('username')} ({PROFILE_USERNAME}_profile.json)", pers_recs, titles)
    if len(pers_recs) < TOP_N:
        failures.append(f"personalized query returned {len(pers_recs)} < {TOP_N} results")

    return _report(failures)


def _report(failures: list[str]) -> int:
    if failures:
        print("\nSMOKE FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nSMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
