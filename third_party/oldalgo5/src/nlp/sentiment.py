from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd

def _pick_price_column(df: pd.DataFrame) -> pd.Series:
    # Common price columns by preference
    for col in ["close", "Close", "adj_close", "Adj Close", "Adj_Close", "price", "Price"]:
        if col in df.columns:
            return df[col].astype(float)
    # fallback: first numeric column
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not num_cols:
        raise ValueError("compute_sentiment_scores: no numeric column to infer price")
    return df[num_cols[0]].astype(float)

def compute_sentiment_scores(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Basit, veri-sızıntısız (lookback-only) *sentiment proxy*.

    - Fiyat getirilerinden (pct_change) bir momentum/vol proxy'si türetir.
    - Rolling ortalama ve stdev ile normalize eder, ardından tanh ile [-1,1] aralığına sıkıştırır.
    - Çıktı: df.index ile aynı uzunlukta, NaN içermez, adı 'sentiment_score'.

    Parametreler
    -----------
    df : DataFrame
        Fiyat kolonlarını içeren veri çerçevesi (Close/close vb.)
    window : int
        Rolling pencere boyutu (varsayılan 20).

    Dönüş
    -----
    pd.Series (float): sentiment_score in [-1, 1]
    """
    if df is None or len(df) == 0:
        return pd.Series([], dtype=float, name="sentiment_score")

    px = _pick_price_column(df)
    rets = px.pct_change().fillna(0.0)

    mean = rets.rolling(window, min_periods=1).mean()
    std = rets.rolling(window, min_periods=1).std(ddof=0).replace({0.0: np.nan}).fillna(1e-12)

    z = (rets - mean) / std
    s = np.tanh(z)  # bound to (-1,1)
    out = pd.Series(s, index=df.index, name="sentiment_score").fillna(0.0)
    # guard bounds (numeric stability)
    out = out.clip(-1.0, 1.0)
    return out
