# src/algo5/app/runtime.py
"""Event-driven runtime wiring (Week-4/5)."""
from __future__ import annotations

from algo5.app.components import ExecutionEngine, PortfolioManager, RiskGuard, Strategy
from algo5.core.bus import EventBus
from algo5.core.events import OrderAuthorized, OrderFilled, OrderRequested, Tick
from algo5.engine.execution.gateways.paper import PaperGateway


def build_event_driven_app(
    initial_cash: float = 10_000.0,
) -> tuple[EventBus, Strategy, RiskGuard, ExecutionEngine, PortfolioManager]:
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


# --- CLI entry for quick demos (Week 5) ---
def main() -> None:
    """Minimal CLI for a tiny synthetic demo.

    Relationships:
    - Reuses `build_event_driven_app()` to wire Strategy/Risk/Execution/Portfolio.
    - Publishes `Tick` events and prints `PortfolioUpdated` snapshots.
    - Keeps all tests/backwards-compat intact (only appends a function).
    """
    import argparse

    import pandas as pd

    from algo5.core.events import PortfolioUpdated, Tick

    ap = argparse.ArgumentParser(prog="algo5-sim", description="Algo5 demo runner")
    ap.add_argument("--bars", type=int, default=2, help="Number of synthetic bars")
    ap.add_argument("--symbol", type=str, default="AAPL", help="Symbol to publish")
    ap.add_argument("--o", type=float, default=100.0, help="Base open price")
    args = ap.parse_args()

    bus, strat, risk, exe, pf = build_event_driven_app(initial_cash=10_000.0)

    def on_update(e: PortfolioUpdated, _bus) -> None:
        print(f"[{e.timestamp}] equity={e.equity:.2f} cash={e.cash:.2f} pos={e.position}")

    bus.subscribe(PortfolioUpdated, on_update)

    base = float(args.o)
    for i in range(int(args.bars)):
        ts = pd.Timestamp.utcnow().floor("s") + pd.Timedelta(seconds=i)
        o = base + i * 2.0
        high = o + 1.0
        low = o - 1.0
        close = o + 0.5
        bus.publish(Tick(ts, args.symbol, o, high, low, close, 1000.0))


if __name__ == "__main__":
    # Allow: `python -m algo5.app.runtime` or installed `algo5-sim`
    main()
