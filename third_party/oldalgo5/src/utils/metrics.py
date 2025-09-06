import numpy as np
import pandas as pd

def _max_drawdown_from_equity(equity: pd.Series) -> float:
    if equity is None or len(equity) == 0:
        return 0.0
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min()) * -1.0  # positive number

def calculate_metrics(equity: pd.Series, returns: pd.Series, ann_factor: int = 252) -> dict:
    equity = equity.astype(float)
    returns = returns.astype(float)
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0) if len(equity) > 1 else 0.0
    sharpe = 0.0
    std = returns.std()
    if std and std > 0:
        sharpe = float(returns.mean() / std * np.sqrt(ann_factor))
    max_dd = _max_drawdown_from_equity(equity)  # positive number like 0.2
    calmar = 0.0
    if max_dd and max_dd > 0:
        calmar = float(total_return / max_dd)
    return {
        "total_return": total_return,
        "sharpe": sharpe,
        "max_drawdown": max_dd,   # positive drawdown fraction
        "calmar": calmar,
    }
