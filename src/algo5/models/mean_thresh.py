from __future__ import annotations
import numpy as np
import pandas as pd

class MeanThreshClassifier:
    """Çok hafif bir sınıflandırıcı.
    X içinde en az 'ret1' kolonu bekler.
    Predict: rolling mean('ret1') > threshold => 1 (long), aksi 0 (flat)
    """
    def __init__(self, window: int = 5, threshold: float = 0.0):
        self.window = int(window)
        self.threshold = float(threshold)
        self.fitted_ = False

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        # Model parametreleri sabit, sadece 'fit edildi' işareti
        if "ret1" not in X.columns:
            raise ValueError("X must contain 'ret1' column")
        self.fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if "ret1" not in X.columns:
            raise ValueError("X must contain 'ret1' column")
        rm = X["ret1"].rolling(self.window).mean().bfill()
        pred = (rm > self.threshold).astype(int).to_numpy()
        return pred
