from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import pandas as pd

CACHE_ROOT = Path(os.getenv("ALGO5_CACHE_ROOT", ".cache/features"))

def _key(dataset_id: str, feature_spec: dict) -> str:
    payload = json.dumps({"dataset": dataset_id, "spec": feature_spec}, sort_keys=True)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()

def path_for(dataset_id: str, feature_spec: dict) -> Path:
    p = CACHE_ROOT / dataset_id / f"{_key(dataset_id, feature_spec)}.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def exists(dataset_id: str, feature_spec: dict) -> bool:
    return path_for(dataset_id, feature_spec).exists()

def save(dataset_id: str, feature_spec: dict, df: pd.DataFrame) -> str:
    p = path_for(dataset_id, feature_spec)
    df.to_parquet(p)
    return str(p)

def load(dataset_id: str, feature_spec: dict) -> pd.DataFrame:
    return pd.read_parquet(path_for(dataset_id, feature_spec))
