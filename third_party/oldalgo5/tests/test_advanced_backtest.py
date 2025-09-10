from src.utils.data import demo_ohlcv, normalize_ohlcv
from src.core.strategies.registry_ext import create
from src.core.backtest.advanced_engine import AdvancedBacktestEngine

def test_backtest_runs():
    df = normalize_ohlcv(demo_ohlcv(300))
    strat = create("ma_crossover", fast_period=10, slow_period=30)
    prepared = strat.prepare(df)
    sig = strat.generate_signals(prepared)
    out = AdvancedBacktestEngine().run_backtest(prepared, sig)
    assert "equity" in out and "returns" in out and "trades" in out
    assert out["equity"].iloc[-1] > 0
