from __future__ import annotations
from pathlib import Path
from typing import Tuple, Union
import pandas as pd

Key = Union[str, Tuple[str, str]]


class FeatureStore:
    def __init__(self, root: Path | str | None = None):
        from .cache import DEFAULT_CACHE_ROOT, _ensure_dir

        self.root = Path(root) if root else DEFAULT_CACHE_ROOT
        _ensure_dir(self.root)

    def _path_for(self, key: Key, *, prefer: str | None = None) -> Path:
        if isinstance(key, str):
            ns, name = key.split("/", 1)
        else:
            ns, name = key
        d = self.root / ns
        d.mkdir(parents=True, exist_ok=True)
        ext = prefer or ".parquet"
        return d / f"{name}{ext}"

    def _has_pyarrow(self) -> bool:
        try:
            import pyarrow  # noqa: F401

            return True
        except Exception:
            return False

    def save(self, key: Key, df: pd.DataFrame, *, overwrite: bool = False) -> Path:
        if self._has_pyarrow():
            path = self._path_for(key, prefer=".parquet")
            if path.exists() and not overwrite:
                raise FileExistsError(f"Feature exists: {path}")
            df.to_parquet(path)
            return path
        # fallback to CSV for environments without parquet engine
        path = self._path_for(key, prefer=".csv")
        if path.exists() and not overwrite:
            raise FileExistsError(f"Feature exists: {path}")
        df.to_csv(path)
        return path

    def load(self, key: Key) -> pd.DataFrame:
        # prefer parquet, else csv
        p_parq = self._path_for(key, prefer=".parquet")
        if p_parq.exists():
            return pd.read_parquet(p_parq)
        p_csv = self._path_for(key, prefer=".csv")
        if p_csv.exists():
            return pd.read_csv(p_csv, index_col=0, parse_dates=True)
        raise FileNotFoundError(f"No stored feature for key {key}")
