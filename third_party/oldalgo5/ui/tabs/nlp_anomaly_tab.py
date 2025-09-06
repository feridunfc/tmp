import streamlit as st, plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
def run(state):
    st.header("📰 NLP & ⚠️ Anomaly", anchor=False)
    if "data" not in state: st.warning("Önce data."); return
    df=state["data"]; sym=sorted(df["Symbol"].unique())[0]; px=df[df["Symbol"]==sym]["Close"].astype(float)
    method=st.radio("Method", ["Z-Score","IsolationForest"], key="anom_method")
    if method=="Z-Score":
        thr=st.slider("|z| ≥",2.0,6.0,3.0,0.5,key="anom_z_thr"); win=st.slider("Window",10,150,50,5,key="anom_z_win")
        rets=px.pct_change().fillna(0.0); z=(rets-rets.rolling(int(win),1).mean())/(rets.rolling(int(win),1).std(ddof=0).replace({0:1e-12})); mask=z.abs()>=float(thr)
    else:
        est=IsolationForest(n_estimators=200, contamination=0.02, random_state=42); X=px.pct_change().fillna(0.0).to_frame("ret"); est.fit(X); mask=(est.predict(X)==-1)
    fig=go.Figure(); fig.add_trace(go.Scatter(x=px.index,y=px.values,mode="lines",name="Price"))
    if mask.any(): fig.add_trace(go.Scatter(x=px.index[mask], y=px[mask], mode="markers", name="Anomaly"))
    fig.update_layout(height=320, margin=dict(l=8,r=8,t=8,b=8)); st.plotly_chart(fig, width='stretch', key="anom_plot")
