# src/strategies/ml_models/random_forest_strategy.py
from __future__ import annotations
import logging
from typing import Any, List
import numpy as np
import pandas as pd

from strategies.base_ml_strategy import BaseMLStrategy
from strategies.registry import Field

logger = logging.getLogger(__name__)

class RandomForestStrategy(BaseMLStrategy):
    family = "ai"
    name = "Random Forest (ML)"
    values = [-1, 0, 1]
    is_strategy = True

    @staticmethod
    def param_schema() -> List[Field]:
        return [
            Field(name="horizon", type="int",   default=1,   low=1,  high=20),
            Field(name="threshold", type="float", default=0.5, low=0.0, high=1.0, step=0.01),
            Field(name="neutral_band", type="float", default=0.1, low=0.0, high=0.5, step=0.01),
            Field(name="seed", type="int", default=42, low=0, high=10000),
            Field(name="n_estimators", type="int", default=200, low=50, high=1000, step=10),
            Field(name="max_depth", type="int", default=8, low=2, high=50, step=1),
            Field(name="max_features", type="str", default="sqrt", options=["sqrt", "log2", "auto"]),
            Field(name="min_samples_leaf", type="int", default=1, low=1, high=50, step=1),
        ]

    def create_model(self, **params: Any):
        try:
            from sklearn.ensemble import RandomForestClassifier
        except Exception as e:
            logger.warning("scikit-learn import edilemedi: %s", e)
            raise

        return RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 200)),
            max_depth=int(params.get("max_depth", 8)),
            max_features=params.get("max_features", "sqrt"),
            min_samples_leaf=int(params.get("min_samples_leaf", 1)),
            random_state=int(params.get("seed", 42)),
            n_jobs=-1,
        )

    # Basit bir örnek feature/target; projendeki gerçek featurizer'a bağlayabilirsin
    def prepare_features(self, df: pd.DataFrame):
        close = df["Close"] if "Close" in df.columns else df["close"]
        ret = close.pct_change().fillna(0.0)
        X = pd.DataFrame({
            "ret_1": ret.shift(1),
            "ret_2": ret.shift(2),
            "ret_3": ret.shift(3),
            "vol_5": ret.rolling(5).std(),
        }).dropna()
        # horizon kadar ileri getiriyi sınıflandır (up/down)
        horizon = int(self.params.get("horizon", 1))
        fut = close.pct_change(horizon).shift(-horizon).reindex(X.index).fillna(0.0)
        y = (fut > 0).astype(int)
        return X, y

# (opsiyonel) modül seviye kısayollar:
def param_schema(): return RandomForestStrategy.param_schema()
