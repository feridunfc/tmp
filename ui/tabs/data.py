import os
import streamlit as st
from algo5.data.loader import demo_ohlcv
from algo5.data.quality.monitor import DataQualityMonitor
from algo5.data.feature_store.store import FeatureStore
from algo5.data.feature_store.cache import set_cache_root


def run():
    st.header("Data Quality & Cache")
    df = demo_ohlcv(periods=120)
    st.dataframe(df.head(), width="stretch")
    if st.button("Check Quality"):
        st.json(DataQualityMonitor().run(df))
    if st.button("Build Cache"):
        root = set_cache_root(os.getenv("ALGO5_CACHE_ROOT", ".cache/features"))
        p = FeatureStore(root=root).save(("raw", "demo"), df, overwrite=True)
        st.success(f"Saved to {p}")
