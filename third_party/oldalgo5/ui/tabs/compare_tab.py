import streamlit as st
import pandas as pd
from persist.db import list_runs, query_runs, DEFAULT_DB

def run(state):
    st.header("📊 Compare", anchor=False)
    db_path = st.text_input("DB path", value=DEFAULT_DB, key="cmp_db")
    # simple filters
    col1, col2 = st.columns(2)
    with col1:
        f_strategy = st.text_input("Strategy filter", value="", key="cmp_strat_f")
    with col2:
        f_symbol = st.text_input("Symbol filter", value="", key="cmp_sym_f")

    if st.button("Load", key="cmp_load"):
        if f_strategy and f_symbol:
            df = query_runs(strategy=f_strategy, symbol=f_symbol, db_path=db_path)
        elif f_strategy:
            df = query_runs(strategy=f_strategy, db_path=db_path)
        elif f_symbol:
            df = query_runs(symbol=f_symbol, db_path=db_path)
        else:
            df = list_runs(db_path=db_path)
        if df.empty:
            st.info("No runs found for current filters.")
        else:
            st.dataframe(df, width='stretch', key="cmp_tbl")
