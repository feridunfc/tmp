from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskConfig:
    enabled: bool = True
    vol_target_pct: Optional[float] = 15.0  # % cinsinden; None/0 => kapalı
    vol_lookback: int = 20
    ann_factor: int = 252
    stop_loss_pct: Optional[float] = None  # % cinsinden; None => kapalı
