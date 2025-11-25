"""Lightweight latency & memory profiling helpers."""

from __future__ import annotations

import time
import tracemalloc
from contextlib import contextmanager
from typing import Callable, TypeVar

T = TypeVar("T")


@contextmanager
def latency_timer(label: str):
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[LATENCY] {label}: {elapsed_ms:.2f} ms")


def profile_memory(func: Callable[..., T]) -> Callable[..., T]:  # type: ignore
    def wrapper(*args, **kwargs):  # type: ignore
        tracemalloc.start()
        start = time.perf_counter()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(
            f"[PROFILE] {func.__name__} latency={elapsed_ms:.2f}ms current={current/1024:.1f}KB peak={peak/1024:.1f}KB"
        )
        return result
    return wrapper  # type: ignore


__all__ = ["latency_timer", "profile_memory"]
