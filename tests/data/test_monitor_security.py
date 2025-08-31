
import pandas as pd
import pytest
from src.algo5.data.quality.monitor import DataQualityMonitor

def test_monitor_safe_write_base_dir(tmp_path):
    df = pd.DataFrame(
        {
            "Open":[1], "High":[1], "Low":[1], "Close":[1], "volume":[1]
        },
        index=pd.date_range("2025-01-01", periods=1, tz="UTC"),
    )
    base = tmp_path / "reports"
    base.mkdir()

    # allowed write inside base_dir
    mon_ok = DataQualityMonitor(out_path=str(base / "dq.json"), base_dir=base)
    rep = mon_ok.run(df)
    assert (base / "dq.json").exists()
    assert rep["checksum"]

    # forbidden: path escape outside base_dir
    outside = tmp_path.parent / "dq.json"
    mon_bad = DataQualityMonitor(out_path=str(outside), base_dir=base)
    with pytest.raises(PermissionError):
        mon_bad.run(df)
