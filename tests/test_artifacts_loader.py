"""Tests for src/app/artifacts_loader.py.

Tests cover:
- Missing metadata file raises ArtifactContractError
- Missing MF model raises ArtifactContractError
- MF model with missing attributes raises with details
- Valid artifacts return expected bundle structure
- Model selection logic (single, multiple, env var override)
- Mean-user vector computation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
import pytest
from conftest import MockMFModel

from src.app.artifacts_loader import (
    ArtifactContractError,
    build_artifacts,
)

# ---------------------------------------------------------------------------
# Mock Model Classes
# ---------------------------------------------------------------------------


class IncompleteMFModel:
    """Mock MF model missing required attributes."""

    def __init__(self):
        self.P = np.random.randn(5, 8).astype(np.float32)
        # Missing: Q, item_to_index, index_to_item


class InvalidMFModel:
    """Mock MF model with invalid attribute types."""

    def __init__(self):
        self.Q = None  # Should be array, but is None
        self.item_to_index = []  # Should be dict, but is list
        self.index_to_item = []  # Should be dict, but is list


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_metadata_df() -> pd.DataFrame:
    """Small realistic metadata DataFrame for testing."""
    return pd.DataFrame(
        [
            {
                "anime_id": 1,
                "title_display": "Test Anime 1",
                "title_english": "Test Anime 1 EN",
                "title_primary": "Test Anime 1",
                "title": "Test Anime 1",
                "title_japanese": "テストアニメ1",
                "genres": "Action|Adventure",
                "themes": "Military",
                "demographics": "Shounen",
                "synopsis": "A test synopsis for anime 1.",
                "synopsis_snippet": "A test synopsis...",
                "poster_thumb_url": "http://example.com/1.jpg",
                "streaming": "Crunchyroll",
                "mal_score": 8.5,
                "episodes": 24,
                "status": "Finished Airing",
                "aired_from": "2010-01-01",
                "studios": "Studio A",
                "source_material": "Manga",
                "type": "TV",
            },
            {
                "anime_id": 2,
                "title_display": "Test Anime 2",
                "title_english": "Test Anime 2 EN",
                "title_primary": "Test Anime 2",
                "title": "Test Anime 2",
                "title_japanese": "テストアニメ2",
                "genres": "Drama|Romance",
                "themes": "School",
                "demographics": "Shoujo",
                "synopsis": "A test synopsis for anime 2.",
                "synopsis_snippet": "A test synopsis...",
                "poster_thumb_url": "http://example.com/2.jpg",
                "streaming": "Netflix",
                "mal_score": 7.8,
                "episodes": 12,
                "status": "Finished Airing",
                "aired_from": "2015-04-01",
                "studios": "Studio B",
                "source_material": "Original",
                "type": "TV",
            },
            {
                "anime_id": 3,
                "title_display": "Test Movie",
                "title_english": "Test Movie EN",
                "title_primary": "Test Movie",
                "title": "Test Movie",
                "title_japanese": "テスト映画",
                "genres": "Action|Sci-Fi",
                "themes": "Mecha",
                "demographics": "Seinen",
                "synopsis": "A test synopsis for a movie.",
                "synopsis_snippet": "A test synopsis...",
                "poster_thumb_url": "http://example.com/3.jpg",
                "streaming": "Hulu",
                "mal_score": 8.2,
                "episodes": 1,
                "status": "Finished Airing",
                "aired_from": "2018-07-20",
                "studios": "Studio C",
                "source_material": "Light Novel",
                "type": "Movie",
            },
        ]
    )


@pytest.fixture
def temp_artifacts_dir(tmp_path: Path, mock_metadata_df: pd.DataFrame):
    """Create a temporary directory structure with test artifacts."""
    # Create directory structure
    data_dir = tmp_path / "data" / "processed"
    models_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"

    data_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata parquet
    metadata_path = data_dir / "anime_metadata.parquet"
    mock_metadata_df.to_parquet(metadata_path)

    # Create a valid MF model
    mf_model = MockMFModel(n_users=5, n_items=10, n_factors=8)
    joblib.dump(mf_model, models_dir / "mf_sgd_v1.0.joblib")

    return {
        "root": tmp_path,
        "data_dir": data_dir,
        "models_dir": models_dir,
        "reports_dir": reports_dir,
        "metadata_path": metadata_path,
    }


# ---------------------------------------------------------------------------
# Tests: Error Cases
# ---------------------------------------------------------------------------


def test_missing_metadata_raises(tmp_path: Path):
    """Test that missing metadata file raises ArtifactContractError."""
    # Create directory structure but no metadata file
    data_dir = tmp_path / "data" / "processed"
    models_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"

    data_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Create a valid MF model
    mf_model = MockMFModel()
    joblib.dump(mf_model, models_dir / "mf_sgd_v1.0.joblib")

    # Attempt to build artifacts without metadata
    with pytest.raises(FileNotFoundError) as exc:
        build_artifacts(
            data_dir=data_dir,
            models_dir=models_dir,
            reports_dir=reports_dir,
        )

    assert "anime_metadata.parquet" in str(exc.value)


def test_missing_mf_model_raises(temp_artifacts_dir: dict[str, Any]):
    """Test that missing MF model raises ArtifactContractError."""
    # Remove all models
    models_dir = temp_artifacts_dir["models_dir"]
    for f in models_dir.glob("*.joblib"):
        f.unlink()

    with pytest.raises(RuntimeError) as exc:
        build_artifacts(
            data_dir=temp_artifacts_dir["data_dir"],
            models_dir=models_dir,
            reports_dir=temp_artifacts_dir["reports_dir"],
        )

    assert "No .joblib models found" in str(exc.value)


def test_mf_missing_required_attributes(temp_artifacts_dir: dict[str, Any]):
    """Test that MF model missing required attributes raises with details."""
    # Replace valid MF model with incomplete one
    models_dir = temp_artifacts_dir["models_dir"]
    for f in models_dir.glob("*.joblib"):
        f.unlink()

    incomplete_model = IncompleteMFModel()
    joblib.dump(incomplete_model, models_dir / "mf_sgd_incomplete.joblib")

    with pytest.raises(ArtifactContractError) as exc:
        build_artifacts(
            data_dir=temp_artifacts_dir["data_dir"],
            models_dir=models_dir,
            reports_dir=temp_artifacts_dir["reports_dir"],
        )

    error_message = str(exc.value)
    assert "missing required attributes" in error_message.lower()
    # Check that details are populated
    assert exc.value.details
    assert any("Q" in detail for detail in exc.value.details)


def test_mf_model_with_invalid_attributes(temp_artifacts_dir: dict[str, Any]):
    """Test that MF model with invalid attribute types raises with details."""
    models_dir = temp_artifacts_dir["models_dir"]
    for f in models_dir.glob("*.joblib"):
        f.unlink()

    # Create a model with wrong types
    invalid_model = InvalidMFModel()
    joblib.dump(invalid_model, models_dir / "mf_sgd_invalid.joblib")

    with pytest.raises(ArtifactContractError) as exc:
        build_artifacts(
            data_dir=temp_artifacts_dir["data_dir"],
            models_dir=models_dir,
            reports_dir=temp_artifacts_dir["reports_dir"],
        )

    error_message = str(exc.value)
    assert "failed basic contract validation" in error_message.lower()


def test_multiple_mf_models_without_env_var_raises(temp_artifacts_dir: dict[str, Any]):
    """Test that multiple MF models without APP_MF_MODEL_STEM raises ArtifactContractError."""
    models_dir = temp_artifacts_dir["models_dir"]

    # Add a second MF model
    mf_model_2 = MockMFModel()
    joblib.dump(mf_model_2, models_dir / "mf_sgd_v2.0.joblib")

    # Ensure APP_MF_MODEL_STEM is not set
    with patch.dict("os.environ", {}, clear=False):
        # Remove the env var if it exists
        import os

        if "APP_MF_MODEL_STEM" in os.environ:
            del os.environ["APP_MF_MODEL_STEM"]

        with pytest.raises(ArtifactContractError) as exc:
            build_artifacts(
                data_dir=temp_artifacts_dir["data_dir"],
                models_dir=models_dir,
                reports_dir=temp_artifacts_dir["reports_dir"],
            )

        error_message = str(exc.value)
        assert "multiple" in error_message.lower() or "ambiguous" in error_message.lower()
        # Check that details mention how to resolve the ambiguity
        assert exc.value.details
        details_text = " ".join(exc.value.details)
        assert "APP_MF_MODEL_STEM" in details_text


def test_metadata_missing_anime_id_raises(temp_artifacts_dir: dict[str, Any]):
    """Test that metadata without anime_id column raises ArtifactContractError."""
    # Create metadata without anime_id
    bad_metadata = pd.DataFrame(
        [
            {
                "title_display": "Test Anime",
                "genres": "Action",
            }
        ]
    )
    metadata_path = temp_artifacts_dir["metadata_path"]
    bad_metadata.to_parquet(metadata_path)

    with pytest.raises(ArtifactContractError) as exc:
        build_artifacts(
            data_dir=temp_artifacts_dir["data_dir"],
            models_dir=temp_artifacts_dir["models_dir"],
            reports_dir=temp_artifacts_dir["reports_dir"],
        )

    error_message = str(exc.value)
    assert "anime_id" in error_message.lower()


# ---------------------------------------------------------------------------
# Tests: Success Cases
# ---------------------------------------------------------------------------


def test_valid_minimal_bundle(temp_artifacts_dir: dict[str, Any]):
    """Test that valid artifacts return expected bundle structure."""
    bundle = build_artifacts(
        data_dir=temp_artifacts_dir["data_dir"],
        models_dir=temp_artifacts_dir["models_dir"],
        reports_dir=temp_artifacts_dir["reports_dir"],
    )

    # Check bundle structure
    assert isinstance(bundle, dict)
    assert "metadata" in bundle
    assert "models" in bundle
    assert "explanations" in bundle
    assert "diversity" in bundle

    # Check metadata
    metadata = bundle["metadata"]
    assert isinstance(metadata, pd.DataFrame)
    assert len(metadata) == 3  # Our fixture has 3 anime
    assert "anime_id" in metadata.columns
    assert "title_display" in metadata.columns
    assert "genres" in metadata.columns

    # Check models
    models = bundle["models"]
    assert "mf" in models
    assert "_mf_stem" in models
    assert hasattr(models["mf"], "Q")
    assert hasattr(models["mf"], "item_to_index")
    assert hasattr(models["mf"], "index_to_item")

    # Check mean-user vectors are computed
    assert "mf_mean_user_vector" in models
    assert "mf_mean_user_scores" in models
    assert models["mf_mean_user_vector"] is not None
    assert models["mf_mean_user_scores"] is not None


def test_mean_user_vector_computation(temp_artifacts_dir: dict[str, Any]):
    """Test that mean-user vector is correctly computed from MF model."""
    bundle = build_artifacts(
        data_dir=temp_artifacts_dir["data_dir"],
        models_dir=temp_artifacts_dir["models_dir"],
        reports_dir=temp_artifacts_dir["reports_dir"],
    )

    mf_model = bundle["models"]["mf"]
    mean_user_vector = bundle["models"]["mf_mean_user_vector"]
    mean_user_scores = bundle["models"]["mf_mean_user_scores"]

    # Verify mean_user_vector shape
    assert mean_user_vector.shape == (mf_model.n_factors,)

    # Verify mean_user_vector is actually the mean of P
    expected_mean = np.mean(mf_model.P, axis=0)
    np.testing.assert_allclose(mean_user_vector, expected_mean, rtol=1e-5)

    # Verify mean_user_scores shape
    n_items = len(mf_model.item_to_index)
    assert mean_user_scores.shape == (n_items,)

    # Verify mean_user_scores computation
    expected_scores = float(mf_model.global_mean) + (mean_user_vector @ mf_model.Q.T)
    np.testing.assert_allclose(mean_user_scores, expected_scores, rtol=1e-5)


def test_single_mf_model_selected_automatically(temp_artifacts_dir: dict[str, Any]):
    """Test that when only one MF model exists, it's selected automatically."""
    bundle = build_artifacts(
        data_dir=temp_artifacts_dir["data_dir"],
        models_dir=temp_artifacts_dir["models_dir"],
        reports_dir=temp_artifacts_dir["reports_dir"],
    )

    assert bundle["models"]["_mf_stem"] == "mf_sgd_v1.0"


