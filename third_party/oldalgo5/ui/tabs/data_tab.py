import streamlit as st
from ui.services import sdk
from ui.components.common import notify


def run(state):
    st.header("📊 Data", anchor=False)

    if st.button("Load Data", key="data_load_btn"):
        df = sdk.load_data(state["symbols"], interval=state["interval"], start=state.get("start_date"),
                           end=state.get("end_date"))
        sdk.validate_data(df)
        state["data"] = df
        notify(f"Loaded {len(df):,} rows for {df['Symbol'].nunique()} symbols.", "success")

        # Düzeltme: width parametresi kaldırıldı veya None yapıldı
        st.dataframe(df.groupby("Symbol").tail(5), key="data_tail")

    if "data" in state:
        # Düzeltme: width parametresi kaldırıldı veya None yapıldı
        st.dataframe(state["data"].head(10), key="data_head")