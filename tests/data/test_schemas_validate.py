from algo5.data.validate import validate_ohlcv

def test_validate_happy_path(demo_df):
    df2, rep = validate_ohlcv(demo_df)
    assert rep["ok"]
    assert set(rep["missing"]) == set()

def test_rename_close_if_lowercase(demo_df):
    df = demo_df.rename(columns={"Close": "close"})
    out, rep = validate_ohlcv(df, raise_errors=False)
    assert rep["renamed"]["close"] == "Close"

def test_missing_columns_raises(demo_df):
    df = demo_df.drop(columns=["Volume"])  # required
    try:
        validate_ohlcv(df, raise_errors=True)
    except ValueError:
        assert True
    else:
        assert False, "should raise"