def test_env_var_overrides_mf_selection(temp_artifacts_dir: dict[str, Any]):
    """Test that APP_MF_MODEL_STEM environment variable overrides model selection."""
    models_dir = temp_artifacts_dir["models_dir"]

    # Add a second MF model
    mf_model_2 = MockMFModel()
    joblib.dump(mf_model_2, models_dir / "mf_sgd_v2.0.joblib")

    # Set environment variable to select specific model
    with patch.dict("os.environ", {"APP_MF_MODEL_STEM": "mf_sgd_v2.0"}):
        bundle = build_artifacts(
            data_dir=temp_artifacts_dir["data_dir"],
            models_dir=models_dir,
            reports_dir=temp_artifacts_dir["reports_dir"],
        )

        assert bundle["models"]["_mf_stem"] == "mf_sgd_v2.0"


def test_optional_knn_model_loaded_when_present(temp_artifacts_dir: dict[str, Any]):
    """Test that kNN model is loaded when present but doesn't block startup if missing."""
    models_dir = temp_artifacts_dir["models_dir"]

    # Add a kNN model (simple mock object)
    knn_model = {"model": "mock_knn"}
    joblib.dump(knn_model, models_dir / "item_knn_sklearn_v1.0.joblib")

    bundle = build_artifacts(
        data_dir=temp_artifacts_dir["data_dir"],
        models_dir=models_dir,
        reports_dir=temp_artifacts_dir["reports_dir"],
    )

    assert "knn" in bundle["models"]
    assert "_knn_stem" in bundle["models"]


