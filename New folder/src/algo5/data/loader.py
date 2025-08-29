import pandas as pd
import numpy as np

def demo_ohlcv(periods: int = 120, start="2024-01-01") -> pd.DataFrame:
    """
    Basit sentetik OHLCV veri üretir.
    Varsayılan 120 bar; testlerde [:100] dilimi için yeterli uzunluk sağlar.
    """
    idx = pd.date_range(start=start, periods=periods, freq="D")
    base = np.linspace(100, 100 + periods - 1, periods, dtype=float)
    close = base.copy()
    open_ = close - 1
    high = close + 1
    low = close - 2
    vol = 1000 + np.arange(periods, dtype=int)
    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )
    return df
