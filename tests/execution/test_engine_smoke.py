import pandas as pd

from algo5.metrics.metrics import compute_metrics, compute_nav


def test_metrics_nav_smoke():
    rets = pd.Series(
        [0.0, 0.01, -0.005, 0.002], index=pd.date_range("2024-01-01", periods=4, freq="D")
    )
    nav = compute_nav(rets)
    assert isinstance(nav, pd.Series)
    assert len(nav) == 4

    m = compute_metrics(nav)
    for k in ("sharpe", "max_drawdown", "total_return", "vol"):
        assert k in m
    assert all(isinstance(v, float) for v in m.values())
