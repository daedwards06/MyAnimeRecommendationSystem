import json
from pathlib import Path

import pandas as pd


def summarize(path: Path):
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        return {"file": str(path), "error": str(e)}
    dtypes = {k: str(v) for k, v in df.dtypes.items()}
    nulls = {k: int(v) for k, v in df.isna().sum().items()}
    return {
        "file": str(path),
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "dtypes": dtypes,
        "null_counts": nulls,
    }


def main():
    files = [
        Path("data/processed/anime_metadata.parquet"),
        Path("data/processed/anime_metadata_202511_full.parquet"),
    ]
    out = [summarize(p) for p in files if p.exists()]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
