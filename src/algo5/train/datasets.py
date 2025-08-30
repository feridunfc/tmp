from __future__ import annotations
import pandas as pd
import numpy as np

def make_supervised_ohlcv(df: pd.DataFrame):
    """OHLCV'den basit özellik/etiket: 
    - X: ret1 (% değişim)
    - y: ertesi kapanışın bir önceki kapanıştan büyük olup olmadığı (0/1)
    Index korunur, NaN'lar kırpılır.
    """
    close = df["Close"].astype(float)
    ret1 = close.pct_change()
    X = pd.DataFrame({"ret1": ret1})
    y = (close.shift(-1) > close).astype(int)
    XY = pd.concat([X, y.rename("y")], axis=1).dropna()
    X2 = XY[["ret1"]]
    y2 = XY["y"].to_numpy()
    return X2, y2
