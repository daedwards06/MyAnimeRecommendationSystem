"""Check genre format in metadata."""
import pandas as pd
import sys

df = pd.read_parquet('data/processed/anime_metadata.parquet')
print("Checking genre formats:", flush=True)
print("Total rows:", len(df), flush=True)
print(flush=True)

for i in range(5):
    row = df.iloc[i]
    genres = row['genres']
    print(f"{i}. {row['title_display']}")
    print(f"   Type: {type(genres)}")
    print(f"   Value: {genres}")
    print(f"   Repr: {repr(genres)}")
    
    # Try parsing
    if isinstance(genres, str):
        parsed = set([g.strip() for g in genres.split("|") if g.strip()])
        print(f"   Parsed (string): {parsed}")
    elif hasattr(genres, '__iter__') and not isinstance(genres, str):
        parsed = set([str(g).strip() for g in genres if g])
        print(f"   Parsed (array): {parsed}")
    print()
