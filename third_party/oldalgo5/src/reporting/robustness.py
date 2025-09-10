# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple, Union
import numpy as np
import pandas as pd

def _to_series(x) -> pd.Series:
    if isinstance(x, pd.Series):
        return x
    if isinstance(x, pd.DataFrame):
        return x.iloc[:, 0]
    arr = np.array(x)
    idx = pd.RangeIndex(len(arr))
    return pd.Series(arr, index=idx)

def _block_bootstrap(r: pd.Series, n: int = 1000, block: int = 1) -> Dict[str, np.ndarray]:
    r = pd.to_numeric(_to_series(r), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if r.empty:
        return {"sharpe": np.array([]), "maxdd": np.array([])}

    r = r.values
    T = len(r)
    block = max(1, int(block))
    sims_sh, sims_dd = [], []

    for _ in range(int(n)):
        out = []
        i = 0
        while i < T:
            j = np.random.randint(0, max(1, T - block + 1))
            out.extend(r[j:j+block])
            i += block
        out = np.array(out[:T], dtype=float)

        mu = np.nanmean(out)
        sigma = np.nanstd(out, ddof=1)
        sharpe = (mu / (sigma + 1e-12)) * np.sqrt(252.0)
        eq = (1.0 + out).cumprod()
        peak = np.maximum.accumulate(eq)
        dd = np.nanmax((peak - eq) / peak) if eq.size else np.nan

        sims_sh.append(sharpe)
        sims_dd.append(dd)

    return {"sharpe": np.array(sims_sh), "maxdd": np.array(sims_dd)}

def monte_carlo_bootstrap(returns, n_sims: int | None = None, n: int | None = None, block: int = 1) -> Dict[str, np.ndarray]:
    """Geriye dönük uyumluluk: hem n_sims hem n param adını kabul eder."""
    sims = int(n_sims if n_sims is not None else (n if n is not None else 1000))
    return _block_bootstrap(returns, n=sims, block=block)

def worst_k_days(returns, k_pct: Union[float, int] | None = None, k: Union[float, int] | None = None) -> Tuple[pd.Index, float]:
    """En kötü k% günün toplam etkisini döndürür (r toplamı).
    Geriye dönük: k_pct veya k kabul eder. k 1-100 arası yüzdelik gibi ele alınır.
    """
    r = pd.to_numeric(_to_series(returns), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if r.empty:
        return r.index, 0.0
    frac = k_pct if k_pct is not None else k
    frac = float(frac if frac is not None else 5.0)
    if frac > 1.0:
        frac = frac / 100.0
    frac = min(max(frac, 0.0), 1.0)
    m = max(1, int(np.floor(len(r) * frac)))
    worst = r.sort_values().iloc[:m]
    effect = float(worst.sum())
    return worst.index, effect
