"""Quick repair script to backfill poster_thumb_url from existing files."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

PROCESSED_PATH = Path("data/processed/anime_metadata.parquet")
IMAGES_DIR = Path("data/processed/images/posters")

# Load metadata
df = pd.read_parquet(PROCESSED_PATH)
print(f"Loaded {len(df)} anime records")

# Find all thumbnail files
thumb_files = list(IMAGES_DIR.glob("*_thumb.webp"))
print(f"Found {len(thumb_files)} thumbnail files")

# Before count
before = df["poster_thumb_url"].notna().sum() if "poster_thumb_url" in df.columns else 0
print(f"Before repair: {before} records with poster_thumb_url")

# Ensure columns exist
for col in ["poster_thumb_url", "image_last_fetched", "image_attribution", "image_md5"]:
    if col not in df.columns:
        df[col] = None

# Update metadata for each thumbnail
updated = 0
df_indexed = df.set_index("anime_id")

for tf in thumb_files:
    stem = tf.name.replace("_thumb.webp", "")
    if not stem.isdigit():
        continue
    aid = int(stem)
    
    if aid not in df_indexed.index:
        print(f"Skipping {aid} - not in metadata")
        continue
    
    # Set relative path
    rel_path = tf.relative_to(PROCESSED_PATH.parent).as_posix()
    df_indexed.at[aid, "poster_thumb_url"] = rel_path
    
    # Set attribution if missing
    if pd.isna(df_indexed.at[aid, "image_attribution"]):
        df_indexed.at[aid, "image_attribution"] = "Images via Jikan / MyAnimeList"
    
    # Set last fetched from file mtime
    try:
        mtime = datetime.fromtimestamp(tf.stat().st_mtime, tz=timezone.utc).isoformat()
        df_indexed.at[aid, "image_last_fetched"] = mtime
    except Exception:
        pass
    
    updated += 1
    if updated % 1000 == 0:
        print(f"Processed {updated} thumbnails...")

# Convert back and save
df_repaired = df_indexed.reset_index()
after = df_repaired["poster_thumb_url"].notna().sum()

print(f"\nAfter repair: {after} records with poster_thumb_url")
print(f"Updated: {updated} records")
print(f"Net gain: {after - before}")

# Save
df_repaired.to_parquet(PROCESSED_PATH, index=False)
print(f"Saved to {PROCESSED_PATH}")
