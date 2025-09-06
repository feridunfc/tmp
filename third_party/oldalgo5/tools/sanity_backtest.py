from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "src").resolve()
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ["PYTHONPATH"] = str(SRC)

import numpy as np
import pandas as pd
from strategies.registry import get_strategy, bootstrap

bootstrap("static")

def toy_df(n=300):
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n))
    df = pd.DataFrame({
        "Open": close + np.random.randn(n)*0.1,
        "High": close + np.abs(np.random.randn(n))*0.5,
        "Low":  close - np.abs(np.random.randn(n))*0.5,
        "Close": close,
        "Volume": 1000 + np.random.randint(0, 100, size=n),
    }, index=idx)
    return df

def pnl_from_signals(df, sig, fee_bps=5):
    ret = df["Close"].pct_change().fillna(0.0)
    pos = sig.shift(1).fillna(0.0)
    gross = pos * ret
    # basit komisyon: pozisyon değişiminde bps
    turn = pos.diff().abs().fillna(0.0)
    fees = turn * (fee_bps/10000.0)
    net = gross - fees
    eq = (1.0 + net).cumprod()
    sharpe = np.sqrt(252) * (net.mean() / (net.std() + 1e-12))
    return {
        "sharpe": float(sharpe),
        "cumret": float(eq.iloc[-1] - 1.0),
        "trades": int((turn > 0).sum())
    }

for key, params in [
    ("rb_ma_crossover", {"fast": 10, "slow": 30}),
    ("rb_atr_breakout", {"atr_window": 14, "k": 2.0}),
]:
    s = get_strategy(key)
    df = toy_df()
    d2 = s.prepare(df, **params)
    sig = s.generate_signals(d2, **params)
    res = pnl_from_signals(d2, sig)
    print(f"{key}: sharpe={res['sharpe']:.2f}  cumret={res['cumret']:.2%}  trades={res['trades']}")
