from __future__ import annotations
import pandas as pd
import streamlit as st
import plotly.graph_objects as pgo

from ui.common.services import get_active_df, get_registry, ensure_backtest

def _tscv_splits(n: int, k: int):
    # Basit TimeSeriesSplit fallback (sklearn yoksa)
    fold_size = n // (k+1)
    for i in range(k):
        tr_end = fold_size*(i+1)
        te_end = fold_size*(i+2)
        yield range(0, tr_end), range(tr_end, min(te_end, n))

def render(ctx):
    st.subheader("🚶 Walk-Forward")
    reg = get_registry()
    names = reg.list_strategies()

    with st.form("wf_form"):
        sel = st.selectbox("Strateji", names, index=0, key="wf_strategy")
        splits = st.slider("WF Split sayısı", 2, 10, 4, key="wf_splits")
        run = st.form_submit_button("Koş", type="primary", width='stretch')
    if not run:
        return

    df = get_active_df()
    df = df.rename(columns={c: c.lower() for c in df.columns})
    if "Close" not in df.columns and "close" in df.columns:
        df["Close"] = df["close"]

    Strat = reg.get_strategy(sel)
    be = ensure_backtest(ctx)

    eq_all = []
    idx = df.index

    for tr, te in _tscv_splits(len(df), splits):
        dtr = df.iloc[list(tr)].copy()
        dte = df.iloc[list(te)].copy()
        strat = Strat()
        pre_tr = strat.prepare(dtr) if hasattr(strat, "prepare") else dtr
        pre_te = strat.prepare(dte) if hasattr(strat, "prepare") else dte
        sig = strat.generate_signals(pre_te)
        out = be.run_backtest(pre_te, sig)
        eq_all.append(out["equity"])

    if eq_all:
        eq = pd.concat(eq_all).sort_index()
        fig = pgo.Figure()
        fig.add_trace(pgo.Scatter(x=eq.index, y=eq.values, name="WF Equity"))
        st.plotly_chart(fig, width='stretch')
