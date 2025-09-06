
import pandas as pd
from src.core.execution.paper_engine import PaperTradingEngine

def test_paper_engine_basic():
    eng = PaperTradingEngine(10000.0, commission_rate=0.0, slippage_rate=0.0)
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    px = pd.Series([100.0, 101.0, 102.0], index=idx)
    eng.update_market_data("AAPL", px.iloc[:1])
    eng.place_order("AAPL", "buy", 10, "market")
    assert eng.positions["AAPL"].quantity == 10
    eng.update_market_data("AAPL", px.iloc[:2])
    eng.place_order("AAPL", "sell", 5, "market")
    assert eng.positions["AAPL"].quantity == 5
    eng.update_portfolio_value()
    assert eng.portfolio_value > 0
