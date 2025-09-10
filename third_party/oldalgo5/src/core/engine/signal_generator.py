from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Callable, Any
import numpy as np
from ...events.bus import EventBus
from ...events.domain import MarketDataEvent, SignalEvent

@dataclass
class Signal:
    symbol: str
    strength: float  # -1..+1
    direction: int   # -1,0,+1
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]

    def to_event(self) -> SignalEvent:
        return SignalEvent(
            timestamp=self.timestamp,
            source=self.source,
            data={
                "symbol": self.symbol,
                "raw_signal": float(self.direction),
                "target_weight": float(np.clip(self.strength, -1.0, 1.0)),
                "meta": self.metadata,
            }
        )

class SignalGenerator:
    """MarketDataEvent geldiğinde kayıtlı stratejileri tetikler ve SignalEvent üretir."""
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.strategies: Dict[str, Callable[[MarketDataEvent], list[Signal]]] = {}
        self.event_bus.subscribe(MarketDataEvent, self._on_market)

    def register(self, name: str, strategy_fn: Callable[[MarketDataEvent], list[Signal]]):
        self.strategies[name] = strategy_fn

    def _on_market(self, event: MarketDataEvent):
        for name, strat_fn in list(self.strategies.items()):
            try:
                signals = strat_fn(event)
                for s in signals:
                    self.event_bus.publish(s.to_event())
            except Exception as e:
                print(f"[SignalGenerator] {name} error:", e)
