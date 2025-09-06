import json

from algo5.core.observability import structured_log, parse_structured_log


def test_structured_log_shape():
    s = structured_log("unit.test", price=100, meta={"x": 1})
    doc = json.loads(s)
    assert {"ts", "event", "trace_id"} <= set(doc.keys())
    assert doc["event"] == "unit.test"
    assert isinstance(doc["trace_id"], str) and len(doc["trace_id"]) >= 16
    assert doc["price"] == 100
    assert doc["meta"]["x"] == 1


def test_parse_roundtrip():
    s = structured_log("roundtrip", foo="bar")
    doc = parse_structured_log(s)
    assert doc["event"] == "roundtrip"
    assert doc["foo"] == "bar"
