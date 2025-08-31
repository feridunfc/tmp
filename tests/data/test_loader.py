
import pandas as pd
from src.algo5.data.loader import demo_ohlcv, bear_market_demo

def test_loader_shapes_and_tz():
    df = demo_ohlcv(periods=10, seed=1)
    assert set(["Open","High","Low","Close","volume","co2e_per_tick"]).issubset(df.columns)
    assert isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None

def test_bear_trend_decreases():
    df = bear_market_demo(periods=50, seed=1)
    assert df["Close"].iloc[-1] < df["Close"].iloc[0]
