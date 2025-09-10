from __future__ import annotations
import streamlit as st

def render(ctx):
    st.subheader("📈 Paper Trading (Demo)")
    st.info("Gateway/Order emülasyonu henüz dummy. Sonraki sürümde canlı veri bağlayacağız.")
    st.write("• Sanal bakiye: 100,000\n• Emir türleri: MARKET (demo)\n• İşlem geçmişi: (yakında)")
