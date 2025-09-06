import streamlit as st
from ui.services import ml
def run(state):
    st.header("🧠 Train", anchor=False)
    if "data" not in state: st.warning("Önce Data."); return
    df=state["data"]
    algo=st.selectbox("Algorithm", ["rf","lr"], format_func=lambda x: {"rf":"RandomForest","lr":"LogReg"}[x], key="tr_algo")
    if algo=="rf":
        n = st.number_input("n_estimators", 50, 1000, 200, 50, key="tr_n"); d = st.number_input("max_depth", 2, 20, 5, 1, key="tr_d"); params={"n_estimators":int(n),"max_depth":int(d)}
    else: params = {}
    horizon=st.number_input("Horizon", 1, 20, 1, 1, key="tr_hor"); thr=st.number_input("Label threshold", 0.0, 0.02, 0.0, 0.001, key="tr_thr")
    name=st.text_input("Save as", "latest.pkl", key="tr_name")
    if st.button("Train & Save", key="tr_btn"):
        model, scores, feats = ml.train_model(df, algo=algo, params=params, horizon=int(horizon), threshold=float(thr))
        path = ml.save_model(model, feats, name=name); st.success(f"Saved {path.name} | AUC={scores['auc']:.3f} ACC={scores['acc']:.3f}")
