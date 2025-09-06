from __future__ import annotations
from .trailing_oco import wrap_matcher as _algo5_wrap  # noqa: E402

from algo5.engine.execution.models import TIF, Fill, Order, OrderType, Side


def _commission(price: float, qty: float, fees_bps: float) -> float:
    # \"\"\"Basit komisyon hesaplamasÄ± (bps).\"\"\"
    return abs(price * qty) * (fees_bps / 1e4)


def match_order_on_bar(  # noqa: C901
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
    # \"\"\"Tek bar Ã¼zerinde order eÅŸleÅŸtirme.

    # Notlar:
    # - low iÃ§in l alias'Ä±nÄ± da kabul eder.
    # - Fill.qty yÃ¶nlÃ¼dÃ¼r: BUY -> +qty, SELL -> -qty.
    # \"\"\"
    # Alias: l -> low
    if low is None and "l" in kwargs:
        low = kwargs["l"]

    if low is None:
        raise TypeError(
            "match_order_on_bar(): required arg 'low' not provided (low=... ya da l=...)."
        )
    if c is None:
        raise TypeError("match_order_on_bar(): required arg 'c' not provided (c=...).")

    # YÃ¶n iÅŸareti
    sign = 1 if order.side == Side.BUY else -1
    q = sign * order.qty

    # MARKET â†’ Open
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
        # IOC/FOK ise bar sonunda yoksa dÃ¼ÅŸer
        if order.tif in (TIF.IOC, TIF.FOK):
            return None
        return None  # GTC: kuyrukta kalÄ±r

    # STOP (stop-market)
    if order.type == OrderType.STOP and order.stop_price is not None:
        S = order.stop_price
        triggered = (h >= S) if order.side == Side.BUY else (low <= S)
        if triggered:
            # Gap korumasÄ±
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
            # IOC/FOK ise tetiklenmediyse dÃ¼ÅŸsÃ¼n; GTC ise kuyrukta kalsÄ±n
            return None if order.tif in (TIF.IOC, TIF.FOK) else None

        # Tetiklendiyse aynÄ± barda limit ÅŸartÄ±na bak
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


# -- Trailing/OCO wrapper activation --
if "_ALGO5_TRAIL_OCO_PATCHED" not in globals():
    match_order_on_bar = _algo5_wrap(match_order_on_bar)
    _ALGO5_TRAIL_OCO_PATCHED = True
