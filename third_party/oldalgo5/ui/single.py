from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as pgo

from ui.common.services import get_active_df, get_registry, ensure_backtest

def _param_inputs(schema, prefix: str="single"):
    if not isinstance(schema, (list, tuple)):
        return {}
    params = {}
    for i, f in enumerate(schema):
        if not isinstance(f, dict):
            continue
        ftype = f.get("type", "int")
        fname = f.get("name", f"param_{i}")
        fdef  = f.get("default", 0)
        key = f"{prefix}_{fname}_{i}"
        if ftype in ("int","integer"):
            params[fname] = st.number_input(fname, value=int(fdef), step=1, key=key)
        elif ftype in ("float","number"):
            params[fname] = st.number_input(fname, value=float(fdef), step=0.1, key=key)
        elif ftype in ("select","choice"):
            opts = f.get("options", [])
            params[fname] = st.selectbox(fname, options=opts, index=0 if opts else None, key=key)
        elif ftype in ("bool","boolean"):
            params[fname] = st.checkbox(fname, value=bool(fdef), key=key)
        else:
            params[fname] = st.text_input(fname, value=str(fdef), key=key)
    return params

def render(ctx):
    st.subheader("🔁 Tek Backtest")
    reg = get_registry()
    names = reg.list_strategies()
    if not names:
        st.error("Kayıtlı strateji bulunamadı.")
        return

    with st.form("single_form"):
        sel = st.selectbox("Strateji", names, index=0, key="single_strategy")
        # örnek param schema
        proto = reg.get_strategy(sel)
        try:
            schema = proto().param_schema() if hasattr(proto(), "param_schema") else []
        except Exception:
            schema = []
        params = _param_inputs(schema, prefix="single_param")
        run = st.form_submit_button("Çalıştır", width='stretch', type="primary")

    if not run:
        return

    df = get_active_df()
    # Kolonları normalize et
    lowmap = {c: c.lower() for c in df.columns}
    df = df.rename(columns=lowmap)
    if "close" not in df.columns and "Close" in lowmap.values():
        st.warning("Veride 'close' kolonu bulunamadı.")
        return

    # Stratejiyi kur
    Strat = reg.get_strategy(sel)
    strat = Strat(**params) if params else Strat()

    # Prepare + Signals
    try:
        prepared = strat.prepare(df) if hasattr(strat, "prepare") else df
    except Exception as e:
        st.error(f"prepare() hatası: {e}")
        return

    # 'Close' bekleyen legacy kodlara köprü
    if "Close" not in prepared.columns and "close" in prepared.columns:
        prepared["Close"] = prepared["close"]

    try:
        signals = strat.generate_signals(prepared)
    except Exception as e:
        st.error(f"generate_signals() hatası: {e}")
        return

    be = ensure_backtest(ctx)
    try:
        out = be.run_backtest(prepared, signals)
    except Exception as e:
        # Basit fallback PnL
        r = prepared["close"].pct_change().fillna(0.0)
        sig = signals.shift(1).fillna(0)
        net = (r*sig).fillna(0.0)
        equity = (1+net).cumprod()
        out = {"equity": equity, "metrics": {"total_return": float(equity.iloc[-1]-1.0)}}
        st.warning(f"BacktestEngine fallback kullanıldı: {e}")

    eq = out.get("equity", None)
    metrics = out.get("metrics", {})

    if isinstance(eq, pd.Series):
        fig = pgo.Figure()
        fig.add_trace(pgo.Scatter(x=eq.index, y=eq.values, name="Equity"))
        fig.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig, width='stretch')
    st.json(metrics)

    # Sinyal özetleri
    st.write("Sinyal dağılımı:")
    vc = signals.value_counts(dropna=False).sort_index()
    st.write(vc.to_frame("adet").T)
