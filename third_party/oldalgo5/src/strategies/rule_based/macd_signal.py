from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd

from strategies.base import Strategy, ensure_ohlcv
from strategies.registry import register_strategy

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=int(n), adjust=False).mean()

@dataclass
class ParamSchema:
    fast: int = field(default=12, metadata={"low": 5, "high": 30, "step": 1})
    slow: int = field(default=26, metadata={"low": 10, "high": 60, "step": 1})
    signal: int = field(default=9, metadata={"low": 3, "high": 20, "step": 1})

@register_strategy("rb_macd")
class MACDSignal(Strategy):
    """MACD vs Signal çizgisi kesişimi: yukarı kesişim +1, aşağı -1."""
    name = "MACD Signal"
    family = "rule"
    version = "1.0"

    def param_schema(self):
        return ParamSchema

    def prepare(self, df: pd.DataFrame, **params) -> pd.DataFrame:
        df = ensure_ohlcv(df)
        f = int(params.get("fast", ParamSchema.fast))
        s = int(params.get("slow", ParamSchema.slow))
        k = int(params.get("signal", ParamSchema.signal))
        close = df["Close"]
        macd = _ema(close, f) - _ema(close, s)
        macd_signal = _ema(macd, k)
        df["macd"] = macd
        df["macd_signal"] = macd_signal
        df["macd_hist"] = macd - macd_signal
        return df

    def generate_signals(self, df: pd.DataFrame, **params) -> pd.Series:
        cross_up = (df["macd"] > df["macd_signal"]) & (df["macd"].shift() <= df["macd_signal"].shift())
        cross_dn = (df["macd"] < df["macd_signal"]) & (df["macd"].shift() >= df["macd_signal"].shift())
        sig = pd.Series(0, index=df.index, dtype=int)
        sig[cross_up] = 1
        sig[cross_dn] = -1
        return sig
