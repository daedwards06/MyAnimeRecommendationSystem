"""Lightweight latency & memory profiling helpers."""

from __future__ import annotations

import logging
import time
import tracemalloc
from collections.abc import Callable
from contextlib import contextmanager
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

_last_timings = {}

@contextmanager
def latency_timer(label: str):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    elapsed_ms = elapsed * 1000
    _last_timings[label] = elapsed
    logger.debug(f"[LATENCY] {label}: {elapsed_ms:.2f} ms")

def get_last_timing():
    """Get the last recorded timings dictionary."""
    return _last_timings.copy()

def profile_memory(func: Callable[..., T]) -> Callable[..., T]:  # type: ignore
    def wrapper(*args, **kwargs):  # type: ignore
        tracemalloc.start()
        start = time.perf_counter()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug(
            f"[PROFILE] {func.__name__} latency={elapsed_ms:.2f}ms current={current/1024:.1f}KB peak={peak/1024:.1f}KB"
        )
        return result
    return wrapper  # type: ignore


__all__ = ["latency_timer", "profile_memory"]
