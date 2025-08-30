# ruff: noqa: E402
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.tabs.data import run as data_tab
from ui.tabs.live import run as live_tab
from ui.tabs.robustness import run as rb_tab
from ui.tabs.diagnostics import run as diag_tab

st.set_page_config(page_title="ALGO5 – W1..W6", page_icon="📦", layout="wide")
st.title("ALGO5 – Data, Live (Paper) & Robustness")

tab = st.sidebar.radio("Tabs", ["Data", "Live (Paper)", "Robustness", "Diagnostics"], key="main_tabs")
if tab == "Data":
    data_tab()
elif tab == "Live (Paper)":
    live_tab()
elif tab == "Robustness":
    rb_tab()
elif tab == "Diagnostics":
    diag_tab()
