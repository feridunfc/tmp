import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.core.backtest.engine import BacktestEngine, FeesConfig
from src.core.strategies.registry import get_strategy
from src.core.data import normalize_ohlcv

def demo_df(n=400):
    now_utc = datetime.now(timezone.utc)
    idx = pd.date_range(now_utc - timedelta(hours=n), periods=n, freq="h", tz="UTC")
    p = 100 + np.cumsum(np.random.randn(n)) * 0.1
    raw = pd.DataFrame(
        {"Open": p, "High": p+0.2, "Low": p-0.2, "Close": p, "Volume": 1000},
        index=idx
    )
    return normalize_ohlcv(raw)

def test_backtest_engine_runs_end_to_end():
    df = demo_df()
    strat = get_strategy("sma_crossover", fast=5, slow=20)
    pre = strat.prepare(df)
    sig = strat.generate_signals(pre)
    eng = BacktestEngine(FeesConfig(5,10))
    res = eng.run_backtest(pre, sig)
    assert "equity" in res and "metrics" in res
    assert len(res["equity"]) == len(pre)
