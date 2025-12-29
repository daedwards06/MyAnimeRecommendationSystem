"""Quick, deterministic probe: are Jikan-derived metadata features likely useful?

Purpose
-------
This is a *side test* (Phase 4 / Chunk A3 support) that does NOT change app behavior.
It analyzes an existing golden-queries artifact JSON and measures whether metadata
feature overlap differs between:
  - items flagged as violations vs non-violations (using the golden artifact)

It uses ONLY local artifacts:
  - data/processed/anime_metadata.parquet
  - reports/artifacts/phase4_golden_queries_*.json

No network calls.

Usage (PowerShell)
------------------
  python scripts/probe_jikan_feature_signal.py \
    --golden-json reports/artifacts/phase4_golden_queries_20251229165531.json

Outputs
-------
  - reports/jikan_feature_probe_<ts>.md
  - reports/artifacts/jikan_feature_probe_<ts>.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPORTS_DIR = Path("reports")
REPORTS_ARTIFACTS_DIR = REPORTS_DIR / "artifacts"
METADATA_PATH = Path("data/processed/anime_metadata.parquet")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _as_set(val: Any) -> set[str]:
    if val is None:
        return set()
    if isinstance(val, str):
        # Some columns may be stored as "A|B|C" strings.
        parts = [p.strip() for p in val.split("|")]
        return {p for p in parts if p}
    if hasattr(val, "__iter__") and not isinstance(val, (bytes, bytearray)):
        out: set[str] = set()
        for x in val:
            if x is None:
                continue
            s = str(x).strip()
            if s:
                out.add(s)
        return out
    s = str(val).strip()
    return {s} if s else set()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter / union) if union else 0.0


@dataclass(frozen=True)
class FeatureRow:
    query_id: str
    anime_id: int
    is_violation: bool
    overlap_genres: float
    overlap_themes: float
    overlap_studios: float
    overlap_demographics: float
    overlap_producers: float
    type_match: float
    source_match: float


def _load_metadata() -> pd.DataFrame:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Missing metadata parquet: {METADATA_PATH.as_posix()}")
    md = pd.read_parquet(METADATA_PATH)
    if "anime_id" not in md.columns:
        raise RuntimeError("metadata parquet missing required column: anime_id")
    md = md.copy()
    md["anime_id"] = md["anime_id"].astype(int)
    return md


def _idx_by_id(md: pd.DataFrame) -> dict[int, dict[str, Any]]:
    # Keep only columns we probe to reduce memory.
    cols = [
        "anime_id",
        "genres",
        "themes",
        "studios",
        "demographics",
        "producers",
        "type",
        "source_material",
    ]
    cols = [c for c in cols if c in md.columns]
    slim = md[cols]
    out: dict[int, dict[str, Any]] = {}
    for _, r in slim.iterrows():
        out[int(r["anime_id"])] = r.to_dict()
    return out


def _probe_one(
    *,
    query_id: str,
    seed_ids: list[int],
    rec_ids: list[int],
    violation_ids: set[int],
    by_id: dict[int, dict[str, Any]],
) -> list[FeatureRow]:
    seed_genres: set[str] = set()
    seed_themes: set[str] = set()
    seed_studios: set[str] = set()
    seed_demographics: set[str] = set()
    seed_producers: set[str] = set()
    seed_types: set[str] = set()
    seed_sources: set[str] = set()

    for sid in seed_ids:
        row = by_id.get(int(sid))
        if not row:
            continue
        seed_genres |= _as_set(row.get("genres"))
        seed_themes |= _as_set(row.get("themes"))
        seed_studios |= _as_set(row.get("studios"))
        seed_demographics |= _as_set(row.get("demographics"))
        seed_producers |= _as_set(row.get("producers"))
        seed_types |= _as_set(row.get("type"))
        seed_sources |= _as_set(row.get("source_material"))

    out: list[FeatureRow] = []
    for aid in rec_ids:
        row = by_id.get(int(aid)) or {}

        genres = _as_set(row.get("genres"))
        themes = _as_set(row.get("themes"))
        studios = _as_set(row.get("studios"))
        demographics = _as_set(row.get("demographics"))
        producers = _as_set(row.get("producers"))
        typ = _as_set(row.get("type"))
        src = _as_set(row.get("source_material"))

        out.append(
            FeatureRow(
                query_id=str(query_id),
                anime_id=int(aid),
                is_violation=bool(int(aid) in violation_ids),
                overlap_genres=_jaccard(seed_genres, genres),
                overlap_themes=_jaccard(seed_themes, themes),
                overlap_studios=_jaccard(seed_studios, studios),
                overlap_demographics=_jaccard(seed_demographics, demographics),
                overlap_producers=_jaccard(seed_producers, producers),
                type_match=1.0 if (seed_types and typ and bool(seed_types & typ)) else 0.0,
                source_match=1.0 if (seed_sources and src and bool(seed_sources & src)) else 0.0,
            )
        )

    return out


def _summarize(df: pd.DataFrame, col: str) -> dict[str, Any]:
    v = df[df["is_violation"]]
    g = df[~df["is_violation"]]

    def _mean(x: pd.Series) -> float:
        try:
            return float(x.mean())
        except Exception:
            return 0.0

    out = {
        "feature": col,
        "violation_mean": _mean(v[col]) if not v.empty else None,
        "non_violation_mean": _mean(g[col]) if not g.empty else None,
        "delta_non_minus_violation": (float(_mean(g[col]) - _mean(v[col]))) if (not v.empty and not g.empty) else None,
        "n_total": int(len(df)),
        "n_violations": int(len(v)),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe Jikan-derived feature signal using an existing golden artifact")
    ap.add_argument(
        "--golden-json",
        type=str,
        required=True,
        help="Path to reports/artifacts/phase4_golden_queries_<ts>.json",
    )
    args = ap.parse_args()

    golden_path = Path(args.golden_json)
    if not golden_path.exists():
        raise FileNotFoundError(f"Golden artifact not found: {golden_path.as_posix()}")

    md = _load_metadata()
    by_id = _idx_by_id(md)

    golden = json.loads(golden_path.read_text(encoding="utf-8"))

    rows: list[FeatureRow] = []
    for q in golden.get("queries", []) or []:
        qid = str(q.get("id"))
        seed_ids = [int(x) for x in (q.get("resolved_seed_ids") or [])]
        rec_ids = [int(r.get("anime_id")) for r in (q.get("recommendations") or []) if r.get("anime_id") is not None]
        violation_ids = {int(v.get("anime_id")) for v in (q.get("violations") or []) if v.get("anime_id") is not None}

        rows.extend(
            _probe_one(
                query_id=qid,
                seed_ids=seed_ids,
                rec_ids=rec_ids,
                violation_ids=violation_ids,
                by_id=by_id,
            )
        )

    df = pd.DataFrame([r.__dict__ for r in rows])

    features = [
        "overlap_genres",
        "overlap_themes",
        "overlap_studios",
        "overlap_demographics",
        "overlap_producers",
        "type_match",
        "source_match",
    ]

    summaries = [_summarize(df, c) for c in features]

    ts = _ts()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    out_json = {
        "schema": "jikan_feature_probe_v1",
        "timestamp_utc": ts,
        "golden_json": golden_path.as_posix(),
        "n_rows": int(len(df)),
        "n_violations": int(df["is_violation"].sum()) if not df.empty else 0,
        "summary": summaries,
    }

    json_path = REPORTS_ARTIFACTS_DIR / f"jikan_feature_probe_{ts}.json"
    json_path.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    md_lines: list[str] = []
    md_lines.append("# Jikan Feature Probe (Side Test)")
    md_lines.append("")
    md_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    md_lines.append(f"Golden artifact: {golden_path.as_posix()}")
    md_lines.append("")
    md_lines.append("This probe checks whether simple seed→candidate feature overlap differs between items flagged as golden violations vs non-violations.")
    md_lines.append("It does not change app logic; it is meant to inform which metadata features are worth wiring in Chunk A3.")
    md_lines.append("")

    md_lines.append("| Feature | Violation mean | Non-violation mean | Delta (non - viol) | N | Violations |")
    md_lines.append("|---|---:|---:|---:|---:|---:|")
    for s in summaries:
        md_lines.append(
            "| {feature} | {vmean} | {gmean} | {delta} | {n} | {nv} |".format(
                feature=s["feature"],
                vmean="" if s["violation_mean"] is None else f"{float(s['violation_mean']):.4f}",
                gmean="" if s["non_violation_mean"] is None else f"{float(s['non_violation_mean']):.4f}",
                delta="" if s["delta_non_minus_violation"] is None else f"{float(s['delta_non_minus_violation']):.4f}",
                n=int(s["n_total"]),
                nv=int(s["n_violations"]),
            )
        )

    md_path = REPORTS_DIR / f"jikan_feature_probe_{ts}.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[ok] wrote {md_path.as_posix()}")
    print(f"[ok] wrote {json_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
