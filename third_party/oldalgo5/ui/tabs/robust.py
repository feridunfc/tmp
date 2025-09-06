from __future__ import annotations
import streamlit as st
import numpy as np
from ui.common.components import plot_histogram

def render(ctx):
    st.subheader("🛡️ Robustness Testleri")
    demo = np.random.normal(0, 1, 1000)
    plot_histogram(demo, "Demo Sharpe Dağılımı", bins=40, key="robust_hist")
