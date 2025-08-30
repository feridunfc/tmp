from __future__ import annotations
import numpy as np
import pandas as pd

def _mask_extreme(returns: pd.Series, k: int, pick_best: bool) -> pd.Series:
    if k <= 0 or returns.empty:
        return returns.copy()
    # argsort ascending; best (largest) at tail
    order = np.argsort(returns.values)
    idx = order[-k:] if pick_best else order[:k]
    mask = np.ones(len(returns), dtype=bool)
    mask[idx] = False
    return returns[mask]

def remove_best_k_days(returns: pd.Series, k: int = 5) -> pd.Series:
    """Drop the top-k positive return days (stress loss of best sessions)."""
    return _mask_extreme(returns, k=int(k), pick_best=True)

def remove_worst_k_days(returns: pd.Series, k: int = 5) -> pd.Series:
    """Drop the top-k negative return days (optimistic stress)."""
    return _mask_extreme(returns, k=int(k), pick_best=False)
