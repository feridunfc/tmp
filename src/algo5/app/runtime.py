# \"\"\"Event-driven runtime wiring (Week-4/5).\"\"\"
from __future__ import annotations

from typing import Tuple

from algo5.core.bus import EventBus
from algo5.core.events import (
    Tick,
    OrderRequested,
    OrderAuthorized,
    OrderFilled,
)
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

    # Wire subscriptions
    bus.subscribe(Tick, strat.on_tick)
    bus.subscribe(OrderRequested, risk.on_order_requested)
    bus.subscribe(OrderAuthorized, exe.on_order_authorized)
    bus.subscribe(OrderFilled, pf.on_order_filled)
    bus.subscribe(OrderFilled, risk.on_order_filled)
    bus.subscribe(Tick, pf.on_tick)

    return bus, strat, risk, exe, pf
