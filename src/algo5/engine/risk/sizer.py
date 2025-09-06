from __future__ import annotations
import pandas as pd


class Sizer:
    def size(self, returns: pd.Series, signal: pd.Series) -> pd.Series:
        return signal.astype(float).clip(0.0, 1.0)
