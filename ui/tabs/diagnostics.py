import streamlit as st
from algo5.data.loader import demo_ohlcv
from algo5.metrics.core import sharpe, max_drawdown
from algo5.metrics.trading import equity_from_returns

def run():
    st.subheader("Diagnostics / Metrics")
    df = demo_ohlcv(periods=200)
    rets = df["Close"].pct_change().fillna(0.0)
    eq = equity_from_returns(100_000.0, rets)
    c1, c2, c3 = st.columns(3)
    c1.metric("Final Equity", f"{eq.iloc[-1]:,.2f}")
    c2.metric("Sharpe (ann.)", f"{sharpe(rets):.2f}")
    c3.metric("Max Drawdown", f"{max_drawdown(eq)*100:.2f}%")
    st.line_chart(eq)
