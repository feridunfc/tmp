from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime

class ExchangeGateway(ABC):
    @abstractmethod
    def connect(self) -> None: ...
    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "market",
                    price: Optional[float] = None) -> str: ...
    @abstractmethod
    def cancel_order(self, order_id: str) -> None: ...
    @abstractmethod
    def get_positions(self) -> Dict[str, float]: ...
    @abstractmethod
    def last_price(self, symbol: str) -> Optional[float]: ...
