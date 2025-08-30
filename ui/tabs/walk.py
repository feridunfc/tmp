import streamlit as st
from algo5.data.loader import demo_ohlcv
from algo5.engine.backtest.walkforward import WFConfig, walk_forward
from algo5.train.runner import train_eval_simple

def run():
    st.subheader("Walk-Forward")
    df = demo_ohlcv(300)
    n_splits = st.slider("Splits", 2, 8, 3, 1, key="w4_splits")
    train_frac = st.slider("Train fraction", 0.5, 0.9, 0.7, 0.05, key="w4_trainfrac")
    params = {"window": 5, "threshold": 0.0}
    if st.button("Run Walk-Forward", key="btn_wf"):
        out = walk_forward(df, lambda d, p: train_eval_simple(d, p, train_frac=train_frac),
                           params, WFConfig(n_splits=n_splits, train_frac=train_frac))
        st.write(out)
