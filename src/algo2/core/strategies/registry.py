from __future__ import annotations
import pandas as pd


class _SmaCrossover:
    def __init__(self, fast: int = 5, slow: int = 20):
        self.fast = int(fast)
        self.slow = int(slow)

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        c = out["close"].astype(float)
        out["ma_fast"] = c.rolling(self.fast).mean()
        out["ma_slow"] = c.rolling(self.slow).mean()
        return out

    def generate_signals(self, pre: pd.DataFrame) -> pd.Series:
        sig = (pre["ma_fast"] > pre["ma_slow"]).astype(float)
        return sig.reindex(pre.index).fillna(0.0)


def get_strategy(name: str, **kwargs):
    name = (name or "").lower()
    if name == "sma_crossover":
        return _SmaCrossover(**kwargs)
    raise ValueError(f"unknown strategy: {name}")
