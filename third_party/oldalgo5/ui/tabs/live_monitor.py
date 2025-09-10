import streamlit as st, numpy as np, time, pandas as pd
def run(state):
    st.header("📡 Live Monitor", anchor=False)
    if "mon_series" not in state:
        state["mon_series"]=pd.Series([100.0])
    running = st.checkbox("Run", value=False, key="mon_run")
    ph = st.empty()
    while running:
        last = float(state["mon_series"].iloc[-1])
        new = last*(1+np.random.normal(0,0.002))
        state["mon_series"] = pd.concat([state["mon_series"], pd.Series([new])], ignore_index=True).iloc[-500:]
        ph.line_chart(state["mon_series"])
        time.sleep(0.2)
