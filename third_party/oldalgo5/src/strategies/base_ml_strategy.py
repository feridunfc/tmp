from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
import pandas as pd, numpy as np
from sklearn.base import BaseEstimator
import joblib
from datetime import datetime

class BaseMLStrategy(ABC):
    def __init__(self, strategy_id: str = "ml_strategy", **kwargs):
        self.strategy_id = strategy_id
        self.model: BaseEstimator | None = None
        self.is_trained: bool = False
        self.training_metrics: Dict[str, float] = {}
        self.feature_columns: List[str] = []
        self.target_column: str = 'target'
        self.params: Dict[str, Any] = dict(kwargs)
        self.metadata = {
            'strategy_type': 'ml',
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'last_trained': None,
            'version': '1.0'
        }

    @staticmethod
    def param_schema() -> List[Any]:
        from src.strategies.registry import Field
        return [
            Field(name="threshold", type="float", default=0.5, low=0.0, high=1.0, step=0.01),
            Field(name="neutral_band", type="float", default=0.1, low=0.0, high=0.5, step=0.01),
        ]

    @abstractmethod
    def create_model(self, **params) -> BaseEstimator: ...

    @abstractmethod
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]: ...

    def fit(self, df: pd.DataFrame, **fit_params) -> Dict[str, float]:
        X, y = self.prepare_features(df)
        self.feature_columns = list(X.columns)
        self.model = self.create_model(**self.params)
        self.model.fit(X, y, **fit_params)
        self.training_metrics = self._calc_train_metrics(X, y)
        self.is_trained = True
        self.metadata['last_trained'] = datetime.now().isoformat(timespec='seconds')
        return self.training_metrics

    def _prob_from_estimator(self, X: pd.DataFrame) -> np.ndarray:
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)[:, 1]
        if hasattr(self.model, 'decision_function'):
            z = self.model.decision_function(X)
            return 1.0 / (1.0 + np.exp(-z))
        return self.model.predict(X).astype(float)

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model is not trained; call fit() first.")
        X, _ = self.prepare_features(df)
        return self._prob_from_estimator(X)

    def predict_proba_from_X(self, X: pd.DataFrame) -> np.ndarray:
        return self._prob_from_estimator(X)

    def generate_signals(self, df: pd.DataFrame, *, threshold: float = 0.5, neutral_band: float = 0.1) -> pd.Series:
        """Her durumda df.index ile aynı uzunlukta bir seri döndür."""
        p = self.predict_proba(df)
        hi = threshold + neutral_band/2.0
        lo = threshold - neutral_band/2.0
        sig = np.where(p >= hi, 1.0, np.where(p <= lo, -1.0, 0.0))

        # Uzunluk uyumsuzluklarına karşı güvenlik: baştan 0'larla doldur
        n_df = len(df)
        n_sig = len(sig)
        if n_sig < n_df:
            pad = n_df - n_sig
            sig = np.concatenate([np.zeros(pad, dtype=float), sig])
        elif n_sig > n_df:
            sig = sig[-n_df:]

        return pd.Series(sig, index=df.index, name='signal')

    def _calc_train_metrics(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        proba = self.predict_proba_from_X(X)
        pred = (proba >= 0.5).astype(int)
        out = {
            'accuracy': float(accuracy_score(y, pred)),
            'precision': float(precision_score(y, pred, zero_division=0)),
            'recall': float(recall_score(y, pred, zero_division=0)),
            'f1': float(f1_score(y, pred, zero_division=0)),
        }
        try: out['roc_auc'] = float(roc_auc_score(y, proba))
        except Exception: out['roc_auc'] = float('nan')
        return out

    def save_model(self, path: str) -> None:
        joblib.dump({
            'model': self.model,
            'metadata': self.metadata,
            'training_metrics': self.training_metrics,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'params': self.params,
        }, path)

    def load_model(self, path: str) -> None:
        obj = joblib.load(path)
        self.model = obj['model']
        self.metadata = obj.get('metadata', self.metadata)
        self.training_metrics = obj.get('training_metrics', {})
        self.feature_columns = obj.get('feature_columns', [])
        self.target_column = obj.get('target_column', 'target')
        self.params = obj.get('params', {})
        self.is_trained = True
