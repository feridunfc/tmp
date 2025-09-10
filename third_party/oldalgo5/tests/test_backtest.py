
import pandas as pd
from src.backtest.simple import run_backtest_from_signals
def test_backtest_simple():
    idx = pd.date_range("2020-01-01", periods=200, freq="B")
    df = pd.DataFrame({"Open":100.0,"High":100.0,"Low":100.0,"Close":100.0,"Volume":1}, index=idx)
    import numpy as np
    sig = pd.Series(([0]*50 + [1]*50 + [0]*50 + [-1]*50)[:len(idx)], index=idx)
    eq, pos, met, t = run_backtest_from_signals(df, sig)
    assert met["Bars"] == len(idx)
