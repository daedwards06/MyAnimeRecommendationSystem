import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import argparse
import subprocess

from src.models.constants import DEFAULT_SAMPLE_USERS, TOP_K_DEFAULT

# The ablation reports every variant at these K; `--k`, the headline K, is added if missing.
ABLATION_KS = (5, 10, 20)
# evaluate_hybrid.py scores popularity, item-kNN, MF, implicit ALS, every weighted blend and RRF;
# evaluate_content_only.py scores TF-IDF and embeddings.
VARIANT_SCRIPTS = {
    "cf": "scripts/evaluate_hybrid.py",
    "content": "scripts/evaluate_content_only.py",
}


def run(cmd: list[str]):
    print("RUN:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main(k: int, sample_users: int, variants: list[str]):
    ks = sorted(set(ABLATION_KS) | {k})
    groups = list(VARIANT_SCRIPTS) if "all" in variants else variants
    for group in groups:
        run([sys.executable, VARIANT_SCRIPTS[group], "--k", *map(str, ks), "--sample-users", str(sample_users)])
    if "all" not in variants:
        return
    # Optional: cold-start and explanations for report context
    run([sys.executable, "scripts/evaluate_cold_start.py", "--k", str(k), "--sample-users", str(sample_users)])
    run([sys.executable, "scripts/explain_hybrid_examples.py", "--k", str(k), "--sample-users", str(sample_users), "--max-users", "5"])
    # Update report at the end
    run([sys.executable, "scripts/update_phase3_report.py"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run unified evaluation across all models and update the report")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT, help=f"Headline K; the ablation also runs K in {ABLATION_KS}")
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    parser.add_argument(
        "--variants", nargs="+", default=["all"], choices=["all", *VARIANT_SCRIPTS],
        help="'all' runs every ablation variant plus cold-start, explanations and the Phase 3 report; "
             "a group name re-runs only that group's variants",
    )
    args = parser.parse_args()
    main(args.k, args.sample_users, args.variants)
