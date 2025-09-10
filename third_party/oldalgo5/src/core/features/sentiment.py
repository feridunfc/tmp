from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class SentimentConfig:
    method: str = "price_proxy"   # placeholder: fiyat tabanlı türetilmiş sentiment
    window: int = 24
    smooth: int = 12

class SentimentEngine:
    """
    Hafif, bağımsız sentiment tahmini:
    - fiyat getirilerinden türetilmiş, -1..+1 arası normalize edilmiş 'sentiment_score'
    - gerçek API'ler yoksa sistem offline da çalışsın diye
    """
    def __init__(self, cfg: SentimentConfig = SentimentConfig()):
        self.cfg = cfg

    def compute(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        rets = close.pct_change().fillna(0.0)
        # zscore benzeri normalizasyon
        w = int(max(3, self.cfg.window))
        mu = rets.rolling(w, min_periods=1).mean()
        sd = rets.rolling(w, min_periods=1).std(ddof=0).replace(0, np.nan).fillna(1e-8)
        z = (rets - mu) / sd
        # yumuşatma
        s = int(max(1, self.cfg.smooth))
        sm = z.ewm(span=s, adjust=False).mean()
        score = np.tanh(sm)  # -1..+1
        return score.reindex(df.index).fillna(0.0).clip(-1.0, 1.0)
