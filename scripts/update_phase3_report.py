import sys
from pathlib import Path
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.models.constants import METRICS_DIR


def _latest_json(prefix: str) -> Path | None:
    files = sorted(METRICS_DIR.glob(f"{prefix}_*.json"))
    return files[-1] if files else None


def _load_metrics(prefix: str):
    p = _latest_json(prefix)
    if not p:
        return None
    try:
        data = json.loads(p.read_text())
        return {
            "ndcg": float(data.get("ndcg@k_mean", 0.0)),
            "map": float(data.get("map@k_mean", 0.0)),
            "users": int(data.get("users_evaluated", 0)),
            "coverage": float(data.get("item_coverage@k", 0.0)),
            "gini": float(data.get("gini_index@k", 0.0)),
        }
    except Exception:
        return None


def build_table(rows):
    header = "| Model | NDCG@10 | MAP@10 | Users | Coverage | Gini |\n|---|---|---|---|---|---|"
    lines = [header]
    for name, m in rows:
        if m is None:
            lines.append(f"| {name} | — | — | — | — | — |")
        else:
            cov = m.get('coverage', 0.0)
            gini = m.get('gini', 0.0)
            lines.append(f"| {name} | {m['ndcg']:.5f} | {m['map']:.5f} | {m['users']} | {cov:.3f} | {gini:.3f} |")
    return "\n".join(lines)


def main():
    report = ROOT / "reports/phase3_summary.md"
    report.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        ("Popularity Baseline", _load_metrics("popularity_baseline")),
        ("MF (FunkSVD, SGD)", _load_metrics("mf_sgd")),
        ("Item kNN (profile)", _load_metrics("item_knn_sklearn")),
        ("Hybrid Weighted", _load_metrics("hybrid_weighted")),
        ("Hybrid RRF", _load_metrics("hybrid_rrf")),
        ("Content TF-IDF", _load_metrics("content_tfidf")),
        ("Content Embeddings", _load_metrics("content_embeddings")),
    ]

    table = build_table(rows)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = (
        "\n\n## Auto-generated metrics (latest)\n\n"
        f"Generated: {ts}\n\n"
        f"{table}\n"
    )

    # Cold-start metrics (if present)
    cold = _load_metrics("cold_start_content_tfidf")
    if cold:
        cold_table = build_table([("Cold-Start Content TF-IDF", cold)])
        block += ("\n\n### Cold-Start (new items only)\n\n" + cold_table + "\n")

    # Add small explanation snippet if exists
    expl = _latest_json("hybrid_explanations")
    if expl and expl.exists():
        try:
            j = json.loads(expl.read_text())
            # Show up to 1 user with top-5 and contribution shares
            if j:
                first_user = next(iter(j.keys()))
                entry = j[first_user]
                block += ("\n\n### Hybrid explanation example\n\n"
                          f"User {first_user}: top={entry.get('top', [])[:5]}\n\n"
                          "(See experiments/metrics/hybrid_explanations.json for full breakdown.)\n")
        except Exception:
            pass

    # Append block (non-destructive)
    with report.open("a", encoding="utf-8") as f:
        f.write(block)
    print("Updated report with latest metrics table.")


if __name__ == "__main__":
    main()
