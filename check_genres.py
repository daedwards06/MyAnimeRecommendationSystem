import pandas as pd

df = pd.read_parquet('data/processed/anime_metadata.parquet')
print(f'Genres column exists: {"genres" in df.columns}')
if "genres" in df.columns:
    print(f'Total rows: {len(df)}')
    print(f'Non-null genres: {df["genres"].notna().sum()}')
    print(f'Sample genres (first 5 non-null):')
    for i, genre in enumerate(df["genres"].dropna().head(5)):
        print(f'  {i+1}. {genre} (type: {type(genre).__name__})')
    
    # Try extracting all unique genres
    all_genres = set()
    for genres_str in df["genres"].dropna():
        if isinstance(genres_str, str):
            all_genres.update([g.strip() for g in genres_str.split("|") if g.strip()])
    print(f'\nTotal unique genres found: {len(all_genres)}')
    if len(all_genres) > 0:
        print(f'Sample genres: {sorted(list(all_genres))[:10]}')
    else:
        print('No genres extracted!')
