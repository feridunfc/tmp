from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from ..matcher import match_order_on_bar
from ..models import Order, Fill, Side


@dataclass
class PaperGateway:
    initial_capital: float = 100_000.0
    fees_bps: float = 1.0
    slippage_bps: float = 1.0

    cash: float = field(init=False)
    position: float = field(init=False, default=0.0)
    orders: List[Order] = field(init=False, default_factory=list)
    trades: List[Fill] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.cash = float(self.initial_capital)

    # API
    def submit(self, order: Order) -> None:
        self.orders.append(order)

    def on_bar(self, o: float, h: float, l: float, c: float) -> List[Fill]:
        fills: List[Fill] = []
        pending: List[Order] = []
        for od in self.orders:
            f = match_order_on_bar(od, o, h, l, c, fees_bps=self.fees_bps, slippage_bps=self.slippage_bps)
            if f is None:
                pending.append(od)  # GTC için kuyrukta kalsın
                continue
            self._apply_fill(od, f)
            self.trades.append(f)
            fills.append(f)
        self.orders = pending
        return fills

    def _apply_fill(self, od: Order, f: Fill) -> None:
        notional = f.price * f.qty
        if od.side == Side.BUY:
            self.position += f.qty
            self.cash -= notional + f.commission
        else:
            self.position -= f.qty
            self.cash += notional - f.commission

    def equity(self, last_price: float) -> float:
        return self.cash + self.position * last_price

    # small helper for tests
    def state(self, last_price: float) -> Dict[str, float]:
        return {"cash": self.cash, "pos": self.position, "equity": self.equity(last_price)}
