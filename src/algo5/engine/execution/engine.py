# mypy: ignore-errors
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from .metrics import compute_metrics


@dataclass
class TradeCosts:
    commission: float = 0.0
    slippage_bps: float = 1.0


def apply_costs(sig: pd.Series, commission: float, slippage_bps: float) -> pd.Series:
    pos = sig.fillna(0.0)
    trades = pos.diff().abs().fillna(0.0)
    slippage = slippage_bps / 10000.0
    return trades * (commission + slippage)


def backtest_vectorized(df: pd.DataFrame, signal: pd.Series, costs: TradeCosts):
    c = df["close"]
    ret = c.pct_change().fillna(0.0)
    pos = signal.shift(1).fillna(0.0)
    raw = pos * ret
    cost_series = apply_costs(pos, costs.commission, costs.slippage_bps)
    strat_ret = raw - cost_series
    equity = (1 + strat_ret).cumprod()
    stats = compute_metrics(equity, strat_ret)
    return equity, strat_ret, stats


def time_series_splits(n: int, n_splits: int, min_train: int = 60):
    splits = []
    fold_size = (n - min_train) // n_splits if n_splits > 0 else 0
    start = 0
    train_end = min_train
    for _i in range(n_splits):
        test_end = min(n, train_end + fold_size)
        splits.append((slice(start, train_end), slice(train_end, test_end)))
        train_end = test_end
    if splits and splits[-1][1].stop < n:
        splits[-1] = (splits[-1][0], slice(splits[-1][1].start, n))
    return splits


def run_walkforward(
    df: pd.DataFrame,
    train_fn: Callable[[pd.DataFrame], dict],
    infer_fn: Callable[[pd.DataFrame, dict], pd.Series],
    costs: TradeCosts,
    n_splits: int = 5,
    min_train: int = 252,
):
    n = len(df)
    if n < min_train + n_splits:
        raise ValueError("Not enough data for walk-forward")
    folds = time_series_splits(n, n_splits, min_train)
    all_equity = pd.Series(index=df.index, dtype=float)
    all_ret = pd.Series(index=df.index, dtype=float)
    fold_stats = []
    for tr, te in folds:
        train_df = df.iloc[tr]
        test_df = df.iloc[te]
        if train_df.empty or test_df.empty:
            continue
        state = train_fn(train_df)
        sig = infer_fn(test_df, state).reindex(test_df.index).fillna(0.0)
        eq, r, s = backtest_vectorized(test_df, sig, costs)
        all_equity.loc[test_df.index] = eq
        all_ret.loc[test_df.index] = r
        fold_stats.append(s)
    overall_equity = all_equity.ffill().fillna(1.0)
    overall_stats = compute_metrics(overall_equity, all_ret.fillna(0.0))
    return {
        "equity": overall_equity,
        "ret": all_ret.fillna(0.0),
        "fold_stats": fold_stats,
        "overall": overall_stats,
    }
