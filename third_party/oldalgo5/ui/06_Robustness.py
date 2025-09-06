import streamlit as st
import pandas as pd
from src.reporting.robustness import bootstrap_from_returns, MCConfig, crisis_report

st.set_page_config(page_title="ALGO2 • Robustness", layout="wide")
st.title("🛡️ Robustness & Monte Carlo")

mode = st.radio("Veri Türü", ["Returns (bar)", "Trades (pnl_pct)"], horizontal=True)
uploaded = st.file_uploader("CSV yükle", type=["csv"])

cfg_col, _ = st.columns([1,3])
with cfg_col:
    n_paths = st.number_input("Simülasyon Sayısı", 100, 10000, 1000, 100)
    method = st.selectbox("Bootstrap", ["iid", "block"], index=0)
    block = st.number_input("Block Length", 2, 200, 20, 1)

if uploaded:
    df = pd.read_csv(uploaded)
    if mode.startswith("Returns"):
        s = df.get("returns")
    else:
        s = df.get("pnl_pct")
    if s is None:
        st.error("Beklenen kolon bulunamadı.")
    else:
        res = bootstrap_from_returns(s, MCConfig(n_paths=int(n_paths), method=method, block=int(block)))
        st.dataframe(res.describe().T, width='stretch')
        st.bar_chart(res["sharpe"])
        st.bar_chart(res["max_dd"])
        st.subheader("Kriz Raporu")
        st.dataframe(crisis_report(s), width='stretch')
else:
    st.info("CSV yükleyin (returns veya pnl_pct kolonu).")
