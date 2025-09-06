from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class OrderEvent:
    order_id: str
    symbol: str
    qty: float
    side: str              # "BUY" | "SELL"
    ts: datetime

@dataclass
class FillEvent:
    order_id: str
    symbol: str
    filled_qty: float
    price: float
    commission: float
    ts: datetime

class ExecutionGateway:
    async def place_order(self, order: OrderEvent) -> FillEvent:
        raise NotImplementedError
