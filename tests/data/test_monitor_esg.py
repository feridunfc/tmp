
import pandas as pd
from src.algo5.data.quality.monitor import DataQualityMonitor

def test_monitor_esg_and_report_fields(tmp_path):
    # 1000 rows → ~40 g ESG proxy (based on validator's simple model)
    idx = pd.date_range("2025-01-01", periods=1000, freq="min", tz="UTC")
    df = pd.DataFrame(
        {
            "Open":[1]*1000,
            "High":[2]*1000,
            "Low":[0.5]*1000,
            "Close":[1.5]*1000,
            "volume":[1]*1000,
        },
        index=idx,
    )
    out_file = tmp_path / "dq_report.json"
    mon = DataQualityMonitor(out_path=str(out_file), base_dir=tmp_path)
    rep = mon.run(df)

    assert "co2e_per_tick" in rep and rep["co2e_per_tick"] > 0
    assert "checksum" in rep and rep["checksum"]
    assert "stats" in rep and rep["stats"]["rows"] == 1000
    assert out_file.exists()
