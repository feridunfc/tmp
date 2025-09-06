from __future__ import annotations
from typing import Dict
import numpy as np
import pandas as pd


def compute_nav(returns: pd.Series) -> pd.Series:
    """Getiri serisinden (r_t) NAV serisi (1.0 bazlı) üretir."""
    rets: pd.Series = returns.astype(float).fillna(0.0)
    cum: pd.Series = (1.0 + rets).cumprod()
    return cum


def compute_metrics(nav: pd.Series) -> Dict[str, float]:
    """NAV serisinden temel metrikleri hesaplar."""
    nav = nav.astype(float)
    rets: pd.Series = nav.pct_change().dropna()
    vol: float = float(rets.std() * np.sqrt(252)) if len(rets) else 0.0
    sharpe: float = (
        float((rets.mean() / rets.std()) * np.sqrt(252)) if len(rets) and rets.std() > 0 else 0.0
    )
    rollmax: pd.Series = nav.expanding().max()
    mdd: float = float(((nav - rollmax) / rollmax).min()) if len(nav) else 0.0
    total_return: float = float(nav.iloc[-1] / nav.iloc[0] - 1.0) if len(nav) else 0.0
    return {"sharpe": sharpe, "max_drawdown": mdd, "total_return": total_return, "vol": vol}
