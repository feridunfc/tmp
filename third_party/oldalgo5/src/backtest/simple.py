
import pandas as pd
import numpy as np

def returns_from_price(px: pd.Series) -> pd.Series:
    return px.pct_change().fillna(0.0)

def run_backtest_from_signals(df: pd.DataFrame, sig: pd.Series, *, commission=0.0005, slippage=0.0005, capital=100000.0):
    px = df["Close"].astype(float)
    sig = pd.Series(sig, index=px.index).astype(float).fillna(0.0).clip(-1,1)
    pos = sig.shift(1).fillna(0.0)
    ret = returns_from_price(px)
    change = pos.diff().fillna(pos).abs()
    costs = change * (commission + slippage)
    strat_ret = pos * ret - costs
    equity = (1 + strat_ret).cumprod() * float(capital)
    ann = 252
    mu = strat_ret.mean() * ann
    sd = strat_ret.std(ddof=0) * (ann ** 0.5)
    sharpe = float(mu / sd) if sd > 0 else 0.0
    dd = (equity / equity.cummax()) - 1.0
    metrics = {
        "AnnReturn": float(mu),
        "Vol": float(sd),
        "Sharpe": float(sharpe),
        "MaxDD": float(abs(dd.min())),
        "CAGR": float((equity.iloc[-1] / equity.iloc[0]) ** (ann / len(equity)) - 1 if len(equity) > 1 else 0.0),
        "FinalEquity": float(equity.iloc[-1]),
        "Bars": int(len(equity)),
    }
    trades_tbl = pd.DataFrame({"Signal": sig, "Price": px}, index=px.index)
    trades_tbl = trades_tbl[(change > 0)]
    trades_tbl["Action"] = np.where(pos.diff().fillna(pos) > 0, "Enter", "Exit")
    trades_tbl.index.name = "Date"
    return equity, pos, metrics, trades_tbl
