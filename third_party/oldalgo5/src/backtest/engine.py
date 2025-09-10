from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from .metrics import sharpe, maxdd, calmar
from utils.data import normalize_ohlcv
from utils.metrics import calculate_metrics
from core.risk.engine import RiskEngine
from strategies.registry import get_strategy

@dataclass
class Fees:
    commission_bps: float = 1.0
    slippage_bps: float   = 2.0

class BacktestEngine:
    def __init__(self, fees: Fees = Fees(), delay: int = 1):
        self.fees = fees
        self.delay = max(0, int(delay))

    def run(self, df: pd.DataFrame, signal: pd.Series) -> dict:
        sig = signal.shift(self.delay).fillna(0).astype(int)
        r = df["close"].pct_change().fillna(0.0)

        gross = sig.shift(1).fillna(0) * r  # position * next return
        trade = (sig != sig.shift(1)).astype(int)
        fee = trade * (self.fees.commission_bps + self.fees.slippage_bps) / 1e-4 / 10000  # corrected below
        # simpler: bps cost per trade
        fee = trade * (self.fees.commission_bps + self.fees.slippage_bps) / 1e4
        net = gross - fee
        eq = (1 + net).cumprod()

        metrics = {
            "total_return": float(eq.iloc[-1] - 1.0) if len(eq) else 0.0,
            "sharpe": sharpe(net),
            "max_drawdown": maxdd(eq),
            "calmar": calmar(net, eq),
            "trades": int(trade.sum())
        }
        return {"returns": net, "equity": eq, "metrics": metrics}
