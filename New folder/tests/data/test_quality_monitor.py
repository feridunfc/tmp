
import pytest

mon_mod = pytest.importorskip("algo5.data.quality.monitor")

def test_schema_check_ok(demo_df):
    mon = mon_mod.DataQualityMonitor()
    report = mon.run(demo_df)
    assert "SchemaCheck" in report
    assert report["SchemaCheck"].get("ok") is True

def test_schema_check_missing(demo_df):
    mon = mon_mod.DataQualityMonitor()
    df_bad = demo_df.drop(columns=["Volume"])
    report = mon.run(df_bad)
    assert report["SchemaCheck"].get("ok") is False
    assert "Volume" in set(report["SchemaCheck"].get("missing", []))
