from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from .context import RiskContext
from .rules import RiskRule
from .sizer import Sizer
from ..execution.models import Order, Side, OrderType, TIF

@dataclass
class RiskChain:
    rules: List[RiskRule] = field(default_factory=list)
    sizer: Optional[Sizer] = None

    def propose(self, side: Side, ctx: RiskContext, *,
                order_type: OrderType = OrderType.MARKET,
                limit_price=None, stop_price=None, tif: TIF = TIF.GTC) -> Optional[Order]:
        if self.sizer is None:
            return None
        qty = float(self.sizer.size(ctx))
        if qty <= 0:
            return None
        order = Order(side=side, qty=qty, type=order_type,
                      limit_price=limit_price, stop_price=stop_price, tif=tif)
        return self.process(order, ctx)

    def process(self, order: Order, ctx: RiskContext) -> Optional[Order]:
        cur: Optional[Order] = order
        for rule in self.rules:
            if cur is None:
                return None
            cur = rule.apply(cur, ctx)
        return cur
