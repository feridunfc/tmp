from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any
from pathlib import Path
import json

CATALOG = Path(".cache/features/catalog.json")
CATALOG.parent.mkdir(parents=True, exist_ok=True)
if not CATALOG.exists():
    CATALOG.write_text("{}")

@dataclass
class Entry:
    dataset_id: str
    description: str
    rows: int

def register(entry: Entry) -> None:
    db = json.loads(CATALOG.read_text())
    db[entry.dataset_id] = asdict(entry)
    CATALOG.write_text(json.dumps(db, indent=2, sort_keys=True))

def list_entries() -> Dict[str, Any]:
    return json.loads(CATALOG.read_text())
