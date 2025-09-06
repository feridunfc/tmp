import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CACHE_ROOT = Path(os.getenv("ALGO5_CACHE_ROOT", ".cache/features"))
DEFAULT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def set_cache_root(path: str | os.PathLike[str]):
    global DEFAULT_CACHE_ROOT
    DEFAULT_CACHE_ROOT = Path(path)
    DEFAULT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CACHE_ROOT


def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


class SmartCache:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else DEFAULT_CACHE_ROOT
        _ensure_dir(self.root)

    def _ns_dir(self, namespace: str) -> Path:
        d = self.root / namespace
        _ensure_dir(d)
        return d

    def _key_path(self, namespace: str, key: str) -> Path:
        return self._ns_dir(namespace) / f"{key}.json"

    def set(self, namespace: str, key: str, value: Any):
        p = self._key_path(namespace, key)
        p.write_text(json.dumps(value), encoding="utf-8")
        return p

    def get(self, namespace: str, key: str) -> Any | None:
        p = self._key_path(namespace, key)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
