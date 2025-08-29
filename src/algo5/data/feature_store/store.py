
from __future__ import annotations
from pathlib import Path
from typing import Tuple
import pandas as pd
from .cache import get_cache_root, ensure_dir

class FeatureStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else get_cache_root()
        ensure_dir(self.root)

    def _path_for(self, key: str | Tuple[str, str]) -> Path:
        if isinstance(key, tuple):
            namespace, name = key
        else:
            # "ns/name" or just "name"
            parts = key.split("/", 1)
            if len(parts) == 2:
                namespace, name = parts
            else:
                namespace, name = "default", parts[0]
        return self.root / namespace / f"{name}.parquet"

    def save(self, key: str | Tuple[str, str], df: pd.DataFrame, *, overwrite: bool = False) -> Path:
        path = self._path_for(key)
        ensure_dir(path.parent)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Feature exists: {path}")
        df.to_parquet(path)
        return path

    # compat aliases for tests
    write = save
    put = save

    def load(self, key: str | Tuple[str, str]) -> pd.DataFrame:
        path = self._path_for(key)
        return pd.read_parquet(path)
