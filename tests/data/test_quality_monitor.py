from __future__ import annotations

from algo5.data.quality.monitor import DataQualityMonitor


def test_schema_check_ok(demo_df):
    rep = DataQualityMonitor().run(demo_df)
    assert rep["ok"]
    assert "checksum" in rep


def test_schema_check_missing(demo_df):
    bad = demo_df.drop(columns=["volume"])
    rep = DataQualityMonitor().run(bad)
    assert rep["ok"] is False
    assert "volume" in rep["SchemaCheck"]["missing"]
