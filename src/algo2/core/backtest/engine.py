from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from algo5.metrics.metrics import compute_nav
from algo2.core.risk.engine import RiskEngine


@dataclass(slots=True)
class FeesConfig:
    bps: float = 0.0
    per_trade: float = 0.0


class BacktestEngine:
    def __init__(self, fees: FeesConfig | None = None, risk_engine: RiskEngine | None = None):
        self.fees = fees or FeesConfig()
        self.risk = risk_engine

    def run_backtest(self, pre: pd.DataFrame, signal: pd.Series) -> dict:
        rets = pre["close"].astype(float).pct_change().fillna(0.0)
        w = signal.reindex(pre.index).fillna(0.0).clip(0.0, 1.0)
        if self.risk is not None:
            w = self.risk.size_positions(rets, w)
            # fiyat tabanlı stoplar
            adj, _ = self.risk.apply_stops(rets, pre["close"].astype(float))
            w = (w * adj).clip(0.0, 1.0)
        pnl = w * rets  # basit model: ağırlık * getiri
        nav = compute_nav(pnl)
        return {"equity": nav, "returns": pnl}
