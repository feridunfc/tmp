import pytest

from algo5.data.validate import validate_ohlcv


def test_validate_happy_path(demo_df):
    df, rep = validate_ohlcv(demo_df, raise_errors=False)
    assert rep["ok"] and df.equals(demo_df)


def test_rename_close_if_lowercase(demo_df):
    df2, rep = validate_ohlcv(demo_df.rename(columns={"Close": "close"}), raise_errors=False)
    assert rep["renamed"].get("close") == "Close" and "Close" in df2.columns


def test_missing_columns_raises(demo_df):
    bad = demo_df.drop(columns=["Volume"])
    with pytest.raises(ValueError):
        validate_ohlcv(bad, raise_errors=True)
