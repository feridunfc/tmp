from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
# from core.execution.paper_engine import PaperTradingEngine

@dataclass
class PaperOrder:
    order_id: str
    symbol: str
    side: str  # 'buy' | 'sell'
    quantity: float
    order_type: str  # 'market' | 'limit'
    price: Optional[float] = None
    status: str = 'pending'
    created_at: datetime = None
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    realized_pnl: float = 0.0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class PaperTradingEngine:
    def __init__(self, initial_capital: float = 100000.0, *, commission_rate: float = 0.0001, slippage_rate: float = 0.0001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}
        self.avg_cost: Dict[str, float] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.order_history: List[PaperOrder] = []
        self.portfolio_value = initial_capital
        self.portfolio_history: List[Dict] = []
        self.market_data: Dict[str, pd.Series] = {}
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

    # --- Market data ---
    def update_market_data(self, symbol: str, series: pd.Series):
        self.market_data[symbol] = series

    def get_current_price(self, symbol: str) -> Optional[float]:
        s = self.market_data.get(symbol)
        if s is not None and len(s) > 0:
            return float(s.iloc[-1])
        return None

    # --- Orders ---
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = 'market', price: Optional[float] = None) -> PaperOrder:
        oid = f"ord_{len(self.orders)+1}_{datetime.now().timestamp()}"
        o = PaperOrder(order_id=oid, symbol=symbol, side=side, quantity=float(quantity), order_type=order_type, price=price)
        self.orders[oid] = o
        self.order_history.append(o)
        if order_type == 'market':
            self.execute_order(oid)
        return o

    def execute_order(self, order_id: str):
        o = self.orders.get(order_id)
        if not o or o.status != 'pending':
            return
        px = self.get_current_price(o.symbol)
        if px is None:
            return
        slip = px * self.slippage_rate
        exec_px = px + slip if o.side == 'buy' else px - slip
        commission = exec_px * o.quantity * self.commission_rate

        if o.side == 'buy':
            total_cost = exec_px * o.quantity + commission
            if self.cash >= total_cost:
                self.cash -= total_cost
                new_qty = self.positions.get(o.symbol, 0.0) + o.quantity
                # avg cost update
                prev_qty = self.positions.get(o.symbol, 0.0)
                prev_cost = self.avg_cost.get(o.symbol, exec_px)
                if new_qty > 0:
                    self.avg_cost[o.symbol] = (prev_cost * prev_qty + exec_px * o.quantity) / new_qty
                self.positions[o.symbol] = new_qty
                o.status = 'filled'; o.filled_at = datetime.now(); o.filled_price = exec_px
        else:  # sell
            cur = self.positions.get(o.symbol, 0.0)
            if cur >= o.quantity:
                self.positions[o.symbol] = cur - o.quantity
                proceeds = exec_px * o.quantity - commission
                self.cash += proceeds
                # realized PnL vs avg cost
                avg = self.avg_cost.get(o.symbol, exec_px)
                o.realized_pnl = (exec_px - avg) * o.quantity - commission
                if self.positions[o.symbol] == 0:
                    # reset avg cost when flat
                    self.avg_cost[o.symbol] = avg  # keep last avg
                o.status = 'filled'; o.filled_at = datetime.now(); o.filled_price = exec_px

        self.update_portfolio_value()

    def close_all_positions(self):
        # Market close all longs (no short support in this simple engine)
        for sym, qty in list(self.positions.items()):
            if qty > 0:
                self.place_order(sym, 'sell', qty, 'market')

    # --- Portfolio ---
    def update_portfolio_value(self):
        total = self.cash
        for sym, qty in self.positions.items():
            px = self.get_current_price(sym)
            if px is not None:
                total += px * qty
        self.portfolio_value = total
        self.portfolio_history.append({
            'timestamp': datetime.now(),
            'total_value': self.portfolio_value,
            'cash': self.cash,
            'positions': self.positions.copy()
        })

    def positions_df(self) -> pd.DataFrame:
        rows = []
        for sym, qty in self.positions.items():
            px = self.get_current_price(sym) or float('nan')
            avg = self.avg_cost.get(sym, float('nan'))
            mv = qty * px if px==px else float('nan')
            u_pnl = (px - avg) * qty if (px==px and avg==avg) else float('nan')
            rows.append({'symbol': sym, 'qty': qty, 'avg_cost': avg, 'last_price': px, 'market_value': mv, 'unrealized_pnl': u_pnl})
        return pd.DataFrame(rows)

    def orders_df(self) -> pd.DataFrame:
        rows = []
        for o in self.order_history:
            rows.append({
                'ts': o.filled_at or o.created_at,
                'symbol': o.symbol,
                'side': o.side,
                'qty': o.quantity,
                'price': o.filled_price or o.price,
                'status': o.status,
                'realized_pnl': o.realized_pnl
            })
        return pd.DataFrame(rows)
