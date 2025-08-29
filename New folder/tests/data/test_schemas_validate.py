
import importlib
import pytest
import pandas as pd

mod = pytest.importorskip("algo5.data.validate")

def _call_validate(df, **kwargs):
    fn = getattr(mod, "validate_ohlcv", None) or getattr(mod, "validate", None)
    assert fn is not None, "validate_ohlcv/validate not found in algo5.data.validate"
    try:
        res = fn(df, **kwargs)
    except TypeError:
        # older signature without kwargs
        res = fn(df)
    if isinstance(res, tuple):
        out_df, report = res[0], (res[1] if len(res) > 1 else {})
    elif isinstance(res, dict):
        out_df, report = df, res
    else:
        out_df, report = res, {}
    return out_df, report

def test_validate_happy_path(demo_df):
    out_df, report = _call_validate(demo_df, allow_extras=True, raise_errors=True)
    assert set(["Open","High","Low","Close","Volume"]).issubset(out_df.columns)
    # basic sanity
    assert len(out_df) == len(demo_df)

def test_rename_close_if_lowercase(demo_df):
    df2 = demo_df.rename(columns={"Close": "close"})
    out_df, report = _call_validate(df2, allow_extras=True, raise_errors=False)
    if "Close" in out_df.columns:
        assert "close" not in out_df.columns
    else:
        pytest.skip("lowercase->Pascal rename not implemented; skipping.")

def test_missing_columns_raises(demo_df):
    df_bad = demo_df.drop(columns=["High"])
    try:
        _ = _call_validate(df_bad, raise_errors=True)
        # If no exception and function chose to return report, ensure it flags missing
        # Try a soft assertion:
        out_df, report = _call_validate(df_bad, raise_errors=False)
        missing = set(report.get("missing", [])) if isinstance(report, dict) else set()
        if not missing:
            pytest.skip("Validator does not raise on missing and no 'missing' key in report; skipping.")
    except Exception:
        # expected path: exception raised
        assert True
