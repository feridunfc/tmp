
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Any, Iterable

# --- cache root handling ---------------------------------------------------
DEFAULT_CACHE_ROOT = Path(".cache") / "features"
_OVERRIDE_ROOT: Path | None = None

def set_cache_root(path: str | os.PathLike[str] | Path) -> Path:
    """
    Set a runtime override for cache root. Tests can call this.
    Env var ALGO5_CACHE_ROOT still has highest priority if set.
    """
    global _OVERRIDE_ROOT
    _OVERRIDE_ROOT = Path(path).resolve()
    return _OVERRIDE_ROOT

def get_cache_root() -> Path:
    env = os.getenv("ALGO5_CACHE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    if _OVERRIDE_ROOT is not None:
        return _OVERRIDE_ROOT
    return DEFAULT_CACHE_ROOT.resolve()

# public helper (and backward compatible alias)
def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

# some code used a private name; keep alias for compat
_ensure_dir = ensure_dir

# --- simple json-based smart cache ----------------------------------------
class SmartCache:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else get_cache_root()
        ensure_dir(self.root)

    def _ns_dir(self, namespace: str) -> Path:
        return ensure_dir(self.root / namespace)

    def _item_path(self, namespace: str, name: str) -> Path:
        return self._ns_dir(namespace) / f"{name}.json"

    def set(self, namespace: str, name: str, value: Any) -> Path:
        path = self._item_path(namespace, name)
        with path.open("w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False)
        return path

    def get(self, namespace: str, name: str) -> Any | None:
        path = self._item_path(namespace, name)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, namespace: str, name: str) -> bool:
        return self._item_path(namespace, name).exists()

    def delete(self, namespace: str, name: str) -> None:
        p = self._item_path(namespace, name)
        if p.exists():
            p.unlink()

    def list_namespaces(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted([p.name for p in self.root.iterdir() if p.is_dir()])

    def list_items(self, namespace: str) -> list[str]:
        d = self._ns_dir(namespace)
        if not d.exists():
            return []
        items: set[str] = set()
        for p in d.iterdir():
            if p.suffix in {".json", ".parquet"}:
                items.add(p.stem)
        return sorted(items)
