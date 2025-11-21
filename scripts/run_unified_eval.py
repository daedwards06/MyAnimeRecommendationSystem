import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import argparse
import subprocess

from src.models.constants import TOP_K_DEFAULT, DEFAULT_SAMPLE_USERS


def run(cmd: list[str]):
    print("RUN:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main(k: int, sample_users: int):
    run([sys.executable, "scripts/evaluate_knn_mf.py", "--k", str(k), "--sample-users", str(sample_users)])
    run([sys.executable, "scripts/evaluate_hybrid.py", "--k", str(k), "--sample-users", str(sample_users)])
    run([sys.executable, "scripts/evaluate_content_only.py", "--k", str(k), "--sample-users", str(sample_users)])
    # Optional: cold-start and explanations for report context
    run([sys.executable, "scripts/evaluate_cold_start.py", "--k", str(k), "--sample-users", str(sample_users)])
    run([sys.executable, "scripts/explain_hybrid_examples.py", "--k", str(k), "--sample-users", str(sample_users), "--max-users", "5"])
    # Update report at the end
    run([sys.executable, "scripts/update_phase3_report.py"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run unified evaluation across all models and update the report")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--sample-users", type=int, default=DEFAULT_SAMPLE_USERS)
    args = parser.parse_args()
    main(args.k, args.sample_users)
