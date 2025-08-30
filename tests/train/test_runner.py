import numpy as np
from algo5.data.loader import demo_ohlcv
from algo5.train.runner import train_eval_simple

def test_train_eval_simple_runs():
    df = demo_ohlcv(180)
    res = train_eval_simple(df, {"window": 5, "threshold": 0.0}, train_frac=0.7)
    assert 0.0 <= res.acc <= 1.0
    assert res.n_train > 0 and res.n_val > 0
