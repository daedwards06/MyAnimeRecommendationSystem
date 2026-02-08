"""Compare quality factor modes on golden queries.

This script runs golden queries with all three QUALITY_FACTOR_MODE settings:
  - "mal_scaled" (default): quality = clamp((MAL - 5) / 4, 0.15, 1.0)
  - "binary": quality = 1.0 if MAL >= 6.0 else 0.5
  - "disabled": quality = 1.0 (no quality gating)

Outputs a comparison report showing:
  - Which niche anime (MAL 6-7) emerge or disappear under different modes
  - Ranking changes for existing recommendations
  - Overall diversity and quality metrics per mode

Usage:
    python scripts/compare_quality_factor_modes.py

Output:
    reports/quality_factor_mode_comparison_<timestamp>.md
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

from src.app.artifacts_loader import build_artifacts, set_determinism
from src.app.constants import QUALITY_FACTOR_MODE, compute_quality_factor
from src.app.recommender import HybridComponents, HybridRecommender, choose_weights
from src.app.scoring_pipeline import (
    ScoringContext,
    run_seed_based_pipeline,
)


@dataclass
class ComparisonResult:
    """Results for one query under one quality factor mode."""

    query_id: str
    seed_titles: list[str]
    mode: str
    top_n: list[dict[str, Any]]  # Top-N recommendations
    niche_anime: list[dict[str, Any]]  # Niche anime (MAL 6-7) in top-N
    diversity_genres: int
    avg_mal_score: float
    min_mal_score: float
    max_mal_score: float


def load_golden_queries() -> list[dict[str, Any]]:
    """Load golden queries from the Phase 4 golden queries file."""
    golden_path = ROOT / "data" / "samples" / "golden_queries_phase4.json"
    if not golden_path.exists():
        raise FileNotFoundError(f"Golden queries file not found: {golden_path}")

    import json

    cfg = json.loads(golden_path.read_text(encoding="utf-8"))
    return cfg.get("queries", [])


def build_recommender(bundle: dict[str, Any]) -> tuple[HybridComponents, HybridRecommender]:
    """Build HybridComponents and HybridRecommender from artifact bundle."""
    mf_model = bundle.get("models", {}).get("mf")
    if mf_model is None:
        raise RuntimeError("MF model not found in bundle")

    index_to_item = mf_model.index_to_item
    n_items = len(index_to_item)
    item_ids = np.asarray([int(index_to_item[i]) for i in range(n_items)], dtype=np.int64)

    p = mf_model.P
    q = mf_model.Q
    if p is None or q is None:
        raise RuntimeError("MF model P/Q is None")

    # Use demo user (index 0) for seed-based scoring
    demo_user_index = 0
    demo_scores = float(mf_model.global_mean) + (p[demo_user_index] @ q.T)
    mf_scores = np.asarray(demo_scores, dtype=np.float32).reshape(1, -1)

    components = HybridComponents(mf=mf_scores, knn=None, pop=None, item_ids=item_ids)

    # Build recommender
    recommender = HybridRecommender(components)

    return components, recommender


def run_query_with_mode(
    *,
    query_id: str,
    seed_titles: list[str],
    quality_mode: str,
    bundle: dict[str, Any],
    components: HybridComponents,
    recommender: HybridRecommender,
    top_n: int = 20,
) -> ComparisonResult:
    """Run a single query with the specified quality factor mode.

    Args:
        query_id: Unique identifier for the query
        seed_titles: List of anime titles to use as seeds
        quality_mode: Quality factor mode ("mal_scaled", "binary", "disabled")
        bundle: Artifact bundle from build_artifacts()
        components: HybridComponents instance
        recommender: HybridRecommender instance
        top_n: Number of recommendations to return

    Returns:
        ComparisonResult with recommendations and metrics
    """
    # Temporarily set the quality factor mode via environment variable
    original_mode = os.environ.get("QUALITY_FACTOR_MODE")
    os.environ["QUALITY_FACTOR_MODE"] = quality_mode

    # Force reload of the constant (this is a hack but works for this script)
    from src.app import constants

    constants.QUALITY_FACTOR_MODE = quality_mode

    metadata = bundle["metadata"]

    # Resolve seed titles to anime IDs
    seed_ids = []
    for title in seed_titles:
        matches = metadata[metadata["title_display"].str.lower() == title.lower()]
        if len(matches) > 0:
            seed_ids.append(int(matches.iloc[0]["anime_id"]))
        else:
            print(f"Warning: Seed title '{title}' not found in metadata")

    if not seed_ids:
        raise ValueError(f"No valid seeds found for query {query_id}")

    # Build scoring context
    ctx = ScoringContext(
        metadata=metadata,
        bundle=bundle,
        recommender=recommender,
        components=components,
        seed_ids=seed_ids,
        seed_titles=seed_titles,
        watched_ids=set(),
        top_n=top_n,
        genre_filter=[],
        type_filter=[],
        year_range=(1960, 2025),
        seed_ranking_mode="completion",  # Standard mode
    )

    # Run pipeline
    result = run_seed_based_pipeline(ctx)

    # Restore original mode
    if original_mode is not None:
        os.environ["QUALITY_FACTOR_MODE"] = original_mode
        constants.QUALITY_FACTOR_MODE = original_mode
    else:
        os.environ.pop("QUALITY_FACTOR_MODE", None)
        constants.QUALITY_FACTOR_MODE = "mal_scaled"

    # Extract metrics
    recommendations = result.ranked_items[:top_n]

    # Identify niche anime (MAL 6.0-7.5)
    niche_anime = []
    for rec in recommendations:
        mal = rec.get("mal_score")
        if mal is not None and 6.0 <= mal <= 7.5:
            niche_anime.append(rec)

    # Compute diversity and quality metrics
    all_genres = set()
    mal_scores = []
    for rec in recommendations:
        genres = rec.get("genres", [])
        if isinstance(genres, list):
            all_genres.update(genres)
        mal = rec.get("mal_score")
        if mal is not None:
            mal_scores.append(mal)

    avg_mal = sum(mal_scores) / len(mal_scores) if mal_scores else 0.0
    min_mal = min(mal_scores) if mal_scores else 0.0
    max_mal = max(mal_scores) if mal_scores else 0.0

    return ComparisonResult(
        query_id=query_id,
        seed_titles=seed_titles,
        mode=quality_mode,
        top_n=recommendations,
        niche_anime=niche_anime,
        diversity_genres=len(all_genres),
        avg_mal_score=avg_mal,
        min_mal_score=min_mal,
        max_mal_score=max_mal,
    )


def compare_modes(
    query_id: str,
    seed_titles: list[str],
    bundle: dict[str, Any],
    components: HybridComponents,
    recommender: HybridRecommender,
    top_n: int = 20,
) -> tuple[ComparisonResult, ComparisonResult, ComparisonResult]:
    """Run the same query with all three quality factor modes.

    Returns:
        (mal_scaled_result, binary_result, disabled_result)
    """
    print(f"Running query '{query_id}' with seeds: {seed_titles}")

    mal_scaled = run_query_with_mode(
        query_id=query_id,
        seed_titles=seed_titles,
        quality_mode="mal_scaled",
        bundle=bundle,
        components=components,
        recommender=recommender,
        top_n=top_n,
    )
    print(f"  [OK] mal_scaled: {len(mal_scaled.niche_anime)} niche anime in top-{top_n}")

    binary = run_query_with_mode(
        query_id=query_id,
        seed_titles=seed_titles,
        quality_mode="binary",
        bundle=bundle,
        components=components,
        recommender=recommender,
        top_n=top_n,
    )
    print(f"  [OK] binary: {len(binary.niche_anime)} niche anime in top-{top_n}")

    disabled = run_query_with_mode(
        query_id=query_id,
        seed_titles=seed_titles,
        quality_mode="disabled",
        bundle=bundle,
        components=components,
        recommender=recommender,
        top_n=top_n,
    )
    print(f"  [OK] disabled: {len(disabled.niche_anime)} niche anime in top-{top_n}")

    return mal_scaled, binary, disabled


def generate_markdown_report(
    results: list[tuple[ComparisonResult, ComparisonResult, ComparisonResult]],
    out_path: Path,
) -> None:
    """Generate a markdown report comparing quality factor modes."""
    lines = []
    lines.append("# Quality Factor Mode Comparison")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append("This report compares recommendation results across three quality factor modes:")
    lines.append("")
    lines.append("- **mal_scaled** (default): `quality = clamp((MAL - 5) / 4, 0.15, 1.0)`")
    lines.append("  - Favors high-MAL titles; penalizes niche anime with MAL 6-7")
    lines.append("  - A niche anime with MAL 6.5 gets quality_factor=0.375, cutting its neural similarity contribution by 62%")
    lines.append("")
    lines.append("- **binary**: `quality = 1.0 if MAL >= 6.0 else 0.5`")
    lines.append("  - Mild penalty only for very low-rated titles; gentler gate for niche gems")
    lines.append("")
    lines.append("- **disabled**: `quality = 1.0` (always)")
    lines.append("  - Pure relevance - trusts semantic similarity fully without quality gating")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary stats
    lines.append("## Summary Statistics")
    lines.append("")

    summary_data = []
    for mal_scaled, binary, disabled in results:
        summary_data.append(
            {
                "Query": mal_scaled.query_id,
                "mal_scaled_niche": len(mal_scaled.niche_anime),
                "mal_scaled_avg_mal": f"{mal_scaled.avg_mal_score:.2f}",
                "binary_niche": len(binary.niche_anime),
                "binary_avg_mal": f"{binary.avg_mal_score:.2f}",
                "disabled_niche": len(disabled.niche_anime),
                "disabled_avg_mal": f"{disabled.avg_mal_score:.2f}",
            }
        )

    lines.append("| Query | mal_scaled (niche/avg MAL) | binary (niche/avg MAL) | disabled (niche/avg MAL) |")
    lines.append("|-------|----------------------------|------------------------|--------------------------|")
    for row in summary_data:
        lines.append(
            f"| {row['Query']} | "
            f"{row['mal_scaled_niche']} / {row['mal_scaled_avg_mal']} | "
            f"{row['binary_niche']} / {row['binary_avg_mal']} | "
            f"{row['disabled_niche']} / {row['disabled_avg_mal']} |"
        )

    lines.append("")
    lines.append("**Niche anime**: MAL score between 6.0 and 7.5")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed per-query comparisons
    lines.append("## Detailed Query Comparisons")
    lines.append("")

    for mal_scaled, binary, disabled in results:
        lines.append(f"### Query: `{mal_scaled.query_id}`")
        lines.append("")
        lines.append(f"**Seeds**: {', '.join(mal_scaled.seed_titles)}")
        lines.append("")

        # Find niche anime that appear in binary/disabled but not mal_scaled
        mal_scaled_ids = {rec["anime_id"] for rec in mal_scaled.top_n}
        binary_ids = {rec["anime_id"] for rec in binary.top_n}
        disabled_ids = {rec["anime_id"] for rec in disabled.top_n}

        mal_scaled_niche_ids = {rec["anime_id"] for rec in mal_scaled.niche_anime}
        binary_niche_ids = {rec["anime_id"] for rec in binary.niche_anime}
        disabled_niche_ids = {rec["anime_id"] for rec in disabled.niche_anime}

        # Niche anime that emerge in binary
        binary_new_niche = binary_niche_ids - mal_scaled_niche_ids
        # Niche anime that emerge in disabled
        disabled_new_niche = disabled_niche_ids - mal_scaled_niche_ids

        if binary_new_niche or disabled_new_niche:
            lines.append("#### Niche Anime That Emerge")
            lines.append("")

            if binary_new_niche:
                lines.append("**In binary mode (not in mal_scaled top-20):**")
                lines.append("")
                for niche_id in binary_new_niche:
                    rec = next((r for r in binary.niche_anime if r["anime_id"] == niche_id), None)
                    if rec:
                        rank_in_binary = next(
                            (i + 1 for i, r in enumerate(binary.top_n) if r["anime_id"] == niche_id),
                            None,
                        )
                        mal = rec.get("mal_score", "N/A")
                        title = rec.get("title_display", rec.get("title", "Unknown"))
                        lines.append(f"- **#{rank_in_binary}: {title}** (MAL {mal})")
                lines.append("")

            if disabled_new_niche:
                lines.append("**In disabled mode (not in mal_scaled top-20):**")
                lines.append("")
                for niche_id in disabled_new_niche:
                    rec = next((r for r in disabled.niche_anime if r["anime_id"] == niche_id), None)
                    if rec:
                        rank_in_disabled = next(
                            (i + 1 for i, r in enumerate(disabled.top_n) if r["anime_id"] == niche_id),
                            None,
                        )
                        mal = rec.get("mal_score", "N/A")
                        title = rec.get("title_display", rec.get("title", "Unknown"))
                        lines.append(f"- **#{rank_in_disabled}: {title}** (MAL {mal})")
                lines.append("")
        else:
            lines.append("_No new niche anime emerge in binary or disabled modes._")
            lines.append("")

        # Top-5 comparison
        lines.append("#### Top-5 Comparison")
        lines.append("")
        lines.append("| Rank | mal_scaled | binary | disabled |")
        lines.append("|------|------------|--------|----------|")

        for i in range(min(5, len(mal_scaled.top_n))):
            ms_rec = mal_scaled.top_n[i] if i < len(mal_scaled.top_n) else None
            b_rec = binary.top_n[i] if i < len(binary.top_n) else None
            d_rec = disabled.top_n[i] if i < len(disabled.top_n) else None

            ms_title = f"{ms_rec.get('title_display', ms_rec.get('title', 'Unknown'))} ({ms_rec.get('mal_score', 'N/A')})" if ms_rec else ""
            b_title = f"{b_rec.get('title_display', b_rec.get('title', 'Unknown'))} ({b_rec.get('mal_score', 'N/A')})" if b_rec else ""
            d_title = f"{d_rec.get('title_display', d_rec.get('title', 'Unknown'))} ({d_rec.get('mal_score', 'N/A')})" if d_rec else ""

            lines.append(f"| {i + 1} | {ms_title} | {b_title} | {d_title} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Key findings
    lines.append("## Key Findings")
    lines.append("")
    lines.append("### Niche Anime Discovery")
    lines.append("")

    total_mal_scaled_niche = sum(len(ms.niche_anime) for ms, _, _ in results)
    total_binary_niche = sum(len(b.niche_anime) for _, b, _ in results)
    total_disabled_niche = sum(len(d.niche_anime) for _, _, d in results)

    lines.append(f"- **mal_scaled**: {total_mal_scaled_niche} total niche anime across {len(results)} queries")
    lines.append(f"- **binary**: {total_binary_niche} total niche anime (+{total_binary_niche - total_mal_scaled_niche})")
    lines.append(
        f"- **disabled**: {total_disabled_niche} total niche anime (+{total_disabled_niche - total_mal_scaled_niche})"
    )
    lines.append("")

    lines.append("### Average MAL Score")
    lines.append("")

    avg_mal_scaled = sum(ms.avg_mal_score for ms, _, _ in results) / len(results)
    avg_binary = sum(b.avg_mal_score for _, b, _ in results) / len(results)
    avg_disabled = sum(d.avg_mal_score for _, _, d in results) / len(results)

    lines.append(f"- **mal_scaled**: {avg_mal_scaled:.2f}")
    lines.append(f"- **binary**: {avg_binary:.2f} ({avg_binary - avg_mal_scaled:+.2f})")
    lines.append(f"- **disabled**: {avg_disabled:.2f} ({avg_disabled - avg_mal_scaled:+.2f})")
    lines.append("")

    lines.append("### Interpretation")
    lines.append("")
    lines.append(
        "- **binary mode** allows more niche anime (MAL 6-7) to surface while maintaining "
        "a basic quality threshold. This is a good balance for users who want diverse, "
        "relevant recommendations without excessive bias toward mainstream titles."
    )
    lines.append("")
    lines.append(
        "- **disabled mode** surfaces the most niche content, trusting semantic similarity "
        "fully. This may be preferred by users seeking hidden gems, but risks surfacing "
        "low-quality or poorly-rated titles."
    )
    lines.append("")
    lines.append(
        "- **mal_scaled mode** (default) maintains the highest average MAL score but may "
        "miss highly relevant niche titles that have lower community ratings."
    )
    lines.append("")

    # Write to file
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to: {out_path}")


def main() -> None:
    """Main entry point."""
    print("Quality Factor Mode Comparison")
    print("=" * 60)
    print()

    # Set determinism
    set_determinism()

    # Load artifacts
    print("Loading artifacts...")
    bundle = build_artifacts()
    print(f"[OK] Loaded metadata: {len(bundle['metadata'])} anime")

    # Build recommender
    print("Building recommender...")
    components, recommender = build_recommender(bundle)
    print("[OK] Recommender ready")
    print()

    # Load golden queries
    queries = load_golden_queries()
    print(f"Loaded {len(queries)} golden queries")
    print()

    # Run comparisons
    results = []
    for query in queries[:5]:  # Limit to first 5 queries for faster execution
        query_id = query.get("id", "unknown")
        seed_titles = query.get("seed_titles", [])

        if not seed_titles:
            print(f"Skipping query '{query_id}': no seed titles")
            continue

        try:
            comparison = compare_modes(query_id, seed_titles, bundle, components, recommender, top_n=20)
            results.append(comparison)
        except Exception as e:
            print(f"Error processing query '{query_id}': {e}")
            import traceback

            traceback.print_exc()
            continue

        print()

    # Generate report
    if results:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = ROOT / "reports" / f"quality_factor_mode_comparison_{timestamp}.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        generate_markdown_report(results, out_path)
        print()
        print("[SUCCESS] Comparison complete!")
    else:
        print("[ERROR] No results to generate report")


if __name__ == "__main__":
    main()
