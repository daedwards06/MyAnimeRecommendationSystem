import pandas as pd

df = pd.read_parquet('data/processed/anime_metadata.parquet')

print('Type value counts:')
print(df['type'].value_counts(dropna=False).head(15))
print(f'\nTotal records: {len(df)}')
print(f'Non-null types: {df["type"].notna().sum()}')
print(f'\nSample of Sci-Fi anime types:')
scifi = df[df['genres'].astype(str).str.contains('Sci-Fi', case=False, na=False)]
print(scifi[['anime_id', 'title_display', 'type']].head(10))
