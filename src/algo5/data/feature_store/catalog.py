from __future__ import annotations
from typing import List
from . import cache as _cache


def list_namespaces() -> List[str]:
    root = _cache.DEFAULT_CACHE_ROOT
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def list_items(namespace: str) -> List[str]:
    root = _cache.DEFAULT_CACHE_ROOT / namespace
    if not root.exists():
        return []
    return sorted(
        [p.stem for p in root.iterdir() if p.suffix in {".json", ".parquet", ".csv"}]
    )
