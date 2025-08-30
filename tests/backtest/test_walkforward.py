from algo5.data.loader import demo_ohlcv
from algo5.engine.backtest.walkforward import WFConfig, time_series_windows, walk_forward
from algo5.train.runner import train_eval_simple

def test_time_series_windows_shape():
    n = 120
    cfg = WFConfig(n_splits=3, train_frac=0.7)
    wins = list(time_series_windows(n, cfg))
    assert len(wins) >= 2
    for tr, va in wins:
        assert tr.stop < va.stop

def test_walk_forward_runs():
    df = demo_ohlcv(180)
    cfg = WFConfig(n_splits=3, train_frac=0.7)
    out = walk_forward(df, lambda d, p: train_eval_simple(d, p), {"window": 5, "threshold": 0.0}, cfg)
    assert out["splits"] >= 2
