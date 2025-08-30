
from __future__ import annotations
import numpy as np
import pandas as pd

def _trend_pos(close: pd.Series, w: int = 20) -> pd.Series:
    ema = close.ewm(span=w, adjust=False).mean()
    return (close > ema).astype(float)

def _meanrev_pos(close: pd.Series, w: int = 5, thr: float = 0.0) -> pd.Series:
    z = (close - close.rolling(w).mean()) / (close.rolling(w).std(ddof=0) + 1e-12)
    pos = np.where(z < -1.0 - thr, 1.0, np.where(z > 1.0 + thr, 0.0, np.nan))
    return pd.Series(pos, index=close.index).ffill().fillna(0.0)

def regime_aware_position(close: pd.Series, regime: pd.Series) -> pd.Series:
    tr = _trend_pos(close)
    mr = _meanrev_pos(close)
    out = pd.Series(0.0, index=close.index)
    out[regime == 0] = tr[regime == 0]
    out[regime == 1] = 0.0
    out[regime == 2] = (0.5 * mr)[regime == 2]
    return out.clip(0.0, 1.0).fillna(0.0)
