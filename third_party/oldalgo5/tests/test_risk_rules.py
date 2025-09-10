import numpy as np
import pandas as pd
from src.core.risk.config import RiskConfig
from src.core.risk.engine import RiskEngine

def test_vol_target_scales_down_when_vol_is_high():
    rets = pd.Series(np.r_[np.random.randn(100)*0.001, np.random.randn(100)*0.05])
    sig = pd.Series(1.0, index=rets.index)
    risk = RiskEngine(RiskConfig(enabled=True, vol_target_pct=15.0, vol_lookback=20, ann_factor=252))
    w = risk.size_positions(rets, sig)
    assert w.iloc[-1] < w.iloc[0]

def test_price_stops_flatten_positions():
    px = pd.Series(100 + np.r_[np.linspace(0, 10, 50), np.linspace(10, -20, 50)])
    strat_ret = px.pct_change().fillna(0)
    risk = RiskEngine(RiskConfig(enabled=True, stop_loss_pct=5.0))
    adj, logs = risk.apply_stops(strat_ret, px)
    assert adj.eq(0).sum() >= 1
