from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from algo5.metrics.metrics import compute_metrics, compute_nav

StrategyFn = Callable[[dict[str, pd.DataFrame], dict], dict[str, pd.Series]]


def _clip_align(series: pd.Series, ref_index: pd.Index) -> pd.Series:
    s = series.astype(float).reindex(ref_index).ffill().fillna(0.0)
    return s.clip(lower=0.0, upper=1.0)


def run_vector_backtest(
    prices: dict[str, pd.DataFrame],
    strategy_fn: StrategyFn,
    cfg: dict | None = None,
    initial_capital: float = 100_000.0,
    freq: str = "D",
) -> dict[str, Any]:
    """
    Basit portföy backtest:
    - strategy_fn(prices,cfg) -> {symbol: exposure_series(0..1)}
    - her symbol için r_t = close.pct_change
    - portföy getirisi: ortalama(exposure * r_t) (eşit ağırlık basit yaklaşım)
    - NAV -> metrikler
    """
    cfg = cfg or {}
    if not prices:
        return {"metrics": {}, "portfolio_equity": pd.Series(dtype=float)}

    # Referans indeks: ilk sembolün close indeksini al
    first_df = next(iter(prices.values()))
    ref_index = first_df.index

    # Getiriler
    rets_per_symbol: dict[str, pd.Series] = {}
    for sym, df in prices.items():
        if "close" not in df.columns:
            raise ValueError(f"{sym}: 'close' kolonu yok")
        rets_per_symbol[sym] = df["close"].astype(float).pct_change().reindex(ref_index).fillna(0.0)

    # Strateji exposure'ları
    exposures = strategy_fn(prices, cfg)  # {sym: Series (0..1)}
    if not exposures:
        # Hiç exposure yoksa 0 getiri
        portfolio_rets = pd.Series(0.0, index=ref_index, dtype=float)
    else:
        aligned = []
        for sym, exp in exposures.items():
            if sym in rets_per_symbol:
                e = _clip_align(exp, ref_index)
                aligned.append(e * rets_per_symbol[sym])
        if aligned:
            # eşit ağırlık ortalaması
            stacked = np.vstack([a.to_numpy(dtype=float) for a in aligned])
            portfolio_rets = pd.Series(stacked.mean(axis=0), index=ref_index, dtype=float)
        else:
            portfolio_rets = pd.Series(0.0, index=ref_index, dtype=float)

    nav = compute_nav(portfolio_rets)  # 1.0 bazlı
    portfolio_equity = nav * float(initial_capital)
    metrics = compute_metrics(portfolio_equity)  # equity üzerinden de çalışır

    return {
        "metrics": metrics,
        "portfolio_equity": portfolio_equity,
        "portfolio_returns": portfolio_rets,
    }
