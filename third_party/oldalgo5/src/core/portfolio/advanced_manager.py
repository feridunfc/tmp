from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import math
from ...events.bus import EventBus
from ...events.domain import MarketDataEvent, FillEvent, PortfolioEvent

@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    last_price: float = 0.0

    def mv(self) -> float:
        return self.quantity * self.last_price

class AdvancedPortfolioManager:
    def __init__(self, event_bus: EventBus, initial_capital: float = 100_000.0):
        self.event_bus = event_bus
        self.cash = float(initial_capital)
        self.positions: Dict[str, Position] = {}
        self.equity_history: List[Dict] = []

        self.event_bus.subscribe(MarketDataEvent, self._on_market)
        self.event_bus.subscribe(FillEvent, self._on_fill)

    def _on_market(self, e: MarketDataEvent):
        sym = e.data.get("symbol")
        px = float(e.data.get("close", 0.0))
        if sym:
            pos = self.positions.get(sym)
            if pos:
                pos.last_price = px
        self._snapshot(e.timestamp)

    def _on_fill(self, e: FillEvent):
        sym = e.data["symbol"]
        qty = float(e.data["quantity"])
        price = float(e.data["price"])
        pos = self.positions.get(sym, Position(symbol=sym, last_price=price))
        # VWAP-like avg price update
        new_qty = pos.quantity + qty
        if new_qty == 0:
            pos.avg_price = 0.0
        else:
            pos.avg_price = (pos.avg_price * pos.quantity + price * qty) / new_qty
        pos.quantity = new_qty
        pos.last_price = price
        self.positions[sym] = pos
        # cash update (no fees for simplicity here)
        self.cash -= price * qty
        self._snapshot(e.timestamp)

    def _snapshot(self, ts: datetime):
        total_mv = sum(p.mv() for p in self.positions.values())
        equity = self.cash + total_mv
        self.equity_history.append({"timestamp": ts, "equity": equity, "cash": self.cash, "mv": total_mv})
        self.event_bus.publish(PortfolioEvent(timestamp=ts, source="portfolio",
                                              data={"equity": equity, "cash": self.cash, "mv": total_mv,
                                                    "positions": {k: vars(v) for k, v in self.positions.items()}}))
