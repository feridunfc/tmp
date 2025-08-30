import streamlit as st, pandas as pd
from algo5.compliance.report import build_html_report
from algo5.compliance.signature import file_sha256
def run():
    st.header("Compliance Report (W7)")
    m = {"sharpe": 1.23, "trades": 12, "max_dd": -0.1}
    t = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=5, freq="D"),"side":["buy","sell","buy","sell","buy"],"qty":[1]*5,"price":[100,101,102,103,104]})
    if st.button("Build Report", key="btn_build_report"):
        path = build_html_report("demo_run", m, t, outdir=".reports"); st.success(f"Report created: {path}"); st.code(file_sha256(path))
