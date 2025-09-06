"""
Utility helpers for backtest engine.
"""

import pandas as pd


def compute_returns(equity_series):
    s = pd.Series(equity_series).astype(float)
    return s.pct_change().fillna(0.0)


def resample_ohlc(df, rule="1D"):
    return (
        df.resample(rule)
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )
