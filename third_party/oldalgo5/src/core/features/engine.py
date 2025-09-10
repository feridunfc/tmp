from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd

from .sentiment import SentimentEngine, SentimentConfig
from core.anomaly.detector import SimpleAnomalyDetector, AnomalyConfig

@dataclass
class FeatureConfig:
    use_sentiment: bool = True
    use_anomaly: bool = True
    sentiment_kwargs: dict = field(default_factory=dict)
    anomaly_kwargs: dict = field(default_factory=dict)

class FeatureEngineerEngine:
    """
    İsteğe bağlı feature üretimi:
    - sentiment_score
    - anomaly_score
    """
    def __init__(self, cfg: FeatureConfig = FeatureConfig()):
        self.cfg = cfg

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if self.cfg.use_sentiment:
            scfg = SentimentConfig(**(self.cfg.sentiment_kwargs or {}))
            sengine = SentimentEngine(scfg)
            out["sentiment_score"] = sengine.compute(out)
        if self.cfg.use_anomaly:
            acfg = AnomalyConfig(**(self.cfg.anomaly_kwargs or {}))
            ad = SimpleAnomalyDetector(acfg)
            out["anomaly_score"] = ad.compute(out)
        return out
