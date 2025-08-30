# ruff: noqa: E402
from pathlib import Path
import sys

# --- add repo root to sys.path (run: streamlit run ui/streamlit_app.py)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# Tabs
from ui.tabs.data import run as data_tab
try:
    from ui.tabs.diagnostics import run as diag_tab
    HAS_DIAG = True
except Exception:
    HAS_DIAG = False

st.set_page_config(page_title="ALGO5 – W1/W2/W3", page_icon="📦", layout="wide")
st.title("ALGO5 – Data, Execution & Metrics")

tabs = ["Data"] + (["Diagnostics"] if HAS_DIAG else [])
tab = st.sidebar.radio("Tabs", tabs, key="sidebar_tabs")

if tab == "Data":
    data_tab()
elif tab == "Diagnostics" and HAS_DIAG:
    diag_tab()
