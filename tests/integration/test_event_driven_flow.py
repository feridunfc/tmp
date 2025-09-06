import pandas as pd

from algo5.app.runtime import build_event_driven_app
from algo5.core.events import OrderRejected, PortfolioUpdated, Tick


def test_market_then_limit_sell_flow():
    bus, strat, risk, exe, pf = build_event_driven_app(initial_cash=10_000.0)

    updates = []
    bus.subscribe(PortfolioUpdated, lambda e, b: updates.append(e))

    # Bar-1: up bar -> MARKET BUY 1 @o=100
    t1 = Tick(pd.Timestamp("2025-01-01 09:30:00"), "AAPL", 100.0, 101.0, 99.0, 100.5, 1000)
    bus.publish(t1)

    # Bar-2: kÃ¢r hedefi ~%2 => 100.5*1.02=102.51; high=103 iÃ§inde -> LIMIT SELL fill
    t2 = Tick(pd.Timestamp("2025-01-01 09:31:00"), "AAPL", 102.0, 103.0, 101.0, 102.6, 1200)
    bus.publish(t2)

    assert len(updates) >= 1
    last = updates[-1]
    assert last.position == 0.0
    assert last.equity > 10_000.0
    assert last.realized_pnl >= 0.0


def test_risk_rejects_when_position_limit_exceeded():
    bus, strat, risk, exe, pf = build_event_driven_app(initial_cash=10_000.0)
    risk.max_position = 0.0  # herhangi bir alÄ±ÅŸ reddedilsin

    rejections = []
    bus.subscribe(OrderRejected, lambda e, b: rejections.append(e))

    t1 = Tick(pd.Timestamp("2025-01-01 09:30:00"), "AAPL", 100.0, 101.0, 99.0, 100.5, 1000)
    bus.publish(t1)

    assert len(rejections) == 1
    assert "limit" in rejections[0].reason.lower()
