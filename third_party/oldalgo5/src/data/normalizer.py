
from __future__ import annotations
import pandas as pd, numpy as np

REQUIRED = ["open","high","low","close","volume"]

def normalize_ohlcv(raw: pd.DataFrame, auto_adjust: bool=True) -> pd.DataFrame:
    df = raw.copy()
    # sütunları lowercase + boşluk→_
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

    # yfinance: adj_close → close (auto_adjust=True ise)
    if auto_adjust:
        if "adj_close" in df.columns:
            df["close"] = df["adj_close"]
        # eski isim varyantı:
        if "adj close" in raw.columns and "close" in raw.columns:
            ratio = raw["Adj Close"] / raw["Close"]
            for c in ("open","high","low","close"):
                if c in df.columns:
                    df[c] = df[c] * ratio.values

    # index datetime + UTC
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # kolon yoksa hata
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"normalize_ohlcv: missing columns {missing}")

    # sırala & sadece gerekli kolonları ver
    df = df.sort_index()
    return df[REQUIRED]
