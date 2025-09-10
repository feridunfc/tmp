from __future__ import annotations
from dataclasses import dataclass

@dataclass
class AppContext:
    commission_bps: float = 0.0
    slippage_bps: float = 0.0
    data_mode: str = "synthetic"
