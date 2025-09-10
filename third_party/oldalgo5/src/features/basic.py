
import pandas as pd
import numpy as np

def _sma(s, n):
    return s.rolling(int(n), min_periods=max(2, int(n)//2)).mean()

def _ema(s, n):
    return s.ewm(span=int(n), adjust=False, min_periods=max(2, int(n)//2)).mean()

def _rsi(prices, n=14):
    delta = prices.diff()
    up = (delta.clip(lower=0)).ewm(alpha=1/n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / (down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def make_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    px = df["Close"].astype(float)
    out = pd.DataFrame(index=df.index)
    out["ret1"] = px.pct_change().fillna(0.0)
    out["sma_fast"] = _sma(px, 10)
    out["sma_slow"] = _sma(px, 30)
    out["ema_fast"] = _ema(px, 12)
    out["ema_slow"] = _ema(px, 26)
    out["rsi"] = _rsi(px, 14)
    out["vol"] = px.pct_change().rolling(20, min_periods=10).std().bfill().fillna(0.0)
    out["zret20"] = (out["ret1"] - out["ret1"].rolling(20, min_periods=10).mean()) / (out["ret1"].rolling(20, min_periods=10).std() + 1e-9)
    out["ret"] = out["ret1"]
    return out.ffill().bfill()

def bbands(px: pd.Series, n=20, k=2.0):
    m = px.rolling(n, min_periods=n//2).mean()
    s = px.rolling(n, min_periods=n//2).std()
    upper = m + k*s
    lower = m - k*s
    return m, upper, lower

def macd(px: pd.Series, fast=12, slow=26, signal=9):
    macd = px.ewm(span=fast, adjust=False).mean() - px.ewm(span=slow, adjust=False).mean()
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist

def atr(df: pd.DataFrame, n=14):
    high, low, close = df["High"], df["Low"], df["Close"]
    tr1 = (high - low).abs()
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n//2).mean().ffill()
