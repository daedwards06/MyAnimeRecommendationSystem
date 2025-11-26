import pandas as pd

df = pd.read_parquet('data/processed/anime_metadata.parquet')
cols = [c for c in df.columns if 'synop' in c.lower()]
print(f'Synopsis columns: {cols}')

if 'synopsis' in df.columns:
    sample = df["synopsis"].dropna().iloc[0]
    print(f'Full synopsis length: {len(str(sample))}')
    print(f'First 200 chars: {str(sample)[:200]}')

if 'synopsis_snippet' in df.columns:
    sample_snippet = df["synopsis_snippet"].dropna().iloc[0]
    print(f'\nSnippet length: {len(str(sample_snippet))}')
    print(f'First 200 chars: {str(sample_snippet)[:200]}')
