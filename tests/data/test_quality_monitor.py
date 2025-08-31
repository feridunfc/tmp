from algo5.data.quality.monitor import DataQualityMonitor


def test_schema_check_ok(demo_df):
    rep = DataQualityMonitor().run(demo_df)
    assert rep["ok"] and "checksum" in rep
