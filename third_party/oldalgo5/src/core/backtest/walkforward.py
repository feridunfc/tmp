from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from typing import Dict, Any, Iterable, Tuple, List
import json

from utils.exceptions import StrategyValidationError, DataIntegrityError

def _validate_df(df: pd.DataFrame) -> None:
    req = {"Close"}
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise DataIntegrityError(f"Missing columns: {missing}")
    if df["Close"].isna().any():
        raise DataIntegrityError("Close has NaNs. Please clean data.")

def _param_grid(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Very small grid from schema (lo..lo+4*step) and domain guards (e.g., fast<slow)."""
    # Build list of candidate values
    cand = {}
    for p, s in schema.items():
        t = s.get("type")
        if t == "int":
            lo = int(s.get("min", 2)); step = int(max(1, s.get("step", 1)))
            hi = int(s.get("max", lo + step * 4))
            hi = min(hi, lo + step * 4)  # small local grid
            cand[p] = list(range(lo, hi + 1, step))
        elif t == "float":
            lo = float(s.get("min", 0.1)); step = float(s.get("step", 0.1))
            cand[p] = [lo + i * step for i in range(5)]
        else:
            # pass-through default
            cand[p] = [s.get("default")]
    # Cartesian
    keys = list(cand.keys())
    vals = [cand[k] for k in keys]
    grid: List[Dict[str, Any]] = []
    def rec(i: int, cur: Dict[str, Any]):
        if i == len(keys):
            # Guards
            if "fast" in cur and "slow" in cur:
                if not (int(cur["fast"]) < int(cur["slow"])):
                    return
            grid.append(cur.copy())
            return
        k = keys[i]
        for v in vals[i]:
            cur[k] = v
            rec(i+1, cur)
    rec(0, {})
    if not grid:
        raise StrategyValidationError("Parameter grid is empty after applying guards (e.g., fast < slow).")
    return grid

def _safe_series(x: pd.Series) -> pd.Series:
    return x.ffill().bfill()

def run_walkforward(strategy_cls, df: pd.DataFrame, schema: Dict[str, Any], *, n_splits: int = 5,
                    backtest_fn, commission: float, slippage: float, capital: float) -> pd.DataFrame:
    """Walk-forward with tiny param grid derived from schema; pick best on train and evaluate on test."""
    _validate_df(df)
    grid = _param_grid(schema)
    close = _safe_series(df["Close"])
    # Time series split
    tscv = TimeSeriesSplit(n_splits=n_splits)
    rows = []
    idx = close.index
    for fold, (tr, te) in enumerate(tscv.split(close), start=1):
        train_idx = idx[tr]; test_idx = idx[te]
        train_df = df.loc[train_idx]
        test_df = df.loc[test_idx]
        best = None
        best_sharpe = -1e9
        # Find best on train
        for params in grid:
            sig = strategy_cls.generate_signals(train_df, params)  # pyright: ignore
            eq, pos, metrics, _ = backtest_fn(train_df, sig,
                                              commission=commission, slippage=slippage, capital=capital)
            sharpe = float(metrics.get("Sharpe", 0.0)) if isinstance(metrics, dict) else float(metrics["Sharpe"].mean())
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best = params
        if best is None:
            raise StrategyValidationError("No viable parameter set produced trades on training fold.")
        # Evaluate on test
        sig_te = strategy_cls.generate_signals(test_df, best)
        eq, pos, met, _ = backtest_fn(test_df, sig_te,
                                      commission=commission, slippage=slippage, capital=capital)
        # Normalize metrics
        if isinstance(met, dict):
            m = met
        else:
            # data frame row/series
            m = {k: float(np.nanmean(v)) for k, v in met.items()}
        rows.append({
            "Fold": fold,
            "TrainStart": str(train_idx[0]),
            "TrainEnd": str(train_idx[-1]),
            "TestStart": str(test_idx[0]),
            "TestEnd": str(test_idx[-1]),
            "Trades": int(m.get("Trades", m.get("N", 0))),
            "Sharpe": float(m.get("Sharpe", 0.0)),
            "CAGR": float(m.get("CAGR", m.get("AnnReturn", 0.0))),
            "MaxDD": float(m.get("MaxDD", 0.0)),
            "AnnReturn": float(m.get("AnnReturn", m.get("CAGR", 0.0))),
            "EquityEnd": float(eq.iloc[-1]) if hasattr(eq, "iloc") else float(eq[-1]),
            "BestParams": json.dumps(best),
        })
    return pd.DataFrame(rows)
