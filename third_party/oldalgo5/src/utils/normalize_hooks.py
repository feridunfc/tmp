
# -*- coding: utf-8 -*-
"""Runtime patch helpers to normalize OHLCV at entry points (v2.10)."""
from __future__ import annotations
from typing import Any, Callable
from functools import wraps
from utils.data import normalize_ohlcv
from core.backtest.engine import BacktestEngine

try:
    from utils.data import normalize_ohlcv
except Exception:
    # fallback: identity
    def normalize_ohlcv(df): return df

def _wrap_first_arg(normalizer: Callable):
    def decorator(func):
        @wraps(func)
        def wrapper(self, df, *args, **kwargs):
            try:
                df = normalizer(df)
            except Exception:
                pass
            return func(self, df, *args, **kwargs)
        return wrapper
    return decorator

def patch_engine_and_strategies() -> None:
    """Monkey-patch BacktestEngine.run_backtest / run_walkforward to normalize df.
    Safe: if imports or attributes fail, it silently no-ops.
    """
    try:
        from core.backtest.engine import BacktestEngine
    except Exception:
        return

    # Patch run_backtest
    try:
        if hasattr(BacktestEngine, "run_backtest"):
            orig = BacktestEngine.run_backtest
            BacktestEngine.run_backtest = _wrap_first_arg(normalize_ohlcv)(orig)
    except Exception:
        pass

    # Patch run_walkforward (first arg expected to be df)
    try:
        if hasattr(BacktestEngine, "run_walkforward"):
            orig_wf = BacktestEngine.run_walkforward
            BacktestEngine.run_walkforward = _wrap_first_arg(normalize_ohlcv)(orig_wf)
    except Exception:
        pass
