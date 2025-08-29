import pandas as pd
from algo5.data.validate import validate_ohlcv

def test_validate_happy_path(demo_df):
    df, rep = validate_ohlcv(demo_df, raise_errors=True)
    assert rep["ok"] is True

def test_rename_close_if_lowercase(demo_df):
    df2 = demo_df.rename(columns={"Close":"close"})
    df3, rep = validate_ohlcv(df2, raise_errors=True)
    assert "close" in rep["renamed"] and rep["renamed"]["close"] == "Close"

def test_missing_columns_raises(demo_df):
    df2 = demo_df.drop(columns=["Volume"])
    try:
        validate_ohlcv(df2, raise_errors=True)
        raise AssertionError("should raise")
    except ValueError as e:
        assert "Missing required columns" in str(e)
