from __future__ import annotations

import pandas as pd
import numpy as np


def demo_ohlcv(periods: int = 120) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=periods, freq="D")
    base = 100.0 + np.arange(periods, dtype=float)
    df = pd.DataFrame(
        {
            "Open": base,
            "High": base + 1.0,
            "Low": base - 1.0,
            "Close": base,
            "Volume": 1000 + np.arange(periods, dtype=int),
        },
        index=idx,
    )
    return df
