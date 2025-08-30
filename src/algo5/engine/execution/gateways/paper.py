from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
from ..matcher import match_order_on_bar, Fill
from ..models import Order

@dataclass
class PaperGateway:
    fills: List[Fill] = field(default_factory=list)
    _last_bar: Tuple[float, float, float, float] | None = None

    def on_bar(self, o: float, h: float, l: float, c: float) -> None:
        self._last_bar = (o, h, l, c)

    def submit(self, order: Order) -> Fill | None:
        if self._last_bar is None:
            return None
        o, h, l, c = self._last_bar
        fill = match_order_on_bar(order, o, h, l, c)
        if fill:
            self.fills.append(fill)
        return fill
