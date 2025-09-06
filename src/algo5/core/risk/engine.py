from __future__ import annotations

from math import sqrt

import numpy as np
import pandas as pd

from .config import RiskConfig


class RiskEngine:
    def __init__(self, cfg: RiskConfig | None = None):
        self.cfg = cfg or RiskConfig()

    def size_positions(self, returns: pd.Series, signal: pd.Series) -> pd.Series:
        idx = returns.index
        w = signal.astype(float).reindex(idx).fillna(0.0).clip(0.0, 1.0)

        if not self.cfg.enabled:
            return w
        target_pct = self.cfg.vol_target_pct
        if not target_pct or target_pct <= 0:
            return w

        rets = returns.astype(float).fillna(0.0)
        lookback = max(2, int(self.cfg.vol_lookback))
        vol = rets.ewm(span=lookback, adjust=False).std(bias=False)  # EWMA std
        ann_vol = vol * sqrt(float(self.cfg.ann_factor))

        scale = (target_pct / 100.0) / ann_vol.replace(0.0, np.nan)  # 0’a bölme koruması
        scale = scale.clip(upper=1.0).fillna(1.0)

        sized = (w * scale).clip(0.0, 1.0).reindex(idx)
        return sized

    def apply_stops(
        self, strategy_returns: pd.Series, price: pd.Series
    ) -> tuple[pd.Series, list[dict]]:
        logs: list[dict] = []
        sl = self.cfg.stop_loss_pct
        idx = price.index
        if not (self.cfg.enabled and sl and sl > 0):
            return pd.Series(1.0, index=idx), logs

        px = price.astype(float)
        roll_max = px.cummax()
        dd = px / roll_max - 1.0
        thr = -float(sl) / 100.0

        adj = pd.Series(1.0, index=idx)
        adj.loc[dd <= thr] = 0.0

        if (adj == 0.0).any():
            logs.append({"type": "stop_triggered", "count": int((adj == 0.0).sum())})
        return adj, logs
