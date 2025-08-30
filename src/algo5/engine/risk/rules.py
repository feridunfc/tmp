from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .context import RiskContext
from ..execution.models import Order, Side

class RiskRule:
    def apply(self, order: Order, ctx: RiskContext) -> Optional[Order]:
        return order

@dataclass
class MaxPositionQty(RiskRule):
    max_qty: float
    def apply(self, order: Order, ctx: RiskContext) -> Optional[Order]:
        available = float(self.max_qty) - abs(float(ctx.position_qty))
        if available <= 0:
            return None
        allowed_qty = min(abs(float(order.qty)), available)
        if allowed_qty <= 0:
            return None
        return Order(
            side=order.side, qty=allowed_qty, type=order.type,
            limit_price=order.limit_price, stop_price=order.stop_price, tif=order.tif
        )

@dataclass
class MaxNotional(RiskRule):
    max_notional: float
    def apply(self, order: Order, ctx: RiskContext) -> Optional[Order]:
        price = max(float(ctx.last_price), 1e-12)
        max_qty = float(self.max_notional) / price
        qty = min(abs(float(order.qty)), max_qty)
        if qty <= 0:
            return None
        return Order(
            side=order.side, qty=qty, type=order.type,
            limit_price=order.limit_price, stop_price=order.stop_price, tif=order.tif
        )
