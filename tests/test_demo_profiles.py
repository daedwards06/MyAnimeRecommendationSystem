"""Demo taste profiles: valid fixtures, fully inside the MF index, and read-only."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from src.app.constants import DEFAULT_MF_MODEL_STEM, METADATA_PARQUET, PERSONAS_JSON
from src.data import user_profiles
from src.data.user_profiles import PROFILES_DIR, validate_profile

ROOT = Path(__file__).resolve().parents[1]
DEMO_PATHS = sorted(PROFILES_DIR.glob("demo_*_profile.json"))
MF_PATH = ROOT / "models" / f"{DEFAULT_MF_MODEL_STEM}.joblib"


def _load_build_script():
    spec = importlib.util.spec_from_file_location("build_demo_profiles", ROOT / "scripts" / "build_demo_profiles.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mf_item_ids() -> set[int]:
    # An un-pulled Git LFS pointer is a few hundred bytes of text.
    if not MF_PATH.exists() or MF_PATH.stat().st_size < 1_000_000:
        pytest.skip("MF model artifact not available")
    import joblib

    return {int(i) for i in joblib.load(MF_PATH).item_to_index}


def test_one_demo_profile_per_persona():
    personas = json.loads((ROOT / PERSONAS_JSON).read_text(encoding="utf-8"))
    assert len(DEMO_PATHS) == len(personas) == 2


@pytest.mark.parametrize("path", DEMO_PATHS, ids=lambda p: p.stem)
def test_demo_profile_validates(path: Path):
    profile = json.loads(path.read_text(encoding="utf-8"))
    ok, err = validate_profile(profile)
    assert ok, err
    assert profile["demo"] is True
    assert f"{profile['username']}_profile.json" == path.name
    assert 25 <= len(profile["ratings"]) <= 35
    assert all(7 <= r <= 10 for r in profile["ratings"].values())
    assert {int(k) for k in profile["ratings"]} == set(profile["watched_ids"])


@pytest.mark.parametrize("path", DEMO_PATHS, ids=lambda p: p.stem)
def test_every_rated_id_in_mf_index(path: Path, mf_item_ids: set[int]):
    profile = json.loads(path.read_text(encoding="utf-8"))
    missing = {int(k) for k in profile["ratings"]} - mf_item_ids
    assert not missing


def test_build_is_deterministic_and_matches_committed(mf_item_ids: set[int]):
    script = _load_build_script()
    personas = json.loads((ROOT / PERSONAS_JSON).read_text(encoding="utf-8"))
    metadata = pd.read_parquet(
        ROOT / "data" / "processed" / METADATA_PARQUET, columns=["anime_id", "genres", "members_count"]
    )
    first = script.build_profiles(personas, metadata, mf_item_ids)
    assert first == script.build_profiles(personas, metadata, mf_item_ids)
    for profile in first:
        committed = json.loads((PROFILES_DIR / f"{profile['username']}_profile.json").read_text(encoding="utf-8"))
        assert committed == profile


def test_save_refuses_demo_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(user_profiles, "PROFILES_DIR", tmp_path)
    with pytest.raises(ValueError, match="read-only demo"):
        user_profiles.save_profile("demo_x", {"demo": True, "watched_ids": [1], "ratings": {1: 8}})
    assert not list(tmp_path.iterdir())


def test_save_refuses_to_overwrite_demo_file(tmp_path, monkeypatch):
    monkeypatch.setattr(user_profiles, "PROFILES_DIR", tmp_path)
    demo_file = tmp_path / "demo_x_profile.json"
    demo_file.write_text(json.dumps({"username": "demo_x", "demo": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="read-only demo"):
        user_profiles.save_profile("demo_x", {"watched_ids": [1], "ratings": {1: 4}})
    assert json.loads(demo_file.read_text(encoding="utf-8")) == {"username": "demo_x", "demo": True}


def test_save_still_writes_regular_profiles(tmp_path, monkeypatch):
    monkeypatch.setattr(user_profiles, "PROFILES_DIR", tmp_path)
    path = user_profiles.save_profile("someone", {"watched_ids": [1], "ratings": {1: 8}})
    assert json.loads(path.read_text(encoding="utf-8"))["ratings"] == {"1": 8}
