from __future__ import annotations
import numpy as np
import pandas as pd

def _to_series(x) -> pd.Series:
    if isinstance(x, pd.Series):
        return x.astype(float)
    if isinstance(x, pd.DataFrame):
        return x.squeeze().astype(float)
    return pd.Series(np.asarray(x, dtype=float))

def sharpe(returns, risk_free: float = 0.0, periods: int = 252) -> float:
    r = _to_series(returns).fillna(0.0)
    adj = risk_free / float(periods)
    excess = r - adj
    std = excess.std(ddof=0)
    if std == 0 or np.isnan(std):
        return 0.0
    return (excess.mean() * np.sqrt(periods)) / std

def max_drawdown(equity, *, mode: str = "end") -> float:
    """
    Drawdown hesaplaması.
    mode:
      - 'end'  : SON değerdeki drawdown (testlerin beklediği)
      - 'peak' : seri boyunca en kötü (peak->trough) drawdown
    """
    eq = _to_series(equity)
    running_max = eq.cummax()
    dd = (eq / running_max) - 1.0
    if mode == "peak":
        return float(dd.min())
    return float(dd.iloc[-1])
