from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import pandas as pd


class FeatureStore:
    """
    Basit dosya tabanlı feature store.
    - root: cache kök dizini (varsayılan: $ALGO5_CACHE_ROOT veya '.cache/features')
    - format: 'parquet' (şimdilik tek format)
    - namespace: opsiyonel alt klasör; aynı store içinde mantıksal ayrım sağlar
    Anahtar eşleme kuralları:
      * key = "ns/name"  -> root/ns/name.parquet
      * key = ("ns","name") -> root/ns/name.parquet
      * key = "name" ve namespace="raw" -> root/raw/name.parquet
      * key = "name" ve namespace=None  -> root/name.parquet
    """

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        format: str = "parquet",
        namespace: str | None = None,
    ) -> None:
        if root is None:
            root = os.getenv("ALGO5_CACHE_ROOT", ".cache/features")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.format = format
        self.namespace = namespace

    # --- public API (geriye dönük: save/write/put ve load/read/get)
    def save(self, key: str | Tuple[str, str], df: pd.DataFrame, *, overwrite: bool = True) -> Path:
        path = self._path_for(key)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Feature exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)
        return path

    write = save
    put = save

    def load(self, key: str | Tuple[str, str]) -> pd.DataFrame:
        path = self._path_for(key)
        return pd.read_parquet(path)

    read = load
    get = load

    # --- internals
    def _path_for(self, key: str | Tuple[str, str]) -> Path:
        ns: str | None
        name: str

        if isinstance(key, tuple):
            ns, name = key
        elif isinstance(key, str) and "/" in key:
            # "ns/name[/alt/...]" destekle
            parts = key.split("/")
            ns = parts[0] or self.namespace
            name = "/".join(parts[1:]) if len(parts) > 1 else "feature"
        else:
            ns = self.namespace
            name = key if isinstance(key, str) else str(key)

        base = self.root / ns if ns else self.root
        # .parquet uzantısını garanti et
        fname = name if str(name).endswith(".parquet") else f"{name}.parquet"
        return base / fname
