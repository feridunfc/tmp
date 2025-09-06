from __future__ import annotations
import asyncio, random
from datetime import datetime
from .gateway import OrderEvent, FillEvent

class PaperGateway:
    """
    Latency + slippage + bps komisyon simülasyonu.
    """
    def __init__(self, *, latency_ms=(10,120), slippage_bps=2.0, commission_bps=1.0, price_provider=None):
        self.latency_ms = latency_ms
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps
        self.price_provider = price_provider  # callable(symbol)->last_price

    async def place_order(self, order: OrderEvent) -> FillEvent:
        # latency
        await asyncio.sleep(random.uniform(*self.latency_ms)/1000.0)

        px = float(self.price_provider(order.symbol)) if self.price_provider else 100.0
        slip = px * (self.slippage_bps / 1e4) * (1 if order.side=="BUY" else -1)
        exec_px = px + slip
        comm = abs(order.qty) * exec_px * (self.commission_bps / 1e4)

        return FillEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            filled_qty=order.qty,
            price=exec_px,
            commission=comm,
            ts=datetime.utcnow()
        )
