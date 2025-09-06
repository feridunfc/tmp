from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import List, Tuple

import numpy as np
import pandas as pd


@dataclass
class RiskConfig:
    enabled: bool = True
    # None -> kapalı anlamına gelsin; sayıya çevrilebilen her şey kabul
    vol_target_pct: float | None = 15.0
    vol_lookback: int | None = 20
    ann_factor: int | None = 252
    stop_loss_pct: float | None = None


def _as_float(x, default: float) -> float:
    try:
        return float(x) if x is not None else float(default)
    except Exception:
        return float(default)


class RiskEngine:
    def __init__(self, cfg: RiskConfig | None = None):
        self.cfg = cfg or RiskConfig()

    def size_positions(self, returns: pd.Series, signal: pd.Series) -> pd.Series:
        """
        Volatility targeting (EWMA):
        - NaN üretmeden ilk bardan itibaren tanımlı kılar
        - Düşük vol -> daha yüksek ağırlık; yüksek vol -> daha düşük ağırlık
        - Ağırlıklar [0, 1] aralığına kırpılır
        """
        idx = returns.index
        w = signal.astype(float).reindex(idx).fillna(0.0).clip(0.0, 1.0)

        # None güvenli hedef/parametreler
        target_pct = _as_float(getattr(self.cfg, "vol_target_pct", None), 0.0)
        lookback = max(2, int(_as_float(getattr(self.cfg, "vol_lookback", None), 20)))
        ann = _as_float(getattr(self.cfg, "ann_factor", None), 252.0)

        if not (bool(getattr(self.cfg, "enabled", True)) and target_pct > 0.0):
            return w

        rets = returns.astype(float).fillna(0.0)

        # EWMA std: hızlı tepki, NaN yok
        vol = rets.ewm(span=lookback, adjust=False).std(bias=False)
        ann_vol = vol * sqrt(ann)

        target = target_pct / 100.0

        # 0'a bölme koruması ve üstten kırpma
        scale = target / ann_vol.replace(0.0, np.nan)
        scale = scale.clip(upper=1.0).fillna(1.0)

        sized = (w * scale).clip(0.0, 1.0).reindex(idx)
        return sized

    def apply_stops(
        self, strategy_returns: pd.Series, price: pd.Series
    ) -> Tuple[pd.Series, List[dict]]:
        """Basit fiyat bazlı stop: drawdown eşik aşıldığında pozisyonu 0'a çeker."""
        logs: List[dict] = []
        sl_pct = _as_float(getattr(self.cfg, "stop_loss_pct", None), 0.0)
        if not (bool(getattr(self.cfg, "enabled", True)) and sl_pct > 0.0):
            return pd.Series(1.0, index=price.index), logs

        px = price.astype(float)
        roll_max = px.cummax()
        dd = px / roll_max - 1.0
        thr = -sl_pct / 100.0

        adj = pd.Series(1.0, index=px.index)
        adj.loc[dd <= thr] = 0.0

        if (adj == 0.0).any():
            logs.append({"type": "stop_triggered", "count": int((adj == 0.0).sum())})
        return adj, logs


__all__ = ["RiskConfig", "RiskEngine"]
