from __future__ import annotations
import numpy as np
import pandas as pd

def _pick_price_column(df: pd.DataFrame) -> pd.Series:
    for col in ["close", "Close", "adj_close", "Adj Close", "Adj_Close", "price", "Price"]:
        if col in df.columns:
            return df[col].astype(float)
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not num_cols:
        raise ValueError("anomaly_mask_zscore: no numeric column to infer price")
    return df[num_cols[0]].astype(float)

def anomaly_mask_zscore(df: pd.DataFrame, *, window: int = 20, threshold: float = 3.0) -> pd.Series:
    """
    Rolling z-score ile anomali maskesi üretir (True = anomali).

    - Fiyat getirileri (pct_change) üzerinden hesaplanır.
    - Rolling ortalama ve std ile normalize edilir.
    - |z| >= threshold ise anomali kabul edilir.

    Dönüş: pd.Series(bool) — df.index ile aynı
    """
    if df is None or len(df) == 0:
        return pd.Series([], dtype=bool)
    px = _pick_price_column(df)
    rets = px.pct_change().fillna(0.0)

    mu = rets.rolling(window, min_periods=1).mean()
    sd = rets.rolling(window, min_periods=1).std(ddof=0).replace({0.0: np.nan}).fillna(1e-12)
    z = (rets - mu) / sd
    mask = z.abs() >= float(threshold)
    return pd.Series(mask.values, index=df.index, name="anomaly_zscore")
