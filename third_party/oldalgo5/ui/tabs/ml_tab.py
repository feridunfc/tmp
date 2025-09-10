import streamlit as st
import pandas as pd
from core.services.model_manager import ModelManager
from strategies.ml_models.random_forest_strategy import RandomForestStrategy
from strategies.ml_models.logistic_regression_strategy import LogisticRegressionStrategy

def run(state):
    st.header("🤖 ML Training", anchor=False)
    if 'model_manager' not in state:
        state['model_manager'] = ModelManager()
    mm: ModelManager = state['model_manager']

    # Choose model type
    mdl_name = st.selectbox("Model Type", ["RandomForest", "LogisticRegression"], key="ml_mtype")
    model_id = st.text_input("Model ID", value=f"{mdl_name.lower()}_model", key="ml_mid")

    # Hyperparams
    if mdl_name == "RandomForest":
        n_estimators = st.number_input("n_estimators", 50, 1000, 200, 50, key="ml_rf_ne")
        max_depth = st.number_input("max_depth", 3, 50, 10, 1, key="ml_rf_md")
        params = {"n_estimators": int(n_estimators), "max_depth": int(max_depth)}
        ctor = lambda: RandomForestStrategy(strategy_id=model_id, **params)
    else:
        C = st.number_input("C", 0.01, 10.0, 1.0, 0.01, key="ml_lr_c")
        max_iter = st.number_input("max_iter", 100, 5000, 1000, 100, key="ml_lr_mi")
        params = {"C": float(C), "max_iter": int(max_iter)}
        ctor = lambda: LogisticRegressionStrategy(strategy_id=model_id, **params)

    up = st.file_uploader("Training CSV (columns: Date index, Close, ...)", type=["csv"], key="ml_csv")
    if up and st.button("Train & Save", key="ml_train_btn"):
        df = pd.read_csv(up)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']); df.set_index('Date', inplace=True)
        model = ctor()
        met = mm.train(model_id, model, df)
        st.success("Trained & saved.")
        st.json(met)

    st.subheader("Saved Models")
    st.dataframe(pd.DataFrame(mm.list()), width='stretch', key="ml_list")
