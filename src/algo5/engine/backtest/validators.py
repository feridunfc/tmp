from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def validate_ohlc_monotonic(
    df: pd.DataFrame, required: Iterable[str] = ("open", "high", "low", "close")
) -> bool:
    if df is None or df.empty:
        raise ValueError("validate_ohlc_monotonic: empty df")
    dfl = df.rename(columns=lambda c: str(c).lower()).copy()
    req = set(map(str.lower, required))
    if not req.issubset(dfl.columns):
        missing = req - set(dfl.columns)
        raise ValueError(f"validate_ohlc_monotonic: missing columns: {missing}")

    high_check = dfl["high"] >= dfl[["open", "high", "close"]].max(axis=1)
    low_check = dfl["low"] <= dfl[["open", "low", "close"]].min(axis=1)
    bad = (~high_check) | (~low_check)
    if bool(bad.any()):
        raise AssertionError(f"OHLC monotonicity violated on {int(bad.sum())} rows")
    return True


def enforce_one_bar_delay(series: pd.Series) -> pd.Series:
    """Signal/weight?i 1 bar geciktirir (NaN -> 0.0)."""
    return series.shift(1).fillna(0.0)
