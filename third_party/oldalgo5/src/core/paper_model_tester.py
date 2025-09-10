
from __future__ import annotations
import pandas as pd
from typing import Callable, Dict
from .execution.paper_engine import PaperTradingEngine

def _ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    def pick(name):
        return cols.get(name, name.capitalize())
    need = {"Open": pick("open"), "High": pick("high"), "Low": pick("low"), "Close": pick("close")}
    out = pd.DataFrame({k: df[v] for k,v in need.items() if v in df.columns}, index=df.index)
    return out

class ModelPaperTester:
    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.001, slippage_rate: float = 0.001):
        self.engine = PaperTradingEngine(initial_capital, commission_rate, slippage_rate)

    def run_backtest(self, data: pd.DataFrame, model_predictor: Callable[[pd.DataFrame], float], symbol: str = "AAPL", trade_size: float = 1.0, buy_thr: float = 0.6, sell_thr: float = 0.4) -> pd.DataFrame:
        df = _ensure_cols(data)
        res = []
        for i in range(len(df)):
            cur = df.iloc[: i+1]
            self.engine.update_market_data(symbol, cur["Close"])
            pred = float(model_predictor(cur))
            if pred >= buy_thr:
                self.engine.place_order(symbol, 'buy', trade_size, 'market')
            elif pred <= sell_thr:
                self.engine.place_order(symbol, 'sell', trade_size, 'market')
            self.engine.update_portfolio_value()
            res.append({
                "timestamp": cur.index[-1],
                "price": float(cur["Close"].iloc[-1]),
                "prediction": pred,
                "portfolio_value": float(self.engine.portfolio_value),
                "cash": float(self.engine.cash),
            })
        return pd.DataFrame(res).set_index("timestamp")

    @staticmethod
    def max_drawdown(series: pd.Series) -> float:
        peak = series.cummax()
        dd = (series - peak) / peak
        return float(dd.min())

    def metrics(self, results: pd.DataFrame) -> Dict[str, float]:
        ret = results["portfolio_value"].pct_change().fillna(0.0)
        ann = 252
        mu = float(ret.mean() * ann)
        sd = float(ret.std(ddof=0) * (ann ** 0.5))
        sharpe = mu / sd if sd > 0 else 0.0
        mdd = abs(self.max_drawdown(results["portfolio_value"]))
        total_ret = float(results["portfolio_value"].iloc[-1] / results["portfolio_value"].iloc[0] - 1.0) if len(results) > 1 else 0.0
        return {"AnnReturn": mu, "Vol": sd, "Sharpe": sharpe, "MaxDD": mdd, "TotalReturn": total_ret}
