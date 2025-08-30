import streamlit as st
import pandas as pd
from algo5.data.loader import demo_ohlcv
from algo5.train.runner import train_eval_simple
from algo5.hpo.space import default_space
from algo5.hpo.runner import grid_search

def run():
    st.subheader("Train & HPO")
    df = demo_ohlcv(240)
    window = st.slider("Window", 2, 20, 5, 1, key="w4_window")
    threshold = st.number_input("Threshold", value=0.0, step=0.0005, format="%.6f", key="w4_thresh")
    if st.button("Train simple", key="btn_train_simple"):
        res = train_eval_simple(df, {"window": window, "threshold": float(threshold)})
        st.write(f"Acc: {res.acc:.3f}  |  train={res.n_train}  val={res.n_val}")
    if st.button("Run Grid Search", key="btn_grid"):
        space = default_space()
        table, best = grid_search(df, space, lambda d, p: train_eval_simple(d, p))
        st.write("Best params:", best)
        st.dataframe(table.head(10))
