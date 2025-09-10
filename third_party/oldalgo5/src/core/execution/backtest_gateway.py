
from __future__ import annotations
from .gateway import ExecutionGateway, OrderEvent, FillEvent
from datetime import datetime

class BacktestExecutionGateway(ExecutionGateway):
    """Anında fill, basit bps komisyon ve slippage."""
    def place_order(self, order: OrderEvent, market_price: float) -> FillEvent:
        # apply slippage in the direction of the trade
        slip = market_price * (self.slippage_bps / 10000.0) * (1 if order.side > 0 else -1)
        px = float(market_price + slip)
        commission = abs(order.quantity * px) * (self.commission_bps / 10000.0)
        return FillEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=px,
            commission=commission,
            timestamp=datetime.utcnow()
        )
