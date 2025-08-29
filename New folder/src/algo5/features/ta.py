from __future__ import annotations
import pandas as pd

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(int(n), min_periods=int(n)).mean()

def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=int(span), adjust=False).mean()

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = -diff.clip(upper=0.0)
    rs = gain.rolling(period).mean() / (loss.rolling(period).mean() + 1e-12)
    return 100 - (100 / (1 + rs))

def build_ta_v1(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"].astype(float)
    for n in spec.get("sma", []):
        col = f"SMA_{int(n)}"
        if col not in df.columns:
            df[col] = sma(close, int(n))
    for n in spec.get("ema", []):
        col = f"EMA_{int(n)}"
        if col not in df.columns:
            df[col] = ema(close, int(n))
    for n in spec.get("rsi", []):
        col = f"RSI_{int(n)}"
        if col not in df.columns:
            df[col] = rsi(close, int(n))
    return df
