
import streamlit as st, numpy as np, pandas as pd
from algo5.explain.shap_adapter import explain as shap_explain

class Lin:
    def __init__(self, w): self.w = np.asarray(w)
    def predict(self, X): return np.asarray(X) @ self.w

def run():
    st.subheader("Explainability")
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(200,3)), columns=["x1","x2","x3"])
    y = 2*X["x1"] - 1*X["x2"] + rng.normal(0,0.1, size=200)
    model = Lin([2.0, -1.0, 0.0])
    res = shap_explain(model, X, y)
    st.write(f"method: {res['method']}")
    st.bar_chart(res["values"])
