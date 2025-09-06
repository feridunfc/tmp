from __future__ import annotations
import streamlit as st

def render(ctx):
    st.subheader("🧠 Train / Retrain")
    st.info("Model eğitimi ve periyodik yeniden eğitim pipeline'ı sonraki sürüme hazırlanıyor.")
    st.write("• Plan: feature store + model registry + cron retrain")
