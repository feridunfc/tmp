import pandas as pd
import numpy as np
from strategies.registry import list_strategies, get_strategy, bootstrap

bootstrap("static")

def _df(n=60):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n))
    return pd.DataFrame({
        "Open": close, "High": close+1, "Low": close-1, "Close": close, "Volume": 1000
    }, index=idx)

def test_smoke_all():
    df = _df()
    for name in list_strategies():
        s = get_strategy(name)
        d2 = s.prepare(df)
        sig = s.generate_signals(d2)
        assert len(sig) == len(d2)
