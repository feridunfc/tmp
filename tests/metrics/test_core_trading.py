import pandas as pd
from algo5.metrics.core import sharpe, max_drawdown
from algo5.metrics.trading import equity_from_returns

def test_metrics_on_toy_series():
    rets = pd.Series([0.01, -0.02, 0.01])
    eq = equity_from_returns(100.0, rets)
    assert abs(eq.iloc[-1] - 99.9698) < 1e-3  # 100 * 1.01 * 0.98 * 1.01
    s = sharpe(rets, risk_free=0.0, periods=252)
    assert abs(s - 0.0) < 1e-9
    dd = max_drawdown(eq)
    assert dd < 0
    assert abs(dd - (-0.01012)) < 5e-4
