from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from ..matcher import match_order_on_bar
from ..models import Order, Fill


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

    from typing import List  # dosyada yoksa ekleyin

    def on_bar(
        self,
        o: float,
        h: float,
        low: float | None = None,
        c: float | None = None,
        **kwargs,
    ) -> List[Fill]:
        # Back-compat: allow callers to pass l=... instead of low=...
        if low is None and "l" in kwargs:
            low = kwargs["l"]

        if low is None:
            raise TypeError(
                "on_bar(): required arg 'low' not provided (use 'low=...' or 'l=...')."
            )
        if c is None:
            raise TypeError("on_bar(): required arg 'c' not provided (use 'c=...').")

        fills: List[Fill] = []
        remaining: List[Order] = []

        for order in self.orders:
            fill = match_order_on_bar(
                order,
                o=o,
                h=h,
                low=low,
                c=c,
                fees_bps=self.fees_bps,
                slippage_bps=self.slippage_bps,
            )
            if fill is not None:
                fills.append(fill)
            else:
                remaining.append(order)

        # Filled olmayanlar kuyrukta kalsın
        self.orders = remaining

        # Filleri hesap/pozisyona uygula
        for f in fills:
            self._apply_fill(f)

        return fills

    def _apply_fill(self, f: Fill) -> None:
        """Fill'i uygula: nakit ve pozisyonu güncelle, işlemi kaydet."""
        commission = getattr(f, "commission", 0.0) or 0.0
        self.cash -= f.qty * f.price + commission
        self.position += f.qty
        self.trades.append(f)

    def equity(self, last_price: float) -> float:
        return self.cash + self.position * last_price

    # small helper for tests
    def state(self, last_price: float) -> Dict[str, float]:
        return {
            "cash": self.cash,
            "pos": self.position,
            "equity": self.equity(last_price),
        }
