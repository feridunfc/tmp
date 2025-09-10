import pandas as pd, numpy as np
from typing import Dict, Tuple
from ui.services import risk as R

def _ensure_datetime_index(n=600):
    end = pd.Timestamp.today().normalize()
    return pd.date_range(end=end, periods=n, freq="B")

def load_data(symbols="AAPL", interval="1d", start=None, end=None):
    rng = np.random.default_rng(7); idx = _ensure_datetime_index(600); dfs = []
    for sym in [s.strip() for s in str(symbols).split(",") if s.strip()]:
        ret = rng.normal(0.0003, 0.01, len(idx))
        price = 100*(1+pd.Series(ret, index=idx)).cumprod()
        high = price*(1+rng.uniform(0.0,0.01,len(idx)))
        low  = price*(1-rng.uniform(0.0,0.01,len(idx)))
        openp = price.shift(1).fillna(price.iloc[0])
        vol = rng.integers(2e5, 8e5, len(idx))
        df = pd.DataFrame({"Open":openp,"High":high,"Low":low,"Close":price,"Volume":vol}, index=idx)
        df["Symbol"]=sym; dfs.append(df)
    out = pd.concat(dfs, axis=0); out.index.name="Date"
    if start is not None: out = out[out.index >= pd.to_datetime(start)]
    if end is not None: out = out[out.index <= pd.to_datetime(end)]
    return out.sort_index()

def validate_data(df: pd.DataFrame):
    req = {"Open","High","Low","Close","Volume","Symbol"}
    if not req.issubset(df.columns): raise ValueError("Missing required OHLCV columns")
    if not isinstance(df.index, pd.DatetimeIndex): raise TypeError("Index must be DatetimeIndex")
    return True

def returns_from_price(px: pd.Series) -> pd.Series:
    return px.astype(float).pct_change().fillna(0.0)

# ui/services/sdk.py

def run_backtest_with_signals(df: pd.DataFrame, signals: pd.Series, *, commission=0.001, slippage=0.0005, capital=100000.0, latency_bars=0, risk_cfg:Dict=None):
    px  = df["Close"].astype(float)
    sig = pd.Series(signals, index=px.index).astype(int).fillna(0)

    if int(latency_bars) > 0:
        sig = sig.shift(int(latency_bars)).fillna(0)

    # Pozisyon (-1/0/1) ve getiriler
    pos = sig.shift(1).fillna(0).clip(-1, 1)
    ret = returns_from_price(px)

    # ✅ Vektörel trade değişimi: -1→+1 geçişte 2 trade sayılır
    change = pos.diff().fillna(pos)             # ilk bar'da pos kadar değişim
    trades = change.abs()                        # 0, 1, 2 ...
    costs  = trades * (commission + slippage)

    raw_ret   = pos * ret - costs

    risk_cfg = risk_cfg or {}
    strat_ret = R.apply_vol_target(raw_ret, target=risk_cfg.get("vol_target"))
    equity    = (1 + strat_ret).cumprod() * float(capital)

    if risk_cfg.get("max_dd_stop", False):
        equity    = R.apply_maxdd_stop(equity, dd_limit=float(risk_cfg.get("max_dd_limit", 0.25)))
        strat_ret = equity.pct_change().fillna(0.0)

    ann   = 252
    mu    = strat_ret.mean() * ann
    sd    = strat_ret.std(ddof=0) * (ann ** 0.5)
    sharpe = float(mu / sd) if sd > 0 else 0.0
    dd     = (equity / equity.cummax() - 1.0)
    metrics = {
        "AnnReturn": float(mu),
        "Vol": float(sd),
        "Sharpe": float(sharpe),
        "MaxDD": float(abs(dd.min())),
        "CAGR": float((equity.iloc[-1] / equity.iloc[0]) ** (ann / len(equity)) - 1 if len(equity) > 1 else 0.0),
        "FinalEquity": float(equity.iloc[-1]),
        "Bars": int(len(equity)),
    }

    # ✅ Trades tablosu: mask + vektörel Action/Price/Signal
    trade_mask = trades > 0
    trades_tbl = pd.DataFrame({
        "Action": np.where(change > 0, "Enter", "Exit"),
        "Price": px.astype(float),
        "Signal": sig.astype(int),
    })
    trades_tbl = trades_tbl[trade_mask]
    trades_tbl.index.name = "Date"

    return equity, pos, metrics, trades_tbl
