from __future__ import annotations

import uuid
from typing import Any
from .models import Order, OrderType, Side


def _attach(obj: Any, **fields: Any) -> None:
    """Mypy'yi rahatsız etmeden dinamik attribute ekle/override et."""
    for k, v in fields.items():
        setattr(obj, k, v)


def build_bracket(
    side: Side,
    qty: float,
    entry: float,
    take_profit: float | None = None,
    stop_loss: float | None = None,
    *,
    trail_amount: float | None = None,
    trail_pct: float | None = None,
    symbol: str = "AAPL",
) -> list[Order]:
    """
    Tek çağrıda bracket (entry + OCO exits) oluşturur.

    - Entry: LIMIT (oco_id verilmez)
    - Exits (TP/SL): aynı oco_id ile OCO kardeş yapılır
    - Trailing istenirse SL için type alanı 'TRAILING_STOP' stringine ayarlanır ve
      trail_amount / trail_pct alanları dinamik olarak eklenir (matcher wrapper bunu okur)
    """
    orders: list[Order] = []

    # 1) Entry
    entry_o = Order(
        side=side,
        qty=qty,
        type=OrderType.LIMIT,
        limit_price=float(entry),
        symbol=symbol,
    )
    orders.append(entry_o)

    # 2) Exits share OCO
    exit_side = Side.SELL if side == Side.BUY else Side.BUY
    oco = uuid.uuid4().hex

    if take_profit is not None:
        tp = Order(
            side=exit_side,
            qty=qty,
            type=OrderType.LIMIT,
            limit_price=float(take_profit),
            symbol=symbol,
        )
        _attach(tp, oco_id=oco, parent_id=getattr(entry_o, "id", None))
        orders.append(tp)

    if stop_loss is not None:
        sl = Order(
            side=exit_side,
            qty=qty,
            type=OrderType.STOP,
            stop_price=float(stop_loss),
            symbol=symbol,
        )
        # Trailing semantiği
        if trail_amount is not None or trail_pct is not None:
            _attach(sl, type="TRAILING_STOP")
            if trail_amount is not None:
                _attach(sl, trail_amount=float(trail_amount))
            if trail_pct is not None:
                _attach(sl, trail_pct=float(trail_pct))

        _attach(sl, oco_id=oco, parent_id=getattr(entry_o, "id", None))
        orders.append(sl)

    return orders
