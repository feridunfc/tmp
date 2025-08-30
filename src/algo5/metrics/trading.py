from __future__ import annotations
import pandas as pd

def equity_from_returns(starting_capital: float, returns: pd.Series) -> pd.Series:
    rets = returns.astype(float).fillna(0.0)
    curve = (1.0 + rets).cumprod() * float(starting_capital)
    curve.name = "equity"
    return curve