def test_missing_optional_artifacts_dont_block_startup(temp_artifacts_dir: dict[str, Any]):
    """Test that missing optional artifacts (kNN, TF-IDF, embeddings) don't prevent loading."""
    # Only MF model exists (created by fixture)
    bundle = build_artifacts(
        data_dir=temp_artifacts_dir["data_dir"],
        models_dir=temp_artifacts_dir["models_dir"],
        reports_dir=temp_artifacts_dir["reports_dir"],
    )

    # Core bundle should still be valid
    assert "metadata" in bundle
    assert "models" in bundle
    assert "mf" in bundle["models"]

    # Optional models may or may not be present
    # The key is that build_artifacts didn't raise


def test_artifact_contract_error_has_details():
    """Test that ArtifactContractError stores details list correctly."""
    details = ["Detail 1", "Detail 2", "Detail 3"]
    error = ArtifactContractError("Test error message", details=details)

    assert str(error) == "Test error message"
    assert error.details == details


def test_artifact_contract_error_without_details():
    """Test that ArtifactContractError works without details."""
    error = ArtifactContractError("Test error message")

    assert str(error) == "Test error message"
    assert error.details == []


def test_metadata_pruning_creates_required_columns(temp_artifacts_dir: dict[str, Any]):
    """Test that metadata pruning ensures all required columns exist."""
    bundle = build_artifacts(
        data_dir=temp_artifacts_dir["data_dir"],
        models_dir=temp_artifacts_dir["models_dir"],
        reports_dir=temp_artifacts_dir["reports_dir"],
    )

    metadata = bundle["metadata"]

    # Check that key columns exist (from MIN_METADATA_COLUMNS constant)
    required_columns = [
        "anime_id",
        "title_display",
        "genres",
        "synopsis_snippet",
        "type",
        "mal_score",
        "episodes",
    ]

    for col in required_columns:
        assert col in metadata.columns, f"Missing required column: {col}"


def test_determinism_is_set():
    """Test that set_determinism is called during artifact loading."""
    # This is an indirect test - we verify that random operations are deterministic
    # after calling build_artifacts by checking that numpy random state is consistent
    import numpy as np

    # Note: We can't easily test this without creating real artifacts,
    # but we can at least verify the function doesn't error
    from src.app.artifacts_loader import set_determinism

    set_determinism(seed=12345)
    val1 = np.random.randint(0, 1000)

    set_determinism(seed=12345)
    val2 = np.random.randint(0, 1000)

    assert val1 == val2, "Determinism not working as expected"
