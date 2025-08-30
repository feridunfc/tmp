from __future__ import annotations
from dataclasses import dataclass
from .models import Order, OrderType, Side, TIF

@dataclass
class Fill:
    qty: float
    price: float
    fees: float = 0.0

def _apply_bps(price: float, bps: float, side: Side) -> float:
    sign = 1 if side is Side.BUY else -1
    return price * (1 + sign * (bps / 1e4))

def match_order_on_bar(order: Order, o: float, h: float, l: float, c: float, *,
                       fee_bps: float = 0.0, slippage_bps: float = 0.0) -> Fill | None:
    px = None
    if order.type is OrderType.MARKET:
        px = c
    elif order.type is OrderType.LIMIT:
        if order.side is Side.BUY and l <= float(order.limit_price) <= h:
            px = float(order.limit_price)
        elif order.side is Side.SELL and l <= float(order.limit_price) <= h:
            px = float(order.limit_price)
    elif order.type is OrderType.STOP:
        if order.side is Side.BUY and h >= float(order.stop_price):
            px = max(float(order.stop_price), o)
        elif order.side is Side.SELL and l <= float(order.stop_price):
            px = min(float(order.stop_price), o)

    if px is None:
        return None

    px = _apply_bps(px, slippage_bps, order.side)
    notional = abs(order.qty) * px
    fees = notional * (fee_bps / 1e4)
    return Fill(qty=order.qty, price=px, fees=fees)
