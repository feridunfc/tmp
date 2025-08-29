
from __future__ import annotations
import streamlit as st
import pandas as pd

from algo5.data.loader import demo_ohlcv
from algo5.data.quality.monitor import DataQualityMonitor
from algo5.data.feature_store.store import FeatureStore
from algo5.data.feature_store.cache import get_cache_root, ensure_dir

def run() -> None:
    st.subheader("Data Quality & Cache")

    if "data" not in st.session_state:
        st.session_state["data"] = demo_ohlcv(periods=120)
    df: pd.DataFrame = st.session_state["data"]

    st.dataframe(df.head(15), use_container_width=True)
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Check Quality", use_container_width=True):
            rep = DataQualityMonitor().run(df)
            st.success("Quality OK" if rep.get("ok") else "Quality issues")
            st.json(rep)

    with col2:
        if st.button("Build Cache", use_container_width=True):
            # make sure root/ns exists (Windows-safe)
            ensure_dir(get_cache_root() / "raw")
            store = FeatureStore()
            path = store.save(("raw", "demo_ohlcv"), df, overwrite=True)
            st.success(f"Cached: {path}")
