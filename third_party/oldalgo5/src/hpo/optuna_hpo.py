
import optuna
import pandas as pd
from typing import Dict, Any
from strategies.registry import get_registry
from core.backtest.walkforward import run_walkforward
from core.backtest.simple import run_backtest_from_signals

def _space_from_schema(schema: Dict[str, Any], trial: optuna.Trial) -> Dict[str, Any]:
    params = {}
    for k, s in schema.items():
        t = s.get("type","int")
        if t == "int":
            params[k] = trial.suggest_int(k, int(s.get("min",0)), int(s.get("max",10)), step=int(s.get("step",1)))
        elif t == "float":
            params[k] = trial.suggest_float(k, float(s.get("min",0.0)), float(s.get("max",1.0)))
        else:
            params[k] = s.get("default","")
    return params

def optimize(strategy_name: str, df: pd.DataFrame, *, n_trials: int = 25, folds: int = 5, commission=0.0005, slippage=0.0005, capital=100000.0, storage_url: str | None = None):
    REG, _ = get_registry()
    assert strategy_name in REG, f"strategy not found: {strategy_name}"
    schema = REG[strategy_name]["schema"]

    def objective(trial: optuna.Trial) -> float:
        params = _space_from_schema(schema, trial)
        grid = {k:[v] for k,v in params.items()}
        Strat = type("W",(object,),{"_param_schema":schema,"generate_signals":staticmethod(REG[strategy_name]["gen"])})
        res = run_walkforward(
            Strat, df, grid, n_splits=int(folds),
            backtest_fn=lambda d,s,**kw: run_backtest_from_signals(d,s, commission=commission, slippage=slippage, capital=capital),
            commission=commission, slippage=slippage, capital=capital
        )
        if res is None or res.empty:
            return -1e9
        return float(res["Sharpe"].mean())

    study = optuna.create_study(direction="maximize", study_name=f"hpo_{strategy_name}", storage=storage_url, load_if_exists=True)
    study.optimize(objective, n_trials=int(n_trials))
    return study
