# src/algo5/data/feature_store/cache.py
from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pandas as pd

CACHE_ROOT = Path(os.getenv("ALGO5_CACHE_ROOT", ".cache/features"))
CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def df_checksum(df: pd.DataFrame) -> str:
    # indeks dahil stabil checksum
    h = pd.util.hash_pandas_object(df, index=True).values
    return hashlib.md5(h).hexdigest()


def key_for(name: str, checksum: str) -> str:
    return f"{name}-{checksum[:12]}"


def path_for(key: str) -> Path:
    return CACHE_ROOT / f"{key}.parquet"


def meta_for(key: str) -> Path:
    return CACHE_ROOT / f"{key}.meta.json"


def write_df(df: pd.DataFrame, key: str) -> Path:
    p = path_for(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p)
    meta: Dict[str, Any] = {
        "key": key,
        "rows": int(len(df)),
        "cols": list(map(str, df.columns)),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "path": str(p),
    }
    meta_for(key).write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return p


def exists(key: str) -> bool:
    return path_for(key).exists()


def read_df(key: str) -> pd.DataFrame:
    return pd.read_parquet(path_for(key))
