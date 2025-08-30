from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .context import RiskContext

class Sizer(ABC):
    @abstractmethod
    def size(self, ctx: RiskContext) -> float: ...

@dataclass
class FixedSizer(Sizer):
    qty: float
    def size(self, ctx: RiskContext) -> float:
        return float(self.qty)

@dataclass
class PercentNotionalSizer(Sizer):
    percent: float  # 0..1
    def size(self, ctx: RiskContext) -> float:
        if ctx.last_price <= 0:
            return 0.0
        return (ctx.capital * float(self.percent)) / ctx.last_price
