
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Protocol

class _Predictor(Protocol):
    def predict(self, X: np.ndarray | pd.DataFrame) -> np.ndarray: ...

def permutation_importance(model: _Predictor, X: pd.DataFrame, y: np.ndarray | pd.Series,
                           metric: str = "mse", n_repeats: int = 5, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    base_pred = model.predict(X)
    if metric == "mse":
        def loss(y_true, y_pred): return float(np.mean((y_true - y_pred) ** 2))
    else:
        def loss(y_true, y_pred): return float(np.mean(y_true != (y_pred > 0.5)))
    base = loss(y, base_pred)
    scores = {}
    for col in X.columns:
        diffs = []
        for _ in range(n_repeats):
            Xp = X.copy()
            Xp[col] = rng.permutation(Xp[col].to_numpy())
            diffs.append(loss(y, model.predict(Xp)) - base)
        scores[col] = float(np.mean(diffs))
    s = pd.Series(scores).sort_values(ascending=False)
    s.name = "permutation_importance"
    return s
