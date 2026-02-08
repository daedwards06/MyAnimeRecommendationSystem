"""Benchmark script to demonstrate the performance improvement of indexed metadata lookups.

This script compares O(N) lookups vs O(1) indexed lookups for metadata access.
"""

import time
import pandas as pd
import numpy as np

def create_sample_metadata(n_items: int = 13000) -> pd.DataFrame:
    """Create sample metadata similar to the real dataset."""
    return pd.DataFrame({
        "anime_id": range(1, n_items + 1),
        "title_display": [f"Anime {i}" for i in range(1, n_items + 1)],
        "genres": [f"Action|Comedy|Drama" for _ in range(n_items)],
        "type": np.random.choice(["TV", "Movie", "OVA"], n_items),
        "aired_from": [f"20{np.random.randint(5, 24):02d}-01-01" for _ in range(n_items)],
        "mal_score": np.random.uniform(5, 9, n_items),
    })

def benchmark_old_method(metadata: pd.DataFrame, anime_ids: list[int], iterations: int = 1) -> float:
    """Benchmark the old O(N) lookup method."""
    start = time.perf_counter()
    for _ in range(iterations):
        for anime_id in anime_ids:
            row_df = metadata.loc[metadata["anime_id"] == anime_id].head(1)
            if not row_df.empty:
                _ = row_df.iloc[0]["genres"]
    end = time.perf_counter()
    return end - start

def benchmark_new_method(metadata: pd.DataFrame, anime_ids: list[int], iterations: int = 1) -> float:
    """Benchmark the new O(1) indexed lookup method."""
    start = time.perf_counter()
    for _ in range(iterations):
        metadata_by_id = metadata.set_index("anime_id", drop=False)
        for anime_id in anime_ids:
            try:
                row = metadata_by_id.loc[anime_id]
                _ = row["genres"]
            except KeyError:
                pass
    end = time.perf_counter()
    return end - start

def main():
    print("=" * 70)
    print("Metadata Lookup Performance Benchmark")
    print("=" * 70)
    
    # Create sample metadata (13K items, similar to real data)
    print("\nCreating sample metadata (13,000 items)...")
    metadata = create_sample_metadata(13000)
    
    # Simulate looking up 30 recommendations (typical result set size)
    anime_ids = np.random.choice(metadata["anime_id"].values, size=30, replace=False).tolist()
    
    print(f"Benchmark: Looking up {len(anime_ids)} items from {len(metadata)} total items")
    print("-" * 70)
    
    # Run benchmarks with multiple iterations for more stable results
    iterations = 100
    
    print(f"\n1. Old Method (O(N) per lookup):")
    print("   metadata.loc[metadata['anime_id'] == id].head(1)")
    old_time = benchmark_old_method(metadata, anime_ids, iterations)
    print(f"   Time: {old_time:.4f}s for {iterations} iterations")
    print(f"   Average per iteration: {old_time/iterations*1000:.2f}ms")
    
    print(f"\n2. New Method (O(1) indexed lookup):")
    print("   metadata_by_id = metadata.set_index('anime_id')")
    print("   metadata_by_id.loc[id]")
    new_time = benchmark_new_method(metadata, anime_ids, iterations)
    print(f"   Time: {new_time:.4f}s for {iterations} iterations")
    print(f"   Average per iteration: {new_time/iterations*1000:.2f}ms")
    
    print("\n" + "=" * 70)
    print(f"SPEEDUP: {old_time/new_time:.1f}x faster")
    print(f"TIME SAVED: {(old_time - new_time)/iterations*1000:.2f}ms per recommendation batch")
    print("=" * 70)
    
    # Calculate theoretical complexity difference
    n_metadata = len(metadata)
    n_lookups = len(anime_ids)
    old_ops = n_metadata * n_lookups  # O(N*M)
    new_ops = n_metadata + n_lookups  # O(N + M) - index creation + lookups
    
    print(f"\nTheoretical complexity:")
    print(f"  Old: O(N×M) = {n_metadata} × {n_lookups} = {old_ops:,} comparisons")
    print(f"  New: O(N+M) = {n_metadata} + {n_lookups} = {new_ops:,} operations")
    print(f"  Theoretical reduction: {old_ops/new_ops:.1f}x fewer operations")
    print("=" * 70)

if __name__ == "__main__":
    main()
