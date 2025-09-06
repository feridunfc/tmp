from __future__ import annotations

import pandas as pd

from algo5.engine.backtest.validators import enforce_one_bar_delay, validate_ohlc_monotonic


def test_validate_ohlc_monotonic_ok():
    idx = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 14],
            "high": [11, 12, 13, 14, 15],
            "low": [9, 10, 11, 12, 13],
            "close": [10.5, 11.5, 12.5, 13.5, 14.5],
        },
        index=idx,
    )
    assert validate_ohlc_monotonic(df) is True


def test_enforce_one_bar_delay_shifts_and_fills_zero():
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    s = pd.Series([0, 1, 0.5], index=idx, dtype=float)
    out = enforce_one_bar_delay(s)
    assert out.iloc[0] == 0.0
    assert out.iloc[1] == 0.0
    assert out.iloc[2] == 1.0
