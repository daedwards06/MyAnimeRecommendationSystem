"""
Inspect MF model structure to understand factor matrices
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib

from src.models.constants import MF_MODEL_STEM, MODELS_DIR

model_path = MODELS_DIR / f"{MF_MODEL_STEM}.joblib"
model = joblib.load(model_path)

print("=" * 60)
print("MF MODEL STRUCTURE")
print("=" * 60)

print(f"\nModel type: {type(model)}")
print(f"\nModel attributes: {dir(model)}")

if hasattr(model, '__dict__'):
    print(f"\nModel __dict__ keys: {model.__dict__.keys()}")
    
    for key, value in model.__dict__.items():
        if hasattr(value, 'shape'):
            print(f"\n{key}: shape={value.shape}, dtype={value.dtype}")
        else:
            print(f"\n{key}: {type(value)}")

print("\n" + "=" * 60)
