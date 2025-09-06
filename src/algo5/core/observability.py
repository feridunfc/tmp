from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, cast


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_normalize(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _normalize(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        try:
            return _normalize(vars(obj))
        except Exception:
            pass
    return str(obj)


def structured_log(event: str, trace_id: str | None = None, **fields: Any) -> str:
    payload: dict[str, Any] = {
        "ts": _iso_now(),
        "event": str(event),
        "trace_id": trace_id or uuid.uuid4().hex,
        **{k: _normalize(v) for k, v in fields.items()},
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def parse_structured_log(s: str) -> dict[str, Any]:
    doc = json.loads(s)
    if not isinstance(doc, dict):
        raise TypeError("structured log payload must be a JSON object")
    return cast(dict[str, Any], doc)


__all__ = ["structured_log", "parse_structured_log"]
