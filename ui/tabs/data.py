import os
import streamlit as st
from algo5.data.loader import demo_ohlcv
from algo5.data.quality.monitor import DataQualityMonitor
from algo5.data.feature_store.store import FeatureStore
from algo5.data.feature_store.cache import set_cache_root

def run():
    st.subheader("Data Quality & Feature Store")

    # Demo DF veya session'dan
    df = st.session_state.get("data")
    if df is None:
        df = demo_ohlcv(periods=120)
        st.info("Demo dataframe kullanılıyor. (st.session_state['data'] bulunamadı)")

    # Cache kökü (opsiyonel)
    cache_root = os.getenv("ALGO5_CACHE_ROOT")
    if cache_root:
        set_cache_root(cache_root)

    # --- Buttons (unique keys + new width API)
    cols = st.columns(2)
    with cols[0]:
        do_check = st.button("Check Quality", key="btn_check_quality")
    with cols[1]:
        do_build = st.button("Build Cache", key="btn_build_cache")    # --- Actions
    if do_check:
        rep = DataQualityMonitor().run(df)
        st.write("**Quality Report**")
        st.json(rep, expanded=False)

    if do_build:
        store = FeatureStore()  # default namespace
        path = store.save(("raw", "demo"), df, overwrite=True)  # ensures parents=True
        st.success(f"Cached ➜ {path}")

    st.write("**Preview**")
    st.dataframe(df, height=360, width="stretch")
