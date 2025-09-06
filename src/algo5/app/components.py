from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict
import logging

from algo5.core.bus import EventBus
from algo5.core.events import (
    Tick,
    OrderRequested,
    OrderAuthorized,
    OrderRejected,
    OrderFilled,
    PortfolioUpdated,
)
from algo5.engine.execution.models import Order, Side, OrderType
from algo5.engine.execution.matcher import match_order_on_bar
from algo5.engine.execution.gateways.paper import PaperGateway

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """Basit strateji - up bar'da al, sonraki barda sat (prev close * 1.02)."""

    strategy_id: str = "simple_mean_reversion"
    state: str = "flat"
    last_tick: Optional[Tick] = None

    def on_tick(self, event: Tick, bus: EventBus) -> None:
        prev = self.last_tick
        self.last_tick = event

        # 1) flat & up bar -> MARKET BUY
        if self.state == "flat" and event.c > event.o:
            order = Order(
                side=Side.BUY,
                qty=1.0,
                type=OrderType.MARKET,
                symbol=event.symbol,
            )
            bus.publish(OrderRequested(order=order, strategy_id=self.strategy_id))
            self.state = "long"
            return

        # 2) long & new bar -> LIMIT SELL at prev close * 1.02 if in range
        if self.state == "long" and prev is not None:
            target = round(prev.c * 1.02, 2)
            lo = getattr(event, "l", getattr(event, "low", None))
            hi = getattr(event, "h", getattr(event, "high", None))
            if lo is not None and hi is not None and lo <= target <= hi:
                order = Order(
                    side=Side.SELL,
                    qty=1.0,
                    type=OrderType.LIMIT,
                    limit_price=target,
                    symbol=event.symbol,
                )
                bus.publish(OrderRequested(order=order, strategy_id=self.strategy_id))
                self.state = "flat"


@dataclass
class RiskGuard:
    """Risk kontrolü - pozisyon ve notional limitleri."""

    max_position: float = 10.0
    max_notional: float = 10000.0
    current_position: float = 0.0
    current_notional: float = 0.0

    def on_order_requested(self, event: OrderRequested, bus: EventBus) -> None:
        order = event.order

        position_change = order.qty if order.side == Side.BUY else -order.qty
        new_position = self.current_position + position_change
        if abs(new_position) > self.max_position:
            bus.publish(
                OrderRejected(
                    order=order,
                    reason=f"Position limit exceeded: {new_position} > {self.max_position}",
                )
            )
            return

        est_px = order.limit_price if order.limit_price is not None else 100.0
        est_notional = abs(order.qty) * est_px
        if est_notional > self.max_notional:
            bus.publish(
                OrderRejected(
                    order=order,
                    reason=f"Notional limit exceeded: {est_notional} > {self.max_notional}",
                )
            )
            return

        bus.publish(OrderAuthorized(order=order))

    def on_order_filled(self, event: OrderFilled, bus: EventBus) -> None:
        f = event.fill
        self.current_position += f.qty
        self.current_notional = abs(self.current_position) * f.price


@dataclass
class ExecutionEngine:
    """Emir execution engine (in-memory pending queue + matcher)."""

    gateway: PaperGateway
    pending_orders: Dict[str, Order] = field(default_factory=dict)
    last_tick: Optional[Tick] = None
    order_counter: int = 0

    def on_tick(self, event: Tick, bus: EventBus) -> None:
        self.last_tick = event
        if not self.pending_orders:
            return

        # l / low alias desteği
        low_arg = getattr(event, "l", getattr(event, "low", None))

        to_remove = []
        for oid, order in list(self.pending_orders.items()):
            f = match_order_on_bar(
                order=order,
                o=event.o,
                h=event.h,
                low=low_arg,
                c=event.c,
            )
            if f is not None:
                bus.publish(OrderFilled(fill=f, order_id=oid))
                to_remove.append(oid)

        for oid in to_remove:
            del self.pending_orders[oid]

    def on_order_authorized(self, event: OrderAuthorized, bus: EventBus) -> None:
        self.order_counter += 1
        oid = f"order_{self.order_counter}"
        self.pending_orders[oid] = event.order
        if self.last_tick is not None:
            self.on_tick(self.last_tick, bus)


@dataclass
class PortfolioManager:
    """Portföy yönetimi: cash/position/equity + PnL."""

    cash: float = 10000.0
    position: float = 0.0
    entry_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_tick: Optional[Tick] = None

    def on_order_filled(self, event: OrderFilled, bus: EventBus) -> None:
        f = event.fill
        commission = getattr(f, "commission", 0.0)
        proceeds = abs(f.qty) * f.price

        # Cash
        if f.qty > 0:  # BUY
            self.cash -= proceeds + commission
        else:  # SELL
            self.cash += proceeds - commission

        # Position & entry
        old_pos = self.position
        self.position += f.qty

        if old_pos != 0 and self.position == 0:
            # closing entire position
            self.realized_pnl += (f.price - self.entry_price) * abs(old_pos)

        if self.position != 0:
            self.entry_price = ((old_pos * self.entry_price) + (f.qty * f.price)) / self.position
        else:
            self.entry_price = 0.0

        self._publish_update(bus)

    def on_tick(self, event: Tick, bus: EventBus) -> None:
        self.last_tick = event
        self._publish_update(bus)

    def _publish_update(self, bus: EventBus) -> None:
        if self.last_tick is None:
            return
        px = self.last_tick.c
        self.unrealized_pnl = (px - self.entry_price) * self.position
        equity = self.cash + self.position * px
        bus.publish(
            PortfolioUpdated(
                timestamp=self.last_tick.ts,
                cash=self.cash,
                position=self.position,
                equity=equity,
                unrealized_pnl=self.unrealized_pnl,
                realized_pnl=self.realized_pnl,
            )
        )
