from __future__ import annotations
from typing import Protocol
import pandas as pd
import numpy as np

class BaseEstimator(Protocol):
    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "BaseEstimator": ...
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...
