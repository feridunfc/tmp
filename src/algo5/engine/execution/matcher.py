from __future__ import annotations


from algo5.engine.execution.models import Order, OrderType, Side, TIF, Fill


def _commission(price: float, qty: float, fees_bps: float) -> float:
    # \"\"\"Basit komisyon hesaplaması (bps).\"\"\"
    return abs(price * qty) * (fees_bps / 1e4)


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
    # \"\"\"Tek bar üzerinde order eşleştirme.

    # Notlar:
    # - low için l alias'ını da kabul eder.
    # - Fill.qty yönlüdür: BUY -> +qty, SELL -> -qty.
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
        # IOC/FOK ise bar sonunda yoksa düşer
        if order.tif in (TIF.IOC, TIF.FOK):
            return None
        return None  # GTC: kuyrukta kalır

    # STOP (stop-market)
    if order.type == OrderType.STOP and order.stop_price is not None:
        S = order.stop_price
        triggered = (h >= S) if order.side == Side.BUY else (low <= S)
        if triggered:
            # Gap koruması
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
            # IOC/FOK ise tetiklenmediyse düşsün; GTC ise kuyrukta kalsın
            return None if order.tif in (TIF.IOC, TIF.FOK) else None

        # Tetiklendiyse aynı barda limit şartına bak
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
