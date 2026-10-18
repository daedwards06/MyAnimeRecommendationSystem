"""The synopsis neural embeddings artifact must load where torch is not installed.

The deployed app installs requirements.txt only (no torch). An artifact whose pickle
references a torch type is skipped at load time, silently before Task 0.8.
"""

from __future__ import annotations

import joblib
import numpy as np
import pytest


def test_neural_artifact_stores_library_versions_as_plain_str():
    """A str subclass (torch.__version__ is a TorchVersion) must not leak into the pickle."""
    import pickle

    from src.app.synopsis_neural_embeddings import build_artifact_from_embeddings

    class FakeVersion(str):
        pass

    art = build_artifact_from_embeddings(
        anime_ids=np.array([1, 2]),
        embeddings=np.full((2, 4), 0.5, dtype=np.float32),  # unit-norm rows
        model_name="m",
        model_library_versions={"torch": FakeVersion("2.2.0+cu121")},
        text_preprocessing={},
    )

    assert type(art.model_library_versions["torch"]) is str
    assert b"FakeVersion" not in pickle.dumps(art)


def test_neural_artifact_loads_without_torch(monkeypatch):
    """The deployed app has no torch; the neural artifact must unpickle without it.

    Skips where the artifacts are absent or are LFS pointer files (CI checks out without
    LFS objects, so the files exist but hold a short text pointer).
    """
    import sys

    from src.models.constants import MODELS_DIR

    def _is_lfs_pointer(path) -> bool:
        with path.open("rb") as fh:
            return fh.read(64).startswith(b"version https://git-lfs")

    paths = [
        p
        for p in sorted(MODELS_DIR.glob("synopsis_neural_embeddings*.joblib"))
        if not _is_lfs_pointer(p)
    ]
    if not paths:
        pytest.skip("No neural embeddings artifact present (LFS not pulled)")

    for name in [m for m in sys.modules if m == "torch" or m.startswith("torch.")]:
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.setitem(sys.modules, "torch", None)

    for path in paths:
        joblib.load(path)
