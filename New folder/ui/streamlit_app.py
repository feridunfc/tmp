# ui/streamlit_app.py
# --- bootstrap sys.path so 'ui' and 'algo5' imports always work
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]   # repo root
SRC  = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import streamlit as st
from ui.tabs.data import run as data_tab


import streamlit as st
from ui.tabs.data import run as data_tab

st.set_page_config(page_title="ALGO5", page_icon="📦", layout="wide")
st.title("ALGO5 – Week-1 Data")

tab = st.sidebar.radio("Tabs", ["Data"])
if tab == "Data":
    data_tab()
