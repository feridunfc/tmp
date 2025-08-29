from __future__ import annotations
import numpy as np
import pandas as pd

def demo_ohlcv(*, periods: int = 120, start: str = "2024-01-01", freq: str = "D") -> pd.DataFrame:
    idx = pd.date_range(start, periods=periods, freq=freq)
    base = np.arange(periods, dtype=float)
    df = pd.DataFrame({
        "Open": 100 + base,
        "High": 101 + base,
        "Low":  99 + base,
        "Close":100 + base,
        "Volume": 1000 + np.arange(periods, dtype=int),
    }, index=idx)
    return df
