from __future__ import annotations
import streamlit as st
import pandas as pd
from ui.common.services import get_active_df, get_registry, ensure_backtest

def render(ctx):
    st.subheader("🔎 HPO (Demo)")
    st.info("Basit bir HPO vitrini: Optuna entegrasyonu henüz isteğe bağlı. Bu demo, farklı parametre kombinasyonlarını dener.")
    reg = get_registry()
    names = reg.list_strategies()

    with st.form("hpo_form"):
        sel = st.selectbox("Strateji", names, index=0, key="hpo_strategy")
        n_trials = st.number_input("Deneme sayısı", 1, 100, 10, key="hpo_trials")
        run = st.form_submit_button("Başlat", type="primary", width='stretch')
    if not run:
        return

    Strat = reg.get_strategy(sel)
    df = get_active_df().rename(columns={c: c.lower() for c in get_active_df().columns})
    if "Close" not in df.columns and "close" in df.columns:
        df["Close"] = df["close"]
    be = ensure_backtest(ctx)

    rows = []
    for i in range(int(n_trials)):
        # çok basit önerici: MA stratejisi varsayımı
        params = {}
        if sel.lower().startswith("ma"):
            short = 10 + 2*i
            long  = max(short+5, 30 + 3*i)
            params = {"short": short, "long": long}
        strat = Strat(**params)
        pre = strat.prepare(df) if hasattr(strat, "prepare") else df
        sig = strat.generate_signals(pre)
        out = be.run_backtest(pre, sig)
        eq = out["equity"]
        total_return = float(eq.iloc[-1]-1)
        rows.append({"trial": i, "params": params, "total_return": round(total_return*100, 2)})
    st.dataframe(pd.DataFrame(rows), width='stretch')
