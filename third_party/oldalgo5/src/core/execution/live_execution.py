from __future__ import annotations
from typing import Dict
from ...events.bus import EventBus
from ...events.domain import SignalEvent, OrderEvent, FillEvent
from .paper_gateway import PaperGateway  # use paper as default stub

class LiveExecutionEngine:
    def __init__(self, event_bus: EventBus, gateway=None, max_position_size: float = 0.2):
        self.event_bus = event_bus
        self.gateway = gateway or PaperGateway()
        self.max_position_size = float(max_position_size)
        self.pending: Dict[str, OrderEvent] = {}
        self.event_bus.subscribe(SignalEvent, self._on_signal)

    def _on_signal(self, event: SignalEvent):
        symbol = event.data.get("symbol")
        weight = float(event.data.get("target_weight", 0.0))
        side = "buy" if weight > 0 else "sell"
        qty = abs(weight) * 100  # demo sizing
        # risk-lite: position size cap
        current = self.gateway.get_positions().get(symbol, 0.0)
        if abs(current) + qty > self.max_position_size * 1000:  # naive cap
            return
        oid = self.gateway.place_order(symbol, side, qty, order_type="market")
        # publish order + fill immediately (paper)
        self.event_bus.publish(OrderEvent(timestamp=event.timestamp, source="live_exec",
                                          data={"order_id": oid, "symbol": symbol, "side": side, "qty": qty}))
        last_px = self.gateway.last_price(symbol)
        if last_px is not None:
            self.event_bus.publish(FillEvent(timestamp=event.timestamp, source="live_exec",
                                             data={"order_id": oid, "symbol": symbol, "price": float(last_px),
                                                   "quantity": qty, "signal_timestamp": event.timestamp.timestamp()}))
    def _validate_signal(self, signal_event):
        # max position (target weight) kontrolü
        tw = abs(signal_event.data.get("target_weight", 0.0))
        if tw > getattr(self, "max_position_size", 0.2):
            return False

        # concentration: tek sembol ağırlığı (portföyden çek)
        try:
            port = self.portfolio.get_portfolio_state()
            total_val = max(port["total_value"], 1e-6)
            sym_val = 0.0
            pos = port["positions"].get(signal_event.symbol)
            if pos:
                sym_val = pos.get("market_value", 0.0)
            if sym_val/total_val > getattr(self, "max_concentration", 0.5):
                return False
        except Exception:
            pass

        # vol cap (opsiyonel): sinyal gücü volatiliteye göre kısılabilir
        return True
