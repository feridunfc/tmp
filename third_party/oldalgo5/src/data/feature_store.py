from __future__ import annotations
from pathlib import Path
from typing import Callable, Dict, Optional
import hashlib
import pandas as pd

class ParquetFeatureStore:
    """
    Basit, Parquet tabanlı feature store.
    Anahtar: symbol, timeframe, feature_version, start_end_hash
    """
    def __init__(self, storage_dir: str = "feature_store"):
        self.root = Path(storage_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash_index(df: pd.DataFrame) -> str:
        if df.index.size == 0:
            return "empty"
        first = str(df.index[0])
        last = str(df.index[-1])
        raw = f"{first}|{last}|{len(df)}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _path(self, symbol: str, timeframe: str, version: str, idx_hash: str) -> Path:
        fn = f"{symbol}_{timeframe}_v{version}_{idx_hash}.parquet"
        d = self.root / symbol / timeframe / f"v{version}"
        d.mkdir(parents=True, exist_ok=True)
        return d / fn

    def get_or_build(
        self,
        base_df: pd.DataFrame,
        *,
        symbol: str,
        timeframe: str,
        feature_version: str,
        spec: Dict,
        build_fn: Callable[[pd.DataFrame, Dict], pd.DataFrame],
        force_rebuild: bool = False,
    ) -> pd.DataFrame:
        idx_hash = self._hash_index(base_df)
        p = self._path(symbol, timeframe, feature_version, idx_hash)
        if p.exists() and not force_rebuild:
            return pd.read_parquet(p)
        features = build_fn(base_df, spec)
        features.to_parquet(p, index=True)
        return features
