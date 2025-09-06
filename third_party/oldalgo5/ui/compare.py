from __future__ import annotations
import pandas as pd
import streamlit as st
import plotly.graph_objects as pgo
from ui.common.services import get_active_df, get_registry, ensure_backtest

def render(ctx):
    st.subheader("⚖️ Karşılaştır")
    reg = get_registry()
    names = reg.list_strategies()

    with st.form("compare_form"):
        chosen = st.multiselect("Stratejiler", names, default=names[:1], key="compare_strats")
        run = st.form_submit_button("Karşılaştır", type="primary", width='stretch')
    if not run or not chosen:
        return

    df = get_active_df()
    df = df.rename(columns={c: c.lower() for c in df.columns})
    if "Close" not in df.columns and "close" in df.columns:
        df["Close"] = df["close"]

    be = ensure_backtest(ctx)
    curves, rows, errors = {}, [], []

    for name in chosen:
        try:
            Strat = reg.get_strategy(name)
            strat = Strat()
            prepared = strat.prepare(df) if hasattr(strat, "prepare") else df
            sig = strat.generate_signals(prepared)
            out = be.run_backtest(prepared, sig)
            eq = out["equity"]; curves[name]=eq
            m = out.get("metrics", {})
            rows.append({"Strateji": name,
                         "Toplam Getiri %": round(m.get("total_return", float(eq.iloc[-1]-1))*100, 2),
                         "Sharpe": round(m.get("sharpe", 0.0), 3),
                         "MaxDD %": round(m.get("max_drawdown", 0.0)*100, 2)})
        except Exception as e:
            errors.append((name, str(e)))

    if errors:
        with st.expander("Hata Alanlar"):
            for n,e in errors:
                st.error(f"{n}: {e}")

    if rows:
        cmp_df = pd.DataFrame(rows)
        st.dataframe(cmp_df, width='stretch')

    if curves:
        fig = pgo.Figure()
        for n,eq in curves.items():
            fig.add_trace(pgo.Scatter(x=eq.index, y=eq.values, name=n))
        st.plotly_chart(fig, width='stretch')
