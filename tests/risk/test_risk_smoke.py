from __future__ import annotations
import numpy as np
import pandas as pd
from algo5.core.risk import RiskEngine, RiskConfig


def test_sl_triggers_and_closes():
    idx = pd.date_range("2024-01-01", periods=200, freq="H", tz="UTC")
    price = pd.Series(np.r_[np.linspace(100, 110, 100), np.linspace(110, 90, 100)], index=idx)
    rets = price.pct_change().fillna(0.0)
    signal = pd.Series(1.0, index=idx)

    risk = RiskEngine(RiskConfig(enabled=True, stop_loss_pct=5.0, vol_target_pct=None))
    w = risk.size_positions(rets, signal)
    adj, logs = risk.apply_stops(rets, price)

    assert (w >= 0.0).all() and (w <= 1.0).all()
    assert adj.min() == 0.0  # drawdown %5 görünce sıfırlanmış olmalı
    assert any(log.get("type") == "stop_triggered" for log in logs)
