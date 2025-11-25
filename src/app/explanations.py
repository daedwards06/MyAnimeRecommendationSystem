"""Formatting utilities for per-item hybrid contribution explanations."""

from __future__ import annotations

from typing import Dict


def format_explanation(contributions: Dict[str, float]) -> str:
    parts = []
    for key in ("mf", "knn", "pop"):
        val = contributions.get(key, 0.0) * 100.0
        parts.append(f"{key} {val:.1f}%")
    return " | ".join(parts)


__all__ = ["format_explanation"]
