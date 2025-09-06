from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class RiskConfig:
    enabled: bool = True
    stop_loss_pct: float | None = None  # ör: 5.0 => %5
    vol_target_pct: float | None = None  # ör: 10.0 => yıllık %10
    vol_lookback: int = 20
    ann_factor: int = 252
