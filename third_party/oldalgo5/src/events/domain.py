from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

class EventType(Enum):
    MARKET = "market"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"
    RISK = "risk"
    PORTFOLIO = "portfolio"
    CONFIG = "config"
    HEARTBEAT = "heartbeat"

@dataclass
class BaseEvent:
    type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

# Concrete domain events
@dataclass
class MarketDataEvent(BaseEvent):
    type: EventType = EventType.MARKET

@dataclass
class SignalEvent(BaseEvent):
    type: EventType = EventType.SIGNAL
    # convenience accessors
    @property
    def symbol(self) -> str:
        return self.data.get("symbol","")
    @property
    def raw_signal(self) -> float:
        return float(self.data.get("raw_signal", 0.0))
    @property
    def target_weight(self) -> float:
        return float(self.data.get("target_weight", 0.0))

@dataclass
class OrderEvent(BaseEvent):
    type: EventType = EventType.ORDER

@dataclass
class FillEvent(BaseEvent):
    type: EventType = EventType.FILL

@dataclass
class RiskEvent(BaseEvent):
    type: EventType = EventType.RISK

@dataclass
class PortfolioEvent(BaseEvent):
    type: EventType = EventType.PORTFOLIO
