from __future__ import annotations
from .models import Order, OrderType, Side, Fill, TIF


def _commission(price: float, qty: float, bps: float) -> float:
    return abs(price * qty) * (bps / 1e4)


def match_order_on_bar(
    order: Order,
    o: float, h: float, l: float, c: float,
    *, fees_bps: float = 0.0, slippage_bps: float = 0.0
) -> Fill | None:
    # MARKET → Open
    if order.type == OrderType.MARKET:
        px = o * (1 + (slippage_bps / 1e4) * (1 if order.side == Side.BUY else -1))
        return Fill(order_id=order.id, qty=order.qty, price=px,
                    commission=_commission(px, order.qty, fees_bps),
                    slippage_bps=slippage_bps)

    # LIMIT
    if order.type == OrderType.LIMIT and order.limit_price is not None:
        L = order.limit_price
        crossed = (l <= L <= h)
        if crossed:
            px = L
            return Fill(order_id=order.id, qty=order.qty, price=px,
                        commission=_commission(px, order.qty, fees_bps))
        # IOC/FOK iptal koşulu (bar sonunda hala fill yoksa)
        if order.tif in (TIF.IOC, TIF.FOK):
            return None
        return None  # GTC: bu bar yok

    # STOP
    if order.type == OrderType.STOP and order.stop_price is not None:
        S = order.stop_price
        triggered = (h >= S) if order.side == Side.BUY else (l <= S)
        if triggered:
            if order.side == Side.BUY:
                px = max(o, S)  # gap yukarı
            else:
                px = min(o, S)  # gap aşağı
            return Fill(order_id=order.id, qty=order.qty, price=px,
                        commission=_commission(px, order.qty, fees_bps))
        if order.tif in (TIF.IOC, TIF.FOK):
            return None
        return None

    # STOP-LIMIT
    if order.type == OrderType.STOP_LIMIT and order.stop_price is not None and order.limit_price is not None:
        S, L = order.stop_price, order.limit_price
        triggered = (h >= S) if order.side == Side.BUY else (l <= S)
        if not triggered:
            return None if order.tif in (TIF.IOC, TIF.FOK) else None
        # tetiklendiyse limit şartını aynı barda kontrol et
        crossed = (l <= L <= h)
        if crossed:
            px = L
            return Fill(order_id=order.id, qty=order.qty, price=px,
                        commission=_commission(px, order.qty, fees_bps))
        return None

    return None
