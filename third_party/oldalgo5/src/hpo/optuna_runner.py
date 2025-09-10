from typing import Callable, Dict, Any
import optuna

def run_hpo(objective_builder: Callable[[optuna.Trial], Callable[[], float]], n_trials: int = 20):
    """objective_builder: trial -> objective() returning float (maximize)"""
    study = optuna.create_study(direction="maximize")
    def _obj(trial: optuna.Trial):
        fn = objective_builder(trial)
        return fn()
    study.optimize(_obj, n_trials=n_trials)
    return study
