from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from strategies.base import Strategy, ensure_ohlcv
from strategies.registry import register_strategy

@dataclass
class ParamSchema:
    window: int = field(default=14, metadata={"low": 5, "high": 50, "step": 1})
    overbought: float = field(default=70.0, metadata={"low": 55.0, "high": 90.0, "step": 1.0})
    oversold: float = field(default=30.0, metadata={"low": 10.0, "high": 45.0, "step": 1.0})

@register_strategy("rb_rsi_threshold")
class RSIThreshold(Strategy):
    """Basit RSI eşik stratejisi: RSI<oversold -> +1, RSI>overbought -> -1."""
    name = "RSI Threshold"
    family = "rule"
    version = "1.0"

    def param_schema(self):
        return ParamSchema

    def prepare(self, df: pd.DataFrame, **params) -> pd.DataFrame:
        df = ensure_ohlcv(df)
        w = int(params.get("window", ParamSchema.window))
        delta = df["Close"].diff()
        up = np.where(delta > 0, delta, 0.0)
        down = np.where(delta < 0, -delta, 0.0)
        roll_up = pd.Series(up, index=df.index).ewm(span=w, adjust=False).mean()
        roll_down = pd.Series(down, index=df.index).ewm(span=w, adjust=False).mean()
        rs = (roll_up / (roll_down + 1e-12)).clip(lower=0)
        rsi = 100 - (100 / (1 + rs))
        df["rsi"] = rsi
        return df

    def generate_signals(self, df: pd.DataFrame, **params) -> pd.Series:
        overbought = float(params.get("overbought", ParamSchema.overbought))
        oversold = float(params.get("oversold", ParamSchema.oversold))
        rsi = df["rsi"]
        sig = pd.Series(0, index=df.index, dtype=int)
        sig[rsi < oversold] = 1
        sig[rsi > overbought] = -1
        # opsiyonel: tekrar eden aynı sinyali azaltmak için sadece değişimleri bırak
        # sig = sig.where(sig != sig.shift(), other=0)
        return sig
