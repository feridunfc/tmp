from __future__ import annotations
import os, json
from pathlib import Path
from typing import Any
CACHE_ROOT = Path(os.getenv("ALGO5_CACHE_ROOT", ".cache/smart"))
def _ns_dir(namespace: str) -> Path:
    d = CACHE_ROOT / namespace; d.mkdir(parents=True, exist_ok=True); return d
def set(namespace: str, key: str, obj: Any) -> Path:
    d = _ns_dir(namespace); path = d / f"{key}.json"
    with path.open("w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False)
    return path
def get(namespace: str, key: str) -> Any:
    path = CACHE_ROOT / namespace / f"{key}.json"
    if not path.exists(): raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f: return json.load(f)
