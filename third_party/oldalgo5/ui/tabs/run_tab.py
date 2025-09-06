import streamlit as st
import plotly.graph_objects as go
import uuid
import pandas as pd
from ui.components.common import notify, kpi_row
from ui.services.strategy_registry import get_registry
from ui.services import sdk
from ui.services import expdb


def _param_widget(name, spec, prefix):
    t = spec.get("type", "int");
    label = spec.get("label", name)
    if t == "int":
        return st.number_input(label, min_value=int(spec.get("min", 0)), max_value=int(spec.get("max", 100)),
                               value=int(spec.get("default", 0)), step=int(spec.get("step", 1)), key=f"{prefix}_{name}")
    elif t == "float":
        return st.number_input(label, min_value=float(spec.get("min", 0.0)), max_value=float(spec.get("max", 1.0)),
                               value=float(spec.get("default", 0.0)), step=float(spec.get("step", 0.01)),
                               key=f"{prefix}_{name}")
    else:
        return st.text_input(label, value=str(spec.get("default", "")), key=f"{prefix}_{name}")


def run(state):
    st.header("🏃 Run", anchor=False)
    if "data" not in state:
        notify("Önce Data sekmesinden veri yükleyin.", "warning");
        return
    commission = float(state.get("commission_bps", 5.0)) / 10000.0;
    slippage = float(state.get("slippage_bps", 10.0)) / 10000.0
    capital = float(state.get("capital", 100000.0));
    latency_bars = int(state.get("latency_bars", 0))
    risk_cfg = {"vol_target": float(state.get("vol_target", 0.15)), "max_dd_stop": bool(state.get("max_dd_stop", True)),
                "max_dd_limit": float(state.get("max_dd_limit", 0.25))}
    REG, ORDER = get_registry()
    keys = [k for k, _ in ORDER];
    labels = {k: n for k, n in ORDER}
    strat_key = st.selectbox("Strategy", keys, format_func=lambda k: labels[k], key="run_strat")
    schema = REG[strat_key]["schema"];
    params = {}
    for pname, spec in schema.items():
        params[pname] = _param_widget(pname, spec, prefix=f"run_param_{pname}")
    if not st.button("Run Backtest", key="run_btn"): return
    df = state["data"];
    rows = [];
    per = {}
    for sym, g in df.groupby("Symbol", group_keys=False):
        sig = REG[strat_key]["gen"](g, params)
        eq, pos, m, trades = sdk.run_backtest_with_signals(g, sig, commission=commission, slippage=slippage,
                                                           capital=capital, latency_bars=latency_bars,
                                                           risk_cfg=risk_cfg)
        per[sym] = {"equity": eq, "metrics": m, "trades": trades};
        r = m.copy();
        r["Symbol"] = sym;
        rows.append(r)
    met = pd.DataFrame(rows).set_index("Symbol");
    state["last_metrics"] = met
    kpi_row(
        {"Sharpe": float(met["Sharpe"].mean()), "CAGR": float(met["CAGR"].mean()), "MaxDD": float(met["MaxDD"].mean()),
         "AnnRet": float(met["AnnReturn"].mean()), "N": len(met)}, prefix="run")

    # DÜZELTME: width parametresi kaldırıldı
    st.dataframe(met, key="run_metrics")

    sym0 = met.index[0];
    eq = per[sym0]["equity"]
    fig = go.Figure();
    fig.add_trace(go.Scatter(x=eq.index, y=eq.values, mode="lines", name=f"Equity {sym0}"));
    fig.update_layout(height=360, margin=dict(l=8, r=8, t=8, b=8))

    # DÜZELTME: width parametresi kaldırıldı
    st.plotly_chart(fig, key="run_plot")

    st.subheader("Trades")

    # DÜZELTME: width parametresi kaldırıldı
    st.dataframe(per[sym0]["trades"].tail(20), key="run_trades")

    run_id = str(uuid.uuid4())[:8]
    expdb.write_run(run_id=run_id, strategy=labels[strat_key], params=params,
                    metrics={k: float(met[k].mean()) for k in met.columns}, symbols=list(met.index), equity_series=eq)
    st.success(f"Run saved: {run_id}")