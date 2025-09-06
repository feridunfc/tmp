from __future__ import annotations

import json
from dataclasses import dataclass

from algo5.core.observability import structured_log


@dataclass
class DummyEvt:
    x: int
    y: str


def test_structured_log_json_out(capsys):
    evt = DummyEvt(3, "ok")
    line = structured_log(evt, trace_id="abc")
    out, _ = capsys.readouterr()
    parsed = json.loads(line)
    assert parsed["event"] == "DummyEvt"
    assert parsed["trace_id"] == "abc"
    assert parsed["payload"] == {"x": 3, "y": "ok"}
    assert out.strip() == line.strip()
