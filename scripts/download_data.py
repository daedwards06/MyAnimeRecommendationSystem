"""Fetch the raw Kaggle interaction dataset into ``data/raw/``.

The repository does not track the raw Kaggle CSVs (98.8 MB combined, redistributed
data). The Streamlit app does not need them - it runs from the committed parquets in
``data/processed/``. They are only required to rebuild features or retrain models:

  python scripts/build_features.py
  python scripts/discover_new_ids.py --baseline data/raw/anime.csv ...

Usage:
  python scripts/download_data.py            # download, extract, verify
  python scripts/download_data.py --dry-run  # print the plan, touch nothing
  python scripts/download_data.py --force    # re-download even if files exist

Credentials: the ``kaggle`` CLI reads ``KAGGLE_USERNAME`` / ``KAGGLE_KEY`` from the
environment, or ``~/.kaggle/kaggle.json``. Create a token at
https://www.kaggle.com/settings/account under "API" -> "Create New Token".
"""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

RAW_DIR = Path("data/raw")

# The files the pipeline reads are the 2017 CooperUnion snapshot (anime_id schema,
# rating.csv with -1 sentinels), NOT hernan4444/anime-recommendation-database-2020,
# which uses MAL_ID and rating_complete.csv. build_features.py and src/data/cleaning.py
# expect the CooperUnion schema; see docs/DATA_SOURCES.md.
KAGGLE_DATASET = "CooperUnion/anime-recommendations-database"


@dataclass(frozen=True)
class RawFile:
    """One file the pipeline expects under ``data/raw/``."""

    archive_name: str
    local_name: str
    expected_rows: int
    expected_columns: tuple[str, ...]


MANIFEST: tuple[RawFile, ...] = (
    RawFile(
        archive_name="rating.csv",
        local_name="rating.csv",
        expected_rows=7_813_737,
        expected_columns=("user_id", "anime_id", "rating"),
    ),
    RawFile(
        archive_name="anime.csv",
        local_name="anime.csv",
        expected_rows=12_294,
        expected_columns=("anime_id", "name", "genre", "type", "episodes", "rating", "members"),
    ),
)


def rename_plan(manifest: tuple[RawFile, ...], extract_dir: Path, raw_dir: Path) -> list[tuple[Path, Path]]:
    """Map each extracted archive member to its destination under ``raw_dir``."""
    return [(extract_dir / spec.archive_name, raw_dir / spec.local_name) for spec in manifest]


def count_data_rows(path: Path) -> int:
    """Count rows excluding the header, without loading the file into memory."""
    lines = 0
    trailing_newline = True
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            lines += chunk.count(b"\n")
            trailing_newline = chunk.endswith(b"\n")
    if not trailing_newline:
        lines += 1
    return max(lines - 1, 0)


