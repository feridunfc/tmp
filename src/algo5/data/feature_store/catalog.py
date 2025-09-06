from __future__ import annotations

from . import cache as _cache


def list_namespaces() -> list[str]:
    root = _cache.DEFAULT_CACHE_ROOT
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def list_items(namespace: str) -> list[str]:
    root = _cache.DEFAULT_CACHE_ROOT / namespace
    if not root.exists():
        return []
    return sorted([p.stem for p in root.iterdir() if p.suffix in {".json", ".parquet", ".csv"}])
