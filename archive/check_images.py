import pandas as pd
from pathlib import Path

df = pd.read_parquet('data/processed/anime_metadata.parquet')
base = Path('data/processed')

total = len(df)
has_url = df['poster_thumb_url'].notna().sum()
missing = 0
found = 0

for url in df['poster_thumb_url'].dropna()[:100]:
    path = base / url
    if path.exists():
        found += 1
    else:
        missing += 1
        if missing <= 5:
            print(f"Missing: {path}")

print(f'\nTotal anime: {total}')
print(f'Has URL: {has_url}')
print(f'Sample check (100): Found={found}, Missing={missing}')
