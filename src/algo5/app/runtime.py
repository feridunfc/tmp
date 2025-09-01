# src/algo5/app/runtime.py
"""Event-driven runtime wiring (Week-4/5)."""
from __future__ import annotations

from typing import Tuple

from algo5.core.bus import EventBus
from algo5.core.events import Tick, OrderRequested, OrderAuthorized, OrderFilled
from algo5.app.components import Strategy, RiskGuard, ExecutionEngine, PortfolioManager
from algo5.engine.execution.gateways.paper import PaperGateway


def build_event_driven_app(
    initial_cash: float = 10_000.0,
) -> Tuple[EventBus, Strategy, RiskGuard, ExecutionEngine, PortfolioManager]:
    bus = EventBus()
    strat = Strategy()
    risk = RiskGuard()

    gateway = PaperGateway(initial_capital=initial_cash, fees_bps=0.0, slippage_bps=0.0)
    exe = ExecutionEngine(gateway=gateway)
    pf = PortfolioManager(cash=initial_cash)

    # --- Wire subscriptions (önemli sıra) ---
    # 1) Tick'i önce execution görsün (pending emirleri bu bar üzerinde eşleştirebilsin)
    bus.subscribe(Tick, exe.on_tick)

    # 2) Sonra strateji karar versin (OrderRequested yayınlar)
    bus.subscribe(Tick, strat.on_tick)

    # 3) Risk kontrolü -> onay/red
    bus.subscribe(OrderRequested, risk.on_order_requested)

    # 4) Onaylanan emir execution'a düşsün (hemen mevcut bara karşı denenir)
    bus.subscribe(OrderAuthorized, exe.on_order_authorized)

    # 5) Fill'ler portföye ve risk'e işlensin
    bus.subscribe(OrderFilled, pf.on_order_filled)
    bus.subscribe(OrderFilled, risk.on_order_filled)

    # 6) Portföy her Tick'te equity'yi güncellesin
    bus.subscribe(Tick, pf.on_tick)

    return bus, strat, risk, exe, pf
