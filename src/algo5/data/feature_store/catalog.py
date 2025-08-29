
from __future__ import annotations
from pathlib import Path
from .cache import get_cache_root, ensure_dir

def list_namespaces() -> list[str]:
    root = get_cache_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])

def list_items(namespace: str) -> list[str]:
    d = get_cache_root() / namespace
    if not d.exists():
        return []
    out: set[str] = set()
    for p in d.iterdir():
        if p.suffix in {".json", ".parquet"}:
            out.add(p.stem)
    return sorted(out)
