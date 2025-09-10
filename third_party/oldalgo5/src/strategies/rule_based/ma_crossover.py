import pandas as pd
import numpy as np
from strategies.registry import Field

NAME = "MA Crossover"

class MACrossover:
    family = "rule_based"
    name = NAME

    @staticmethod
    def param_schema():
        return [
            Field(name="fast", type="int", default=10, low=2, high=100),
            Field(name="slow", type="int", default=30, low=5, high=300),
            Field(name="signal_on_cross", type="bool", default=True),
        ]

    @staticmethod
    def prepare(df: pd.DataFrame, **params) -> pd.DataFrame:
        fast = int(params.get("fast", 10))
        slow = int(params.get("slow", 30))
        close = df["Close"] if "Close" in df.columns else df["close"]
        df = df.copy()
        df["sma_fast"] = close.rolling(fast, min_periods=fast).mean()
        df["sma_slow"] = close.rolling(slow, min_periods=slow).mean()
        return df

    @staticmethod
    def generate_signals(df: pd.DataFrame, **params) -> pd.Series:
        sign_on_cross = bool(params.get("signal_on_cross", True))
        f = df["sma_fast"]
        s = df["sma_slow"]
        base = np.where(f > s, 1, np.where(f < s, -1, 0))
        if sign_on_cross:
            prev = pd.Series(base).shift(1).fillna(0).values
            sig = np.where((base == 1) & (prev <= 0),  1,
                  np.where((base == -1) & (prev >= 0), -1, 0))
        else:
            sig = base
        return pd.Series(sig, index=df.index, name="signal")

# --- module-level backward compat (registry modül fonksiyonlarını da okuyabiliyor) ---
def param_schema(): return MACrossover.param_schema()
def prepare(df, **params): return MACrossover.prepare(df, **params)
def generate_signals(df, **params): return MACrossover.generate_signals(df, **params)
