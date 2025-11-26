import pandas as pd

df = pd.read_parquet('data/processed/metadata_enriched.parquet')

print(f"Total anime: {len(df)}")
print(f"\nType column exists: {'type' in df.columns}")

if 'type' in df.columns:
    print("\nType value counts:")
    print(df['type'].value_counts())
    print(f"\nSample TV shows:")
    print(df[df['type'] == 'TV'][['anime_id', 'title_display', 'type']].head(3))
    print(f"\nSample Movies:")
    print(df[df['type'] == 'Movie'][['anime_id', 'title_display', 'type']].head(3))
else:
    print("\nNo 'type' column found in metadata")
    print("\nAvailable columns:")
    print(df.columns.tolist())
