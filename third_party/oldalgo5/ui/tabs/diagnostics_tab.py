import streamlit as st, numpy as np, plotly.graph_objects as go
def _acf(x, nlags=20):
    x = np.asarray(x); x = x - x.mean(); res=[1.0]
    for k in range(1, nlags+1):
        num=(x[:-k]*x[k:]).sum(); den=(x*x).sum(); res.append(float(num/den) if den!=0 else 0.0)
    return res
def run(state):
    st.header("🩺 Diagnostics", anchor=False)
    if "data" not in state: st.info("Önce Run."); return
    df=state["data"]; sym=sorted(df["Symbol"].unique())[0]; px=df[df["Symbol"]==sym]["Close"].astype(float); rets=px.pct_change().fillna(0.0)
    c1,c2=st.columns(2)
    with c1:
        fig=go.Figure(); fig.add_trace(go.Histogram(x=rets,name="Returns")); fig.update_layout(title="Return Dist",height=300,margin=dict(l=8,r=8,t=30,b=8)); st.plotly_chart(fig, width='stretch', key="diag_hist")
    with c2:
        ac=_acf(rets.values,20); fig=go.Figure(); fig.add_trace(go.Bar(x=list(range(len(ac))), y=ac)); fig.update_layout(title="ACF(20)",height=300,margin=dict(l=8,r=8,t=30,b=8)); st.plotly_chart(fig, width='stretch', key="diag_acf")
