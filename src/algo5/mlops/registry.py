
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List

REGISTRY_FILE = Path(".mlruns/registry.json")

@dataclass
class ModelMeta:
    name: str
    version: str
    path: str
    checksum: str
    created_ts: float

def _load() -> Dict[str, List[dict]]:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {}

def _save(obj: Dict[str, List[dict]]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def register(meta: ModelMeta) -> None:
    db = _load()
    db.setdefault(meta.name, []).append(asdict(meta))
    _save(db)

def list_models(name: str | None = None) -> Dict[str, List[dict]]:
    db = _load()
    return db if name is None else {name: db.get(name, [])}
