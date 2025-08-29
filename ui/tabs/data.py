from __future__ import annotations
import streamlit as st
from algo5.data.loader import demo_ohlcv
from algo5.data.quality.monitor import DataQualityMonitor
from algo5.data.feature_store.store import FeatureStore

def run():
    st.subheader("Data Quality & Cache")
    # Source data (demo if user didn't upload yet)
    df = demo_ohlcv(periods=120)
    st.dataframe(df.head(10), width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Check Quality"):
            report = DataQualityMonitor().run(df)
            st.success("Quality OK" if report.get("ok") else "Quality issues found")
            st.json(report)
    with col2:
        if st.button("Build Cache"):
            store = FeatureStore()  # default .cache/features
            path = store.save("raw/demo_ohlcv", df, overwrite=True)
            st.success(f"Cached to: {path}")
