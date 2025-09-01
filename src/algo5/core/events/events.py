from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import pandas as pd
from algo5.engine.execution.models import Order, Fill


@dataclass(frozen=True)
class Tick:
    """Piyasa veri tick'i / bar."""

    ts: pd.Timestamp
    symbol: str
    o: float
    h: float
    low: float  # ← ruff E741 için `l` yerine `low`
    c: float
    v: float
    exchange: str = "NYSE"


@dataclass(frozen=True)
class OrderRequested:
    """Stratejiden emir talebi."""

    order: Order
    strategy_id: str = "default"


@dataclass(frozen=True)
class OrderAuthorized:
    """Riskten geçen emir."""

    order: Order
    reason: Optional[str] = "approved"


@dataclass(frozen=True)
class OrderRejected:
    """Risk tarafından reddedilen emir."""

    order: Order
    reason: str


@dataclass(frozen=True)
class OrderFilled:
    """Emrin fill olması."""

    fill: Fill
    order_id: str


@dataclass(frozen=True)
class PortfolioUpdated:
    """Portföy güncellemesi (testler `position` bekliyor)."""

    timestamp: pd.Timestamp
    cash: float
    position: float
    equity: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass(frozen=True)
class SystemHealth:
    """Sistem sağlık durumu."""

    timestamp: pd.Timestamp
    component: str
    status: str  # "HEALTHY", "WARNING", "ERROR"
    message: Optional[str] = None
