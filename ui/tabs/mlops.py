
import streamlit as st, time
from algo5.mlops.registry import list_models, ModelMeta, register
from algo5.mlops.drift import features_psi
import pandas as pd

def run():
    st.subheader("Model Registry")
    if st.button("Register dummy", key="mlops_reg1"):
        register(ModelMeta("toy", "1", "models/toy.pkl", "deadbeef", time.time()))
    st.json(list_models())

    st.subheader("Drift (PSI)")
    ref = pd.DataFrame({"x": [0,1,1,2,2,3,3], "y":[1,1,2,2,3,3,4]})
    cur = pd.DataFrame({"x": [3,2,1,1,0,0,0], "y":[4,3,3,2,2,1,1]})
    st.write(features_psi(ref, cur))
