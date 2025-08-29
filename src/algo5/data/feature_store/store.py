from __future__ import annotations
from pathlib import Path
import os
import pandas as pd

class FeatureStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.getenv("ALGO5_FEATURE_ROOT", ".cache/features")).resolve()

    def _path_for(self, key: str, *, ext: str = ".parquet") -> Path:
        rel = Path(key + ext)
        return (self.root / rel).resolve()

    def save(self, key: str, df: pd.DataFrame, *, overwrite: bool = True):
        # try parquet first, else pickle fallback
        path = self._path_for(key, ext=".parquet")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Feature exists: {path}")
        try:
            df.to_parquet(path)
            return path
        except Exception:
            # fallback
            pkl = self._path_for(key, ext=".pkl")
            df.to_pickle(pkl)
            return pkl

    write = save
    put = save

    def read(self, key: str) -> pd.DataFrame:
        pq = self._path_for(key, ext=".parquet")
        if pq.exists():
            return pd.read_parquet(pq)
        pkl = self._path_for(key, ext=".pkl")
        if pkl.exists():
            return pd.read_pickle(pkl)
        raise FileNotFoundError(f"No feature found for key '{key}' under {self.root}")
