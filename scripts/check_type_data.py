import pandas as pd

df = pd.read_parquet('data/processed/anime_metadata.parquet')

print(f"Total anime: {len(df)}")
print(f"\n'type' column exists: {'type' in df.columns}")

if 'type' in df.columns:
    print(f"\nAnime with type data: {df['type'].notna().sum()}")
    print(f"Anime without type: {df['type'].isna().sum()}")
    
    print(f"\nType distribution:")
    print(df['type'].value_counts())
    
    # Test a few specific anime
    print(f"\nSample anime with types:")
    sample = df[df['type'].notna()][['anime_id', 'title_display', 'type']].head(10)
    print(sample)
    
    # Check Tokyo Ghoul
    tg = df[df['title_display'].str.contains('Tokyo Ghoul', case=False, na=False)]
    if not tg.empty:
        print(f"\nTokyo Ghoul types:")
        print(tg[['anime_id', 'title_display', 'type']])
else:
    print("\n❌ 'type' column not found in metadata!")
