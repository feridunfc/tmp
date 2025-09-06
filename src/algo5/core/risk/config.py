from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskConfig:
    enabled: bool = True
    vol_target_pct: float | None = 15.0  # % cinsinden; None/0 => kapalı
    vol_lookback: int = 20
    ann_factor: int = 252
    stop_loss_pct: float | None = None  # % cinsinden; None => kapalı
