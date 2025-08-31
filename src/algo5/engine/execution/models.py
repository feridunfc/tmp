"""
ALGO5 Execution • models.py

Purpose
-------
Typed order & fill primitives for the execution layer and tests.

Public API
----------
- Enums: OrderType, Side, TIF
- Dataclasses: Order, Fill, BracketOrder, TrailingStopOrder
Notes
-----
Keep the surface minimal and stable; richer fields (broker ids, meta)
ya gateway katmanında tutulur ya da Order içine 'meta' ile eklenir.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


class TIF(Enum):
    GTC = auto()  # Good-Till-Cancel (book’ta kalır)
    IOC = auto()  # Immediate-Or-Cancel (anında dolmazsa iptal)
    FOK = auto()  # Fill-Or-Kill (bar modelinde IOC gibi ele alınır)
    DAY = auto()  # Günlük (bar testte IOC benzeri; seans kapanışında iptal)


@dataclass
class Order:
    side: Side
    qty: float
    type: OrderType
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tif: TIF = TIF.GTC
    parent_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Fill:
    qty: float
    price: float
    fees: float = 0.0


@dataclass
class BracketOrder:
    """Parent fill sonrası OCO niyeti: TP (limit) ve SL (stop) çocukları kitapta bekler."""
    parent: Order
    tp_order: Optional[Order] = None
    sl_order: Optional[Order] = None


@dataclass
class TrailingStopOrder(Order):
    """Long: peak-high’tan, Short: trough-low’dan izler; amount veya pct verilir."""
    trail_amount: float = 0.0
    trail_pct: float = 0.0
    peak_price: Optional[float] = None   # long için
    trough_price: Optional[float] = None # short için

    def is_valid(self) -> bool:
        return (self.trail_amount > 0) ^ (self.trail_pct > 0)
