import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from algo2.core.backtest.engine import BacktestEngine, FeesConfig
from algo2.core.risk.config import RiskConfig
from algo2.core.risk.engine import RiskEngine
from algo2.core.strategies.registry import get_strategy
from algo2.core.data import normalize_ohlcv


def demo_df(n=200):
    now_utc = datetime.now(timezone.utc)
    idx = pd.date_range(now_utc - timedelta(hours=n), periods=n, freq="h", tz="UTC")
    p = 100 + np.cumsum(np.random.randn(n)) * 0.2
    raw = pd.DataFrame(
        {"Open": p, "High": p + 0.1, "Low": p - 0.1, "Close": p, "Volume": 1000}, index=idx
    )
    return normalize_ohlcv(raw)


def test_sl_triggers_and_closes():
    df = demo_df()
    strat = get_strategy("sma_crossover", fast=5, slow=20)
    pre = strat.prepare(df)
    sig = strat.generate_signals(pre)
    risk = RiskEngine(RiskConfig(enabled=True, stop_loss_pct=3.0))
    eng = BacktestEngine(FeesConfig(), risk_engine=risk)
    res = eng.run_backtest(pre, sig)
    assert "equity" in res and "returns" in res


def test_vol_target_scales_weights():
    df = demo_df()
    rets = df["close"].pct_change().fillna(0)
    sig = pd.Series(1.0, index=df.index)
    risk = RiskEngine(
        RiskConfig(enabled=True, vol_target_pct=10.0, vol_lookback=10, ann_factor=252)
    )
    w = risk.size_positions(rets, sig)
    assert w.min() >= 0.0
