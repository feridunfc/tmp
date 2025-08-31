
import pandas as pd
from src.algo5.data.validate import validate_ohlcv

def test_json_payload_validation_ok():
    payload = {
        "timestamp":["2025-01-01T00:00:00Z","2025-01-01T00:01:00Z"],
        "open":[1,2], "high":[1,2], "low":[1,2], "close":[1,2], "volume":[1,2]
    }
    df = pd.DataFrame(
        {"Open":[1,2], "High":[1,2], "Low":[1,2], "Close":[1,2], "volume":[1,2]},
        index=pd.to_datetime(payload["timestamp"]),
    )
    _, rep = validate_ohlcv(df, json_payload=payload)
    assert rep["ok"] and rep["checksum"]

def test_outlier_fail_threshold():
    df = pd.DataFrame(
        {
            "Open":[1,1,1,1000,1],
            "High":[1,1,1,1000,1],
            "Low":[1,1,1,1000,1],
            "Close":[1,1,1,1000,1],
            "volume":[1,1,1,1,1],
        },
        index=pd.date_range("2025-01-01", periods=5, tz="UTC"),
    )
    _, rep = validate_ohlcv(df, strict_outliers_ratio=0.1)
    assert rep["ok"] is False and rep["fail_reason"] == "too_many_outliers"
