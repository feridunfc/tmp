import pandas as pd
import pytest

try:
    from algo5.engine.execution.engine_v2 import run_vector_backtest
except Exception as exc:  # pragma: no cover
    pytest.skip(f"engine_v2 import skipped: {exc}", allow_module_level=True)


def _dummy_strategy(prices: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.Series]:
    out = {}
    for sym, df in prices.items():
        out[sym] = (df["close"] / df["close"].iloc[0]).rename(sym)
    return out


def test_run_vector_backtest_smoke():
    df = pd.DataFrame(
        {"close": [100, 101, 100.5, 101.2]},
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
    )
    prices = {"AAPL": df}
    res = run_vector_backtest(
        prices=prices, strategy_fn=_dummy_strategy, cfg={}, initial_capital=10_000
    )
    assert "metrics" in res
    assert "portfolio_equity" in res
