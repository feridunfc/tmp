from __future__ import annotations
import streamlit as st
import platform, sys, importlib

def render(ctx):
    st.subheader("🩺 Sistem Tanılama")
    st.write({"python": sys.version, "platform": platform.platform()})
    for pkg in ["pandas","numpy","optuna","plotly","sklearn","algo2"]:
        try:
            m = importlib.import_module(pkg)
            ver = getattr(m, "__version__", "unknown")
            st.write(f"✔ {pkg} {ver}")
        except Exception as e:
            st.write(f"✖ {pkg}: {e}")
