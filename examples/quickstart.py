"""Algo5 Quickstart (Week 5)

Purpose:
  - Show end-to-end wiring by publishing two bars.
Relations:
  - Uses `build_event_driven_app()` and `PortfolioUpdated` from core.events.
"""

import pandas as pd

from algo5.app.runtime import build_event_driven_app
from algo5.core.events import PortfolioUpdated, Tick


def main() -> None:
    bus, *_ = build_event_driven_app(initial_cash=10_000.0)

    def log_update(e: PortfolioUpdated, _):
        print(f"[{e.timestamp}] equity={e.equity:.2f} pos={e.position}")

    bus.subscribe(PortfolioUpdated, log_update)

    bars = [
        Tick(pd.Timestamp("2025-01-01 09:30:00"), "AAPL", 100, 101, 99, 100.5, 1000),
        Tick(pd.Timestamp("2025-01-01 09:31:00"), "AAPL", 102, 103, 101, 102.6, 1200),
    ]
    for b in bars:
        bus.publish(b)

    print("✅ Quickstart demo done.")


if __name__ == "__main__":
    main()
