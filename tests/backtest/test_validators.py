import numpy as np
import pandas as pd
import pytest

from algo5.engine.backtest.validators import (
    OHLCVSpec,
    normalize_ohlcv,
    validate_ohlcv,
)


def _make_df(tz="UTC", with_volume=True, n=5):
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz=tz)
    data = {
        "Open": np.arange(n) + 10.0,
        "High": np.arange(n) + 11.0,
        "Low": np.arange(n) + 9.0,
        "Close": np.arange(n) + 10.5,
    }
    if with_volume:
        data["Volume"] = np.arange(n) + 100
    return pd.DataFrame(data, index=idx)


def test_validate_ok_with_volume():
    df = _make_df(with_volume=True)
    validate_ohlcv(df, spec=OHLCVSpec(require_volume=True))


def test_validate_fails_missing_volume():
    df = _make_df(with_volume=False)
    with pytest.raises(ValueError, match="missing"):
        validate_ohlcv(df, spec=OHLCVSpec(require_volume=True))


def test_validate_fails_naive_index_when_required():
    df = _make_df(tz=None)
    with pytest.raises(ValueError, match="timezone"):
        validate_ohlcv(df, spec=OHLCVSpec(require_tz=True))


def test_normalize_localizes_and_casts():
    df = _make_df(tz=None)
    out = normalize_ohlcv(df)
    assert out.index.tz is not None
    assert out.dtypes["Open"].kind in ("f", "i")
