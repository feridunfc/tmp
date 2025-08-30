from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np

from algo5.data.loader import demo_ohlcv
from algo5.robustness.jitter import jitter_returns
from algo5.robustness.worst_days import remove_best_k_days, remove_worst_k_days
from algo5.robustness.mc import block_bootstrap_returns

# optional metrics (W3)
def _equity_from_returns(init_eq: float, rets: pd.Series) -> pd.Series:
    eq = np.cumprod(1.0 + rets.values) * float(init_eq)
    return pd.Series(eq, index=rets.index, name="equity")

def _sharpe(rets: pd.Series, risk_free: float = 0.0, periods: int = 252) -> float:
    if len(rets) < 2:
        return 0.0
    mu = rets.mean() * periods
    sd = rets.std(ddof=1) * np.sqrt(periods)
    return 0.0 if sd == 0 else float(mu / sd)

def _max_dd(eq: pd.Series) -> float:
    roll_max = eq.cummax()
    dd = eq / roll_max - 1.0
    return float(dd.min())

def run():
    st.subheader("Robustness / Stress Testing")
    df = st.session_state.get("data")
    if df is None or df.empty:
        df = demo_ohlcv(periods=252)
        st.session_state["data"] = df

    st.dataframe(df.tail(5))

    rets = df["Close"].pct_change().dropna()

    opt = st.selectbox("Scenario", ["Jitter", "Remove Best-k Days", "Remove Worst-k Days", "Block Bootstrap"], index=0, key="rb_scenario")
    if opt == "Jitter":
        sigma = st.number_input("Sigma", min_value=0.0, value=0.005, step=0.001, format="%.4f", key="rb_sigma")
        seed = st.number_input("Seed", min_value=0, value=42, step=1, key="rb_seed")
        stressed = jitter_returns(rets, sigma=float(sigma), seed=int(seed))
    elif opt == "Remove Best-k Days":
        k = st.number_input("k days", min_value=1, value=5, step=1, key="rb_k_best")
        stressed = remove_best_k_days(rets, k=int(k))
    elif opt == "Remove Worst-k Days":
        k = st.number_input("k days", min_value=1, value=5, step=1, key="rb_k_worst")
        stressed = remove_worst_k_days(rets, k=int(k))
    else:
        block = st.number_input("Block length", min_value=1, value=5, step=1, key="rb_block")
        seed = st.number_input("Seed", min_value=0, value=123, step=1, key="rb_seed_bs")
        stressed = block_bootstrap_returns(rets, block=int(block), seed=int(seed))

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Original equity**")
        eq0 = _equity_from_returns(100.0, rets)
        st.line_chart(eq0)
    with col2:
        st.write("**Stressed equity**")
        eq1 = _equity_from_returns(100.0, stressed)
        st.line_chart(eq1)

    m0 = {"sharpe": _sharpe(rets), "max_dd": _max_dd(eq0)}
    m1 = {"sharpe": _sharpe(stressed), "max_dd": _max_dd(eq1)}

    st.write("**Metrics**")
    st.json({"original": m0, "stressed": m1})
