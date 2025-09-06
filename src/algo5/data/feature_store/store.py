# mypy: disable-error-code=unreachable
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import pickle
import re

import pandas as pd

# ---- module-level cache root (tests bunu kullanıyor) ----
_CACHE_ROOT: Path | None = None


def set_cache_root(path: Path | str) -> None:
    global _CACHE_ROOT
    _CACHE_ROOT = Path(path)
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def _ensure_utc(ts: pd.Timestamp) -> pd.Timestamp:
    if not isinstance(ts, pd.Timestamp):
        ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def _safe_symbol(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


@dataclass
class FeatureStore:
    root: Path | None = None

    def __post_init__(self) -> None:
        # root verilmediyse global cache veya .algo5_store kullan
        base = self.root or _CACHE_ROOT or Path(".algo5_store")
        self.root = Path(base)
        self.root.mkdir(parents=True, exist_ok=True)

        self._data_dir = self.root / "data"  # features (JSON)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._tables_dir = self.root / "tables"  # OHLCV (CSV)
        self._tables_dir.mkdir(parents=True, exist_ok=True)

        self._catalog_path = self.root / "catalog.pkl"
        self._catalog: dict[str, str] = {}
        self._load_catalog()

    # ---------- internal ----------
    def _load_catalog(self) -> None:
        if self._catalog_path.exists():
            with self._catalog_path.open("rb") as f:
                self._catalog = pickle.load(f)
        else:
            self._catalog = {}

    def _save_catalog(self) -> None:
        with self._catalog_path.open("wb") as f:
            pickle.dump(self._catalog, f)

    def _key(self, symbol: str, ts: pd.Timestamp) -> str:
        tsu = _ensure_utc(ts)
        return f"{symbol}:{tsu.isoformat()}"

    def _path_for(self, symbol: str, ts: pd.Timestamp) -> Path:
        tsu = _ensure_utc(ts)
        sym = _safe_symbol(symbol)
        fname = tsu.strftime("%Y%m%dT%H%M%SZ") + ".json"
        return self._data_dir / sym / fname

    # ---------- features (KV) ----------
    def upsert(self, symbol: str, ts: pd.Timestamp, features: dict[str, Any]) -> str:
        payload = json.dumps(features, sort_keys=True, separators=(",", ":")).encode("utf-8")
        checksum = hashlib.sha256(payload).hexdigest()
        key = self._key(symbol, ts)
        path = self._path_for(symbol, ts)
        prev = self._catalog.get(key)

        path.parent.mkdir(parents=True, exist_ok=True)
        if prev == checksum and path.exists():
            return checksum  # idempotent

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                {"symbol": symbol, "ts": _ensure_utc(ts).isoformat(), "features": features},
                f,
                sort_keys=True,
            )
        self._catalog[key] = checksum
        self._save_catalog()
        return checksum

    def read(self, symbol: str, ts: pd.Timestamp) -> dict[str, Any]:
        path = self._path_for(symbol, ts)
        if not path.exists():
            raise FileNotFoundError(path.as_posix())
        with path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        return dict(doc.get("features", {}))

    # ---------- tabular (DataFrame) ----------
    def _table_dir(self, key: str) -> Path:
        return self._tables_dir / _safe_symbol(key)

    def _table_csv(self, key: str) -> Path:
        return self._table_dir(key) / "data.csv"

    def save(self, key: str, df: pd.DataFrame, overwrite: bool = False) -> Path:
        td = self._table_dir(key)
        td.mkdir(parents=True, exist_ok=True)
        path = self._table_csv(key)
        if path.exists() and not overwrite:
            raise FileExistsError(path.as_posix())

        # CSV: bağımlılıksız; index’i yazarız, okurken parse ederiz
        df.to_csv(path, index=True)
        return path

    def load(self, key: str) -> pd.DataFrame:
        path = self._table_csv(key)
        if not path.exists():
            raise FileNotFoundError(path.as_posix())
        out = pd.read_csv(path, index_col=0, parse_dates=True)
        return out


__all__ = ["FeatureStore", "set_cache_root"]
