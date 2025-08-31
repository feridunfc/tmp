from __future__ import annotations
from .models import Order, OrderType, Side, Fill, TIF


def _commission(price: float, qty: float, bps: float) -> float:
    return abs(price * qty) * (bps / 1e4)


def match_order_on_bar(
    order: Order,
    o: float,
    h: float,
    low: float | None = None,
    c: float | None = None,
    *,
    fees_bps: float = 0.0,
    slippage_bps: float = 0.0,
    **kwargs,
) -> Fill | None:
    """Tek bar üzerinde order eşleştirme.

    Notlar:
    - `low` için `l` alias'ını destekler (testler `l=` ile çağırıyor).
    - Fill.qty yönlüdür: BUY -> +qty, SELL -> -qty.
    """
    # Back-compat: allow callers to pass l=... instead of low=...
    if low is None and "l" in kwargs:
        low = kwargs["l"]

    if low is None:
        raise TypeError(
            "match_order_on_bar(): required arg 'low' not provided (use 'low=...' or 'l=...')."
        )
    if c is None:
        raise TypeError(
            "match_order_on_bar(): required arg 'c' not provided (use 'c=...')."
        )

    # Yön işareti
    sign = 1 if order.side == Side.BUY else -1
    q = sign * order.qty

    # MARKET → Open
    if order.type == OrderType.MARKET:
        px = o * (1 + (slippage_bps / 1e4) * (1 if order.side == Side.BUY else -1))
        return Fill(
            order_id=order.id,
            qty=q,
            price=px,
            commission=_commission(px, order.qty, fees_bps),
            slippage_bps=slippage_bps,
        )

    # LIMIT
    if order.type == OrderType.LIMIT and order.limit_price is not None:
        L = order.limit_price
        crossed = low <= L <= h
        if crossed:
            px = L
            return Fill(
                order_id=order.id,
                qty=q,
                price=px,
                commission=_commission(px, order.qty, fees_bps),
            )
        if order.tif in (TIF.IOC, TIF.FOK):
            return None
        return None  # GTC: bu barda yok, kuyrukta kalsın

    # STOP
    if order.type == OrderType.STOP and order.stop_price is not None:
        S = order.stop_price
        triggered = (h >= S) if order.side == Side.BUY else (low <= S)
        if triggered:
            px = max(o, S) if order.side == Side.BUY else min(o, S)
            return Fill(
                order_id=order.id,
                qty=q,
                price=px,
                commission=_commission(px, order.qty, fees_bps),
            )
        if order.tif in (TIF.IOC, TIF.FOK):
            return None
        return None

    # STOP-LIMIT
    if (
        order.type == OrderType.STOP_LIMIT
        and order.stop_price is not None
        and order.limit_price is not None
    ):
        S, L = order.stop_price, order.limit_price
        triggered = (h >= S) if order.side == Side.BUY else (low <= S)
        if not triggered:
            return None if order.tif in (TIF.IOC, TIF.FOK) else None
        crossed = low <= L <= h
        if crossed:
            px = L
            return Fill(
                order_id=order.id,
                qty=q,
                price=px,
                commission=_commission(px, order.qty, fees_bps),
            )
        return None

    return None
