from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

class OrderType:
    MARKET = "market"
    LIMIT = "limit"

@dataclass
class Trade:
    open_time: pd.Timestamp
    close_time: Optional[pd.Timestamp]
    symbol: str
    direction: int     # 1 long, -1 short
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    hold_bars: int
    entry_slippage: float
    exit_slippage: float
    entry_commission: float
    exit_commission: float

def _max_drawdown(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    roll_max = series.cummax()
    dd = (series / roll_max) - 1.0
    return float(dd.min())

def _sharpe(returns: pd.Series, ann: int = 252) -> float:
    r = returns.dropna()
    if r.std(ddof=0) == 0 or len(r) < 2:
        return 0.0
    return float(np.sqrt(ann) * r.mean() / r.std(ddof=0))

class AdvancedBacktestEngine:
    """Trade-level backtester with simple but realistic cost models.
    DataFrame must contain: 'open','high','low','close','volume' (lowercase).
    Signals: -1,0,1 (direction). Uses 1-bar delayed execution by default.
    """
    def __init__(self, initial_capital: float = 100000.0,
                 commission_bps: float = 10.0,  # 0.10%
                 slippage_bps: float = 5.0):     # 0.05%
        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.positions: Dict[str, float] = {}  # signed quantity per symbol
        self.open_trades: Dict[str, Trade] = {}
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        self.commission_bps = float(commission_bps)
        self.slippage_bps = float(slippage_bps)

    # --- cost models ---
    def _calc_commission(self, trade_value: float) -> float:
        return abs(trade_value) * (self.commission_bps / 1e4)

    def _calc_slip_price(self, price: float, direction: int) -> float:
        slip = price * (self.slippage_bps / 1e4)
        return float(price + np.sign(direction) * slip)

    # --- portfolio accounting ---
    def _mark_to_market(self, ts: pd.Timestamp, price: float) -> float:
        pos_value = 0.0
        for sym, qty in self.positions.items():
            pos_value += qty * price  # single-asset demo
        equity = self.cash + pos_value
        self.equity_curve.append((ts, float(equity)))
        return equity

    def _open(self, ts: pd.Timestamp, symbol: str, direction: int, price: float) -> None:
        exec_price = self._calc_slip_price(price, direction)
        # simple position sizing: 10% of cash
        target_fraction = 0.10
        trade_value = self.cash * target_fraction
        if trade_value <= 0:
            return
        qty = trade_value / exec_price * direction
        comm = self._calc_commission(trade_value)
        self.cash -= (trade_value + comm)
        trade = Trade(
            open_time=ts, close_time=None, symbol=symbol, direction=direction,
            entry_price=exec_price, exit_price=0.0, quantity=abs(qty),
            pnl=0.0, pnl_pct=0.0, hold_bars=0,
            entry_slippage=self.slippage_bps/1e4, exit_slippage=0.0,
            entry_commission=comm, exit_commission=0.0
        )
        self.positions[symbol] = self.positions.get(symbol, 0.0) + qty
        self.open_trades[symbol] = trade

    def _close(self, ts: pd.Timestamp, symbol: str, price: float) -> None:
        qty = self.positions.get(symbol, 0.0)
        if qty == 0.0 or symbol not in self.open_trades:
            return
        direction = 1 if qty > 0 else -1
        exec_price = self._calc_slip_price(price, -direction)  # opposite side
        trade_value = abs(qty) * exec_price
        comm = self._calc_commission(trade_value)
        self.cash += trade_value - comm
        tr = self.open_trades.pop(symbol)
        tr.close_time = ts
        tr.exit_price = exec_price
        tr.hold_bars += 1
        tr.pnl = (exec_price - tr.entry_price) * tr.quantity * tr.direction
        tr.pnl_pct = tr.pnl / max(1e-9, tr.entry_price * tr.quantity)
        tr.exit_commission = comm
        tr.exit_slippage = self.slippage_bps/1e4
        self.trades.append(tr)
        self.positions[symbol] = 0.0

    def _flip(self, ts: pd.Timestamp, symbol: str, direction: int, price: float) -> None:
        self._close(ts, symbol, price)
        self._open(ts, symbol, direction, price)

    def run_backtest(self, df: pd.DataFrame, signals: pd.Series,
                     symbol: str = "asset") -> Dict[str, Any]:
        df = df.copy()
        cols = {c.lower(): c for c in df.columns}
        for c in ["open","high","low","close","volume"]:
            if c not in cols:
                raise KeyError(f"AdvancedBacktestEngine: missing column '{c}'")
        sig = signals.shift(1).reindex(df.index).fillna(0.0).astype(float)
        prev_dir = 0

        for ts, row in df.iterrows():
            dir_now = int(np.sign(sig.loc[ts]))
            price = float(row["open"])  # execute at open
            if dir_now != prev_dir:
                if prev_dir == 0 and dir_now != 0:
                    self._open(ts, symbol, dir_now, price)
                elif dir_now == 0 and prev_dir != 0:
                    self._close(ts, symbol, price)
                else:
                    self._flip(ts, symbol, dir_now, price)
                prev_dir = dir_now
            self._mark_to_market(ts, float(row["close"]))
            for tr in self.open_trades.values():
                tr.hold_bars += 1

        if len(df) > 0:
            self._close(df.index[-1], symbol, float(df["close"].iloc[-1]))
            self._mark_to_market(df.index[-1], float(df["close"].iloc[-1]))

        equity = pd.Series({ts: v for ts, v in self.equity_curve}).sort_index()
        rets = equity.pct_change().fillna(0.0)
        out = {
            "equity": equity,
            "returns": rets,
            "trades": self.trades,
            "metrics": {
                "total_return": float(equity.iloc[-1]/equity.iloc[0]-1.0) if len(equity)>1 else 0.0,
                "sharpe": float((rets.mean()/rets.std(ddof=0))*np.sqrt(252)) if rets.std(ddof=0)>0 else 0.0,
                "max_drawdown": float((equity/ equity.cummax()-1.0).min()) if len(equity)>1 else 0.0,
            }
        }
        return out
