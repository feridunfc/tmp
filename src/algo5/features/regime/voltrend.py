
from __future__ import annotations
import numpy as np
import pandas as pd

def make_regime_features(df: pd.DataFrame, windows=(5, 10, 20)) -> pd.DataFrame:
    """Builds simple regime-related features from OHLCV.
    Columns: ret, rv_{w}, mom_{w}, zvol
    """
    close = df["Close"].astype(float)
    out = pd.DataFrame(index=df.index)
    ret = close.pct_change().bfill()
    out["ret"] = ret
    for w in windows:
        out[f"rv_{w}"] = (ret.rolling(w).std(ddof=0) * np.sqrt(252)).bfill()
        out[f"mom_{w}"] = (close / close.rolling(w).mean() - 1.0).bfill()
    vol = ret.rolling(20).std(ddof=0)
    out["zvol"] = ((vol - vol.rolling(100).mean()) / (vol.rolling(100).std(ddof=0) + 1e-12)).bfill()
    return out
