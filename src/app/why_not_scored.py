"""Deterministic exclusion reason labels for seed-based ranked diagnostics.

This module centralizes the strings used for the Phase 5 "why not scored"
reporting so the app and evaluation harness can share a consistent vocabulary.
"""

from __future__ import annotations

# Required breakdown buckets (Phase 5)
NOT_IN_STAGE1_SHORTLIST = "not_in_stage1_shortlist"
BLOCKED_LOW_SEMANTIC_SIM = "blocked_low_semantic_sim"
BLOCKED_LOW_OVERLAP = "blocked_low_overlap"
BLOCKED_OTHER_ADMISSION = "blocked_other_admission"
MISSING_SEMANTIC_VECTOR = "missing_semantic_vector"
DROPPED_BY_QUALITY_FILTERS = "dropped_by_quality_filters"
SCORED = "scored"


REASONS_ORDERED = [
    NOT_IN_STAGE1_SHORTLIST,
    BLOCKED_LOW_SEMANTIC_SIM,
    BLOCKED_LOW_OVERLAP,
    BLOCKED_OTHER_ADMISSION,
    MISSING_SEMANTIC_VECTOR,
    DROPPED_BY_QUALITY_FILTERS,
    SCORED,
]


__all__ = [
    "BLOCKED_LOW_OVERLAP",
    "BLOCKED_LOW_SEMANTIC_SIM",
    "BLOCKED_OTHER_ADMISSION",
    "DROPPED_BY_QUALITY_FILTERS",
    "MISSING_SEMANTIC_VECTOR",
    "NOT_IN_STAGE1_SHORTLIST",
    "REASONS_ORDERED",
    "SCORED",
]
