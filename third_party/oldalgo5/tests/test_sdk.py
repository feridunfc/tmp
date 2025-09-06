import pandas as pd
from ui.services import sdk
def test_load_and_validate():
    df = sdk.load_data("AAPL,MSFT", "1d")
    assert isinstance(df.index, pd.DatetimeIndex)
    sdk.validate_data(df)
def test_backtest_smoke():
    df = sdk.load_data("AAPL", "1d")
    sig = (df["Close"] > df["Close"].rolling(10,1).mean()).astype(int)
    eq,pos,m,tr = sdk.run_backtest_with_signals(df, sig, commission=0.0001, slippage=0.0001, capital=100000.0, latency_bars=1, risk_cfg={"vol_target":0.1,"max_dd_stop":True,"max_dd_limit":0.3})
    assert "Sharpe" in m and eq.iloc[-1] > 0
