# src/algo2/anomaly/iforest_detector.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import IsolationForest
    _HAVE_SK = True
except Exception:
    _HAVE_SK = False

@dataclass
class IForestParams:
    contamination: float = 0.05
    random_state: int = 42

class IsolationForestDetector:
    def __init__(self, params: IForestParams = IForestParams()):
        self.params = params

    def detect(self, df: pd.DataFrame) -> pd.Series:
        if not _HAVE_SK:
            return pd.Series(False, index=df.index)
        clf = IsolationForest(contamination=self.params.contamination, random_state=self.params.random_state)
        y = clf.fit_predict(df.fillna(method="ffill").fillna(0.0).values)
        return pd.Series(y == -1, index=df.index)
