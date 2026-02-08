from __future__ import annotations

from pathlib import Path
from typing import Any

from joblib import dump, load


def save_model(model: Any, name: str, version: str = "1.0", models_dir: Path = Path("models")) -> Path:
    """Save a model artifact with versioned naming convention."""
    path = models_dir / f"{name}_v{version}.joblib"
    models_dir.mkdir(parents=True, exist_ok=True)
    dump(model, path)
    return path


def load_model(name: str, version: str = "1.0", models_dir: Path = Path("models")) -> Any:
    """Load a versioned model artifact."""
    path = models_dir / f"{name}_v{version}.joblib"
    if not path.exists():
        raise FileNotFoundError(path)
    return load(path)
