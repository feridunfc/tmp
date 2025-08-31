import pandas as pd
import numpy as np


def demo_ohlcv(*, periods: int = 120, start: str = "2024-01-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=periods, freq="D")
    base = np.arange(periods, dtype=float)
    return pd.DataFrame(
        {
            "Open": 100 + base,
            "High": 101 + base,
            "Low": 99 + base,
            "Close": 100 + base,
            "Volume": 1000 + np.arange(periods, dtype=int),
        },
        index=idx,
    )
