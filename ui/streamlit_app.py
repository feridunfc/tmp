# ruff: noqa: E402
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.tabs.data import run as data_tab

st.set_page_config(page_title="ALGO5 – Week-1", page_icon="📦", layout="wide")
st.title("ALGO5 – Week-1 Data")

tab = st.sidebar.radio("Tabs", ["Data"])
if tab == "Data":
    data_tab()
