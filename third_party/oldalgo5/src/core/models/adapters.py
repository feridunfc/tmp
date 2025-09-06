from __future__ import annotations
from typing import Any, Optional

# Base adapter
class BaseModelAdapter:
    def fit(self, X, y):
        return self

    def predict(self, X):
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ----- RandomForest (sklearn)
try:
    from sklearn.ensemble import RandomForestClassifier
    _SKLEARN_OK = True
except Exception:  # pragma: no cover - optional
    RandomForestClassifier = None
    _SKLEARN_OK = False

class RandomForestAdapter(BaseModelAdapter):
    def __init__(self, n_estimators: int = 200, random_state: int = 42):
        if not _SKLEARN_OK:
            raise ImportError("scikit-learn is required for RandomForestAdapter")
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)


# ----- LightGBM
try:
    import lightgbm as lgb
    _LGBM_OK = True
except Exception:  # pragma: no cover - optional
    lgb = None
    _LGBM_OK = False

class LightGBMAdapter(BaseModelAdapter):
    def __init__(self, params: Optional[dict] = None, num_boost_round: int = 100):
        if not _LGBM_OK:
            raise ImportError("lightgbm is required for LightGBMAdapter")
        self.params = params or {"objective": "binary", "learning_rate": 0.05}
        self.num_boost_round = num_boost_round
        self._booster = None

    def fit(self, X, y):
        dtrain = lgb.Dataset(X, label=y)
        self._booster = lgb.train(self.params, dtrain, num_boost_round=self.num_boost_round)
        return self

    def predict(self, X):
        if self._booster is None:
            raise RuntimeError("Model not fitted")
        return (self._booster.predict(X) > 0.5).astype(int)


# ----- XGBoost
try:
    import xgboost as xgb
    _XGB_OK = True
except Exception:  # pragma: no cover - optional
    xgb = None
    _XGB_OK = False

class XGBoostAdapter(BaseModelAdapter):
    def __init__(self, params: Optional[dict] = None, num_boost_round: int = 100):
        if not _XGB_OK:
            raise ImportError("xgboost is required for XGBoostAdapter")
        self.params = params or {"objective": "binary:logistic", "eta": 0.05}
        self.num_boost_round = num_boost_round
        self._booster = None

    def fit(self, X, y):
        dtrain = xgb.DMatrix(X, label=y)
        self._booster = xgb.train(self.params, dtrain, num_boost_round=self.num_boost_round)
        return self

    def predict(self, X):
        if self._booster is None:
            raise RuntimeError("Model not fitted")
        dtest = xgb.DMatrix(X)
        return (self._booster.predict(dtest) > 0.5).astype(int)


# ----- Logistic Regression (sklearn)
try:
    from sklearn.linear_model import LogisticRegression
    _LOGREG_OK = True
except Exception:  # pragma: no cover - optional
    LogisticRegression = None
    _LOGREG_OK = False

class LogisticRegressionAdapter(BaseModelAdapter):
    def __init__(self, max_iter: int = 200):
        if not _LOGREG_OK:
            raise ImportError("scikit-learn is required for LogisticRegressionAdapter")
        self.model = LogisticRegression(max_iter=max_iter)

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)
