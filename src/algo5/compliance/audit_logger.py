from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json
class AuditLogger:
    def __init__(self, path: str | Path = ".reports/audit.log"):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def log_event(self, event_type: str, user: str, details: dict):
        rec = {"ts": datetime.utcnow().isoformat(timespec="seconds")+"Z","event_type":event_type,"user":user,"details":details}
        with self.path.open("a", encoding="utf-8") as f: f.write(json.dumps(rec)+"\n")
        return rec
