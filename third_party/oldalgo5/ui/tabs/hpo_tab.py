
import streamlit as st
from src.strategies.registry import get_registry
from src.hpo.optuna_hpo import optimize
from src.persist.db import save_run

def run(state):
    st.header("🔎 HPO (Optuna + Walk-Forward)", anchor=False)
    if "data" not in state:
        st.warning("Önce Data.")
        return
    df = state["data"]
    REG, ORDER = get_registry()
    keys = [k for k,_ in ORDER]
    name = st.selectbox("Strategy", keys, key="hpo_strat")
    trials = st.number_input("Trials", 5, 200, 25, 1, key="hpo_trials")
    folds = st.number_input("Folds", 3, 10, 5, 1, key="hpo_folds")
    commission = float(state.get("commission_bps",5.0))/10000.0
    slippage = float(state.get("slippage_bps",10.0))/10000.0
    capital = float(state.get("capital",100000.0))
    storage = st.text_input("Optuna storage URL (opsiyonel)", value="", key="hpo_store")
    if st.button("Run Optuna HPO", key="hpo_run"):
        study = optimize(name, df, n_trials=int(trials), folds=int(folds),
                         commission=commission, slippage=slippage, capital=capital,
                         storage_url=(storage or None))
        st.success(f"Best value (Sharpe): {study.best_value:.4f}")
        st.json(study.best_params)
        run_id = save_run("hpo", name, symbol="*", params=study.best_params, metrics={"Sharpe": float(study.best_value)})
        st.caption(f"Saved best params as run_id {run_id}")
