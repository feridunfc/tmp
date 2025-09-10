import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.core.strategies.registry import list_strategies, get_strategy
from src.core.data import normalize_ohlcv

def demo_df(n=200):
    now_utc = datetime.now(timezone.utc)
    idx = pd.date_range(now_utc - timedelta(hours=n), periods=n, freq="h", tz="UTC")
    p = 100 + np.cumsum(np.random.randn(n))*0.2
    raw = pd.DataFrame({"Open":p,"High":p+0.1,"Low":p-0.1,"Close":p,"Volume":1000}, index=idx)
    return normalize_ohlcv(raw)

def test_registry_and_strategy_interface():
    assert "sma_crossover" in list_strategies()
    strat = get_strategy("sma_crossover", fast=5, slow=20)
    df = demo_df()
    pre = strat.prepare(df)
    sig = strat.generate_signals(pre)
    assert len(sig) == len(pre)