def read_header(path: Path) -> tuple[str, ...]:
    """Return the CSV header as a tuple of column names."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        row = next(csv.reader(fh), [])
    return tuple(col.strip() for col in row)


def verify_file(spec: RawFile, path: Path) -> list[str]:
    """Return a list of problems with ``path``; empty means it matches the manifest."""
    if not path.exists():
        return [f"{spec.local_name}: missing"]
    problems = []
    header = read_header(path)
    if header != spec.expected_columns:
        problems.append(f"{spec.local_name}: columns {header} != expected {spec.expected_columns}")
    rows = count_data_rows(path)
    if rows != spec.expected_rows:
        problems.append(f"{spec.local_name}: {rows:,} data rows != expected {spec.expected_rows:,}")
    return problems


def verify_manifest(manifest: tuple[RawFile, ...], raw_dir: Path) -> list[str]:
    """Verify every manifest entry against the files in ``raw_dir``."""
    problems: list[str] = []
    for spec in manifest:
        problems.extend(verify_file(spec, raw_dir / spec.local_name))
    return problems


def missing_files(manifest: tuple[RawFile, ...], raw_dir: Path) -> list[str]:
    """Names of manifest files not present in ``raw_dir``."""
    return [spec.local_name for spec in manifest if not (raw_dir / spec.local_name).exists()]


def kaggle_command(dataset: str, dest: Path) -> list[str]:
    """The kaggle CLI invocation used to pull ``dataset`` into ``dest``."""
    return ["kaggle", "datasets", "download", "-d", dataset, "-p", str(dest)]


def describe_plan(dataset: str, manifest: tuple[RawFile, ...], raw_dir: Path) -> str:
    """Human-readable description of what a real run would do."""
    lines = [
        f"Would run: {' '.join(kaggle_command(dataset, Path('<temp dir>')))}",
        f"Would extract the archive and place files in {raw_dir}/:",
    ]
    for spec in manifest:
        dest = raw_dir / spec.local_name
        state = "overwrite" if dest.exists() else "create"
        rename = "" if spec.archive_name == spec.local_name else f" (from {spec.archive_name})"
        lines.append(
            f"  {state:9s} {dest}{rename} - expect {spec.expected_rows:,} rows, "
            f"columns {', '.join(spec.expected_columns)}"
        )
    lines.append("Would then verify row counts and headers against the manifest.")
    return "\n".join(lines)


def require_kaggle_cli() -> str:
    """Return the path to the kaggle CLI, or exit non-zero with install instructions."""
    path = shutil.which("kaggle")
    if path is None:
        sys.exit(
            "error: the 'kaggle' CLI is not on PATH.\n"
            "  Install it:   pip install kaggle\n"
            "  Authenticate: set KAGGLE_USERNAME and KAGGLE_KEY, or place kaggle.json in ~/.kaggle/\n"
            "  Token:        https://www.kaggle.com/settings/account -> API -> Create New Token"
        )
    return path


def download_and_extract(dataset: str, manifest: tuple[RawFile, ...], raw_dir: Path) -> None:
    """Download ``dataset`` from Kaggle and move its files into ``raw_dir``."""
    require_kaggle_cli()
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        print(f"Downloading {dataset} ...")
        result = subprocess.run(kaggle_command(dataset, tmp_dir), check=False)
        if result.returncode != 0:
            sys.exit(
                f"error: kaggle download failed with exit code {result.returncode}. "
                "Check your credentials and that you have accepted the dataset's terms on Kaggle."
            )
        archives = sorted(tmp_dir.glob("*.zip"))
        if not archives:
            sys.exit(f"error: no .zip archive found in {tmp_dir} after download.")
        extract_dir = tmp_dir / "extracted"
        for archive in archives:
            print(f"Extracting {archive.name} ...")
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(extract_dir)
        for source, dest in rename_plan(manifest, extract_dir, raw_dir):
            if not source.exists():
                sys.exit(f"error: expected {source.name} in the archive but it was not found.")
            print(f"Writing {dest}")
            shutil.move(str(source), str(dest))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default=KAGGLE_DATASET, help="Kaggle dataset slug to download")
    ap.add_argument("--raw-dir", type=Path, default=RAW_DIR, help="Destination directory")
    ap.add_argument("--dry-run", action="store_true", help="Print what would happen and exit")
    ap.add_argument("--force", action="store_true", help="Re-download even if the files already exist")
    ap.add_argument("--verify-only", action="store_true", help="Only check existing files against the manifest")
    args = ap.parse_args(argv)

    if args.dry_run:
        print(describe_plan(args.dataset, MANIFEST, args.raw_dir))
        return 0

    if not args.verify_only:
        if args.force or missing_files(MANIFEST, args.raw_dir):
            download_and_extract(args.dataset, MANIFEST, args.raw_dir)
        else:
            print(f"All raw files already present in {args.raw_dir}; verifying (use --force to re-download).")

    problems = verify_manifest(MANIFEST, args.raw_dir)
    if problems:
        print("Manifest verification failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"Verified {len(MANIFEST)} raw files against the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
