# ruff: noqa: E402
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.tabs.data import run as data_tab
from ui.tabs.train import run as train_tab
from ui.tabs.walk import run as walk_tab

st.set_page_config(page_title="ALGO5 – W1..W4", page_icon="📦", layout="wide")
st.title("ALGO5 – Data, Train/HPO, Walk-Forward")

tab = st.sidebar.radio("Tabs", ["Data", "Train", "Walk-Forward"])
if tab == "Data":
    data_tab()
elif tab == "Train":
    train_tab()
elif tab == "Walk-Forward":
    walk_tab()
