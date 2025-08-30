
# ruff: noqa: E402
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.tabs.data import run as data_tab
try:
    from ui.tabs.diagnostics import run as diag_tab
except Exception:
    diag_tab = None
try:
    from ui.tabs.regime import run as regime_tab
except Exception:
    regime_tab = None
try:
    from ui.tabs.mlops import run as mlops_tab
except Exception:
    mlops_tab = None
try:
    from ui.tabs.explain import run as explain_tab
except Exception:
    explain_tab = None

st.set_page_config(page_title="ALGO5 – W1..W14", page_icon="📦", layout="wide")
st.title("ALGO5 – Data → Execution → Risk/Metrics → Regime/MLOps/Explain")

tabs = ["Data"]
if diag_tab: tabs.append("Diagnostics")
if regime_tab: tabs.append("Regime")
if mlops_tab: tabs.append("MLOps")
if explain_tab: tabs.append("Explain")

tab = st.sidebar.radio("Tabs", tabs, key="main_tabs")
if tab == "Data":
    data_tab()
elif tab == "Diagnostics" and diag_tab:
    diag_tab()
elif tab == "Regime" and regime_tab:
    regime_tab()
elif tab == "MLOps" and mlops_tab:
    mlops_tab()
elif tab == "Explain" and explain_tab:
    explain_tab()
