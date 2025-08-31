"""
ALGO5 Execution • matcher.py

Purpose
-------
Deterministic, bar-based matching (1-bar delay → fill at evaluation bar OPEN).
OHLC guardrails ile Market / Limit / Stop / Stop-Limit ve TIF semantiklerini uygular.

Public API
----------
- class FillResult(fill, remaining_order)
- match_order_on_bar(order, o, h, l, c, fee_bps=0.0) -> FillResult
- match_on_bar(order, bar_like, fee_bps=0.0) -> FillResult  # dict/Series uyumlu
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any

from .models import Order, OrderType, Side, TIF, Fill


@dataclass
class FillResult:
    fill: Optional[Fill]
    remaining_order: Optional[Order]

    # Test uyumluluğu için: result.price → result.fill.price şeffaf erişim
    def __getattr__(self, name):
        if self.fill is not None and hasattr(self.fill, name):
            return getattr(self.fill, name)
        raise AttributeError(name)


def match_order_on_bar(
    order: Order,
    o: float,
    h: float,
    l: float,
    c: float,
    *,
    fee_bps: float = 0.0,
) -> FillResult:
    """Deterministic 1-bar delay matcher with OHLC guardrails."""
    px = None
    filled = False

    # MARKET → evaluation bar OPEN
    if order.type == OrderType.MARKET:
        px = float(o)
        filled = True

    # LIMIT → bar aralığına dokunursa TAM limitte fill
    elif order.type == OrderType.LIMIT:
        if order.limit_price is None:
            # eksik fiyat: immediates iptal, GTC kitapta kalsın
            if order.tif in (TIF.IOC, TIF.FOK, TIF.DAY):
                return FillResult(None, None)
            return FillResult(None, order)
        if l <= order.limit_price <= h:
            px = float(order.limit_price)
            filled = True

    # STOP → tetiklenirse MARKET (OPEN’dan fill)
    elif order.type == OrderType.STOP:
        if order.stop_price is None:
            # trailing wrapper için GTC working, immediates cancel
            if order.tif in (TIF.IOC, TIF.FOK, TIF.DAY):
                return FillResult(None, None)
            return FillResult(None, order)
        trig = (order.side == Side.BUY and h >= order.stop_price) or \
               (order.side == Side.SELL and l <= order.stop_price)
        if trig:
            px = float(o)
            filled = True

    # STOP-LIMIT → tetik + limit aynı barda sağlanırsa, TAM limitte fill
    elif order.type == OrderType.STOP_LIMIT:
        if order.stop_price is None or order.limit_price is None:
            if order.tif in (TIF.IOC, TIF.FOK, TIF.DAY):
                return FillResult(None, None)
            return FillResult(None, order)
        trig = (order.side == Side.BUY and h >= order.stop_price) or \
               (order.side == Side.SELL and l <= order.stop_price)
        if trig and (l <= order.limit_price <= h):
            px = float(order.limit_price)
            filled = True

    # TIF politikası
    if not filled:
        if order.tif in (TIF.IOC, TIF.FOK, TIF.DAY):
            # bar modelinde partial yok → dokunmazsa iptal
            return FillResult(None, None)
        return FillResult(None, order)  # GTC kitapta bekler

    # Fill + ücret
    notional = abs(order.qty) * px
    fees = notional * (fee_bps / 1e4)
    return FillResult(Fill(qty=order.qty, price=px, fees=fees), None)


def match_on_bar(order: Order, bar_like: Any, *, fee_bps: float = 0.0) -> FillResult:
    """Bar dict/Series uyumlu sarmalayıcı: 'Open'/'open' anahtarlarını normalize eder."""
    def pick(b: Any, k1: str, k2: str):
        if isinstance(b, dict):
            if k1 in b: return b[k1]
            if k2 in b: return b[k2]
        if hasattr(b, k1): return getattr(b, k1)
        if hasattr(b, k2): return getattr(b, k2)
        try:
            return b[k1]
        except Exception:
            return b[k2]
    o = float(pick(bar_like, "Open", "open"))
    h = float(pick(bar_like, "High", "high"))
    l = float(pick(bar_like, "Low",  "low"))
    c = float(pick(bar_like, "Close","close"))
    return match_order_on_bar(order, o, h, l, c, fee_bps=fee_bps)
