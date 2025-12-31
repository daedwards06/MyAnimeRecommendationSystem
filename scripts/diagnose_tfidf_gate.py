"""Side experiment: inspect TF-IDF neighbors + gate effects.

Prints the top TF-IDF neighbors for a given seed anime_id and shows whether
`synopsis_gate_passes(...)` allows them. This helps confirm whether strong
same-franchise neighbors (often movies/specials) are being excluded by the
hard gate (type/episodes).

Example:
    python scripts/diagnose_tfidf_gate.py --seed-id 21 --top-n 50
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from joblib import load

from src.app.artifacts_loader import build_artifacts
from src.app.synopsis_tfidf import (
    SYNOPSIS_TFIDF_MIN_SIM,
    SynopsisTfidfArtifact,
    compute_seed_similarity_map,
    most_common_seed_type,
    synopsis_gate_passes,
    validate_synopsis_tfidf_artifact,
)


def _safe_ascii(s: Any) -> str:
    return "".join(ch if ord(ch) < 128 else "?" for ch in str(s))


def _load_tfidf_from_bundle_or_models(bundle: dict[str, Any]) -> SynopsisTfidfArtifact:
    art = bundle.get("synopsis_tfidf")
    if art is not None:
        return validate_synopsis_tfidf_artifact(art)

    # Fallback: load most recent TF-IDF artifact from models/
    candidates = sorted(Path("models").glob("synopsis_tfidf_*.joblib"))
    if not candidates:
        raise FileNotFoundError("No synopsis_tfidf_*.joblib found in models/")
    return validate_synopsis_tfidf_artifact(load(candidates[-1]))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seed-id", type=int, default=21, help="Seed anime_id (default: 21 = One Piece)")
    p.add_argument("--top-n", type=int, default=50, help="How many neighbors to display")
    p.add_argument(
        "--min-sim",
        type=float,
        default=float(SYNOPSIS_TFIDF_MIN_SIM),
        help=f"Similarity threshold to highlight (default: {SYNOPSIS_TFIDF_MIN_SIM})",
    )
    args = p.parse_args()

    bundle = build_artifacts()
    metadata: pd.DataFrame = bundle["metadata"].copy()

    # Normalize ids for joining.
    metadata["anime_id"] = pd.to_numeric(metadata["anime_id"], errors="coerce").astype("Int64")
    metadata = metadata.dropna(subset=["anime_id"]).copy()
    metadata["anime_id"] = metadata["anime_id"].astype(int)

    tfidf = _load_tfidf_from_bundle_or_models(bundle)

    seed_id = int(args.seed_id)
    if seed_id not in tfidf.anime_id_to_row:
        raise ValueError(f"seed_id {seed_id} not present in TF-IDF artifact")

    sims_by_id = compute_seed_similarity_map(tfidf, seed_ids=[seed_id])
    seed_type = most_common_seed_type(metadata, [seed_id])

    meta_by_id = metadata.set_index("anime_id").to_dict(orient="index")

    # Sort by similarity desc, then id asc for determinism.
    ranked = sorted(
        ((int(aid), float(sim)) for aid, sim in sims_by_id.items() if int(aid) != seed_id),
        key=lambda x: (-float(x[1]), int(x[0])),
    )

    print(f"Seed: id={seed_id} title={_safe_ascii(meta_by_id.get(seed_id, {}).get('title_display', '?'))}")
    print(f"Seed type target (mode): {seed_type!r}")
    print(f"Neighbors shown: top_n={int(args.top_n)}")
    print("")

    header = "{:<5} {:>7} {:>8} {:>7} {:>6}  {}".format("rank", "sim", "passes", "type", "eps", "title")
    print(header)
    print("-" * len(header))

    pass_count = 0
    high_sim_fail = 0

    for rank, (aid, sim) in enumerate(ranked[: int(args.top_n)], start=1):
        info = meta_by_id.get(aid, {})
        cand_type = info.get("type")
        cand_eps = info.get("episodes")
        passes = synopsis_gate_passes(
            seed_type=seed_type,
            candidate_type=cand_type,
            candidate_episodes=cand_eps,
        )
        if passes:
            pass_count += 1
        if (not passes) and float(sim) >= float(args.min_sim):
            high_sim_fail += 1

        title = _safe_ascii(info.get("title_display", "?"))
        ctype = "" if cand_type is None or pd.isna(cand_type) else str(cand_type)
        eps = "" if cand_eps is None or pd.isna(cand_eps) else str(int(cand_eps))
        print(f"{rank:<5} {sim:7.4f} {str(bool(passes)):>8} {ctype:>7} {eps:>6}  {title}")

    print("")
    print(f"Summary: passes_gate={pass_count}/{min(int(args.top_n), len(ranked))}")
    print(f"Summary: high_sim(>={float(args.min_sim):.3f}) but fails_gate={high_sim_fail}")

    # Extra: show how many of the top-N are movies/specials (common for franchises)
    top_ids = [aid for aid, _ in ranked[: int(args.top_n)]]
    types = []
    for aid in top_ids:
        t = meta_by_id.get(aid, {}).get("type")
        if t is not None and not pd.isna(t):
            types.append(str(t))
    if types:
        counts: dict[str, int] = {}
        for t in types:
            counts[t] = counts.get(t, 0) + 1
        print("Top-N type breakdown:")
        for t, c in sorted(counts.items(), key=lambda x: (-int(x[1]), str(x[0]))):
            print(f"  {t}: {c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
