from algo5.data.quality.monitor import DataQualityMonitor, SchemaCheck

def test_schema_check_ok(demo_df):
    rep = DataQualityMonitor([SchemaCheck()]).run(demo_df)
    assert rep["SchemaCheck"]["ok"]

def test_schema_check_missing(demo_df):
    rep = DataQualityMonitor([SchemaCheck()]).run(demo_df.drop(columns=["Volume"]))
    assert rep["SchemaCheck"]["ok"] is False
