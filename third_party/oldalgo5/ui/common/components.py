from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as pgo

_seq = 0
def _next_key(prefix: str = "k"):
    global _seq
    _seq += 1
    return f"{prefix}_{_seq}"

def plot_equity(eq: pd.Series, name: str = "Equity", key: str | None = None):
    if eq is None or len(eq) == 0:
        st.info("Grafik için veri yok.")
        return
    fig = pgo.Figure()
    fig.add_trace(pgo.Scatter(x=eq.index, y=eq.values, name=name, mode="lines"))
    fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=320)
    st.plotly_chart(fig, width='stretch', key=key or _next_key("eq"))

def plot_histogram(vals, title: str, bins: int = 50, key: str | None = None):
    try:
        s = pd.Series(vals).astype(float)
        s = s[np.isfinite(s)]
    except Exception:
        st.info(f"{title}: gösterilecek veri yok.")
        return
    if s.empty:
        st.info(f"{title}: gösterilecek veri yok.")
        return
    fig = pgo.Figure()
    fig.add_trace(pgo.Histogram(x=s.values, nbinsx=bins, name=title))
    fig.update_layout(title=title, bargap=0.05, height=300, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig, width='stretch', key=key or _next_key("hist"))
