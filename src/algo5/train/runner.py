from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from algo5.train.datasets import make_supervised_ohlcv
from algo5.models.mean_thresh import MeanThreshClassifier

@dataclass
class TrainResult:
    acc: float
    n_train: int
    n_val: int

def train_eval_simple(df: pd.DataFrame, params: dict | None = None, *, train_frac: float = 0.7) -> TrainResult:
    params = params or {}
    X, y = make_supervised_ohlcv(df)
    n = len(X)
    n_train = max(1, int(n * train_frac))
    model = MeanThreshClassifier(window=int(params.get("window", 5)),
                                 threshold=float(params.get("threshold", 0.0)))
    model.fit(X.iloc[:n_train], y[:n_train])
    y_pred = model.predict(X.iloc[n_train:])
    y_true = y[n_train:]
    if len(y_true) == 0:
        return TrainResult(acc=float("nan"), n_train=n_train, n_val=0)
    acc = float((y_pred == y_true).mean())
    return TrainResult(acc=acc, n_train=n_train, n_val=len(y_true))
