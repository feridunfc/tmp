from __future__ import annotations
import json
import uuid
from dataclasses import asdict, is_dataclass
from typing import Any


def structured_log(event: Any, trace_id: str | None = None) -> str:
    # Dataclass **instance** ise asdict; class tipinde ise __dict__ veya boş nesne
    if is_dataclass(event) and not isinstance(event, type):
        payload = asdict(event)
    else:
        payload = getattr(event, "__dict__", {}) or {}

    doc = {
        "event": event.__class__.__name__,
        "trace_id": trace_id or uuid.uuid4().hex,
        "payload": payload,
    }
    line = json.dumps(doc, ensure_ascii=False)
    print(line)
    return line
