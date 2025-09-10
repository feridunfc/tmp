from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class AnomalyConfig:
    method: str = "zscore"   # hafif rolling z-score
    window: int = 24
    threshold: float = 3.0   # |z| > threshold -> skor ~1

class SimpleAnomalyDetector:
    """
    Bağımsız, hafif anomaly_score hesaplayıcı.
    Dönüş: [0,1] arası skor (1 = yüksek anomali)
    """
    def __init__(self, cfg: AnomalyConfig = AnomalyConfig()):
        self.cfg = cfg

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        rets = close.pct_change().fillna(0.0).abs()
        w = int(max(3, self.cfg.window))
        mu = rets.rolling(w, min_periods=1).mean()
        sd = rets.rolling(w, min_periods=1).std(ddof=0).replace(0, np.nan).fillna(1e-8)
        z = (rets - mu) / sd
        th = float(max(0.1, self.cfg.threshold))
        raw = (z.abs() / th).clip(0.0, 1.0)
        return raw.reindex(df.index).fillna(0.0)
