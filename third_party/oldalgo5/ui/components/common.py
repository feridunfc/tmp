import streamlit as st, datetime
def sidebar_controls(state: dict):
    st.sidebar.header("Global Settings", anchor=False)
    state["symbols"] = st.sidebar.text_input("Symbols", value=state.get("symbols","AAPL,MSFT,BTC-USD"), key="sb_symbols")
    state["interval"] = st.sidebar.selectbox("Interval", ["1d","1h","5m"], index=["1d","1h","5m"].index(state.get("interval","1d")), key="sb_interval")
    state["mode"] = st.sidebar.radio("Mode", ["Backtest","Live (Paper)"], index=0, key="sb_mode")
    today = datetime.date.today(); default_start = today.replace(year=today.year-2)
    state["start_date"] = st.sidebar.date_input("Start Date", value=state.get("start_date", default_start), key="sb_start")
    state["end_date"] = st.sidebar.date_input("End Date", value=state.get("end_date", today), key="sb_end")
    st.sidebar.markdown("---")
    state["commission_bps"] = st.sidebar.number_input("Commission (bps)", value=float(state.get("commission_bps",5.0)), step=0.5, key="sb_comm")
    state["slippage_bps"] = st.sidebar.number_input("Slippage (bps)", value=float(state.get("slippage_bps",10.0)), step=0.5, key="sb_slip")
    state["capital"] = st.sidebar.number_input("Initial Capital", value=float(state.get("capital",100000.0)), step=1000.0, key="sb_capital")
    state["max_dd_stop"] = st.sidebar.checkbox("MaxDD Stop", value=bool(state.get("max_dd_stop", True)), key="sb_dd_stop")
    state["max_dd_limit"] = st.sidebar.number_input("MaxDD Limit", value=float(state.get("max_dd_limit", 0.25)), step=0.01, key="sb_max_dd")
    state["vol_target"] = st.sidebar.number_input("Vol Target (ann.)", value=float(state.get("vol_target", 0.15)), step=0.01, key="sb_vol_target")
    state["latency_bars"] = st.sidebar.number_input("Latency (bars)", value=int(state.get("latency_bars", 0)), min_value=0, max_value=5, step=1, key="sb_latency")
# ui/components/common.py
import streamlit as st

def kpi_row(values: dict, *, prefix: str = "") -> None:
    """
    Basit KPI satırı. NOT: st.metric 'key' parametrini desteklemez.
    values: {"Sharpe": 1.23, "CAGR": 0.15, ...}
    """
    cols = st.columns(len(values))
    for col, (k, v) in zip(cols, values.items()):
        # delta kullanmak isterseniz col.metric(label, value, delta=...)
        if isinstance(v, float):
            col.metric(k, f"{v:.4f}")
        else:
            col.metric(k, str(v))

def notify(msg, level="info"):
    getattr(st, level)(msg)
