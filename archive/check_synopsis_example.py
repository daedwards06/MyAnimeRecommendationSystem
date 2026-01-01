import pandas as pd

df = pd.read_parquet('data/processed/anime_metadata.parquet')

# Check what synopsis columns exist
synopsis_cols = [c for c in df.columns if 'synop' in c.lower()]
print(f"Available synopsis columns: {synopsis_cols}\n")

# Get one example anime (one that has data)
for idx in range(min(5, len(df))):
    row = df.iloc[idx]
    title = row.get('title_display') or row.get('title_english') or row.get('title')
    print(f"=== Example {idx+1}: {title} ===")
    
    for col in synopsis_cols:
        val = row.get(col)
        if val is not None and str(val) != 'nan':
            print(f"\n{col}:")
            print(f"  Type: {type(val).__name__}")
            print(f"  Length: {len(str(val))}")
            print(f"  Content: {str(val)[:300]}...")
        else:
            print(f"\n{col}: [None/NaN]")
    
    print("\n" + "="*80 + "\n")
    
    # Just show first non-empty one
    if any(row.get(col) is not None and str(row.get(col)) != 'nan' for col in synopsis_cols):
        break
