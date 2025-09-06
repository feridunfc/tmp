import streamlit as st, numpy as np, plotly.graph_objects as go
def run(state):
    st.header("🛡️ Robustness", anchor=False)
    if "data" not in state: st.info("Önce Run."); return
    n = st.number_input("Monte Carlo N", 50, 2000, 200, 50, key="robust_n")
    df=state["data"]; sym=sorted(df["Symbol"].unique())[0]; px=df[df["Symbol"]==sym]["Close"].astype(float)
    rets=px.pct_change().fillna(0.0).to_numpy(); rng=np.random.default_rng(123); finals=[float(np.prod(1+rets+rng.normal(0.0,0.01,len(rets)))) for _ in range(int(n))]
    fig=go.Figure(); fig.add_trace(go.Histogram(x=finals,name="Final Equity")); fig.update_layout(height=320, margin=dict(l=8,r=8,t=8,b=8)); st.plotly_chart(fig, width='stretch', key="robust_hist")
