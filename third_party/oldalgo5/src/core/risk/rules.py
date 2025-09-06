from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class RiskContext:
    portfolio_value: float
    current_weights: Dict[str, float]      # symbol -> weight ([-1..+1])
    symbol_vol: Dict[str, float]           # symbol -> daily vol (0..)
    max_open_positions: int = 10
    max_weight: float = 0.2                # tek sembole max %20
    vol_cap: float = 0.05                  # günlük vol üst limiti (ör: %5)

class BaseRule:
    name: str = "BaseRule"
    def validate(self, symbol: str, proposed_weight: float, ctx: RiskContext) -> Tuple[bool, float, str]:
        return True, proposed_weight, "ok"

class MaxPositionWeight(BaseRule):
    name = "MaxPositionWeight"
    def validate(self, symbol: str, proposed_weight: float, ctx: RiskContext):
        mw = abs(proposed_weight)
        if mw > ctx.max_weight:
            adj = max(min(proposed_weight, ctx.max_weight), -ctx.max_weight)
            return False, adj, f"clamped to {ctx.max_weight}"
        return True, proposed_weight, "ok"

class MaxOpenPositions(BaseRule):
    name = "MaxOpenPositions"
    def validate(self, symbol: str, proposed_weight: float, ctx: RiskContext):
        open_now = sum(1 for w in ctx.current_weights.values() if abs(w) > 1e-6)
        going_open = open_now + (1 if (abs(proposed_weight) > 1e-6 and abs(ctx.current_weights.get(symbol, 0.0)) <= 1e-6) else 0)
        if going_open > ctx.max_open_positions:
            return False, 0.0, f"too many open positions ({going_open}>{ctx.max_open_positions})"
        return True, proposed_weight, "ok"

class VolatilityCap(BaseRule):
    name = "VolatilityCap"
    def validate(self, symbol: str, proposed_weight: float, ctx: RiskContext):
        v = ctx.symbol_vol.get(symbol, 0.0)
        if v > ctx.vol_cap:
            # volatilite yüksekse önerilen ağırlığı ölçekle
            scale = max(ctx.vol_cap / (v + 1e-12), 0.0)
            adj = proposed_weight * scale
            return False, adj, f"scaled by {scale:.2f} due to vol {v:.2%}"
        return True, proposed_weight, "ok"
