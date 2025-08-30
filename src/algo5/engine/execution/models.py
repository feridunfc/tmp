from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional

class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()

class Side(Enum):
    BUY = "buy"
    SELL = "sell"

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
