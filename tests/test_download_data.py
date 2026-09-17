"""Tests for the raw-data fetcher's pure manifest / rename logic (no network)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("download_data", ROOT / "scripts" / "download_data.py")
assert _spec is not None and _spec.loader is not None
download_data = importlib.util.module_from_spec(_spec)
sys.modules["download_data"] = download_data
_spec.loader.exec_module(download_data)


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    target = tmp_path / "raw"
    target.mkdir()
    return target


def write_csv(path: Path, header: str, rows: int, *, trailing_newline: bool = True) -> Path:
    body = "".join(f"{i},{i},{i}\n" for i in range(rows))
    text = f"{header}\n{body}"
    if rows and not trailing_newline:
        text = text[:-1]
    path.write_text(text, encoding="utf-8")
    return path


def test_manifest_covers_the_files_the_pipeline_reads():
    names = {spec.local_name for spec in download_data.MANIFEST}
    assert names == {"rating.csv", "anime.csv"}


def test_rename_plan_maps_archive_members_to_raw_dir(raw_dir: Path, tmp_path: Path):
    extract_dir = tmp_path / "extracted"
    plan = download_data.rename_plan(download_data.MANIFEST, extract_dir, raw_dir)
    assert plan == [
        (extract_dir / spec.archive_name, raw_dir / spec.local_name) for spec in download_data.MANIFEST
    ]
    assert all(dest.parent == raw_dir for _, dest in plan)


def test_rename_plan_applies_a_differing_local_name(raw_dir: Path, tmp_path: Path):
    spec = download_data.RawFile("rating_complete.csv", "rating.csv", 10, ("user_id",))
    (source, dest), = download_data.rename_plan((spec,), tmp_path, raw_dir)
    assert source.name == "rating_complete.csv"
    assert dest == raw_dir / "rating.csv"


def test_count_data_rows_excludes_the_header(tmp_path: Path):
    path = write_csv(tmp_path / "x.csv", "a,b,c", 5)
    assert download_data.count_data_rows(path) == 5


def test_count_data_rows_counts_a_final_line_without_a_newline(tmp_path: Path):
    path = write_csv(tmp_path / "x.csv", "a,b,c", 5, trailing_newline=False)
    assert download_data.count_data_rows(path) == 5


def test_count_data_rows_on_a_header_only_file(tmp_path: Path):
    path = write_csv(tmp_path / "x.csv", "a,b,c", 0)
    assert download_data.count_data_rows(path) == 0


def test_read_header_returns_column_names(tmp_path: Path):
    path = write_csv(tmp_path / "x.csv", "user_id, anime_id ,rating", 1)
    assert download_data.read_header(path) == ("user_id", "anime_id", "rating")


def test_verify_file_accepts_a_matching_file(raw_dir: Path):
    spec = download_data.RawFile("x.csv", "x.csv", 3, ("a", "b", "c"))
    write_csv(raw_dir / "x.csv", "a,b,c", 3)
    assert download_data.verify_file(spec, raw_dir / "x.csv") == []


def test_verify_file_reports_a_wrong_row_count(raw_dir: Path):
    spec = download_data.RawFile("x.csv", "x.csv", 99, ("a", "b", "c"))
    write_csv(raw_dir / "x.csv", "a,b,c", 3)
    problems = download_data.verify_file(spec, raw_dir / "x.csv")
    assert len(problems) == 1
    assert "3 data rows" in problems[0]


def test_verify_file_reports_a_wrong_schema(raw_dir: Path):
    spec = download_data.RawFile("x.csv", "x.csv", 3, ("user_id", "anime_id", "rating"))
    write_csv(raw_dir / "x.csv", "MAL_ID,Name,Score", 3)
    problems = download_data.verify_file(spec, raw_dir / "x.csv")
    assert any("columns" in p for p in problems)


def test_verify_file_reports_a_missing_file(raw_dir: Path):
    spec = download_data.RawFile("x.csv", "x.csv", 3, ("a",))
    assert download_data.verify_file(spec, raw_dir / "x.csv") == ["x.csv: missing"]


def test_verify_manifest_collects_every_problem(raw_dir: Path):
    problems = download_data.verify_manifest(download_data.MANIFEST, raw_dir)
    assert len(problems) == len(download_data.MANIFEST)
    assert all(p.endswith("missing") for p in problems)


def test_missing_files_lists_only_absent_entries(raw_dir: Path):
    write_csv(raw_dir / "anime.csv", "anime_id,name", 1)
    assert download_data.missing_files(download_data.MANIFEST, raw_dir) == ["rating.csv"]


def test_kaggle_command_targets_the_dataset_and_destination(tmp_path: Path):
    cmd = download_data.kaggle_command("owner/slug", tmp_path)
    assert cmd[:5] == ["kaggle", "datasets", "download", "-d", "owner/slug"]
    assert cmd[-2:] == ["-p", str(tmp_path)]


def test_describe_plan_mentions_every_file_and_touches_nothing(raw_dir: Path):
    text = download_data.describe_plan("owner/slug", download_data.MANIFEST, raw_dir)
    assert "owner/slug" in text
    for spec in download_data.MANIFEST:
        assert spec.local_name in text
        assert f"{spec.expected_rows:,}" in text
    assert list(raw_dir.iterdir()) == []


def test_describe_plan_flags_existing_files_as_overwrites(raw_dir: Path):
    write_csv(raw_dir / "anime.csv", "anime_id,name", 1)
    text = download_data.describe_plan("owner/slug", download_data.MANIFEST, raw_dir)
    assert "overwrite" in text
    assert "create" in text


def test_dry_run_exits_zero_without_the_kaggle_cli(raw_dir: Path, capsys):
    assert download_data.main(["--dry-run", "--raw-dir", str(raw_dir)]) == 0
    assert "Would run: kaggle datasets download" in capsys.readouterr().out


def test_verify_only_exits_non_zero_when_files_are_absent(raw_dir: Path):
    assert download_data.main(["--verify-only", "--raw-dir", str(raw_dir)]) == 1


def test_require_kaggle_cli_exits_with_install_instructions(monkeypatch):
    monkeypatch.setattr(download_data.shutil, "which", lambda _: None)
    with pytest.raises(SystemExit) as excinfo:
        download_data.require_kaggle_cli()
    assert "pip install kaggle" in str(excinfo.value)
    assert "KAGGLE_USERNAME" in str(excinfo.value)
