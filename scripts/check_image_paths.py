import pandas as pd
from pathlib import Path

df = pd.read_parquet('data/processed/anime_metadata.parquet')

print(f"Total anime: {len(df)}")
print(f"\nColumns in metadata:")
print(df.columns.tolist())

if 'poster_thumb_url' in df.columns:
    print(f"\nAnime with thumbnails: {df['poster_thumb_url'].notna().sum()}")
    print(f"\nSample thumbnail paths:")
    print(df[df['poster_thumb_url'].notna()][['anime_id', 'title_display', 'poster_thumb_url']].head(5))
else:
    print("\n❌ No 'poster_thumb_url' column found!")

# Check if image files exist
images_dir = Path('data/processed/images/posters')
if images_dir.exists():
    thumb_files = list(images_dir.glob('*_thumb.webp'))
    print(f"\n📁 Thumbnail files on disk: {len(thumb_files)}")
    if thumb_files:
        print(f"Sample files: {[f.name for f in thumb_files[:5]]}")
else:
    print(f"\n❌ Images directory doesn't exist: {images_dir}")
