from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from uuid import uuid4


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


class TIF(Enum):
    GTC = auto()
    IOC = auto()
    FOK = auto()


@dataclass
class Order:
    side: Side
    qty: float
    type: OrderType
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tif: TIF = TIF.GTC
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class Fill:
    order_id: str
    qty: float
    price: float
    commission: float = 0.0
    slippage_bps: float = 0.0
